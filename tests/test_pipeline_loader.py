"""Tests for pipeline YAML loader."""

import pytest
import tempfile
from pathlib import Path

from xml_lib.pipeline import (
    Pipeline,
    ErrorStrategy,
    ValidateStage,
    TransformStage,
    OutputStage,
    load_pipeline,
)
from xml_lib.pipeline.loader import PipelineLoader


class TestPipelineLoader:
    """Test YAML pipeline loader."""

    def test_load_simple_pipeline(self):
        """Test loading a simple pipeline from YAML."""
        yaml_content = """
name: test_pipeline
description: A test pipeline
error_strategy: fail_fast
rollback_enabled: true

stages:
  - type: validate
    name: validate_input
    schemas_dir: schemas
    strict: true

  - type: output
    name: output_xml
    format: xml
    output_path: out/result.xml
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            pipeline = load_pipeline(yaml_path)

            assert pipeline.name == "test_pipeline"
            assert pipeline.error_strategy == ErrorStrategy.FAIL_FAST
            assert pipeline.rollback_enabled is True
            assert len(pipeline.stages) == 2

            # Check stages
            assert isinstance(pipeline.stages[0], ValidateStage)
            assert pipeline.stages[0].name == "validate_input"

            assert isinstance(pipeline.stages[1], OutputStage)
            assert pipeline.stages[1].name == "output_xml"

        finally:
            yaml_path.unlink()

    def test_load_pipeline_with_error_strategies(self):
        """Test loading pipelines with different error strategies."""
        strategies = [
            ("fail_fast", ErrorStrategy.FAIL_FAST),
            ("continue", ErrorStrategy.CONTINUE),
            ("rollback", ErrorStrategy.ROLLBACK),
            ("retry", ErrorStrategy.RETRY),
            ("skip", ErrorStrategy.SKIP),
        ]

        for yaml_value, expected_strategy in strategies:
            yaml_content = f"""
name: test
error_strategy: {yaml_value}
stages:
  - type: validate
    name: validate
    schemas_dir: schemas
"""
            with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
                f.write(yaml_content)
                yaml_path = Path(f.name)

            try:
                pipeline = load_pipeline(yaml_path)
                assert pipeline.error_strategy == expected_strategy
            finally:
                yaml_path.unlink()

    def test_load_pipeline_invalid_error_strategy(self):
        """Test that invalid error strategy raises error."""
        yaml_content = """
name: test
error_strategy: invalid_strategy
stages:
  - type: validate
    name: validate
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            with pytest.raises(ValueError) as exc_info:
                load_pipeline(yaml_path)

            assert "Invalid error_strategy" in str(exc_info.value)

        finally:
            yaml_path.unlink()

    def test_load_pipeline_with_variables(self):
        """Test loading pipeline with variables."""
        yaml_content = """
name: test
variables:
  version: "1.0"
  timestamp: "2024-01-01"

stages:
  - type: validate
    name: validate
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            loader = PipelineLoader()
            pipeline = loader.load(yaml_path)

            assert loader.variables["version"] == "1.0"
            assert loader.variables["timestamp"] == "2024-01-01"

        finally:
            yaml_path.unlink()

    def test_load_pipeline_without_stages(self):
        """Test that pipeline without stages raises error."""
        yaml_content = """
name: test
error_strategy: fail_fast
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            with pytest.raises(ValueError) as exc_info:
                load_pipeline(yaml_path)

            assert "at least one stage" in str(exc_info.value)

        finally:
            yaml_path.unlink()

    def test_load_nonexistent_file(self):
        """Test loading non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_pipeline(Path("nonexistent.yaml"))

    def test_load_invalid_yaml(self):
        """Test loading invalid YAML raises error."""
        yaml_content = """
