"""XML Lifecycle Validator with Relax NG and Schematron support."""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from lxml import etree

from xml_lib.storage import ContentStore
from xml_lib.types import ValidationError
from xml_lib.guardrails import GuardrailEngine
from xml_lib.telemetry import TelemetrySink


@dataclass
class ValidationResult:
    """Result of validation."""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    validated_files: List[str] = field(default_factory=list)
    checksums: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class Validator:
    """Validates XML documents against lifecycle schemas and guardrails."""

    def __init__(
        self,
        schemas_dir: Path,
        guardrails_dir: Path,
        telemetry: Optional[TelemetrySink] = None,
    ):
        self.schemas_dir = schemas_dir
        self.guardrails_dir = guardrails_dir
        self.telemetry = telemetry
        self.content_store = ContentStore(Path("store"))
        self.guardrail_engine = GuardrailEngine(guardrails_dir)

        # Load schemas
        self.relaxng_lifecycle = self._load_relaxng("lifecycle.rng")
        self.relaxng_guardrails = self._load_relaxng("guardrails.rng")
        self.schematron_lifecycle = self._load_schematron("lifecycle.sch")

    def _load_relaxng(self, filename: str) -> Optional[etree.RelaxNG]:
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

    def _load_schematron(self, filename: str) -> Optional[etree.Schematron]:
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

    def validate_project(self, project_path: Path) -> ValidationResult:
        """Validate all XML files in a project."""
        start_time = datetime.now()
        result = ValidationResult(is_valid=True)

        # Find all XML files
        xml_files = list(project_path.rglob("*.xml"))

        # Track IDs across all files for cross-file validation
        all_ids: Set[str] = set()
        id_locations: Dict[str, str] = {}

        for xml_file in xml_files:
            # Skip schema and guardrail files
            if "schema" in str(xml_file) or xml_file.parent.name == "guardrails":
                continue

            try:
                # Parse XML
                doc = etree.parse(str(xml_file))

                # Calculate checksum
                content = xml_file.read_bytes()
                checksum = hashlib.sha256(content).hexdigest()
                result.checksums[str(xml_file)] = checksum

                # Store in content-addressed storage
                stored_path = self.content_store.store(content, checksum)

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
                        column=e.position[0] if hasattr(e, 'position') else None,
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

        return result

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
        all_ids: Set[str],
        id_locations: Dict[str, str],
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
        timestamps: Dict[str, datetime] = {}
        phase_order = ["begin", "start", "iteration", "end", "continuum"]

        for phase in phases.findall("phase"):
            phase_name = phase.get("name")
            timestamp_str = phase.get("timestamp")

            if timestamp_str:
                try:
                    timestamps[phase_name] = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
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
