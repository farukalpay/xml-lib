"""High-level public API for xml-lib.

This module provides a clean, documented interface for common XML validation,
publishing, and linting workflows. It's designed for developers who want to
integrate xml-lib into their own Python projects programmatically.

Basic Usage:
    >>> from xml_lib.api import validate_xml, quick_validate
    >>>
    >>> # Quick validation with sensible defaults
    >>> result = quick_validate("path/to/project")
    >>> if result.is_valid:
    ...     print(f"✓ Validated {len(result.validated_files)} files")
    ... else:
    ...     for error in result.errors:
    ...         print(f"✗ {error.file}:{error.line} - {error.message}")
    >>>
    >>> # More control with validate_xml
    >>> result = validate_xml(
    ...     "path/to/project",
    ...     schemas_dir="schemas",
    ...     enable_streaming=True,  # For large files
    ...     show_progress=True,     # Show progress bar
    ... )

Advanced Usage:
    >>> from xml_lib.api import create_validator, lint_xml, publish_html
    >>>
    >>> # Create a reusable validator instance
    >>> validator = create_validator(
    ...     schemas_dir="schemas",
    ...     guardrails_dir="lib/guardrails",
    ...     enable_streaming=True,
    ... )
    >>> result = validator.validate_project(Path("project"))
    >>>
    >>> # Lint XML files for formatting and security issues
    >>> lint_result = lint_xml("project", check_security=True)
    >>> print(f"Found {lint_result.error_count} errors, {lint_result.warning_count} warnings")
    >>>
    >>> # Publish XML to HTML
    >>> publish_result = publish_html("project", output_dir="output", xslt_dir="schemas/xslt")

For batch processing and pipeline automation, see the pipeline module:
    >>> from xml_lib.pipeline import load_pipeline, execute_pipeline
    >>> pipeline = load_pipeline("templates/ci-validation.yaml")
    >>> result = execute_pipeline(pipeline, {"input_dir": "project"})
"""

from pathlib import Path
from typing import Optional

from xml_lib.linter import LintResult, XMLLinter
from xml_lib.publisher import PublishResult, Publisher
from xml_lib.sanitize import MathPolicy
from xml_lib.telemetry import FileTelemetrySink, TelemetrySink
from xml_lib.validator import ValidationResult, Validator


def quick_validate(
    project_path: str | Path,
    *,
    show_progress: bool = False,
) -> ValidationResult:
    """Quick validation with sensible defaults - the easiest way to get started.

    This is a convenience function that handles all the boilerplate setup for you.
    It automatically discovers schemas and guardrails in standard locations and
    validates all XML files in the given project directory.

    Args:
        project_path: Path to the directory containing XML files to validate
        show_progress: Whether to show a progress indicator during validation

    Returns:
        ValidationResult with validation outcome, errors, and metadata

    Example:
        >>> from xml_lib.api import quick_validate
        >>>
        >>> # Validate a project directory
        >>> result = quick_validate("my-xml-project")
        >>>
        >>> # Check if validation passed
        >>> if result.is_valid:
        ...     print(f"✓ All {len(result.validated_files)} files are valid!")
        ... else:
        ...     print(f"✗ Found {len(result.errors)} errors:")
        ...     for error in result.errors:
        ...         print(f"  {error.file}:{error.line} - {error.message}")
        >>>
        >>> # With progress indicator for large projects
        >>> result = quick_validate("large-project", show_progress=True)

    Note:
        This function assumes your project has the following structure:
        - schemas/ directory with .rng and .sch files
        - lib/guardrails/ directory with guardrail definitions

        For custom locations or more control, use validate_xml() or create_validator().
    """
    project_path = Path(project_path)

    # Discover schemas and guardrails in standard locations
    schemas_dir = _find_schemas_dir(project_path)
    guardrails_dir = _find_guardrails_dir(project_path)

    return validate_xml(
        project_path=project_path,
        schemas_dir=schemas_dir,
        guardrails_dir=guardrails_dir,
        show_progress=show_progress,
    )


