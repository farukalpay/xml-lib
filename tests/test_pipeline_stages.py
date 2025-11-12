"""Tests for pipeline stages."""

import pytest
import tempfile
from pathlib import Path

from lxml import etree

from xml_lib.pipeline.context import (
    PipelineContext,
    StageResult,
    ValidationError,
    TransformationError,
    OutputError,
)
from xml_lib.pipeline.stages import (
    Stage,
    ValidateStage,
    TransformStage,
    OutputStage,
    CustomStage,
)


class TestStageBase:
    """Test base Stage class."""

    def test_stage_abstract(self):
        """Test that Stage is abstract and cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Stage()

    def test_custom_stage_name(self):
        """Test custom stage names."""

        class TestStage(Stage):
            def execute(self, context):
                return StageResult(stage=self.name, success=True)

        stage = TestStage(name="my_custom_name")
        assert stage.name == "my_custom_name"

    def test_default_stage_name(self):
        """Test default stage name is class name."""

        class MyTestStage(Stage):
            def execute(self, context):
                return StageResult(stage=self.name, success=True)

        stage = MyTestStage()
        assert stage.name == "MyTestStage"

    def test_validate_input_default(self):
        """Test default validate_input returns True."""

        class TestStage(Stage):
            def execute(self, context):
                return StageResult(stage=self.name, success=True)

        stage = TestStage()
        context = PipelineContext(xml_data="<root/>")

        assert stage.validate_input(context) is True

    def test_rollback_default(self):
        """Test default rollback does nothing."""

        class TestStage(Stage):
            def execute(self, context):
                return StageResult(stage=self.name, success=True)

        stage = TestStage()
        context = PipelineContext(xml_data="<root/>")

        # Should not raise
        stage.rollback(context)


class TestValidateStage:
    """Test ValidateStage."""

    def test_create_validate_stage(self):
        """Test creating a validate stage."""
        stage = ValidateStage(
            schemas_dir=Path("schemas"),
            guardrails_dir=Path("guardrails"),
            strict=True,
        )

        assert stage.schemas_dir == Path("schemas")
        assert stage.guardrails_dir == Path("guardrails")
        assert stage.strict is True

    def test_validate_stage_name(self):
        """Test validate stage with custom name."""
        stage = ValidateStage(name="my_validation")
        assert stage.name == "my_validation"

    def test_validate_input_requires_xml(self):
        """Test that validate_input checks for XML data."""
        stage = ValidateStage()

        # With XML data
        context = PipelineContext(xml_data="<root/>")
        assert stage.validate_input(context) is True

        # Empty XML data and no tree
        context_empty = PipelineContext(xml_data="")
        context_empty.xml_tree = None
        assert stage.validate_input(context_empty) is False

    def test_validate_stage_streaming_threshold(self):
        """Test streaming threshold configuration."""
        stage = ValidateStage(
            streaming=False,
            streaming_threshold=5 * 1024 * 1024,  # 5MB
        )

        assert stage.streaming is False
        assert stage.streaming_threshold == 5 * 1024 * 1024

    @pytest.mark.skipif(not Path("schemas").exists(), reason="Requires schemas directory")
    def test_validate_stage_execution(self):
        """Test executing validation stage."""
        # Create a simple valid XML
        xml_data = """<?xml version="1.0"?>
        <root>
            <child>test</child>
        </root>"""

        context = PipelineContext(xml_data=xml_data)
        stage = ValidateStage(strict=False)

        result = stage.execute(context)

        # Result should be a StageResult
        assert isinstance(result, StageResult)
        assert result.stage == stage.name
        assert isinstance(result.success, bool)


class TestTransformStage:
    """Test TransformStage."""

    def test_create_transform_stage_with_xslt(self):
        """Test creating transform stage with XSLT."""
        xslt_path = Path("transform.xsl")
        stage = TransformStage(
            transform=xslt_path,
            params={"key": "value"},
        )

        assert stage.transform == xslt_path
        assert stage.params == {"key": "value"}

    def test_create_transform_stage_with_function(self):
        """Test creating transform stage with Python function."""

        def my_transform(xml_data, context):
            return xml_data.replace("old", "new")

        stage = TransformStage(transform=my_transform)

        assert stage.transform == my_transform
        assert callable(stage.transform)

    def test_transform_stage_validate_input(self):
        """Test transform stage input validation."""
        stage = TransformStage(transform=lambda x, c: x)

        # With XML data
        context = PipelineContext(xml_data="<root/>")
        assert stage.validate_input(context) is True

        # Without XML
        context_empty = PipelineContext(xml_data="")
        context_empty.xml_tree = None
        assert stage.validate_input(context_empty) is False

    def test_transform_with_python_function(self):
        """Test transformation with Python function."""

        def add_attribute(xml_data, context):
            # Simple transformation: add an attribute
            return xml_data.replace("<root>", '<root modified="true">')

        stage = TransformStage(transform=add_attribute, name="add_attr")

        xml_data = "<root><child>test</child></root>"
        context = PipelineContext(xml_data=xml_data)

        result = stage.execute(context)

        assert result.success is True
        assert 'modified="true"' in context.xml_data
        assert context.xml_tree is not None
        assert context.xml_tree.get("modified") == "true"

    def test_transform_with_xslt_file(self):
        """Test transformation with XSLT file."""
        # Create a simple XSLT that copies everything
        xslt_content = """<?xml version="1.0"?>
        <xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
            <xsl:template match="@*|node()">
                <xsl:copy>
                    <xsl:apply-templates select="@*|node()"/>
                </xsl:copy>
            </xsl:template>
        </xsl:stylesheet>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xsl", delete=False) as f:
            f.write(xslt_content)
            xslt_path = Path(f.name)

        try:
            stage = TransformStage(transform=xslt_path, name="xslt_copy")

            xml_data = "<root><child>test</child></root>"
            context = PipelineContext(xml_data=xml_data)

            result = stage.execute(context)

            assert result.success is True
            assert "<child>test</child>" in context.xml_data

        finally:
            xslt_path.unlink()

    def test_transform_error_handling(self):
        """Test transformation error handling."""

        def failing_transform(xml_data, context):
            raise ValueError("Transform failed")

        stage = TransformStage(transform=failing_transform, name="failing")

        context = PipelineContext(xml_data="<root/>")

        with pytest.raises(TransformationError) as exc_info:
            stage.execute(context)

        assert "failing" in str(exc_info.value)


