"""Type definitions and protocols for xml-lib."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Protocol, TypeAlias

# Phase types
PhaseType: TypeAlias = Literal["begin", "start", "iteration", "end", "continuum"]


class Priority(str, Enum):
    """Priority levels for guardrails and validation."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ValidationError:
    """A validation error or warning.

    This is the canonical error type used throughout xml-lib for reporting
    validation issues from schemas, guardrails, and linters.

    Attributes:
        file: Path to the file containing the error
        line: Line number (1-indexed), or None if not applicable
        column: Column number (1-indexed), or None if not applicable
        message: Human-readable error message
        type: Error severity - 'error' or 'warning'
        rule: Name of the rule that triggered this error, if applicable
    """

    file: str
    line: int | None
    column: int | None
    message: str
    type: str  # 'error' or 'warning'
    rule: str | None = None


@dataclass(frozen=True)
class PhaseNode:
    """Node in the lifecycle DAG."""

    phase: PhaseType
    xml_path: Path
    timestamp: datetime
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str | None = None
    checksum: str | None = None


@dataclass
class ValidationResult:
    """Canonical result type for XML validation operations.

    This is the standard result type returned by all validation functions in xml-lib.
    It contains comprehensive information about the validation process and any issues found.

    Attributes:
        is_valid: True if all validations passed without errors
        errors: List of validation errors found (may include schema, guardrail, or structural errors)
        warnings: List of non-fatal warnings that don't prevent validation from passing
        validated_files: List of file paths that were validated
        checksums: Dictionary mapping file paths to SHA-256 checksums
        timestamp: When the validation was performed
        used_streaming: Whether streaming validation was used for any files (for large file handling)

    Example:
        >>> from xml_lib import ValidationResult, ValidationError
        >>> result = ValidationResult(
        ...     is_valid=True,
        ...     errors=[],
        ...     warnings=[],
        ...     validated_files=["test.xml"],
        ...     checksums={"test.xml": "abc123..."},
        ... )
    """

    is_valid: bool
    errors: list[ValidationError] | list[str] = field(default_factory=list)
    warnings: list[ValidationError] | list[str] = field(default_factory=list)
    validated_files: list[str] = field(default_factory=list)
    checksums: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    used_streaming: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CommandResult:
    """Result of a CLI command execution."""

    command: str
    timestamp: datetime
    duration_ms: float
    status: Literal["success", "failure", "warning"]
    summary: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class ValidatorProtocol(Protocol):
    """Protocol for validators."""

    def validate(self, doc: Any) -> ValidationResult:
        """Validate a document."""
        ...


class TransformerProtocol(Protocol):
    """Protocol for transformers."""

    def transform(self, input_path: Path, output_path: Path) -> bool:
        """Transform an input document to an output document."""
        ...


@dataclass
class Reference:
    """Cross-reference between XML documents."""

    source_id: str
    target_id: str
    reference_type: str
    source_file: Path
    target_file: Path | None = None


@dataclass
class Invariant:
    """System invariant that must be maintained."""

    id: str
    description: str
    check: str  # XPath or Python expression
    severity: Priority = Priority.HIGH


@dataclass
class ReferenceError:
    """Error in cross-reference validation."""

    reference: Reference
    error: str
    file_path: Path
    line_number: int | None = None