def validate_xml(
    project_path: str | Path,
    *,
    schemas_dir: Optional[str | Path] = None,
    guardrails_dir: Optional[str | Path] = None,
    math_policy: MathPolicy = MathPolicy.SANITIZE,
    enable_streaming: bool = True,
    streaming_threshold_mb: int = 10,
    show_progress: bool = False,
    telemetry: Optional[TelemetrySink] = None,
) -> ValidationResult:
    """Validate XML files in a project directory with full control over options.

    This function provides a clean interface to the validation system with
    sensible defaults but allows customization of all major options.

    Args:
        project_path: Path to the directory containing XML files to validate
        schemas_dir: Directory containing Relax NG (.rng) and Schematron (.sch) schemas.
            If None, looks for 'schemas/' in the project directory.
        guardrails_dir: Directory containing guardrail rule definitions.
            If None, looks for 'lib/guardrails/' in the project directory.
        math_policy: How to handle mathematical XML content:
            - MathPolicy.SANITIZE (default): Sanitize potentially problematic content
            - MathPolicy.SKIP: Skip files with math content
            - MathPolicy.ERROR: Raise errors on math content
        enable_streaming: Enable memory-efficient streaming for large files (default: True)
        streaming_threshold_mb: Files larger than this (in MB) use streaming (default: 10)
        show_progress: Show a progress indicator during validation
        telemetry: Optional telemetry sink for collecting metrics

    Returns:
        ValidationResult containing:
            - is_valid: bool - whether all files passed validation
            - errors: list of ValidationError objects
            - warnings: list of ValidationError objects
            - validated_files: list of file paths that were validated
            - checksums: dict mapping file paths to SHA-256 checksums
            - used_streaming: bool - whether streaming was used for any files

    Example:
        >>> from xml_lib.api import validate_xml
        >>> from xml_lib.sanitize import MathPolicy
        >>>
        >>> # Basic usage with defaults
        >>> result = validate_xml("my-project")
        >>>
        >>> # Customize behavior
        >>> result = validate_xml(
        ...     "my-project",
        ...     schemas_dir="custom/schemas",
        ...     guardrails_dir="custom/rules",
        ...     math_policy=MathPolicy.SKIP,
        ...     enable_streaming=True,
        ...     streaming_threshold_mb=50,  # 50MB threshold
        ...     show_progress=True,
        ... )
        >>>
        >>> # Check results
        >>> if not result.is_valid:
        ...     for error in result.errors:
        ...         print(f"Error in {error.file} at line {error.line}:")
        ...         print(f"  {error.message}")
        ...         print(f"  Rule: {error.rule}")
        >>>
        >>> # Access metadata
        >>> print(f"Validated {len(result.validated_files)} files")
        >>> print(f"Streaming used: {result.used_streaming}")
        >>> for file, checksum in result.checksums.items():
        ...     print(f"{file}: {checksum}")

    Raises:
        FileNotFoundError: If project_path doesn't exist
        ValueError: If required schemas or guardrails are missing

    See Also:
        - quick_validate(): Simpler function with automatic discovery
        - create_validator(): Create a reusable Validator instance
        - Validator class: For more advanced use cases
    """
    project_path = Path(project_path)

    if not project_path.exists():
        raise FileNotFoundError(f"Project path does not exist: {project_path}")

    # Resolve schema and guardrail directories
    schemas_dir = Path(schemas_dir) if schemas_dir else _find_schemas_dir(project_path)
    guardrails_dir = Path(guardrails_dir) if guardrails_dir else _find_guardrails_dir(project_path)

    # Create validator
    validator = create_validator(
        schemas_dir=schemas_dir,
        guardrails_dir=guardrails_dir,
        math_policy=math_policy,
        enable_streaming=enable_streaming,
        streaming_threshold_bytes=streaming_threshold_mb * 1024 * 1024,
        show_progress=show_progress,
        telemetry=telemetry,
    )

    # Validate the project
    return validator.validate_project(project_path)


