"""XML Lifecycle Validator with Relax NG and Schematron support."""

import hashlib
import io
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from lxml import etree

from xml_lib.guardrails import GuardrailEngine
from xml_lib.sanitize import MathPolicy, Sanitizer
from xml_lib.storage import ContentStore
from xml_lib.telemetry import TelemetrySink
from xml_lib.types import ValidationError


class ProgressReporter:
    """Progress reporter for large XML file validation."""

    SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, enabled: bool = True, tty_only: bool = True):
        """Initialize progress reporter.

        Args:
            enabled: Enable progress reporting
            tty_only: Only show progress if stdout is a TTY
        """
        self.enabled = enabled and (not tty_only or sys.stdout.isatty())
        self.frame_index = 0
        self.current_message = ""

    def update(self, message: str, done: bool = False) -> None:
        """Update progress message.

        Args:
            message: Progress message to display
            done: Whether the operation is complete
        """
        if not self.enabled:
            return

        if done:
            # Clear the line and print completion
            sys.stdout.write("\r\033[K")  # Clear line
            sys.stdout.write(f"✓ {message}\n")
            sys.stdout.flush()
        else:
            # Show spinner
            spinner = self.SPINNER_FRAMES[self.frame_index % len(self.SPINNER_FRAMES)]
            sys.stdout.write(f"\r{spinner} {message}")
            sys.stdout.flush()
            self.frame_index += 1

    def clear(self) -> None:
        """Clear the current progress line."""
        if self.enabled:
            sys.stdout.write("\r\033[K")  # Clear line
            sys.stdout.flush()


@dataclass
class ValidationResult:
    """Result of validation."""

    is_valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)
    validated_files: list[str] = field(default_factory=list)
    checksums: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    used_streaming: bool = False  # Whether streaming validation was used


