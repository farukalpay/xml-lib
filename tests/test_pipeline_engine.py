"""Tests for pipeline execution engine."""

import pytest
import tempfile
import time
from pathlib import Path

from lxml import etree

from xml_lib.pipeline import (
    Pipeline,
    PipelineContext,
    PipelineResult,
    ErrorStrategy,
    Stage,
    StageResult,
    ValidateStage,
    TransformStage,
    OutputStage,
    CustomStage,
    PipelineError,
)


class MockStage(Stage):
    """Mock stage for testing."""

    def __init__(self, name="mock", should_fail=False, sleep_duration=0):
        super().__init__(name)
        self.should_fail = should_fail
        self.sleep_duration = sleep_duration
        self.executed = False

    def execute(self, context):
        self.executed = True

        if self.sleep_duration > 0:
            time.sleep(self.sleep_duration)

        if self.should_fail:
            raise Exception(f"Stage {self.name} failed")

        return StageResult(
            stage=self.name,
            success=True,
            data=context.xml_data,
        )


class TestPipelineCreation:
    """Test pipeline creation and configuration."""

    def test_create_pipeline(self):
        """Test creating a basic pipeline."""
        pipeline = Pipeline(name="test_pipeline")

        assert pipeline.name == "test_pipeline"
        assert pipeline.error_strategy == ErrorStrategy.FAIL_FAST
        assert pipeline.rollback_enabled is True
        assert len(pipeline.stages) == 0

    def test_pipeline_with_error_strategy(self):
        """Test pipeline with specific error strategy."""
        pipeline = Pipeline(
            name="test",
            error_strategy=ErrorStrategy.CONTINUE,
        )

        assert pipeline.error_strategy == ErrorStrategy.CONTINUE

    def test_pipeline_with_rollback_disabled(self):
        """Test pipeline with rollback disabled."""
        pipeline = Pipeline(
            name="test",
            rollback_enabled=False,
        )

        assert pipeline.rollback_enabled is False

    def test_add_stage(self):
        """Test adding stages to pipeline."""
        pipeline = Pipeline(name="test")

        stage1 = MockStage("stage1")
        stage2 = MockStage("stage2")

        pipeline.add_stage(stage1)
        pipeline.add_stage(stage2)

        assert len(pipeline.stages) == 2
        assert pipeline.stages[0] is stage1
        assert pipeline.stages[1] is stage2

    def test_add_stage_chaining(self):
        """Test that add_stage returns self for chaining."""
        pipeline = Pipeline(name="test")

        result = pipeline.add_stage(MockStage("stage1")).add_stage(MockStage("stage2"))

        assert result is pipeline
        assert len(pipeline.stages) == 2

    def test_pipeline_repr(self):
        """Test pipeline string representation."""
        pipeline = Pipeline(name="my_pipeline")
        pipeline.add_stage(MockStage("stage1"))

        repr_str = repr(pipeline)

        assert "my_pipeline" in repr_str
        assert "stages=1" in repr_str

    def test_pipeline_to_dict(self):
        """Test converting pipeline to dictionary."""
        pipeline = Pipeline(
            name="test_pipeline",
            error_strategy=ErrorStrategy.ROLLBACK,
        )
        pipeline.add_stage(MockStage("stage1"))
        pipeline.add_stage(MockStage("stage2"))

        pipeline_dict = pipeline.to_dict()

        assert pipeline_dict["name"] == "test_pipeline"
        assert pipeline_dict["error_strategy"] == "rollback"
        assert len(pipeline_dict["stages"]) == 2