name: test
stages: [this is not valid yaml
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            with pytest.raises(Exception):  # YAML parse error
                load_pipeline(yaml_path)

        finally:
            yaml_path.unlink()


class TestLoadValidateStage:
    """Test loading ValidateStage from YAML."""

    def test_load_validate_stage(self):
        """Test loading validate stage."""
        yaml_content = """
name: test
stages:
  - type: validate
    name: validate_input
    schemas_dir: schemas
    guardrails_dir: guardrails
    strict: true
    streaming: false
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            pipeline = load_pipeline(yaml_path)
            stage = pipeline.stages[0]

            assert isinstance(stage, ValidateStage)
            assert stage.name == "validate_input"
            assert stage.strict is True
            assert stage.streaming is False

        finally:
            yaml_path.unlink()

    def test_load_validate_stage_defaults(self):
        """Test validate stage with default values."""
        yaml_content = """
name: test
stages:
  - type: validate
    name: validate
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            pipeline = load_pipeline(yaml_path)
            stage = pipeline.stages[0]

            assert isinstance(stage, ValidateStage)
            assert stage.strict is True  # default

        finally:
            yaml_path.unlink()


class TestLoadTransformStage:
    """Test loading TransformStage from YAML."""

    def test_load_transform_stage(self):
        """Test loading transform stage with XSLT."""
        # Create a dummy XSLT file
        xslt_content = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:template match="/">
        <xsl:copy-of select="."/>
    </xsl:template>
</xsl:stylesheet>"""

        with tempfile.TemporaryDirectory() as tmpdir:
            xslt_path = Path(tmpdir) / "transform.xsl"
            xslt_path.write_text(xslt_content)

            yaml_content = f"""
name: test
stages:
  - type: transform
    name: my_transform
    transform: {xslt_path.name}
    params:
      key1: value1
      key2: value2
"""
            yaml_path = Path(tmpdir) / "pipeline.yaml"
            yaml_path.write_text(yaml_content)

            pipeline = load_pipeline(yaml_path)
            stage = pipeline.stages[0]

            assert isinstance(stage, TransformStage)
            assert stage.name == "my_transform"
            assert stage.params == {"key1": "value1", "key2": "value2"}

    def test_load_transform_stage_missing_file(self):
        """Test that missing transform file raises error."""
        yaml_content = """
name: test
stages:
  - type: transform
    name: my_transform
    transform: nonexistent.xsl
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            # Loader wraps FileNotFoundError in ValueError with stage info
            with pytest.raises(ValueError) as exc_info:
                load_pipeline(yaml_path)

            assert "Transform file not found" in str(exc_info.value)

        finally:
            yaml_path.unlink()

    def test_load_transform_stage_without_transform(self):
        """Test that transform stage requires 'transform' field."""
        yaml_content = """
name: test
stages:
  - type: transform
    name: my_transform
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            with pytest.raises(ValueError) as exc_info:
                load_pipeline(yaml_path)

            assert "requires 'transform' field" in str(exc_info.value)

        finally:
            yaml_path.unlink()


class TestLoadOutputStage:
    """Test loading OutputStage from YAML."""

    def test_load_output_stage(self):
        """Test loading output stage."""
        yaml_content = """
name: test
stages:
  - type: output
    name: write_html
    format: html
    output_path: out/result.html
    options:
      option1: value1
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            pipeline = load_pipeline(yaml_path)
            stage = pipeline.stages[0]

            assert isinstance(stage, OutputStage)
            assert stage.name == "write_html"
            assert stage.format == "html"
            assert stage.options == {"option1": "value1"}

        finally:
            yaml_path.unlink()

    def test_load_output_stage_without_format(self):
        """Test that output stage requires 'format' field."""
        yaml_content = """
name: test
stages:
  - type: output
    name: write
    output_path: out/result.txt
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            with pytest.raises(ValueError) as exc_info:
                load_pipeline(yaml_path)

            assert "requires 'format' field" in str(exc_info.value)

        finally:
            yaml_path.unlink()

    def test_load_output_stage_without_output_path(self):
        """Test that output stage requires 'output_path' field."""
        yaml_content = """
name: test
stages:
  - type: output
    name: write
    format: xml
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            with pytest.raises(ValueError) as exc_info:
                load_pipeline(yaml_path)

            assert "requires 'output_path' field" in str(exc_info.value)

        finally:
            yaml_path.unlink()


class TestLoadUnknownStageType:
    """Test loading unknown stage type."""

    def test_unknown_stage_type(self):
        """Test that unknown stage type raises error."""
        yaml_content = """
name: test
stages:
  - type: unknown_type
    name: my_stage
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            with pytest.raises(ValueError) as exc_info:
                load_pipeline(yaml_path)

            assert "Unknown stage type" in str(exc_info.value)

        finally:
            yaml_path.unlink()

    def test_stage_without_type(self):
        """Test that stage without 'type' field raises error."""
        yaml_content = """
name: test
stages:
  - name: my_stage
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            with pytest.raises(ValueError) as exc_info:
                load_pipeline(yaml_path)

            assert "must have 'type' field" in str(exc_info.value)

        finally:
            yaml_path.unlink()


class TestVariableResolution:
    """Test variable resolution in pipeline loader."""

    def test_resolve_environment_variables(self):
        """Test resolving environment variables."""
        import os

        os.environ["TEST_VAR"] = "test_value"

        try:
            loader = PipelineLoader()
            variables = loader._resolve_variables({"key": "${TEST_VAR}"})

            assert variables["key"] == "test_value"

        finally:
            del os.environ["TEST_VAR"]

    def test_resolve_datetime_expression(self):
        """Test resolving datetime expression."""
        loader = PipelineLoader()
        variables = loader._resolve_variables({"timestamp": "{{ datetime.now().isoformat() }}"})

        # Should contain an ISO timestamp
        assert "T" in variables["timestamp"]
        assert "-" in variables["timestamp"]

    def test_resolve_config_variables(self):
        """Test resolving variable references in config."""
        loader = PipelineLoader()
        loader.variables = {"version": "1.0", "env": "prod"}

        config = {
            "key1": "value_${version}",
            "key2": "${env}_config",
            "nested": {"key3": "${version}"},
        }

        resolved = loader._resolve_config_variables(config)

        assert resolved["key1"] == "value_1.0"
        assert resolved["key2"] == "prod_config"
        assert resolved["nested"]["key3"] == "1.0"


class TestComplexPipelineLoading:
    """Test loading complex pipelines."""

    def test_load_multi_stage_pipeline(self):
        """Test loading pipeline with multiple stages of different types."""
        # Create necessary files
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create XSLT file
            xslt_content = """<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:template match="/">
        <xsl:copy-of select="."/>
    </xsl:template>
</xsl:stylesheet>"""
            xslt_path = Path(tmpdir) / "transform.xsl"
            xslt_path.write_text(xslt_content)

            # Create pipeline YAML
            yaml_content = f"""
name: complex_pipeline
description: A complex multi-stage pipeline
error_strategy: continue
rollback_enabled: true
max_snapshots: 50

variables:
  version: "1.0"
  timestamp: "{{ datetime.now().isoformat() }}"

stages:
  - type: validate
    name: validate_input
    schemas_dir: schemas
    strict: true

  - type: transform
    name: enrich
    transform: {xslt_path.name}
    params:
      version: "${{version}}"

  - type: validate
    name: validate_enriched
    schemas_dir: schemas
    strict: false

  - type: output
    name: output_xml
    format: xml
    output_path: out/result.xml

  - type: output
    name: output_json
    format: json
    output_path: out/metadata.json
"""
            yaml_path = Path(tmpdir) / "pipeline.yaml"
            yaml_path.write_text(yaml_content)

            pipeline = load_pipeline(yaml_path)

            assert pipeline.name == "complex_pipeline"
            assert pipeline.error_strategy == ErrorStrategy.CONTINUE
            assert pipeline.rollback_enabled is True
            assert pipeline.max_snapshots == 50
            assert len(pipeline.stages) == 5

            # Verify stage types
            assert isinstance(pipeline.stages[0], ValidateStage)
            assert isinstance(pipeline.stages[1], TransformStage)
            assert isinstance(pipeline.stages[2], ValidateStage)
            assert isinstance(pipeline.stages[3], OutputStage)
            assert isinstance(pipeline.stages[4], OutputStage)
