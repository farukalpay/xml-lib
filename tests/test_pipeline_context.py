"""Tests for pipeline context and result types."""

import pytest
from datetime import datetime
from pathlib import Path

from lxml import etree

from xml_lib.pipeline.context import (
    ErrorStrategy,
    PipelineContext,
    PipelineError,
    PipelineResult,
    StageError,
    StageResult,
    TransformationError,
    ValidationError,
)


class TestErrorStrategy:
    """Test error strategy enumeration."""

    def test_error_strategy_values(self):
        """Test that all error strategies have correct values."""
        assert ErrorStrategy.FAIL_FAST.value == "fail_fast"
        assert ErrorStrategy.CONTINUE.value == "continue"
        assert ErrorStrategy.ROLLBACK.value == "rollback"
        assert ErrorStrategy.RETRY.value == "retry"
        assert ErrorStrategy.SKIP.value == "skip"


class TestStageResult:
    """Test stage result representation."""

    def test_create_stage_result(self):
        """Test creating a stage result."""
        result = StageResult(
            stage="test_stage",
            success=True,
            data="<xml/>",
            metadata={"key": "value"},
            duration_seconds=1.5,
        )

        assert result.stage == "test_stage"
        assert result.success is True
        assert result.data == "<xml/>"
        assert result.metadata == {"key": "value"}
        assert result.duration_seconds == 1.5
        assert isinstance(result.timestamp, datetime)

    def test_stage_result_to_dict(self):
        """Test converting stage result to dictionary."""
        result = StageResult(
            stage="test_stage",
            success=True,
            metadata={"key": "value"},
        )

        result_dict = result.to_dict()

        assert result_dict["stage"] == "test_stage"
        assert result_dict["success"] is True
        assert result_dict["error"] is None
        assert result_dict["metadata"] == {"key": "value"}
        assert "timestamp" in result_dict

    def test_stage_result_with_error(self):
        """Test stage result with error."""
        result = StageResult(
            stage="failed_stage",
            success=False,
            error="Something went wrong",
        )

        assert result.success is False
        assert result.error == "Something went wrong"

        result_dict = result.to_dict()
        assert result_dict["error"] == "Something went wrong"


class TestPipelineContext:
    """Test pipeline execution context."""

    def test_create_context_from_xml_string(self):
        """Test creating context from XML string."""
        xml_data = "<root><child>test</child></root>"
        context = PipelineContext(xml_data=xml_data)

        assert context.xml_data == xml_data
        assert context.xml_tree is not None
        assert context.xml_tree.tag == "root"
        assert isinstance(context.execution_id, str)
        assert len(context.execution_id) > 0

    def test_create_context_with_tree(self):
        """Test creating context with parsed tree."""
        xml_data = "<root><child>test</child></root>"
        xml_tree = etree.fromstring(xml_data.encode())

        context = PipelineContext(xml_data=xml_data, xml_tree=xml_tree)

        assert context.xml_data == xml_data
        assert context.xml_tree is xml_tree

    def test_context_with_file_path(self):
        """Test context with input/output paths."""
        xml_data = "<root/>"
        context = PipelineContext(
            xml_data=xml_data,
            input_path=Path("input.xml"),
            output_path=Path("output.xml"),
        )

        assert context.input_path == Path("input.xml")
        assert context.output_path == Path("output.xml")

    def test_context_elapsed_seconds(self):
        """Test elapsed time calculation."""
        import time

        context = PipelineContext(xml_data="<root/>")
        time.sleep(0.1)

        assert context.elapsed_seconds >= 0.1

    def test_context_stage_results(self):
        """Test tracking stage results."""
        context = PipelineContext(xml_data="<root/>")

        assert len(context.stage_results) == 0
        assert context.last_result is None

        # Add a result
        result1 = StageResult(stage="stage1", success=True)
        context.stage_results.append(result1)

        assert len(context.stage_results) == 1
        assert context.last_result is result1

        # Add another result
        result2 = StageResult(stage="stage2", success=True)
        context.stage_results.append(result2)

        assert len(context.stage_results) == 2
        assert context.last_result is result2

    def test_context_all_successful(self):
        """Test checking if all stages succeeded."""
        context = PipelineContext(xml_data="<root/>")

        # No results - should be True
        assert context.all_successful is True

        # All successful
        context.stage_results.append(StageResult(stage="s1", success=True))
        context.stage_results.append(StageResult(stage="s2", success=True))
        assert context.all_successful is True

        # One failure
        context.stage_results.append(StageResult(stage="s3", success=False))
        assert context.all_successful is False

    def test_context_variables(self):
        """Test context variable storage."""
        context = PipelineContext(xml_data="<root/>")

        # Get non-existent variable with default
        assert context.get_variable("missing") is None
        assert context.get_variable("missing", "default") == "default"

        # Set and get variable
        context.set_variable("key", "value")
        assert context.get_variable("key") == "value"

        # Update variable
        context.set_variable("key", "new_value")
        assert context.get_variable("key") == "new_value"

    def test_context_snapshots(self):
        """Test snapshot storage."""
        context = PipelineContext(xml_data="<root/>")

        assert len(context.snapshots) == 0

        # Add snapshots
        context.snapshots.append(("stage1", "<root1/>", None))
        context.snapshots.append(("stage2", "<root2/>", None))

        assert len(context.snapshots) == 2
        assert context.snapshots[0][0] == "stage1"
        assert context.snapshots[1][0] == "stage2"

    def test_context_to_dict(self):
        """Test converting context to dictionary."""
        context = PipelineContext(
            xml_data="<root/>",
            input_path=Path("input.xml"),
        )

        context.set_variable("var1", "value1")
        context.stage_results.append(StageResult(stage="s1", success=True))

        context_dict = context.to_dict()

        assert "execution_id" in context_dict
        assert context_dict["input_path"] == "input.xml"
        assert context_dict["variables"] == {"var1": "value1"}
        assert len(context_dict["stage_results"]) == 1
        assert context_dict["all_successful"] is True

    def test_context_with_invalid_xml(self):
        """Test context with invalid XML data."""
        invalid_xml = "<root><unclosed"
        context = PipelineContext(xml_data=invalid_xml)

        # Should not raise, but tree should be None
        assert context.xml_tree is None


