"""Pipeline execution context and result types."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from lxml import etree


class ErrorStrategy(Enum):
    """Error handling strategies for pipeline execution."""

    FAIL_FAST = "fail_fast"  # Stop on first error
    CONTINUE = "continue"  # Log error, continue pipeline
    ROLLBACK = "rollback"  # Rollback to last snapshot
    RETRY = "retry"  # Retry stage with exponential backoff
    SKIP = "skip"  # Skip failed stage, continue


@dataclass
class StageResult:
    """Result of executing a pipeline stage."""

    stage: str
    success: bool
    data: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    duration_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stage": self.stage,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata,
            "duration_seconds": self.duration_seconds,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class PipelineContext:
    """Execution context passed between pipeline stages.

    This context maintains the current state of XML data being processed,
    tracks execution history, manages rollback snapshots, and provides
    a key-value store for sharing data between stages.
    """

    # Current XML data
    xml_data: str
    xml_tree: Optional[etree._Element] = None

    # File paths
    input_path: Optional[Path] = None
    output_path: Optional[Path] = None
    working_dir: Path = field(default_factory=Path.cwd)

    # State tracking
    stage_results: List[StageResult] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)

    # Rollback state (stage_name, xml_data, xml_tree_string)
    snapshots: List[Tuple[str, str, Optional[str]]] = field(default_factory=list)

    # Metadata
    start_time: datetime = field(default_factory=datetime.now)
    execution_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self):
        """Initialize XML tree if not provided."""
        if self.xml_tree is None and self.xml_data:
            try:
                self.xml_tree = etree.fromstring(self.xml_data.encode())
            except Exception:
                # If parsing fails, leave tree as None
                pass

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed execution time in seconds."""
        return (datetime.now() - self.start_time).total_seconds()

    @property
    def last_result(self) -> Optional[StageResult]:
        """Get the most recent stage result."""
        return self.stage_results[-1] if self.stage_results else None

    @property
    def all_successful(self) -> bool:
        """Check if all stages succeeded."""
        return all(result.success for result in self.stage_results)

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a variable from the context."""
        return self.variables.get(name, default)

    def set_variable(self, name: str, value: Any) -> None:
        """Set a variable in the context."""
        self.variables[name] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization."""
        return {
            "execution_id": self.execution_id,
            "start_time": self.start_time.isoformat(),
            "elapsed_seconds": self.elapsed_seconds,
            "input_path": str(self.input_path) if self.input_path else None,
            "output_path": str(self.output_path) if self.output_path else None,
            "working_dir": str(self.working_dir),
            "variables": self.variables,
            "stage_results": [r.to_dict() for r in self.stage_results],
            "all_successful": self.all_successful,
        }


@dataclass
class PipelineResult:
    """Result of executing a complete pipeline."""

    pipeline_name: str
    success: bool
    context: PipelineContext
    error: Optional[str] = None
    stages_executed: int = 0
    stages_failed: int = 0

    @property
    def duration_seconds(self) -> float:
        """Total pipeline execution time."""
        return self.context.elapsed_seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "pipeline_name": self.pipeline_name,
            "success": self.success,
            "error": self.error,
            "stages_executed": self.stages_executed,
            "stages_failed": self.stages_failed,
            "duration_seconds": self.duration_seconds,
            "context": self.context.to_dict(),
        }


class PipelineError(Exception):
    """Base exception for pipeline errors."""

    pass


class StageError(PipelineError):
    """Exception raised when a stage fails."""

    def __init__(self, stage_name: str, message: str, original_error: Optional[Exception] = None):
        self.stage_name = stage_name
        self.message = message
        self.original_error = original_error
        super().__init__(f"Stage '{stage_name}' failed: {message}")


class ValidationError(StageError):
    """Exception raised during validation stage."""

    pass


class TransformationError(StageError):
    """Exception raised during transformation stage."""

    pass


class OutputError(StageError):
    """Exception raised during output stage."""

    pass
