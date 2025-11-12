"""Tests for test XML file generator."""

from pathlib import Path

import pytest

from xml_lib.streaming.generator import GeneratorConfig, TestFileGenerator
from xml_lib.streaming.parser import StreamingParser


class TestGeneratorConfig:
    """Test GeneratorConfig class."""

    def test_default_config(self):
        """Test default configuration."""
        config = GeneratorConfig()

        assert config.pattern == "simple"
        assert config.element_density == 5
        assert config.max_depth == 10
        assert config.attribute_count == 3

    def test_custom_config(self):
        """Test custom configuration."""
        config = GeneratorConfig(
            pattern="complex",
            max_depth=20,
            attribute_count=5,
        )

        assert config.pattern == "complex"
        assert config.max_depth == 20
        assert config.attribute_count == 5


class TestGeneratorClass:
    """Test TestFileGenerator class."""

    def test_generator_init(self):
        """Test generator initialization."""
        generator = TestFileGenerator()
        assert generator.buffer_size == 8192

        generator_custom = TestFileGenerator(buffer_size=4096)
        assert generator_custom.buffer_size == 4096

    def test_generate_small_file(self, tmp_path):
        """Test generating small XML file."""
        output_file = tmp_path / "test_1mb.xml"
        generator = TestFileGenerator()

        generator.generate(
            output_path=output_file,
            size_mb=1,
            pattern="simple",
        )

        assert output_file.exists()

        # Check file size (should be approximately 1MB)
        file_size = output_file.stat().st_size
        expected_size = 1 * 1024 * 1024
        # Allow 10% tolerance
        assert 0.9 * expected_size <= file_size <= 1.1 * expected_size

        # Verify it's valid XML
        parser = StreamingParser()
        valid, errors = parser.validate_structure(output_file)
        assert valid is True

    def test_generate_patterns(self, tmp_path):
        """Test generating different patterns."""
        patterns = ["simple", "complex", "nested", "realistic"]
        generator = TestFileGenerator()

        for pattern in patterns:
            output_file = tmp_path / f"test_{pattern}.xml"

            generator.generate(
                output_path=output_file,
                size_mb=1,
                pattern=pattern,
            )

            assert output_file.exists()

            # Verify it's valid XML
            parser = StreamingParser()
            valid, errors = parser.validate_structure(output_file)
            assert valid is True, f"Pattern {pattern} generated invalid XML: {errors}"

    def test_generate_with_custom_config(self, tmp_path):
        """Test generating with custom configuration."""
        output_file = tmp_path / "test_custom.xml"
        generator = TestFileGenerator()

        config = GeneratorConfig(
            pattern="complex",
            max_depth=15,
            attribute_count=4,
            namespace_enabled=True,
        )

        generator.generate_with_config(
            output_path=output_file,
            size_mb=1,
            config=config,
        )

        assert output_file.exists()

        # Verify it's valid XML
        parser = StreamingParser()
        valid, errors = parser.validate_structure(output_file)
        assert valid is True

    def test_generate_with_progress_callback(self, tmp_path):
        """Test generation with progress callback."""
        output_file = tmp_path / "test_progress.xml"
        generator = TestFileGenerator()

        progress_calls = []

        def progress_callback(current: int, total: int):
            progress_calls.append((current, total))

        generator.generate(
            output_path=output_file,
            size_mb=1,
            pattern="simple",
            progress_callback=progress_callback,
        )

        assert output_file.exists()
        # Should have received progress updates
        assert len(progress_calls) > 0

    def test_generate_realistic_dataset_users(self, tmp_path):
        """Test generating realistic user dataset."""
        output_file = tmp_path / "users.xml"
        generator = TestFileGenerator()

        generator.generate_realistic_dataset(
            output_path=output_file,
            record_count=100,
            record_type="user",
        )

        assert output_file.exists()

        # Verify structure
        parser = StreamingParser()
        valid, errors = parser.validate_structure(output_file)
        assert valid is True

        # Verify content
        content = output_file.read_text()
        assert "<user" in content
        assert "<username>" in content
        assert "<email>" in content

    def test_generate_realistic_dataset_products(self, tmp_path):
        """Test generating realistic product dataset."""
        output_file = tmp_path / "products.xml"
        generator = TestFileGenerator()

        generator.generate_realistic_dataset(
            output_path=output_file,
            record_count=50,
            record_type="product",
        )

        assert output_file.exists()

        # Verify content
        content = output_file.read_text()
        assert "<product" in content
        assert "<name>" in content
        assert "<price>" in content
        assert "<category>" in content

    def test_generate_realistic_dataset_transactions(self, tmp_path):
        """Test generating realistic transaction dataset."""
        output_file = tmp_path / "transactions.xml"
        generator = TestFileGenerator()

        generator.generate_realistic_dataset(
            output_path=output_file,
            record_count=50,
            record_type="transaction",
        )

        assert output_file.exists()

        # Verify content
        content = output_file.read_text()
        assert "<transaction" in content
        assert "<amount>" in content
        assert "<timestamp>" in content

    def test_generate_realistic_dataset_logs(self, tmp_path):
        """Test generating realistic log dataset."""
        output_file = tmp_path / "logs.xml"
        generator = TestFileGenerator()

        generator.generate_realistic_dataset(
            output_path=output_file,
            record_count=50,
            record_type="log",
        )

        assert output_file.exists()

        # Verify content
        content = output_file.read_text()
        assert "<log" in content
        assert "level=" in content
        assert "<message>" in content

    def test_invalid_pattern(self, tmp_path):
        """Test generating with invalid pattern."""
        output_file = tmp_path / "test.xml"
        generator = TestFileGenerator()

        with pytest.raises(ValueError):
            generator.generate(
                output_path=output_file,
                size_mb=1,
                pattern="invalid_pattern",
            )

    def test_creates_output_directory(self, tmp_path):
        """Test that output directory is created if needed."""
        output_file = tmp_path / "subdir" / "test.xml"
        generator = TestFileGenerator()

        generator.generate(
            output_path=output_file,
            size_mb=1,
            pattern="simple",
        )

        assert output_file.exists()
        assert output_file.parent.exists()

    def test_generated_file_element_count(self, tmp_path):
        """Test that generated file has reasonable element count."""
        output_file = tmp_path / "test.xml"
        generator = TestFileGenerator()

        generator.generate(
            output_path=output_file,
            size_mb=1,
            pattern="simple",
        )

        # Count elements
        parser = StreamingParser()
        element_count = 0

        for event in parser.parse(output_file):
            from xml_lib.streaming.parser import EventType

            if event.type == EventType.START_ELEMENT:
                element_count += 1

        # Should have many elements for 1MB file
        assert element_count > 100

    def test_generated_file_has_xml_declaration(self, tmp_path):
        """Test that generated file has XML declaration."""
        output_file = tmp_path / "test.xml"
        generator = TestFileGenerator()

        generator.generate(
            output_path=output_file,
            size_mb=1,
            pattern="simple",
        )

        content = output_file.read_text()
        assert content.startswith('<?xml version="1.0"')

    def test_generated_file_well_formed(self, tmp_path):
        """Test that generated file is well-formed."""
        output_file = tmp_path / "test.xml"
        generator = TestFileGenerator()

        for pattern in ["simple", "complex", "nested"]:
            generator.generate(
                output_path=output_file,
                size_mb=1,
                pattern=pattern,
            )

            # Parse it to ensure well-formedness
            parser = StreamingParser()
            events = list(parser.parse(output_file))

            # Count start and end elements
            from xml_lib.streaming.parser import EventType

            start_count = sum(
                1 for e in events if e.type == EventType.START_ELEMENT
            )
            end_count = sum(1 for e in events if e.type == EventType.END_ELEMENT)

            # Should be balanced
            assert start_count == end_count


class TestGenerateTestSuite:
    """Test test suite generation."""

    def test_generate_test_suite(self, tmp_path):
        """Test generating a suite of test files."""
        from xml_lib.streaming.generator import generate_test_suite

        output_dir = tmp_path / "test_suite"
        sizes_mb = [1, 2]

        generate_test_suite(output_dir, sizes_mb)

        # Check files exist
        assert (output_dir / "test_1mb.xml").exists()
        assert (output_dir / "test_2mb.xml").exists()

        # Verify files are approximately correct size
        for size_mb in sizes_mb:
            file_path = output_dir / f"test_{size_mb}mb.xml"
            file_size = file_path.stat().st_size
            expected_size = size_mb * 1024 * 1024
            # Allow 20% tolerance for small files
            assert 0.8 * expected_size <= file_size <= 1.2 * expected_size
