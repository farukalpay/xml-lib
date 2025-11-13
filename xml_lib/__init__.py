"""XML-Lib: Production-grade XML lifecycle, guardrails, and mathematical engine.

This library provides a comprehensive toolkit for XML validation, publishing, and
lifecycle management with enterprise-grade guardrails and formal verification.

Quick Start (Programmatic API):
    >>> from xml_lib import quick_validate, validate_xml, lint_xml
    >>>
    >>> # Quick validation with sensible defaults
    >>> result = quick_validate("my-xml-project")
    >>> if result.is_valid:
    ...     print(f"✓ All {len(result.validated_files)} files are valid!")
    >>>
    >>> # More control over validation
    >>> result = validate_xml(
    ...     "my-project",
    ...     enable_streaming=True,
    ...     show_progress=True,
    ... )
    >>>
    >>> # Lint for formatting and security issues
    >>> lint_result = lint_xml("my-project", check_security=True)

CLI Usage:
    The library also provides a comprehensive command-line interface:

    $ xml-lib validate .
    $ xml-lib publish . --output-dir output/
    $ xml-lib lint .
    $ xml-lib shell  # Interactive REPL

For complete documentation, see:
    - API docs: help(xml_lib.api)
    - Validator: help(xml_lib.Validator)
    - Pipeline automation: help(xml_lib.pipeline)
"""

__version__ = "0.1.0"

# High-level convenience functions (recommended for most users)
from xml_lib.api import (
    create_validator,
    lint_xml,
    publish_html,
    quick_validate,
    validate_xml,
)

# Core classes for advanced usage
from xml_lib.linter import LintIssue, LintLevel, LintResult, XMLLinter
from xml_lib.publisher import PublishResult, Publisher
from xml_lib.sanitize import MathPolicy
from xml_lib.telemetry import FileTelemetrySink, TelemetrySink
from xml_lib.types import ValidationError
from xml_lib.validator import ValidationResult, Validator

# CLI entry point (for backward compatibility)
from xml_lib.cli import main as app

# Pipeline automation (for batch processing)
try:
    from xml_lib.pipeline.engine import PipelineEngine
    from xml_lib.pipeline.loader import load_pipeline

    _has_pipeline = True
except ImportError:
    _has_pipeline = False

__all__ = [
    # Version
    "__version__",
    # High-level API (recommended)
    "quick_validate",
    "validate_xml",
    "create_validator",
    "lint_xml",
    "publish_html",
    # Core classes (for advanced usage)
    "Validator",
    "ValidationResult",
    "ValidationError",
    "XMLLinter",
    "LintResult",
    "LintIssue",
    "LintLevel",
    "Publisher",
    "PublishResult",
    # Enums and types
    "MathPolicy",
    "TelemetrySink",
    "FileTelemetrySink",
    # CLI
    "app",
]

# Conditionally export pipeline if available
if _has_pipeline:
    __all__.extend(["PipelineEngine", "load_pipeline"])