class TestPipelineResult:
    """Test pipeline result representation."""

    def test_create_pipeline_result(self):
        """Test creating a pipeline result."""
        context = PipelineContext(xml_data="<root/>")
        result = PipelineResult(
            pipeline_name="test_pipeline",
            success=True,
            context=context,
            stages_executed=3,
            stages_failed=0,
        )

        assert result.pipeline_name == "test_pipeline"
        assert result.success is True
        assert result.context is context
        assert result.stages_executed == 3
        assert result.stages_failed == 0
        assert result.error is None

    def test_pipeline_result_with_failure(self):
        """Test pipeline result with failure."""
        context = PipelineContext(xml_data="<root/>")
        result = PipelineResult(
            pipeline_name="test_pipeline",
            success=False,
            context=context,
            error="Pipeline failed",
            stages_executed=2,
            stages_failed=1,
        )

        assert result.success is False
        assert result.error == "Pipeline failed"
        assert result.stages_failed == 1

    def test_pipeline_result_duration(self):
        """Test pipeline duration calculation."""
        import time

        context = PipelineContext(xml_data="<root/>")
        time.sleep(0.1)

        result = PipelineResult(
            pipeline_name="test",
            success=True,
            context=context,
        )

        assert result.duration_seconds >= 0.1

    def test_pipeline_result_to_dict(self):
        """Test converting pipeline result to dictionary."""
        context = PipelineContext(xml_data="<root/>")
        result = PipelineResult(
            pipeline_name="test_pipeline",
            success=True,
            context=context,
            stages_executed=2,
            stages_failed=0,
        )

        result_dict = result.to_dict()

        assert result_dict["pipeline_name"] == "test_pipeline"
        assert result_dict["success"] is True
        assert result_dict["stages_executed"] == 2
        assert result_dict["stages_failed"] == 0
        assert "context" in result_dict
        assert "duration_seconds" in result_dict


class TestPipelineExceptions:
    """Test pipeline exception types."""

    def test_pipeline_error(self):
        """Test PipelineError exception."""
        error = PipelineError("Test error")
        assert str(error) == "Test error"

    def test_stage_error(self):
        """Test StageError exception."""
        error = StageError("test_stage", "Test error")
        assert error.stage_name == "test_stage"
        assert error.message == "Test error"
        assert "test_stage" in str(error)
        assert "Test error" in str(error)

    def test_stage_error_with_original(self):
        """Test StageError with original exception."""
        original = ValueError("Original error")
        error = StageError("test_stage", "Wrapped error", original)

        assert error.original_error is original

    def test_validation_error(self):
        """Test ValidationError exception."""
        error = ValidationError("validate_stage", "Validation failed")
        assert error.stage_name == "validate_stage"
        assert isinstance(error, StageError)

    def test_transformation_error(self):
        """Test TransformationError exception."""
        error = TransformationError("transform_stage", "Transform failed")
        assert error.stage_name == "transform_stage"
        assert isinstance(error, StageError)

    def test_output_error(self):
        """Test OutputError exception."""
        from xml_lib.pipeline.context import OutputError

        error = OutputError("output_stage", "Output failed")
        assert error.stage_name == "output_stage"
        assert isinstance(error, StageError)