class TestPipelineExecution:
    """Test pipeline execution."""

    def test_execute_pipeline_with_xml_string(self):
        """Test executing pipeline with XML string."""
        pipeline = Pipeline(name="test")
        pipeline.add_stage(MockStage("stage1"))
        pipeline.add_stage(MockStage("stage2"))

        xml_data = "<root><child>test</child></root>"
        result = pipeline.execute(xml_data=xml_data)

        assert isinstance(result, PipelineResult)
        assert result.success is True
        assert result.pipeline_name == "test"
        assert result.stages_executed == 2
        assert result.stages_failed == 0

    def test_execute_pipeline_with_file(self):
        """Test executing pipeline with XML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write("<root><child>test</child></root>")
            xml_path = Path(f.name)

        try:
            pipeline = Pipeline(name="test")
            pipeline.add_stage(MockStage("stage1"))

            result = pipeline.execute(input_xml=xml_path)

            assert result.success is True
            assert result.context.input_path == xml_path

        finally:
            xml_path.unlink()

    def test_execute_pipeline_with_context(self):
        """Test executing pipeline with pre-configured context."""
        context = PipelineContext(xml_data="<root/>")
        context.set_variable("custom", "value")

        pipeline = Pipeline(name="test")
        pipeline.add_stage(MockStage("stage1"))

        result = pipeline.execute(context=context)

        assert result.success is True
        assert result.context is context
        assert result.context.get_variable("custom") == "value"

    def test_execute_without_input(self):
        """Test that execute requires input."""
        pipeline = Pipeline(name="test")

        with pytest.raises(ValueError) as exc_info:
            pipeline.execute()

        assert "input_xml or xml_data must be provided" in str(exc_info.value)

    def test_execute_with_nonexistent_file(self):
        """Test execute with non-existent file."""
        pipeline = Pipeline(name="test")

        with pytest.raises(FileNotFoundError):
            pipeline.execute(input_xml="nonexistent.xml")

    def test_execute_stages_in_order(self):
        """Test that stages execute in order."""
        stage1 = MockStage("stage1")
        stage2 = MockStage("stage2")
        stage3 = MockStage("stage3")

        pipeline = Pipeline(name="test")
        pipeline.add_stage(stage1)
        pipeline.add_stage(stage2)
        pipeline.add_stage(stage3)

        result = pipeline.execute(xml_data="<root/>")

        assert result.success is True
        assert stage1.executed
        assert stage2.executed
        assert stage3.executed

        # Check order in results
        assert len(result.context.stage_results) == 3
        assert result.context.stage_results[0].stage == "stage1"
        assert result.context.stage_results[1].stage == "stage2"
        assert result.context.stage_results[2].stage == "stage3"

    def test_pipeline_duration_tracking(self):
        """Test that pipeline tracks execution duration."""
        pipeline = Pipeline(name="test")
        pipeline.add_stage(MockStage("stage1", sleep_duration=0.1))
        pipeline.add_stage(MockStage("stage2", sleep_duration=0.1))

        result = pipeline.execute(xml_data="<root/>")

        assert result.duration_seconds >= 0.2

    def test_dry_run(self):
        """Test pipeline dry run."""
        pipeline = Pipeline(name="test")
        stage1 = MockStage("stage1")
        stage2 = MockStage("stage2")
        pipeline.add_stage(stage1)
        pipeline.add_stage(stage2)

        stage_names = pipeline.dry_run(xml_data="<root/>")

        assert stage_names == ["stage1", "stage2"]
        # Stages should not have been executed
        assert not stage1.executed
        assert not stage2.executed


class TestPipelineErrorHandling:
    """Test pipeline error handling strategies."""

    def test_fail_fast_strategy(self):
        """Test FAIL_FAST strategy stops on first error."""
        pipeline = Pipeline(name="test", error_strategy=ErrorStrategy.FAIL_FAST)
        pipeline.add_stage(MockStage("stage1"))
        pipeline.add_stage(MockStage("stage2", should_fail=True))
        pipeline.add_stage(MockStage("stage3"))

        result = pipeline.execute(xml_data="<root/>")

        assert result.success is False
        assert result.stages_executed == 2
        assert result.stages_failed == 1
        # With FAIL_FAST, only successful stages are recorded before failure
        assert len(result.context.stage_results) >= 1
        assert result.context.stage_results[0].stage == "stage1"

    def test_continue_strategy(self):
        """Test CONTINUE strategy logs errors but continues."""
        pipeline = Pipeline(name="test", error_strategy=ErrorStrategy.CONTINUE)
        pipeline.add_stage(MockStage("stage1"))
        pipeline.add_stage(MockStage("stage2", should_fail=True))
        pipeline.add_stage(MockStage("stage3"))

        result = pipeline.execute(xml_data="<root/>")

        assert result.success is False
        assert result.stages_executed == 3
        assert result.stages_failed == 1
        # All stages should have results
        assert len(result.context.stage_results) == 3

    def test_skip_strategy(self):
        """Test SKIP strategy skips failed stage and continues."""
        pipeline = Pipeline(name="test", error_strategy=ErrorStrategy.SKIP)
        pipeline.add_stage(MockStage("stage1"))
        pipeline.add_stage(MockStage("stage2", should_fail=True))
        pipeline.add_stage(MockStage("stage3"))

        result = pipeline.execute(xml_data="<root/>")

        assert result.success is False
        assert result.stages_executed == 3
        assert result.stages_failed == 1

        # Check results
        assert len(result.context.stage_results) == 3
        assert result.context.stage_results[0].success is True
        assert result.context.stage_results[1].success is False
        assert result.context.stage_results[2].success is True


class TestPipelineRollback:
    """Test pipeline rollback mechanisms."""

    def test_rollback_creates_snapshots(self):
        """Test that rollback creates snapshots before each stage."""
        pipeline = Pipeline(name="test", rollback_enabled=True)
        pipeline.add_stage(MockStage("stage1"))
        pipeline.add_stage(MockStage("stage2"))

        result = pipeline.execute(xml_data="<root/>")

        assert result.success is True
        # Should have snapshots for each stage
        assert len(result.context.snapshots) == 2

    def test_rollback_disabled_no_snapshots(self):
        """Test that disabling rollback doesn't create snapshots."""
        pipeline = Pipeline(name="test", rollback_enabled=False)
        pipeline.add_stage(MockStage("stage1"))
        pipeline.add_stage(MockStage("stage2"))

        result = pipeline.execute(xml_data="<root/>")

        assert result.success is True
        assert len(result.context.snapshots) == 0

    def test_rollback_on_error(self):
        """Test rollback on stage error."""
        pipeline = Pipeline(name="test", error_strategy=ErrorStrategy.ROLLBACK)

        # Add stage that modifies XML
        def modify_xml(context):
            context.xml_data = context.xml_data.replace("<root>", "<modified>")
            context.xml_tree = etree.fromstring(context.xml_data.encode())
            return StageResult(stage="modify", success=True)

        pipeline.add_stage(CustomStage(function=modify_xml, name="modify"))
        pipeline.add_stage(MockStage("failing", should_fail=True))

        result = pipeline.execute(xml_data="<root><child/></root>")

        assert result.success is False
        # XML should be rolled back to original state
        assert result.context.xml_data == "<root><child/></root>"

    def test_rollback_max_snapshots(self):
        """Test that rollback limits snapshot history."""
        pipeline = Pipeline(name="test", max_snapshots=5, rollback_enabled=True)

        # Add many stages
        for i in range(10):
            pipeline.add_stage(MockStage(f"stage{i}"))

        result = pipeline.execute(xml_data="<root/>")

        assert result.success is True
        # Should only keep last 5 snapshots
        assert len(result.context.snapshots) <= 5


