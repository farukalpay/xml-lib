"""Pipeline stage implementations."""

import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

from lxml import etree

from xml_lib.pipeline.context import (
    OutputError,
    PipelineContext,
    StageError,
    StageResult,
    TransformationError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class Stage(ABC):
    """Abstract base class for pipeline stages.

    Each stage represents a discrete operation in the pipeline (validation,
    transformation, output, etc.) and must implement execute() to perform
    its work. Stages can optionally implement rollback() for undo operations.
    """

    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__

    @abstractmethod
    def execute(self, context: PipelineContext) -> StageResult:
        """Execute the stage with the given context.

        Args:
            context: Pipeline execution context containing XML data and state

        Returns:
            StageResult indicating success/failure and any metadata

        Raises:
            StageError: If the stage encounters an error
        """
        pass

    def validate_input(self, context: PipelineContext) -> bool:
        """Validate that the context is suitable for this stage.

        Override this to add precondition checks before execution.

        Args:
            context: Pipeline execution context

        Returns:
            True if input is valid, False otherwise
        """
        return True

    def rollback(self, context: PipelineContext) -> None:
        """Rollback any changes made by this stage.

        Override this to implement custom rollback logic.

        Args:
            context: Pipeline execution context
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"


class ValidateStage(Stage):
    """Stage that validates XML against schemas and guardrails.

    This stage leverages xml-lib's existing validation infrastructure to
    check XML documents against RelaxNG schemas, Schematron rules, and
    custom guardrails.
    """

    def __init__(
        self,
        schemas_dir: Optional[Path] = None,
        guardrails_dir: Optional[Path] = None,
        strict: bool = True,
        streaming: bool = False,
        streaming_threshold: int = 10 * 1024 * 1024,  # 10MB
        name: Optional[str] = None,
    ):
        """Initialize validation stage.

        Args:
            schemas_dir: Directory containing RelaxNG/Schematron schemas
            guardrails_dir: Directory containing guardrail rules
            strict: If True, treat warnings as errors
            streaming: Force streaming mode for large files
            streaming_threshold: Auto-enable streaming above this size (bytes)
            name: Optional stage name
        """
        super().__init__(name)
        self.schemas_dir = schemas_dir or Path("schemas")
        self.guardrails_dir = guardrails_dir or Path("guardrails")
        self.strict = strict
        self.streaming = streaming
        self.streaming_threshold = streaming_threshold

    def validate_input(self, context: PipelineContext) -> bool:
        """Validate that we have XML data to validate."""
        return bool(context.xml_data or context.xml_tree is not None)

    def execute(self, context: PipelineContext) -> StageResult:
        """Execute validation stage."""
        start_time = time.time()

        try:
            # Import here to avoid circular dependencies
            from xml_lib.validator import Validator
            import tempfile

            # Determine if we should use streaming
            use_streaming = self.streaming
            if not use_streaming and context.xml_data:
                data_size = len(context.xml_data.encode())
                use_streaming = data_size > self.streaming_threshold

            # Create validator
            validator = Validator(
                schemas_dir=self.schemas_dir,
                guardrails_dir=self.guardrails_dir,
            )

            # The Validator class expects a project directory, not a single file
            # For pipeline use, we need to write XML to a temp directory and validate
            if context.input_path and context.input_path.exists():
                # Validate existing file's parent directory
                result = validator.validate_project(context.input_path.parent)
            else:
                # Create a temporary directory with the XML file
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp_path = Path(tmpdir) / "temp.xml"
                    tmp_path.write_text(context.xml_data)
                    result = validator.validate_project(Path(tmpdir))

            # Check if validation passed
            success = result.is_valid
            if self.strict and not success:
                # In strict mode, any validation error fails the stage
                error_msg = f"Validation failed: {len(result.errors)} errors"
                raise ValidationError(self.name, error_msg)

            duration = time.time() - start_time

            return StageResult(
                stage=self.name,
                success=success,
                data=context.xml_data,
                metadata={
                    "errors": [str(e) for e in result.errors[:10]],  # Limit to first 10
                    "warnings": [str(w) for w in result.warnings[:10]],
                    "streaming": use_streaming,
                    "error_count": len(result.errors),
                    "warning_count": len(result.warnings),
                },
                duration_seconds=duration,
            )

        except ValidationError:
            raise
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Validation stage '{self.name}' failed: {e}")
            raise ValidationError(self.name, str(e), e) from e


class TransformStage(Stage):
    """Stage that transforms XML using XSLT or Python functions.

    Supports both XSLT stylesheets and custom Python transformation
    functions, allowing flexible XML manipulation within pipelines.
    """

    def __init__(
        self,
        transform: Union[Path, Callable[[str, PipelineContext], str]],
        params: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
    ):
        """Initialize transformation stage.

        Args:
            transform: XSLT file path or Python transformation function
            params: Parameters to pass to XSLT or function
            name: Optional stage name
        """
        super().__init__(name)
        self.transform = transform
        self.params = params or {}
        self._compiled_transform: Optional[etree.XSLT] = None

    def validate_input(self, context: PipelineContext) -> bool:
        """Validate that we have XML data to transform."""
        return bool(context.xml_data or context.xml_tree is not None)

    def execute(self, context: PipelineContext) -> StageResult:
        """Execute transformation stage."""
        start_time = time.time()

        try:
            if isinstance(self.transform, Path):
                # XSLT transformation
                transformed = self._apply_xslt(context)
            else:
                # Python function transformation
                transformed = self._apply_function(context)

            # Update context with transformed XML
            context.xml_data = transformed
            try:
                context.xml_tree = etree.fromstring(transformed.encode())
            except Exception as e:
                logger.warning(f"Failed to parse transformed XML: {e}")
                context.xml_tree = None

            duration = time.time() - start_time

            return StageResult(
                stage=self.name,
                success=True,
                data=transformed,
                metadata={
                    "transform_type": "xslt" if isinstance(self.transform, Path) else "function",
                    "output_size": len(transformed),
                },
                duration_seconds=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Transform stage '{self.name}' failed: {e}")
            raise TransformationError(self.name, str(e), e) from e

    def _apply_xslt(self, context: PipelineContext) -> str:
        """Apply XSLT transformation."""
        # Compile XSLT if not already done
        if self._compiled_transform is None:
            xslt_tree = etree.parse(str(self.transform))
            self._compiled_transform = etree.XSLT(xslt_tree)

        # Apply transformation
        result_tree = self._compiled_transform(context.xml_tree, **self.params)

        # Convert to string
        return str(result_tree)

    def _apply_function(self, context: PipelineContext) -> str:
        """Apply Python function transformation."""
        return self.transform(context.xml_data, context)


class OutputStage(Stage):
    """Stage that outputs XML to various formats.

    Leverages xml-lib's existing publishers (HTML, PowerPoint, PHP) to
    generate output in multiple formats from XML pipelines.
    """

    SUPPORTED_FORMATS = ["html", "pptx", "php", "json", "xml", "assertions"]

    def __init__(
        self,
        format: str,
        output_path: Path,
        template: Optional[Path] = None,
        options: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
    ):
        """Initialize output stage.

        Args:
            format: Output format (html, pptx, php, json, xml, assertions)
            output_path: Path where output should be written
            template: Optional template file for rendering
            options: Format-specific options
            name: Optional stage name
        """
        super().__init__(name)
        if format not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format '{format}'. "
                f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        self.format = format
        self.output_path = output_path
        self.template = template
        self.options = options or {}

    def validate_input(self, context: PipelineContext) -> bool:
        """Validate that we have XML data to output."""
        return bool(context.xml_data or context.xml_tree is not None)

    def execute(self, context: PipelineContext) -> StageResult:
        """Execute output stage."""
        start_time = time.time()

        try:
            # Ensure output directory exists
            self.output_path.parent.mkdir(parents=True, exist_ok=True)

            # Route to appropriate output handler
            if self.format == "html":
                self._output_html(context)
            elif self.format == "pptx":
                self._output_pptx(context)
            elif self.format == "php":
                self._output_php(context)
            elif self.format == "json":
                self._output_json(context)
            elif self.format == "xml":
                self._output_xml(context)
            elif self.format == "assertions":
                self._output_assertions(context)

            duration = time.time() - start_time

            return StageResult(
                stage=self.name,
                success=True,
                data=context.xml_data,
                metadata={
                    "format": self.format,
                    "output_path": str(self.output_path),
                    "file_size": self.output_path.stat().st_size if self.output_path.exists() else 0,
                },
                duration_seconds=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Output stage '{self.name}' failed: {e}")
            raise OutputError(self.name, str(e), e) from e

    def _output_html(self, context: PipelineContext) -> None:
        """Output as HTML using publisher."""
        from xml_lib.publisher import publish

        publish(
            xml_tree=context.xml_tree,
            output_dir=self.output_path.parent,
            xslt_template=self.template,
            **self.options,
        )

    def _output_pptx(self, context: PipelineContext) -> None:
        """Output as PowerPoint presentation."""
        from xml_lib.pptx_composer import compose_pptx

        compose_pptx(
            xml_tree=context.xml_tree,
            output_path=self.output_path,
            template=self.template,
            **self.options,
        )

    def _output_php(self, context: PipelineContext) -> None:
        """Output as PHP pages."""
        from xml_lib.php.generator import generate_php

        generate_php(
            xml_tree=context.xml_tree,
            output_dir=self.output_path.parent,
            **self.options,
        )

    def _output_json(self, context: PipelineContext) -> None:
        """Output as JSON (context metadata)."""
        import json

        data = context.to_dict()
        self.output_path.write_text(json.dumps(data, indent=2))

    def _output_xml(self, context: PipelineContext) -> None:
        """Output as XML (pretty-printed)."""
        if context.xml_tree is not None:
            xml_str = etree.tostring(
                context.xml_tree,
                pretty_print=True,
                xml_declaration=True,
                encoding="UTF-8",
            ).decode()
        else:
            xml_str = context.xml_data

        self.output_path.write_text(xml_str)

    def _output_assertions(self, context: PipelineContext) -> None:
        """Output as signed assertions ledger."""
        from xml_lib.assertions import create_assertion_ledger

        create_assertion_ledger(
            xml_tree=context.xml_tree,
            output_path=self.output_path,
            **self.options,
        )


class CustomStage(Stage):
    """Stage that executes custom user-defined logic.

    Provides flexibility for pipeline operations not covered by
    built-in stage types.
    """

    def __init__(
        self,
        function: Callable[[PipelineContext], StageResult],
        rollback_function: Optional[Callable[[PipelineContext], None]] = None,
        name: Optional[str] = None,
    ):
        """Initialize custom stage.

        Args:
            function: Function to execute for this stage
            rollback_function: Optional function to call on rollback
            name: Optional stage name
        """
        super().__init__(name)
        self.function = function
        self.rollback_function = rollback_function

    def execute(self, context: PipelineContext) -> StageResult:
        """Execute custom function."""
        start_time = time.time()

        try:
            result = self.function(context)
            result.duration_seconds = time.time() - start_time
            return result

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Custom stage '{self.name}' failed: {e}")
            raise StageError(self.name, str(e), e) from e

    def rollback(self, context: PipelineContext) -> None:
        """Execute custom rollback function if provided."""
        if self.rollback_function:
            self.rollback_function(context)
