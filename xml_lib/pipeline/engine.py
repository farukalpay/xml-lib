"""Core pipeline execution engine."""

import logging
import time
from pathlib import Path
from typing import List, Optional, Union

from lxml import etree

from xml_lib.pipeline.context import (
    ErrorStrategy,
    PipelineContext,
    PipelineError,
    PipelineResult,
    StageResult,
)
from xml_lib.pipeline.stages import Stage

logger = logging.getLogger(__name__)


class Pipeline:
    """Orchestrates execution of multiple XML processing stages.

    The Pipeline class provides a declarative, composable framework for
    chaining XML operations (validation, transformation, output) with
    built-in error recovery, rollback, and state management.

    Example:
        >>> pipeline = Pipeline(name="validate_and_transform")
        >>> pipeline.add_stage(ValidateStage(schemas_dir="schemas"))
        >>> pipeline.add_stage(TransformStage(transform="transform.xsl"))
        >>> result = pipeline.execute(input_xml="input.xml")
    """

    def __init__(
        self,
        name: str = "pipeline",
        error_strategy: ErrorStrategy = ErrorStrategy.FAIL_FAST,
        rollback_enabled: bool = True,
        max_snapshots: int = 100,
    ):
        """Initialize pipeline.

        Args:
            name: Pipeline name for identification
            error_strategy: How to handle stage errors
            rollback_enabled: Whether to enable rollback snapshots
            max_snapshots: Maximum number of snapshots to keep
        """
        self.name = name
        self.error_strategy = error_strategy
        self.rollback_enabled = rollback_enabled
        self.max_snapshots = max_snapshots
        self.stages: List[Stage] = []

    def add_stage(self, stage: Stage) -> "Pipeline":
        """Add a stage to the pipeline.

        Args:
            stage: Stage to add

        Returns:
            Self for method chaining
        """
        self.stages.append(stage)
        return self

    def execute(
        self,
        input_xml: Optional[Union[str, Path]] = None,
        xml_data: Optional[str] = None,
        context: Optional[PipelineContext] = None,
    ) -> PipelineResult:
        """Execute the pipeline.

        Args:
            input_xml: Path to input XML file
            xml_data: XML data as string
            context: Optional pre-configured context

        Returns:
            PipelineResult with execution details

        Raises:
            PipelineError: If pipeline execution fails
        """
        # Create or validate context
        if context is None:
            context = self._create_context(input_xml, xml_data)

        logger.info(
            f"Starting pipeline '{self.name}' with {len(self.stages)} stages "
            f"(execution_id={context.execution_id})"
        )

        stages_executed = 0
        stages_failed = 0
        last_error = None

        try:
            for stage in self.stages:
                logger.info(f"Executing stage: {stage.name}")

                # Validate stage input
                if not stage.validate_input(context):
                    error_msg = f"Stage '{stage.name}' input validation failed"
                    logger.error(error_msg)
                    raise PipelineError(error_msg)

                # Execute stage with error handling
                try:
                    result = self._execute_stage_with_recovery(stage, context)
                    stages_executed += 1

                    if not result.success:
                        stages_failed += 1
                        last_error = result.error

                except Exception as e:
                    stages_executed += 1
                    stages_failed += 1
                    last_error = str(e)

                    # Handle error based on strategy
                    if self.error_strategy == ErrorStrategy.FAIL_FAST:
                        raise
                    elif self.error_strategy == ErrorStrategy.CONTINUE:
                        logger.warning(f"Stage '{stage.name}' failed, continuing: {e}")
                        continue
                    elif self.error_strategy == ErrorStrategy.SKIP:
                        logger.warning(f"Stage '{stage.name}' failed, skipping: {e}")
                        continue
                    else:
                        # ROLLBACK and RETRY are handled in _execute_stage_with_recovery
                        raise

            # Check overall success
            success = stages_failed == 0

            logger.info(
                f"Pipeline '{self.name}' completed: "
                f"{stages_executed} executed, {stages_failed} failed, "
                f"duration={context.elapsed_seconds:.2f}s"
            )

            return PipelineResult(
                pipeline_name=self.name,
                success=success,
                context=context,
                error=last_error,
                stages_executed=stages_executed,
                stages_failed=stages_failed,
            )

        except Exception as e:
            logger.error(f"Pipeline '{self.name}' failed: {e}")
            return PipelineResult(
                pipeline_name=self.name,
                success=False,
                context=context,
                error=str(e),
                stages_executed=stages_executed,
                stages_failed=stages_failed,
            )

    def _create_context(
        self,
        input_xml: Optional[Union[str, Path]],
        xml_data: Optional[str],
    ) -> PipelineContext:
        """Create pipeline context from input."""
        if input_xml:
            # Load from file
            input_path = Path(input_xml)
            if not input_path.exists():
                raise FileNotFoundError(f"Input file not found: {input_path}")

            xml_data = input_path.read_text()
            xml_tree = etree.parse(str(input_path)).getroot()

            return PipelineContext(
                xml_data=xml_data,
                xml_tree=xml_tree,
                input_path=input_path,
            )

        elif xml_data:
            # Use provided XML string
            try:
                xml_tree = etree.fromstring(xml_data.encode())
            except Exception as e:
                logger.warning(f"Failed to parse XML data: {e}")
                xml_tree = None

            return PipelineContext(
                xml_data=xml_data,
                xml_tree=xml_tree,
            )

        else:
            raise ValueError("Either input_xml or xml_data must be provided")

    def _execute_stage_with_recovery(
        self,
        stage: Stage,
        context: PipelineContext,
    ) -> StageResult:
        """Execute stage with error recovery and rollback support.

        Args:
            stage: Stage to execute
            context: Pipeline context

        Returns:
            StageResult from stage execution

        Raises:
            Exception: If stage fails and error strategy is FAIL_FAST
        """
        # Create snapshot before execution
        if self.rollback_enabled:
            self._create_snapshot(context, stage.name)

        try:
            # Execute the stage
            result = stage.execute(context)
            context.stage_results.append(result)
            return result

        except Exception as e:
            # Handle error based on strategy
            if self.error_strategy == ErrorStrategy.FAIL_FAST:
                raise

            elif self.error_strategy == ErrorStrategy.ROLLBACK:
                logger.warning(f"Stage '{stage.name}' failed, rolling back: {e}")
                self._rollback_to_stage(context, stage.name)
                raise PipelineError(f"Stage '{stage.name}' failed and was rolled back") from e

            elif self.error_strategy == ErrorStrategy.RETRY:
                logger.warning(f"Stage '{stage.name}' failed, retrying: {e}")
                return self._retry_stage(stage, context)

            elif self.error_strategy in (ErrorStrategy.SKIP, ErrorStrategy.CONTINUE):
                # Create a failed result and continue
                result = StageResult(
                    stage=stage.name,
                    success=False,
                    error=str(e),
                    data=context.xml_data,
                )
                context.stage_results.append(result)
                return result

            else:
                raise

    def _create_snapshot(self, context: PipelineContext, stage_name: str) -> None:
        """Create a snapshot of current XML state before stage execution.

        Args:
            context: Pipeline context
            stage_name: Name of stage about to execute
        """
        # Store current XML data and tree (as string)
        xml_tree_str = None
        if context.xml_tree is not None:
            xml_tree_str = etree.tostring(context.xml_tree).decode()

        context.snapshots.append((stage_name, context.xml_data, xml_tree_str))

        # Limit snapshot history
        if len(context.snapshots) > self.max_snapshots:
            context.snapshots = context.snapshots[-self.max_snapshots :]

        logger.debug(f"Created snapshot for stage '{stage_name}'")

    def _rollback_to_stage(self, context: PipelineContext, stage_name: str) -> bool:
        """Rollback context to the state before a specific stage.

        Args:
            context: Pipeline context
            stage_name: Name of stage to rollback to

        Returns:
            True if rollback succeeded, False if stage not found
        """
        # Find the snapshot for this stage
        for i, (name, xml_data, xml_tree_str) in enumerate(reversed(context.snapshots)):
            if name == stage_name:
                # Restore XML data and tree
                context.xml_data = xml_data

                if xml_tree_str:
                    try:
                        context.xml_tree = etree.fromstring(xml_tree_str.encode())
                    except Exception as e:
                        logger.warning(f"Failed to restore XML tree from snapshot: {e}")
                        context.xml_tree = None
                else:
                    context.xml_tree = None

                # Remove this snapshot and all after it
                snapshot_index = len(context.snapshots) - i - 1
                context.snapshots = context.snapshots[:snapshot_index]

                logger.info(f"Rolled back to stage '{stage_name}'")
                return True

        logger.warning(f"No snapshot found for stage '{stage_name}'")
        return False

    def _retry_stage(
        self,
        stage: Stage,
        context: PipelineContext,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
    ) -> StageResult:
        """Retry stage execution with exponential backoff.

        Args:
            stage: Stage to retry
            context: Pipeline context
            max_retries: Maximum number of retry attempts
            backoff_factor: Exponential backoff multiplier

        Returns:
            StageResult from successful execution

        Raises:
            Exception: If all retries fail
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                logger.info(f"Retry attempt {attempt + 1}/{max_retries} for stage '{stage.name}'")
                result = stage.execute(context)
                context.stage_results.append(result)
                logger.info(f"Stage '{stage.name}' succeeded on attempt {attempt + 1}")
                return result

            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Calculate backoff time
                    wait_time = backoff_factor**attempt
                    logger.warning(
                        f"Stage '{stage.name}' failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_time:.1f}s: {e}"
                    )
                    time.sleep(wait_time)

        # All retries failed
        logger.error(f"Stage '{stage.name}' failed after {max_retries} attempts")
        result = StageResult(
            stage=stage.name,
            success=False,
            error=f"Failed after {max_retries} attempts: {last_error}",
            data=context.xml_data,
        )
        context.stage_results.append(result)
        return result

    def dry_run(
        self,
        input_xml: Optional[Union[str, Path]] = None,
        xml_data: Optional[str] = None,
    ) -> List[str]:
        """Perform a dry run showing stages without executing.

        Args:
            input_xml: Path to input XML file
            xml_data: XML data as string

        Returns:
            List of stage names that would be executed
        """
        logger.info(f"Dry run for pipeline '{self.name}'")
        stage_names = [stage.name for stage in self.stages]

        for i, name in enumerate(stage_names, 1):
            logger.info(f"  {i}. {name}")

        return stage_names

    def to_dict(self) -> dict:
        """Convert pipeline to dictionary representation."""
        return {
            "name": self.name,
            "error_strategy": self.error_strategy.value,
            "rollback_enabled": self.rollback_enabled,
            "max_snapshots": self.max_snapshots,
            "stages": [
                {
                    "type": stage.__class__.__name__,
                    "name": stage.name,
                }
                for stage in self.stages
            ],
        }

    def __repr__(self) -> str:
        return (
            f"Pipeline(name='{self.name}', stages={len(self.stages)}, "
            f"error_strategy={self.error_strategy.value})"
        )
