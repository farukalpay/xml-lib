"""Type definitions and protocols for xml-lib."""

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


# ValidationResult is defined in validator.py and re-exported here for backward compatibility
# Import it here to avoid circular dependencies - users should import from xml_lib or xml_lib.validator
# This comment serves as documentation that ValidationResult canonical definition is in validator.py


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
