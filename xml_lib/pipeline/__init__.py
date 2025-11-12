"""XML Pipeline Automation - Declarative pipeline system for XML workflows.

This module provides a composable framework for chaining XML operations
(validation, transformation, output) with built-in error recovery, rollback,
and templating.

Example:
    >>> from xml_lib.pipeline import Pipeline, ValidateStage, TransformStage, OutputStage
    >>> from pathlib import Path
    >>>
    >>> # Create pipeline programmatically
    >>> pipeline = Pipeline(name="my_pipeline")
    >>> pipeline.add_stage(ValidateStage(schemas_dir=Path("schemas")))
    >>> pipeline.add_stage(TransformStage(transform=Path("transform.xsl")))
    >>> pipeline.add_stage(OutputStage(format="html", output_path=Path("out/report.html")))
    >>> result = pipeline.execute(input_xml="input.xml")
    >>>
    >>> # Or load from YAML
    >>> from xml_lib.pipeline import load_pipeline
    >>> pipeline = load_pipeline(Path("pipelines/my_pipeline.yaml"))
    >>> result = pipeline.execute(input_xml="input.xml")
"""

from xml_lib.pipeline.context import (
    ErrorStrategy,
    OutputError,
    PipelineContext,
    PipelineError,
    PipelineResult,
    StageError,
    StageResult,
    TransformationError,
    ValidationError,
)
from xml_lib.pipeline.engine import Pipeline
from xml_lib.pipeline.loader import PipelineLoader, load_pipeline
from xml_lib.pipeline.stages import (
    CustomStage,
    OutputStage,
    Stage,
    TransformStage,
    ValidateStage,
)

__all__ = [
    # Core engine
    "Pipeline",
    # Stages
    "Stage",
    "ValidateStage",
    "TransformStage",
    "OutputStage",
    "CustomStage",
    # Context and results
    "PipelineContext",
    "PipelineResult",
    "StageResult",
    # Error handling
    "ErrorStrategy",
    "PipelineError",
    "StageError",
    "ValidationError",
    "TransformationError",
    "OutputError",
    # Loading
    "PipelineLoader",
    "load_pipeline",
]