class Validator:
    """Validates XML documents against lifecycle schemas and guardrails."""

    def __init__(
        self,
        schemas_dir: Path,
        guardrails_dir: Path,
        telemetry: TelemetrySink | None = None,
        math_policy: MathPolicy = MathPolicy.SANITIZE,
        use_streaming: bool = False,
        streaming_threshold_bytes: int = 10 * 1024 * 1024,  # 10MB default
        show_progress: bool = False,
    ):
        """Initialize validator.

        Args:
            schemas_dir: Directory containing schema files
            guardrails_dir: Directory containing guardrail files
            telemetry: Optional telemetry sink
            math_policy: Policy for handling mathematical XML
            use_streaming: Enable streaming validation for large files
            streaming_threshold_bytes: File size threshold for streaming (default 10MB)
            show_progress: Show progress indicator for large files
        """
        self.schemas_dir = schemas_dir
        self.guardrails_dir = guardrails_dir
        self.telemetry = telemetry
        self.content_store = ContentStore(Path("store"))
        self.guardrail_engine = GuardrailEngine(guardrails_dir)
        self.math_policy = math_policy
        self._last_result: ValidationResult | None = None
        self.use_streaming = use_streaming
        self.streaming_threshold_bytes = streaming_threshold_bytes
        self.show_progress = show_progress

        # Load schemas
        self.relaxng_lifecycle = self._load_relaxng("lifecycle.rng")
        self.relaxng_guardrails = self._load_relaxng("guardrails.rng")
        self.schematron_lifecycle = self._load_schematron("lifecycle.sch")

    def _load_relaxng(self, filename: str) -> etree.RelaxNG | None:
        """Load a Relax NG schema."""
        schema_path = self.schemas_dir / filename
        if not schema_path.exists():
            return None

        try:
            doc = etree.parse(str(schema_path))
            return etree.RelaxNG(doc)
        except Exception as e:
            print(f"Warning: Failed to load Relax NG schema {filename}: {e}")
            return None

    def _load_schematron(self, filename: str) -> etree.Schematron | None:
        """Load a Schematron schema."""
        schema_path = self.schemas_dir / filename
        if not schema_path.exists():
            return None

        try:
            doc = etree.parse(str(schema_path))
            return etree.Schematron(doc)
        except Exception as e:
            print(f"Warning: Failed to load Schematron schema {filename}: {e}")
            return None

    def validate_project(
        self,
        project_path: Path,
        math_policy: MathPolicy | None = None,
    ) -> ValidationResult:
        """Validate all XML files in a project."""
        start_time = datetime.now()
        result = ValidationResult(is_valid=True)
        policy = math_policy or self.math_policy
        sanitizer = Sanitizer(Path("out")) if policy == MathPolicy.SANITIZE else None

        # Initialize progress reporter
        progress = ProgressReporter(enabled=self.show_progress) if self.show_progress else None

        # Find all XML files
        xml_files = list(project_path.rglob("*.xml"))

        if progress:
            progress.update(f"Found {len(xml_files)} XML files to validate")

        # Track IDs across all files for cross-file validation
        all_ids: set[str] = set()
        id_locations: dict[str, str] = {}

        for i, xml_file in enumerate(xml_files, 1):
            # Skip schema and guardrail files
            if "schema" in str(xml_file) or xml_file.parent.name == "guardrails":
                continue

            try:
                if progress:
                    progress.update(f"Validating {i}/{len(xml_files)}: {xml_file.name}")

                # Check if we should use streaming validation
                use_streaming_for_file = self._should_use_streaming(xml_file)

                # Parse XML with optional sanitization
                doc = None
                try:
                    if use_streaming_for_file:
                        doc = self._validate_streaming(xml_file, result, progress)
                        if doc is None:
                            continue  # Streaming validation failed, errors already added
                    else:
                        doc = etree.parse(str(xml_file))
                except etree.XMLSyntaxError as parse_error:
                    if policy == MathPolicy.ERROR:
                        raise
                    elif policy == MathPolicy.SKIP:
                        result.warnings.append(
                            ValidationError(
                                file=str(xml_file),
                                line=parse_error.lineno,
                                column=None,
                                message=f"Skipping: {parse_error}",
                                type="warning",
                                rule="xml-syntax",
                            )
                        )
                        continue
                    elif policy == MathPolicy.SANITIZE and sanitizer:
                        # Try sanitizing
                        sanitize_result = sanitizer.sanitize_for_parse(xml_file)
                        if sanitize_result.has_surrogates:
                            # Parse sanitized content
                            doc = etree.parse(io.BytesIO(sanitize_result.content))
                            # Write mapping
                            rel_path = xml_file.relative_to(project_path)
                            sanitizer.write_mapping(rel_path, sanitize_result.mappings)
                        else:
                            raise parse_error

                if doc is None:
                    continue

                # Calculate checksum
                content = xml_file.read_bytes()
                checksum = hashlib.sha256(content).hexdigest()
                result.checksums[str(xml_file)] = checksum

                # Store in content-addressed storage
                self.content_store.store(content, checksum)

                # Validate with Relax NG
                self._validate_relaxng(doc, xml_file, result)

                # Validate with Schematron
                self._validate_schematron(doc, xml_file, result)

                # Check for ID uniqueness across files
                self._check_cross_file_ids(doc, xml_file, all_ids, id_locations, result)

                # Validate temporal monotonicity
                self._validate_temporal_order(doc, xml_file, result)

                result.validated_files.append(str(xml_file))

            except etree.XMLSyntaxError as e:
                result.errors.append(
                    ValidationError(
                        file=str(xml_file),
                        line=e.lineno,
                        column=e.position[0] if hasattr(e, "position") else None,
                        message=str(e),
                        type="error",
                        rule="xml-syntax",
                    )
                )
                result.is_valid = False
            except Exception as e:
                result.errors.append(
                    ValidationError(
                        file=str(xml_file),
                        line=None,
                        column=None,
                        message=f"Unexpected error: {e}",
                        type="error",
                        rule="internal",
                    )
                )
                result.is_valid = False

        # Run guardrail checks
        guardrail_result = self.guardrail_engine.validate(project_path)
        result.errors.extend(guardrail_result.errors)
        result.warnings.extend(guardrail_result.warnings)

        if result.errors:
            result.is_valid = False

        # Run guardrail checks
        if progress:
            progress.update("Running guardrail checks")

        # Log telemetry
        duration = (datetime.now() - start_time).total_seconds()
        if self.telemetry:
            self.telemetry.log_validation(
                project=str(project_path),
                success=result.is_valid,
                duration=duration,
                file_count=len(result.validated_files),
                error_count=len(result.errors),
                warning_count=len(result.warnings),
            )

        # Complete progress
        if progress:
            status = "passed" if result.is_valid else "failed"
            progress.update(
                f"Validation {status}: {len(result.validated_files)} files, "
                f"{len(result.errors)} errors, {len(result.warnings)} warnings",
                done=True,
            )

        self._last_result = result

        return result

    def _validate_file(self, path: Path) -> None:
        """Validate a single XML file following the project validation flow."""
        start_time = datetime.now()
        policy = self.math_policy
        sanitizer = Sanitizer(Path("out")) if policy == MathPolicy.SANITIZE else None
        result = ValidationResult(is_valid=True)

        try:
            raw_content = path.read_bytes()
        except FileNotFoundError:
            raise

        try:
            try:
                doc = etree.parse(io.BytesIO(raw_content))
            except etree.XMLSyntaxError as parse_error:
                if policy == MathPolicy.ERROR:
                    raise
                if policy == MathPolicy.SKIP:
                    result.warnings.append(
                        ValidationError(
                            file=str(path),
                            line=parse_error.lineno,
                            column=None,
                            message=f"Skipping: {parse_error}",
                            type="warning",
                            rule="xml-syntax",
                        )
                    )
                    duration = (datetime.now() - start_time).total_seconds()
                    if self.telemetry:
                        self.telemetry.log_validation(
                            project=str(path),
                            success=True,
                            duration=duration,
                            file_count=0,
                            error_count=0,
                            warning_count=len(result.warnings),
                        )
                    self._last_result = result
                    return
                if policy == MathPolicy.SANITIZE and sanitizer:
                    sanitize_result = sanitizer.sanitize_for_parse(path, policy=self.math_policy)
                    if sanitize_result.has_surrogates:
                        doc = etree.parse(io.BytesIO(sanitize_result.content))
                        rel_path = Path(path.name)
                        sanitizer.write_mapping(rel_path, sanitize_result.mappings)
                    else:
                        raise
                else:
                    raise

            checksum = hashlib.sha256(raw_content).hexdigest()
            result.checksums[str(path)] = checksum
            self.content_store.store(raw_content, checksum)

            self._validate_relaxng(doc, path, result)
            self._validate_schematron(doc, path, result)
            self._check_cross_file_ids(doc, path, set(), {}, result)
            self._validate_temporal_order(doc, path, result)
            result.validated_files.append(str(path))

        except etree.XMLSyntaxError as error:
            result.errors.append(
                ValidationError(
                    file=str(path),
                    line=error.lineno,
                    column=error.position[0] if hasattr(error, "position") else None,
                    message=str(error),
                    type="error",
                    rule="xml-syntax",
                )
            )
        except Exception as error:
            result.errors.append(
                ValidationError(
                    file=str(path),
                    line=None,
                    column=None,
                    message=f"Unexpected error: {error}",
                    type="error",
                    rule="internal",
                )
            )

        guardrail_result = self.guardrail_engine.validate(path.parent)
        result.errors.extend(guardrail_result.errors)
        result.warnings.extend(guardrail_result.warnings)

        if result.errors:
            result.is_valid = False

        duration = (datetime.now() - start_time).total_seconds()
        if self.telemetry:
            self.telemetry.log_validation(
                project=str(path),
                success=result.is_valid,
                duration=duration,
                file_count=len(result.validated_files),
                error_count=len(result.errors),
                warning_count=len(result.warnings),
            )

        self._last_result = result

    def _validate_relaxng(
        self,
        doc: etree._ElementTree,
        xml_file: Path,
        result: ValidationResult,
    ) -> None:
        """Validate with Relax NG schema."""
        if not self.relaxng_lifecycle:
            return

        try:
            self.relaxng_lifecycle.assertValid(doc)
        except etree.DocumentInvalid:
            # Try guardrails schema if lifecycle fails
            if self.relaxng_guardrails:
                try:
                    self.relaxng_guardrails.assertValid(doc)
                    return  # Valid as guardrail
                except etree.DocumentInvalid:
                    pass  # Fall through to report original error

            for error in self.relaxng_lifecycle.error_log:
                result.errors.append(
                    ValidationError(
                        file=str(xml_file),
                        line=error.line,
                        column=error.column,
                        message=error.message,
                        type="error",
                        rule="relaxng",
                    )
                )
            result.is_valid = False

    def _validate_schematron(
        self,
        doc: etree._ElementTree,
        xml_file: Path,
        result: ValidationResult,
    ) -> None:
        """Validate with Schematron rules."""
        if not self.schematron_lifecycle:
            return

        try:
            self.schematron_lifecycle.assertValid(doc)
        except etree.DocumentInvalid:
            for error in self.schematron_lifecycle.error_log:
                error_type = "warning" if "warning" in error.message.lower() else "error"
                validation_error = ValidationError(
                    file=str(xml_file),
                    line=error.line,
                    column=error.column,
                    message=error.message,
                    type=error_type,
                    rule="schematron",
                )

                if error_type == "error":
                    result.errors.append(validation_error)
                    result.is_valid = False
                else:
                    result.warnings.append(validation_error)

    def _check_cross_file_ids(
        self,
        doc: etree._ElementTree,
        xml_file: Path,
        all_ids: set[str],
        id_locations: dict[str, str],
        result: ValidationResult,
    ) -> None:
        """Check for duplicate IDs across files."""
        root = doc.getroot()
        elements_with_ids = root.xpath("//*[@id]")

        for element in elements_with_ids:
            element_id = element.get("id")
            if element_id in all_ids:
                result.errors.append(
                    ValidationError(
                        file=str(xml_file),
                        line=element.sourceline,
                        column=None,
                        message=f"Duplicate ID '{element_id}' already defined in {id_locations[element_id]}",
                        type="error",
                        rule="cross-file-id",
                    )
                )
                result.is_valid = False
            else:
                all_ids.add(element_id)
                id_locations[element_id] = str(xml_file)

    def _validate_temporal_order(
        self,
        doc: etree._ElementTree,
        xml_file: Path,
        result: ValidationResult,
    ) -> None:
        """Validate temporal monotonicity of timestamps."""
        root = doc.getroot()
        if root.tag != "document":
            return

        phases = root.find("phases")
        if phases is None:
            return

        # Extract timestamps from phases
        timestamps: dict[str, datetime] = {}
        phase_order = ["begin", "start", "iteration", "end", "continuum"]

        for phase in phases.findall("phase"):
            phase_name = phase.get("name")
            timestamp_str = phase.get("timestamp")

            if timestamp_str:
                try:
                    timestamps[phase_name] = datetime.fromisoformat(
                        timestamp_str.replace("Z", "+00:00")
                    )
                except ValueError:
                    result.warnings.append(
                        ValidationError(
                            file=str(xml_file),
                            line=phase.sourceline,
                            column=None,
                            message=f"Invalid timestamp format in phase '{phase_name}': {timestamp_str}",
                            type="warning",
                            rule="temporal",
                        )
                    )

        # Check monotonicity
        prev_time = None
        prev_phase = None
        for phase_name in phase_order:
            if phase_name in timestamps:
                curr_time = timestamps[phase_name]
                if prev_time and curr_time < prev_time:
                    result.errors.append(
                        ValidationError(
                            file=str(xml_file),
                            line=None,
                            column=None,
                            message=f"Timestamp for phase '{phase_name}' ({curr_time}) precedes '{prev_phase}' ({prev_time})",
                            type="error",
                            rule="temporal-monotonicity",
                        )
                    )
                    result.is_valid = False
                prev_time = curr_time
                prev_phase = phase_name

    def _should_use_streaming(self, file_path: Path) -> bool:
        """Determine if streaming validation should be used for a file.

        Args:
            file_path: Path to the XML file

        Returns:
            True if streaming should be used
        """
        if not self.use_streaming:
            return False

        try:
            file_size = file_path.stat().st_size
            return file_size >= self.streaming_threshold_bytes
        except Exception:
            return False

    def _validate_streaming(
        self,
        file_path: Path,
        result: ValidationResult,
        progress: ProgressReporter | None = None,
    ) -> etree._ElementTree | None:
        """Validate XML file using streaming iterparse.

        This method provides basic well-formedness checking via iterparse.
        Schema validation still requires full tree, so we fall back to that.

        Args:
            file_path: Path to XML file
            result: ValidationResult to populate
            progress: Optional progress reporter

        Returns:
            Parsed document tree if successful, None otherwise
        """
        try:
            if progress:
                progress.update(f"Streaming parse: {file_path.name}")

            # Use iterparse for basic well-formedness check
            # Note: Relax NG and Schematron require full tree, so we still need to parse fully
            # This streaming approach mainly helps with initial parsing of very large files
            element_count = 0
            context = etree.iterparse(str(file_path), events=("start", "end"))

            for event, elem in context:
                if event == "end":
                    element_count += 1
                    if progress and element_count % 1000 == 0:
                        progress.update(f"Parsed {element_count} elements from {file_path.name}")

                    # Clear element to save memory
                    elem.clear()
                    while elem.getprevious() is not None:
                        del elem.getparent()[0]

            # After streaming validation, we still need full tree for schema validation
            if progress:
                progress.update(f"Building tree for schema validation: {file_path.name}")

            doc = etree.parse(str(file_path))
            result.used_streaming = True
            return doc

        except etree.XMLSyntaxError as e:
            result.errors.append(
                ValidationError(
                    file=str(file_path),
                    line=e.lineno,
                    column=getattr(e, "position", [None])[0],
                    message=str(e),
                    type="error",
                    rule="xml-syntax",
                )
            )
            result.is_valid = False
            return None
        except Exception as e:
            result.errors.append(
                ValidationError(
                    file=str(file_path),
                    line=None,
                    column=None,
                    message=f"Streaming validation error: {e}",
                    type="error",
                    rule="streaming",
                )
            )
            result.is_valid = False
            return None

    def write_assertions(
        self,
        result: ValidationResult,
        output_path: Path,
        jsonl_path: Path,
    ) -> None:
        """Write validation results to assertion ledger and JSON Lines."""
        from xml_lib.assertions import AssertionLedger

        ledger = AssertionLedger()
        ledger.add_validation_result(result)
        ledger.write_xml(output_path)
        ledger.write_jsonl(jsonl_path)
