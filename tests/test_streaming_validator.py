"""Tests for streaming XML validator."""

import tempfile
from pathlib import Path

import pytest

from xml_lib.streaming.validator import (
    StreamingValidationResult,
    StreamingValidator,
    ValidationError,
    ValidationState,
)


@pytest.fixture
def valid_xml():
    """Create a valid XML file."""
    content = """<?xml version="1.0" encoding="UTF-8"?>
<root>
    <item id="1">
        <name>Item 1</name>
        <value>100</value>
    </item>
    <item id="2">
        <name>Item 2</name>
        <value>200</value>
    </item>
</root>"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
        f.write(content)
        path = Path(f.name)

    yield path
    path.unlink()


@pytest.fixture
def invalid_xml():
    """Create an invalid XML file with mismatched tags."""
    content = """<?xml version="1.0" encoding="UTF-8"?>
<root>
    <item>
        <name>Test</name>
    </wrong>
</root>"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
        f.write(content)
        path = Path(f.name)

    yield path
    path.unlink()


@pytest.fixture
def deeply_nested_xml():
    """Create deeply nested XML."""
    content = '<?xml version="1.0"?>\n<root>\n'

    # Create 50 levels of nesting
    for i in range(50):
        content += f'<level{i}>\n'

    content += '<content>Deep</content>\n'

    for i in range(49, -1, -1):
        content += f'</level{i}>\n'

    content += '</root>\n'

    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
        f.write(content)
        path = Path(f.name)

    yield path
    path.unlink()


class TestValidationError:
    """Test ValidationError class."""

    def test_error_creation(self):
        """Test creating validation error."""
        error = ValidationError(
            message="Test error",
            file_position=100,
            line_number=10,
            column_number=5,
            element_name="test",
            error_type="structure",
        )

        assert error.message == "Test error"
        assert error.line_number == 10
        assert error.column_number == 5
        assert error.element_name == "test"

    def test_error_str(self):
        """Test error string formatting."""
        error = ValidationError(
            message="Test error",
            file_position=0,
            line_number=10,
            column_number=5,
            element_name="test",
        )

        error_str = str(error)
        assert "line 10" in error_str
        assert "col 5" in error_str
        assert "test" in error_str
        assert "Test error" in error_str


class TestValidationState:
    """Test ValidationState class."""

    def test_state_creation(self):
        """Test creating validation state."""
        state = ValidationState()

        assert state.file_position == 0
        assert state.errors == []
        assert state.warnings == []
        assert state.elements_validated == 0

    def test_add_error(self):
        """Test adding errors to state."""
        state = ValidationState()
        state.line_number = 10
        state.column_number = 5

        state.add_error("Test error", element_name="test")

        assert len(state.errors) == 1
        assert state.errors[0].message == "Test error"
        assert state.errors[0].line_number == 10

    def test_add_warning(self):
        """Test adding warnings to state."""
        state = ValidationState()
        state.line_number = 15
        state.column_number = 8

        state.add_warning("Test warning", element_name="test")

        assert len(state.warnings) == 1
        assert state.warnings[0].message == "Test warning"
        assert state.warnings[0].line_number == 15


class TestStreamingValidator:
    """Test StreamingValidator class."""

    def test_validator_init(self):
        """Test validator initialization."""
        validator = StreamingValidator()

        assert validator.schema is None
        assert validator.enable_namespaces is True

    def test_validate_simple_valid_xml(self, valid_xml):
        """Test validating simple valid XML."""
        validator = StreamingValidator()
        result = validator.validate_stream(valid_xml, checkpoint_interval_mb=0)

        assert isinstance(result, StreamingValidationResult)
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.elements_validated > 0
        assert result.bytes_processed > 0
        assert result.duration_seconds > 0

    def test_validate_invalid_xml(self, invalid_xml):
        """Test validating invalid XML."""
        validator = StreamingValidator()
        result = validator.validate_stream(invalid_xml, checkpoint_interval_mb=0)

        assert result.is_valid is False
        assert len(result.errors) > 0

        # Should have error about mismatched tags
        error_messages = [e.message for e in result.errors]
        assert any("Mismatched" in msg or "mismatch" in msg.lower() for msg in error_messages)

    def test_validate_deeply_nested(self, deeply_nested_xml):
        """Test validating deeply nested XML."""
        validator = StreamingValidator()
        result = validator.validate_stream(deeply_nested_xml, checkpoint_interval_mb=0)

        # Should complete successfully
        assert result.elements_validated > 0
        assert result.max_depth >= 50

    def test_validate_nonexistent_file(self):
        """Test validating nonexistent file."""
        validator = StreamingValidator()

        with pytest.raises(FileNotFoundError):
            validator.validate_stream("nonexistent.xml")

    def test_memory_tracking(self, valid_xml):
        """Test memory tracking during validation."""
        validator = StreamingValidator()

        # With memory tracking
        result_tracked = validator.validate_stream(
            valid_xml, checkpoint_interval_mb=0, track_memory=True
        )
        assert result_tracked.peak_memory_mb > 0

        # Without memory tracking
        result_untracked = validator.validate_stream(
            valid_xml, checkpoint_interval_mb=0, track_memory=False
        )
        assert result_untracked.peak_memory_mb == 0.0

    def test_throughput_calculation(self, valid_xml):
        """Test throughput calculation."""
        validator = StreamingValidator()
        result = validator.validate_stream(valid_xml, checkpoint_interval_mb=0)

        assert result.throughput_mbps > 0
        assert result.duration_seconds > 0

        # Throughput should be reasonable (not negative or absurdly high)
        assert 0 < result.throughput_mbps < 10000


