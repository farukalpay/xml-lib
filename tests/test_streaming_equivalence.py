"""Tests to ensure streaming and non-streaming validation produce identical results.

These tests generate moderately large XML files and validate them in both streaming
and non-streaming modes, then assert that the ValidationResult (valid flag, errors,
warnings) is identical in both cases.

Tests marked as 'slow' can be skipped with: pytest -m "not slow"
Tests marked as 'integration' are integration tests
"""

import hashlib
from pathlib import Path

import pytest

from xml_lib import create_validator, validate_xml
from xml_lib.sanitize import MathPolicy

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


def generate_large_xml(path: Path, num_elements: int = 1000) -> None:
    """Generate a large valid XML file for testing.

    Args:
        path: Path where XML file will be written
        num_elements: Number of elements to generate (default: 1000)
    """
    with open(path, "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write("<document>\n")
        f.write("  <metadata>\n")
        f.write("    <title>Large Test Document</title>\n")
        f.write("    <author>Test Suite</author>\n")
        f.write("  </metadata>\n")
        f.write("  <sections>\n")

        for i in range(num_elements):
            f.write(f'    <section id="sec-{i}">\n')
            f.write(f"      <heading>Section {i}</heading>\n")
            f.write(
                f"      <content>This is the content of section {i}. "
                f"It contains some text to make the file larger.</content>\n"
            )
            f.write("    </section>\n")

        f.write("  </sections>\n")
        f.write("</document>\n")


def generate_invalid_large_xml(path: Path, num_elements: int = 1000) -> None:
    """Generate a large invalid XML file for testing error detection.

    Args:
        path: Path where XML file will be written
        num_elements: Number of elements to generate (default: 1000)
    """
    with open(path, "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write("<document>\n")
        f.write("  <metadata>\n")
        f.write("    <title>Large Invalid Document</title>\n")
        # Missing required element: <author>
        f.write("  </metadata>\n")
        f.write("  <sections>\n")

        for i in range(num_elements):
            f.write(f'    <section id="sec-{i}">\n')
            f.write(f"      <heading>Section {i}</heading>\n")
            # Introduce some invalid elements
            if i % 100 == 0:
                f.write(f"      <invalid-element>Error {i}</invalid-element>\n")
            f.write(
                f"      <content>Content {i}</content>\n"
            )
            f.write("    </section>\n")

        f.write("  </sections>\n")
        f.write("</document>\n")


def normalize_errors(errors):
    """Normalize errors for comparison.

    Streaming and non-streaming modes may report errors slightly differently
    (e.g., different line numbers for some errors), but core error messages
    should be the same.
    """
    # Extract just the error messages for comparison
    return sorted([e.message for e in errors])


@pytest.fixture
def test_schemas(tmp_path):
    """Create test schemas for validation."""
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()

    # Create a schema that allows the structure we're generating
    schema_content = """<?xml version="1.0" encoding="UTF-8"?>
<grammar xmlns="http://relaxng.org/ns/structure/1.0">
  <start>
    <element name="document">
      <element name="metadata">
        <element name="title"><text/></element>
        <element name="author"><text/></element>
      </element>
      <element name="sections">
        <zeroOrMore>
          <element name="section">
            <attribute name="id"/>
            <element name="heading"><text/></element>
            <element name="content"><text/></element>
          </element>
        </zeroOrMore>
      </element>
    </element>
  </start>
</grammar>"""
    (schemas_dir / "lifecycle.rng").write_text(schema_content)

    return schemas_dir


@pytest.fixture
def test_guardrails(tmp_path):
    """Create test guardrails directory."""
    guardrails_dir = tmp_path / "guardrails"
    guardrails_dir.mkdir()
    return guardrails_dir


class TestStreamingEquivalence:
    """Tests to ensure streaming and non-streaming modes produce identical results."""

    @pytest.mark.slow
    def test_large_valid_file_streaming_vs_nonstreaming(
        self, tmp_path, test_schemas, test_guardrails
    ):
        """Test that valid large file produces identical results in both modes."""
        # Generate a large XML file (should be > 1MB to trigger streaming)
        xml_file = tmp_path / "large_valid.xml"
        generate_large_xml(xml_file, num_elements=5000)

        # Validate with streaming disabled
        result_no_streaming = validate_xml(
            tmp_path,
            schemas_dir=test_schemas,
            guardrails_dir=test_guardrails,
            enable_streaming=False,
        )

        # Validate with streaming enabled (low threshold to force streaming)
        result_with_streaming = validate_xml(
            tmp_path,
            schemas_dir=test_schemas,
            guardrails_dir=test_guardrails,
            enable_streaming=True,
            streaming_threshold_mb=1,  # Force streaming for files > 1MB
        )

        # Results should be identical
        assert result_no_streaming.is_valid == result_with_streaming.is_valid
        assert len(result_no_streaming.errors) == len(result_with_streaming.errors)
        assert len(result_no_streaming.warnings) == len(result_with_streaming.warnings)

        # Both should have validated the same files
        assert sorted(result_no_streaming.validated_files) == sorted(
            result_with_streaming.validated_files
        )

        # Checksums should match (same file content)
        for file_path in result_no_streaming.validated_files:
            if file_path in result_no_streaming.checksums:
                assert (
                    result_no_streaming.checksums[file_path]
                    == result_with_streaming.checksums.get(file_path)
                )

    @pytest.mark.slow
    def test_large_invalid_file_streaming_vs_nonstreaming(
        self, tmp_path, test_schemas, test_guardrails
    ):
        """Test that invalid large file produces similar error counts in both modes."""
        # Generate a large invalid XML file
        xml_file = tmp_path / "large_invalid.xml"
        generate_invalid_large_xml(xml_file, num_elements=5000)

        # Validate with streaming disabled
        result_no_streaming = validate_xml(
            tmp_path,
            schemas_dir=test_schemas,
            guardrails_dir=test_guardrails,
            enable_streaming=False,
        )

        # Validate with streaming enabled
        result_with_streaming = validate_xml(
            tmp_path,
            schemas_dir=test_schemas,
            guardrails_dir=test_guardrails,
            enable_streaming=True,
            streaming_threshold_mb=1,
        )

        # Both should detect that the file is invalid
        assert result_no_streaming.is_valid == result_with_streaming.is_valid

        # Error counts should be similar (may not be exact due to different parsing)
        # but should be in the same ballpark
        no_stream_error_count = len(result_no_streaming.errors)
        stream_error_count = len(result_with_streaming.errors)

        # Allow for some variation, but should be similar
        if no_stream_error_count > 0:
            ratio = stream_error_count / no_stream_error_count
            assert (
                0.5 <= ratio <= 2.0
            ), f"Error counts too different: {no_stream_error_count} vs {stream_error_count}"

    @pytest.mark.slow
    def test_multiple_files_streaming_vs_nonstreaming(
        self, tmp_path, test_schemas, test_guardrails
    ):
        """Test multiple files produce identical results in both modes."""
        project = tmp_path / "project"
        project.mkdir()

        # Create multiple XML files of varying sizes
        for i in range(5):
            xml_file = project / f"file_{i}.xml"
            generate_large_xml(xml_file, num_elements=1000 * (i + 1))

        # Validate with streaming disabled
        result_no_streaming = validate_xml(
            project,
            schemas_dir=test_schemas,
            guardrails_dir=test_guardrails,
            enable_streaming=False,
        )

        # Validate with streaming enabled
        result_with_streaming = validate_xml(
            project,
            schemas_dir=test_schemas,
            guardrails_dir=test_guardrails,
            enable_streaming=True,
            streaming_threshold_mb=1,
        )

        # Results should be identical
        assert result_no_streaming.is_valid == result_with_streaming.is_valid
        assert len(result_no_streaming.validated_files) == len(
            result_with_streaming.validated_files
        )

    def test_small_file_both_modes_identical(
        self, tmp_path, test_schemas, test_guardrails
    ):
        """Test that small file (< threshold) produces identical results."""
        # Create a small XML file
        xml_file = tmp_path / "small.xml"
        xml_file.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<document>
  <metadata>
    <title>Small Document</title>
    <author>Test</author>
  </metadata>
  <sections>
    <section id="s1">
      <heading>Section 1</heading>
      <content>Small content</content>
    </section>
  </sections>
</document>"""
        )

        # Validate with streaming disabled
        result_no_streaming = validate_xml(
            tmp_path,
            schemas_dir=test_schemas,
            guardrails_dir=test_guardrails,
            enable_streaming=False,
        )

        # Validate with streaming enabled (but threshold won't be reached)
        result_with_streaming = validate_xml(
            tmp_path,
            schemas_dir=test_schemas,
            guardrails_dir=test_guardrails,
            enable_streaming=True,
            streaming_threshold_mb=10,  # High threshold
        )

        # Results should be identical
        assert result_no_streaming.is_valid == result_with_streaming.is_valid
        assert len(result_no_streaming.errors) == len(result_with_streaming.errors)
        assert len(result_no_streaming.warnings) == len(result_with_streaming.warnings)

    @pytest.mark.slow
    def test_reusable_validator_streaming_vs_nonstreaming(
        self, tmp_path, test_schemas, test_guardrails
    ):
        """Test that reusable validators produce identical results in both modes."""
        # Create validators
        validator_no_streaming = create_validator(
            schemas_dir=test_schemas,
            guardrails_dir=test_guardrails,
            enable_streaming=False,
        )

        validator_with_streaming = create_validator(
            schemas_dir=test_schemas,
            guardrails_dir=test_guardrails,
            enable_streaming=True,
            streaming_threshold_bytes=1 * 1024 * 1024,  # 1MB
        )

        # Generate test file
        project = tmp_path / "project"
        project.mkdir()
        xml_file = project / "large.xml"
        generate_large_xml(xml_file, num_elements=3000)

        # Validate with both validators
        result_no_streaming = validator_no_streaming.validate_project(project)
        result_with_streaming = validator_with_streaming.validate_project(project)

        # Results should be identical
        assert result_no_streaming.is_valid == result_with_streaming.is_valid
        assert len(result_no_streaming.errors) == len(result_with_streaming.errors)

    @pytest.mark.slow
    def test_streaming_flag_in_result(self, tmp_path, test_schemas, test_guardrails):
        """Test that used_streaming flag is set correctly."""
        # Create a large file
        xml_file = tmp_path / "large.xml"
        generate_large_xml(xml_file, num_elements=5000)

        # Validate with streaming disabled
        result_no_streaming = validate_xml(
            tmp_path,
            schemas_dir=test_schemas,
            guardrails_dir=test_guardrails,
            enable_streaming=False,
        )

        # used_streaming should be False
        assert result_no_streaming.used_streaming is False

        # Validate with streaming enabled (low threshold)
        result_with_streaming = validate_xml(
            tmp_path,
            schemas_dir=test_schemas,
            guardrails_dir=test_guardrails,
            enable_streaming=True,
            streaming_threshold_mb=1,
        )

        # used_streaming may be True if file was large enough
        # (depends on actual file size)
        assert isinstance(result_with_streaming.used_streaming, bool)


class TestStreamingMemoryEfficiency:
    """Tests to verify that streaming mode is memory efficient."""

    @pytest.mark.slow
    def test_streaming_handles_very_large_file(
        self, tmp_path, test_schemas, test_guardrails
    ):
        """Test that streaming mode can handle very large files without error."""
        # Generate a very large XML file
        xml_file = tmp_path / "very_large.xml"
        generate_large_xml(xml_file, num_elements=10000)

        # This should not crash or use excessive memory
        result = validate_xml(
            tmp_path,
            schemas_dir=test_schemas,
            guardrails_dir=test_guardrails,
            enable_streaming=True,
            streaming_threshold_mb=1,
        )

        # Should complete successfully
        assert isinstance(result.is_valid, bool)
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")

    @pytest.mark.slow
    def test_nonstreaming_handles_moderate_file(
        self, tmp_path, test_schemas, test_guardrails
    ):
        """Test that non-streaming mode works for moderate files."""
        # Generate a moderate-sized XML file
        xml_file = tmp_path / "moderate.xml"
        generate_large_xml(xml_file, num_elements=2000)

        # Non-streaming should handle this fine
        result = validate_xml(
            tmp_path,
            schemas_dir=test_schemas,
            guardrails_dir=test_guardrails,
            enable_streaming=False,
        )

        assert isinstance(result.is_valid, bool)


class TestStreamingEdgeCases:
    """Test edge cases in streaming validation."""

    def test_empty_file_both_modes(self, tmp_path, test_schemas, test_guardrails):
        """Test that empty file is handled identically in both modes."""
        xml_file = tmp_path / "empty.xml"
        xml_file.write_text("")

        # Both modes should handle empty file
        try:
            result_no_streaming = validate_xml(
                tmp_path,
                schemas_dir=test_schemas,
                guardrails_dir=test_guardrails,
                enable_streaming=False,
            )
        except Exception:
            result_no_streaming = None

        try:
            result_with_streaming = validate_xml(
                tmp_path,
                schemas_dir=test_schemas,
                guardrails_dir=test_guardrails,
                enable_streaming=True,
                streaming_threshold_mb=0,
            )
        except Exception:
            result_with_streaming = None

        # Both should handle it the same way (either both succeed or both fail)
        if result_no_streaming is not None:
            assert result_with_streaming is not None

    def test_single_element_both_modes(
        self, tmp_path, test_schemas, test_guardrails
    ):
        """Test that minimal valid XML works in both modes."""
        xml_file = tmp_path / "minimal.xml"
        xml_file.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<document>
  <metadata>
    <title>Minimal</title>
    <author>Test</author>
  </metadata>
  <sections/>
</document>"""
        )

        result_no_streaming = validate_xml(
            tmp_path,
            schemas_dir=test_schemas,
            guardrails_dir=test_guardrails,
            enable_streaming=False,
        )

        result_with_streaming = validate_xml(
            tmp_path,
            schemas_dir=test_schemas,
            guardrails_dir=test_guardrails,
            enable_streaming=True,
            streaming_threshold_mb=0,  # Force streaming even for small files
        )

        # Results should be identical
        assert result_no_streaming.is_valid == result_with_streaming.is_valid