class TestPipelineRetry:
    """Test pipeline retry mechanism."""

    def test_retry_strategy(self):
        """Test RETRY strategy retries failed stages."""
        # Create a stage that fails first time but succeeds on retry
        class FlakeyStage(Stage):
            def __init__(self):
                super().__init__("flakey")
                self.attempts = 0

            def execute(self, context):
                self.attempts += 1
                if self.attempts == 1:
                    raise Exception("First attempt failed")
                return StageResult(stage=self.name, success=True)

        pipeline = Pipeline(name="test", error_strategy=ErrorStrategy.RETRY)
        flakey = FlakeyStage()
        pipeline.add_stage(flakey)

        result = pipeline.execute(xml_data="<root/>")

        assert result.success is True
        assert flakey.attempts >= 2  # Should have retried

    def test_retry_exhaustion(self):
        """Test that retry eventually gives up."""
        pipeline = Pipeline(name="test", error_strategy=ErrorStrategy.RETRY)
        pipeline.add_stage(MockStage("always_fails", should_fail=True))

        result = pipeline.execute(xml_data="<root/>")

        assert result.success is False
        # Should have retried and eventually failed
        assert result.stages_failed == 1


class TestPipelineIntegration:
    """Integration tests with real stages."""

    def test_pipeline_with_transform_and_output(self):
        """Test pipeline with transform and output stages."""

        def add_timestamp(xml_data, context):
            return xml_data.replace("</root>", '<timestamp>2024</timestamp></root>')

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.xml"

            pipeline = Pipeline(name="test")
            pipeline.add_stage(TransformStage(transform=add_timestamp, name="add_ts"))
            pipeline.add_stage(OutputStage(format="xml", output_path=output_path, name="write"))

            result = pipeline.execute(xml_data="<root><data>test</data></root>")

            assert result.success is True
            assert output_path.exists()

            content = output_path.read_text()
            assert "<timestamp>2024</timestamp>" in content

    def test_pipeline_with_custom_stage(self):
        """Test pipeline with custom stage."""

        def count_elements(context):
            count = len(context.xml_tree.findall(".//*"))
            context.set_variable("element_count", count)
            return StageResult(
                stage="count",
                success=True,
                metadata={"count": count},
            )

        pipeline = Pipeline(name="test")
        pipeline.add_stage(CustomStage(function=count_elements, name="count_elements"))

        xml_data = "<root><a/><b/><c/></root>"
        result = pipeline.execute(xml_data=xml_data)

        assert result.success is True
        # findall(".//*") finds all descendants: a, b, c = 3 elements
        assert result.context.get_variable("element_count") == 3

    def test_complex_pipeline(self):
        """Test a complex pipeline with multiple stage types."""

        def enrich_xml(xml_data, context):
            return xml_data.replace("<root>", '<root version="2.0">')

        def validate_enriched(context):
            # Check that version attribute was added
            if context.xml_tree.get("version") != "2.0":
                raise ValueError("Version not found")
            return StageResult(stage="validate_enriched", success=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            xml_out = Path(tmpdir) / "output.xml"
            json_out = Path(tmpdir) / "metadata.json"

            pipeline = Pipeline(name="complex")
            pipeline.add_stage(TransformStage(transform=enrich_xml, name="enrich"))
            pipeline.add_stage(CustomStage(function=validate_enriched, name="validate"))
            pipeline.add_stage(OutputStage(format="xml", output_path=xml_out, name="write_xml"))
            pipeline.add_stage(OutputStage(format="json", output_path=json_out, name="write_json"))

            result = pipeline.execute(xml_data="<root><data>test</data></root>")

            assert result.success is True
            assert result.stages_executed == 4
            assert xml_out.exists()
            assert json_out.exists()

            xml_content = xml_out.read_text()
            assert 'version="2.0"' in xml_content