class TestStreamingValidationResult:
    """Test StreamingValidationResult class."""

    def test_result_creation(self):
        """Test creating validation result."""
        result = StreamingValidationResult(
            is_valid=True,
            elements_validated=1000,
            bytes_processed=1024 * 1024,
            duration_seconds=1.5,
            throughput_mbps=0.67,
            peak_memory_mb=50.0,
        )

        assert result.is_valid is True
        assert result.elements_validated == 1000
        assert result.bytes_processed == 1024 * 1024

    def test_format_summary(self):
        """Test formatting result summary."""
        result = StreamingValidationResult(
            is_valid=True,
            file_path="test.xml",
            elements_validated=1000,
            bytes_processed=1024 * 1024,
            duration_seconds=1.5,
            throughput_mbps=0.67,
            peak_memory_mb=50.0,
        )

        summary = result.format_summary()

        assert "STREAMING VALIDATION RESULT" in summary
        assert "✅ VALID" in summary
        assert "test.xml" in summary
        assert "1,000" in summary  # elements formatted with commas

    def test_format_summary_with_errors(self):
        """Test formatting summary with errors."""
        errors = [
            ValidationError("Error 1", 0, 10, 5),
            ValidationError("Error 2", 0, 20, 10),
        ]

        result = StreamingValidationResult(
            is_valid=False,
            errors=errors,
            file_path="test.xml",
        )

        summary = result.format_summary()

        assert "❌ INVALID" in summary
        assert "Errors (2)" in summary
        assert "Error 1" in summary
        assert "Error 2" in summary


class TestCheckpointing:
    """Test checkpoint functionality."""

    def test_validate_with_checkpoints(self, valid_xml, tmp_path):
        """Test validation with checkpoint saving."""
        checkpoint_dir = tmp_path / "checkpoints"
        checkpoint_dir.mkdir()

        validator = StreamingValidator()

        # This file is too small to trigger checkpoints, but should not error
        result = validator.validate_stream(
            valid_xml,
            checkpoint_interval_mb=1,  # Very small interval
            checkpoint_dir=checkpoint_dir,
        )

        assert result.is_valid is True


class TestLargeFileValidation:
    """Test validation of larger files."""

    def test_validate_1mb_xml(self, tmp_path):
        """Test validating 1MB XML file."""
        xml_file = tmp_path / "test_1mb.xml"

        # Generate 1MB XML
        with open(xml_file, "w") as f:
            f.write('<?xml version="1.0"?>\n')
            f.write("<root>\n")

            # Write ~1MB of data
            target_size = 1 * 1024 * 1024
            current_size = 0
            index = 0

            while current_size < target_size:
                line = f'  <item id="{index}"><name>Item {index}</name><value>{index * 100}</value></item>\n'
                f.write(line)
                current_size += len(line)
                index += 1

            f.write("</root>\n")

        # Validate
        validator = StreamingValidator()
        result = validator.validate_stream(xml_file, checkpoint_interval_mb=0)

        assert result.is_valid is True
        assert result.elements_validated > 1000
        assert result.bytes_processed >= target_size

        # Verify memory usage is reasonable
        if result.peak_memory_mb > 0:
            # Memory should be much less than file size
            assert result.peak_memory_mb < 100  # Should use < 100MB for 1MB file

        # Clean up
        xml_file.unlink()

    def test_validate_with_progress(self, tmp_path):
        """Test validation with progress tracking."""
        xml_file = tmp_path / "test_progress.xml"

        # Generate test file
        with open(xml_file, "w") as f:
            f.write('<?xml version="1.0"?>\n')
            f.write("<root>\n")
            for i in range(1000):
                f.write(f'  <item id="{i}">Data {i}</item>\n')
            f.write("</root>\n")

        # Validate with memory tracking
        validator = StreamingValidator()
        result = validator.validate_stream(xml_file, track_memory=True)

        assert result.is_valid is True
        assert result.elements_validated > 0

        # Clean up
        xml_file.unlink()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_xml(self, tmp_path):
        """Test validating empty XML."""
        xml_file = tmp_path / "empty.xml"
        xml_file.write_text('<?xml version="1.0"?>\n<root></root>\n')

        validator = StreamingValidator()
        result = validator.validate_stream(xml_file)

        assert result.is_valid is True
        assert result.elements_validated == 1  # Just root

        xml_file.unlink()

    def test_unclosed_elements(self, tmp_path):
        """Test XML with unclosed elements."""
        xml_file = tmp_path / "unclosed.xml"
        xml_file.write_text('<?xml version="1.0"?>\n<root><item>\n')

        validator = StreamingValidator()

        # Should detect parsing error
        result = validator.validate_stream(xml_file)
        assert result.is_valid is False
        assert len(result.errors) > 0

        xml_file.unlink()

    def test_max_depth_warning(self, tmp_path):
        """Test warning for extremely deep nesting."""
        xml_file = tmp_path / "very_deep.xml"

        # Create XML with depth > 1000
        content = '<?xml version="1.0"?>\n'
        for i in range(1100):
            content += f'<level{i}>\n'
        content += '<content>Very deep</content>\n'
        for i in range(1099, -1, -1):
            content += f'</level{i}>\n'

        xml_file.write_text(content)

        validator = StreamingValidator()
        result = validator.validate_stream(xml_file)

        # Should have error about depth
        assert result.is_valid is False
        assert any("depth" in e.message.lower() or "nesting" in e.message.lower() for e in result.errors)

        xml_file.unlink()