def create_validator(
    *,
    schemas_dir: str | Path,
    guardrails_dir: str | Path,
    math_policy: MathPolicy = MathPolicy.SANITIZE,
    enable_streaming: bool = True,
    streaming_threshold_bytes: int = 10 * 1024 * 1024,
    show_progress: bool = False,
    telemetry: Optional[TelemetrySink] = None,
) -> Validator:
    """Create a reusable Validator instance for multiple validation operations.

    Use this when you need to validate multiple projects with the same
    configuration, or when you want more control over the validation process.

    Args:
        schemas_dir: Directory containing Relax NG (.rng) and Schematron (.sch) schemas
        guardrails_dir: Directory containing guardrail rule definitions
        math_policy: How to handle mathematical XML content (default: SANITIZE)
        enable_streaming: Enable memory-efficient streaming for large files (default: True)
        streaming_threshold_bytes: File size threshold for streaming in bytes (default: 10MB)
        show_progress: Show a progress indicator during validation
        telemetry: Optional telemetry sink for collecting metrics

    Returns:
        Validator instance ready to use

    Example:
        >>> from xml_lib.api import create_validator
        >>> from pathlib import Path
        >>>
        >>> # Create a validator for multiple projects
        >>> validator = create_validator(
        ...     schemas_dir="schemas",
        ...     guardrails_dir="lib/guardrails",
        ...     enable_streaming=True,
        ...     show_progress=True,
        ... )
        >>>
        >>> # Validate multiple projects with the same validator
        >>> for project in ["project1", "project2", "project3"]:
        ...     result = validator.validate_project(Path(project))
        ...     print(f"{project}: {'✓' if result.is_valid else '✗'}")
        >>>
        >>> # Access validator internals for advanced use cases
        >>> print(f"Relax NG schema loaded: {validator.relaxng_lifecycle is not None}")
        >>> print(f"Schematron schema loaded: {validator.schematron_lifecycle is not None}")

    See Also:
        - validate_xml(): Higher-level function for single validation
        - Validator class: Full API documentation
    """
    schemas_dir = Path(schemas_dir)
    guardrails_dir = Path(guardrails_dir)

    return Validator(
        schemas_dir=schemas_dir,
        guardrails_dir=guardrails_dir,
        telemetry=telemetry,
        math_policy=math_policy,
        use_streaming=enable_streaming,
        streaming_threshold_bytes=streaming_threshold_bytes,
        show_progress=show_progress,
    )


def lint_xml(
    path: str | Path,
    *,
    check_indentation: bool = True,
    check_attribute_order: bool = True,
    check_external_entities: bool = True,
    check_formatting: bool = True,
    indent_size: int = 2,
    allow_xxe: bool = False,
) -> LintResult:
    """Lint XML files for formatting issues and security vulnerabilities.

    This function checks XML files for common issues like:
    - Inconsistent indentation
    - Security vulnerabilities (XXE/external entity injection)
    - Attribute ordering
    - Other best practice violations

    Args:
        path: File or directory path to lint
        check_indentation: Check for consistent indentation (default: True)
        check_attribute_order: Check for alphabetically sorted attributes (default: True)
        check_external_entities: Check for XXE vulnerabilities (default: True)
        check_formatting: Check for general formatting issues (default: True)
        indent_size: Expected number of spaces for indentation (default: 2)
        allow_xxe: Allow external entities - False for security (default: False)

    Returns:
        LintResult containing:
            - issues: list of LintIssue objects (errors, warnings, info)
            - files_checked: number of files that were checked
            - error_count: count of error-level issues
            - warning_count: count of warning-level issues
            - has_errors: whether any errors were found

    Example:
        >>> from xml_lib.api import lint_xml
        >>>
        >>> # Lint a directory with all checks
        >>> result = lint_xml("my-project")
        >>>
        >>> # Report findings
        >>> if result.has_errors:
        ...     print(f"Found {result.error_count} errors:")
        ...     for issue in result.issues:
        ...         if issue.level.value == "error":
        ...             print(f"  {issue.format_text()}")
        ...
        >>> # Check specific issues
        >>> print(f"Checked {result.files_checked} files")
        >>> print(f"Errors: {result.error_count}, Warnings: {result.warning_count}")
        >>>
        >>> # Custom indentation check (4 spaces)
        >>> result = lint_xml("project", indent_size=4)
        >>>
        >>> # Skip attribute ordering checks
        >>> result = lint_xml("project", check_attribute_order=False)

    See Also:
        - XMLLinter class: For more advanced linting configurations
        - LintIssue: Individual lint issue representation
    """
    path = Path(path)

    linter = XMLLinter(
        check_indentation=check_indentation,
        check_attribute_order=check_attribute_order,
        check_external_entities=check_external_entities,
        check_formatting=check_formatting,
        indent_size=indent_size,
        allow_xxe=allow_xxe,
    )

    if path.is_file():
        return linter.lint_file(path)
    else:
        return linter.lint_directory(path)