class TestOutputStage:
    """Test OutputStage."""

    def test_create_output_stage(self):
        """Test creating output stage."""
        stage = OutputStage(
            format="xml",
            output_path=Path("out/result.xml"),
        )

        assert stage.format == "xml"
        assert stage.output_path == Path("out/result.xml")

    def test_output_stage_supported_formats(self):
        """Test supported output formats."""
        supported = OutputStage.SUPPORTED_FORMATS

        assert "html" in supported
        assert "pptx" in supported
        assert "php" in supported
        assert "json" in supported
        assert "xml" in supported
        assert "assertions" in supported

    def test_output_stage_invalid_format(self):
        """Test that invalid format raises error."""
        with pytest.raises(ValueError) as exc_info:
            OutputStage(format="invalid", output_path=Path("out.txt"))

        assert "Unsupported format" in str(exc_info.value)

    def test_output_stage_validate_input(self):
        """Test output stage input validation."""
        stage = OutputStage(format="xml", output_path=Path("out.xml"))

        # With XML data
        context = PipelineContext(xml_data="<root/>")
        assert stage.validate_input(context) is True

        # Without XML
        context_empty = PipelineContext(xml_data="")
        context_empty.xml_tree = None
        assert stage.validate_input(context_empty) is False

    def test_output_xml_format(self):
        """Test outputting XML format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.xml"

            stage = OutputStage(format="xml", output_path=output_path, name="write_xml")

            xml_data = "<root><child>test</child></root>"
            context = PipelineContext(xml_data=xml_data)

            result = stage.execute(context)

            assert result.success is True
            assert output_path.exists()

            # Check content
            content = output_path.read_text()
            assert "<root>" in content
            assert "<child>test</child>" in content

    def test_output_json_format(self):
        """Test outputting JSON format (context metadata)."""
        import json

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.json"

            stage = OutputStage(format="json", output_path=output_path, name="write_json")

            xml_data = "<root><child>test</child></root>"
            context = PipelineContext(xml_data=xml_data)
            context.set_variable("key", "value")

            result = stage.execute(context)

            assert result.success is True
            assert output_path.exists()

            # Check JSON content
            with open(output_path) as f:
                data = json.load(f)

            assert "execution_id" in data
            assert data["variables"]["key"] == "value"

    def test_output_creates_parent_directories(self):
        """Test that output stage creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sub" / "dir" / "output.xml"

            stage = OutputStage(format="xml", output_path=output_path)

            xml_data = "<root/>"
            context = PipelineContext(xml_data=xml_data)

            result = stage.execute(context)

            assert result.success is True
            assert output_path.exists()
            assert output_path.parent.exists()


class TestCustomStage:
    """Test CustomStage."""

    def test_create_custom_stage(self):
        """Test creating a custom stage."""

        def my_function(context):
            return StageResult(stage="custom", success=True, data=context.xml_data)

        stage = CustomStage(function=my_function, name="my_custom")

        assert stage.function == my_function
        assert stage.name == "my_custom"

    def test_custom_stage_execution(self):
        """Test executing custom stage."""

        def uppercase_xml(context):
            context.xml_data = context.xml_data.upper()
            return StageResult(
                stage="uppercase",
                success=True,
                data=context.xml_data,
            )

        stage = CustomStage(function=uppercase_xml, name="uppercase")

        xml_data = "<root><child>test</child></root>"
        context = PipelineContext(xml_data=xml_data)

        result = stage.execute(context)

        assert result.success is True
        assert context.xml_data == context.xml_data.upper()
        assert "<ROOT>" in context.xml_data

    def test_custom_stage_with_rollback(self):
        """Test custom stage with rollback function."""
        rollback_called = []

        def my_function(context):
            context.set_variable("modified", True)
            return StageResult(stage="custom", success=True)

        def my_rollback(context):
            rollback_called.append(True)
            context.set_variable("modified", False)

        stage = CustomStage(
            function=my_function,
            rollback_function=my_rollback,
            name="custom_with_rollback",
        )

        context = PipelineContext(xml_data="<root/>")

        # Execute
        result = stage.execute(context)
        assert result.success is True
        assert context.get_variable("modified") is True

        # Rollback
        stage.rollback(context)
        assert len(rollback_called) == 1
        assert context.get_variable("modified") is False

    def test_custom_stage_error_handling(self):
        """Test custom stage error handling."""

        def failing_function(context):
            raise RuntimeError("Custom function failed")

        stage = CustomStage(function=failing_function, name="failing_custom")

        context = PipelineContext(xml_data="<root/>")

        with pytest.raises(Exception):
            stage.execute(context)