def publish_html(
    project_path: str | Path,
    output_dir: str | Path,
    *,
    xslt_dir: Optional[str | Path] = None,
    telemetry: Optional[TelemetrySink] = None,
) -> PublishResult:
    """Publish XML documents to HTML using XSLT 3.0 transformation.

    This function transforms XML documents into HTML using XSLT templates,
    making them human-readable and suitable for documentation or web publishing.

    Args:
        project_path: Path to directory containing XML files to publish
        output_dir: Directory where HTML files will be written
        xslt_dir: Directory containing XSLT templates. If None, uses default templates.
        telemetry: Optional telemetry sink for collecting metrics

    Returns:
        PublishResult containing:
            - success: bool - whether publishing succeeded
            - files: list of generated HTML file paths
            - error: Optional error message if publishing failed

    Example:
        >>> from xml_lib.api import publish_html
        >>>
        >>> # Publish XML to HTML with defaults
        >>> result = publish_html("project", "output/html")
        >>> if result.success:
        ...     print(f"Published {len(result.files)} files:")
        ...     for file in result.files:
        ...         print(f"  - {file}")
        ... else:
        ...     print(f"Publishing failed: {result.error}")
        >>>
        >>> # Use custom XSLT templates
        >>> result = publish_html(
        ...     "project",
        ...     "output/html",
        ...     xslt_dir="custom-templates/xslt",
        ... )

    See Also:
        - Publisher class: For more control over publishing
    """
    project_path = Path(project_path)
    output_dir = Path(output_dir)

    # Resolve XSLT directory
    if xslt_dir is None:
        xslt_dir = _find_xslt_dir(project_path)
    else:
        xslt_dir = Path(xslt_dir)

    # Create publisher
    publisher = Publisher(xslt_dir=xslt_dir, telemetry=telemetry)

    # Publish the project
    return publisher.publish_project(project_path, output_dir)


# Helper functions for directory discovery

def _find_schemas_dir(project_path: Path) -> Path:
    """Find schemas directory relative to project path."""
    # Try common locations
    candidates = [
        project_path / "schemas",
        project_path.parent / "schemas",
        Path.cwd() / "schemas",
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate

    # Default to project/schemas even if it doesn't exist
    return project_path / "schemas"


def _find_guardrails_dir(project_path: Path) -> Path:
    """Find guardrails directory relative to project path."""
    # Try common locations
    candidates = [
        project_path / "lib" / "guardrails",
        project_path / "guardrails",
        project_path.parent / "lib" / "guardrails",
        Path.cwd() / "lib" / "guardrails",
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate

    # Default to project/lib/guardrails even if it doesn't exist
    return project_path / "lib" / "guardrails"


def _find_xslt_dir(project_path: Path) -> Path:
    """Find XSLT directory relative to project path."""
    # Try common locations
    candidates = [
        project_path / "schemas" / "xslt",
        project_path / "xslt",
        project_path.parent / "schemas" / "xslt",
        Path.cwd() / "schemas" / "xslt",
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate

    # Default to project/schemas/xslt even if it doesn't exist
    default_dir = project_path / "schemas" / "xslt"
    default_dir.mkdir(parents=True, exist_ok=True)
    return default_dir


# Re-export commonly used classes and types for convenience
__all__ = [
    # High-level functions
    "quick_validate",
    "validate_xml",
    "create_validator",
    "lint_xml",
    "publish_html",
    # Core classes (for advanced usage)
    "Validator",
    "ValidationResult",
    "XMLLinter",
    "LintResult",
    "Publisher",
    "PublishResult",
    # Enums and types
    "MathPolicy",
    "TelemetrySink",
    "FileTelemetrySink",
]
