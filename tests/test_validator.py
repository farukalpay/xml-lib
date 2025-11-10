"""Tests for XML validator."""

import pytest
from pathlib import Path
from datetime import datetime
from lxml import etree

from xml_lib.validator import Validator, ValidationResult
from xml_lib.types import ValidationError
from xml_lib.storage import ContentStore, deterministic_uuid


@pytest.fixture
def validator():
    """Create validator instance."""
    schemas_dir = Path("schemas")
    guardrails_dir = Path("guardrails")
    return Validator(schemas_dir, guardrails_dir, telemetry=None)


@pytest.fixture
def fixtures_dir():
    """Get fixtures directory."""
    return Path("tests/fixtures")


def test_valid_lifecycle(validator, fixtures_dir):
    """Test validation of valid lifecycle document."""
    result = validator.validate_project(fixtures_dir)

    # Should find the valid lifecycle file
    assert len(result.validated_files) >= 1
    valid_file = [f for f in result.validated_files if "valid_lifecycle" in f]
    assert len(valid_file) >= 1


def test_invalid_amphibians(validator, fixtures_dir):
    """Test validation of invalid amphibians document."""
    # Create validator that will check the invalid file
    result = validator.validate_project(fixtures_dir)

    # Should have errors from the invalid file
    invalid_errors = [
        e
        for e in result.errors
        if "invalid_amphibians" in e.file or "amphibians" in e.message.lower()
    ]

    # We expect multiple errors:
    # - Bad checksum format
    # - Phase ordering (start before begin)
    # - Duplicate IDs
    # - Temporal ordering (backwards timestamp)
    assert not result.is_valid or len(invalid_errors) > 0


def test_cross_file_id_uniqueness(validator, tmp_path):
    """Test cross-file ID uniqueness checking."""
    # Create two files with duplicate IDs
    file1 = tmp_path / "file1.xml"
    file1.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<document id="duplicate-id">
  <phases>
    <phase name="begin">
      <payload>File 1</payload>
    </phase>
  </phases>
</document>
"""
    )

    file2 = tmp_path / "file2.xml"
    file2.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<document id="duplicate-id">
  <phases>
    <phase name="begin">
      <payload>File 2</payload>
    </phase>
  </phases>
</document>
"""
    )

    result = validator.validate_project(tmp_path)

    # Should detect duplicate ID across files
    assert not result.is_valid
    duplicate_errors = [e for e in result.errors if "duplicate" in e.message.lower()]
    assert len(duplicate_errors) > 0


def test_temporal_monotonicity(validator, tmp_path):
    """Test temporal monotonicity validation."""
    xml_file = tmp_path / "temporal.xml"
    xml_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<document>
  <phases>
    <phase name="begin" timestamp="2025-01-15T10:00:00Z">
      <payload>Begin</payload>
    </phase>
    <phase name="start" timestamp="2025-01-15T09:00:00Z">
      <payload>Start in the past</payload>
    </phase>
  </phases>
</document>
"""
    )

    result = validator.validate_project(tmp_path)

    # Should detect temporal ordering violation
    assert not result.is_valid
    temporal_errors = [
        e for e in result.errors if "temporal" in e.rule or "timestamp" in e.message.lower()
    ]
    assert len(temporal_errors) > 0


def test_checksum_format(validator, tmp_path):
    """Test checksum format validation."""
    xml_file = tmp_path / "checksum.xml"
    xml_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<document checksum="invalid">
  <phases>
    <phase name="begin">
      <payload>Test</payload>
    </phase>
  </phases>
</document>
"""
    )

    result = validator.validate_project(tmp_path)

    # Should detect invalid checksum format
    checksum_errors = [
        e for e in result.errors + result.warnings if "checksum" in e.message.lower()
    ]
    assert len(checksum_errors) > 0


def test_content_addressed_storage(tmp_path):
    """Test content-addressed storage."""
    store = ContentStore(tmp_path)

    content = b"<test>Hello World</test>"
    path = store.store(content)

    # Should be stored
    assert path.exists()

    # Should be retrievable
    retrieved = store.retrieve(path.parent.name + path.name.replace(".xml", ""))
    assert retrieved is not None


def test_deterministic_uuid():
    """Test deterministic UUID generation."""
    uuid1 = deterministic_uuid("xml-lib", "test-doc")
    uuid2 = deterministic_uuid("xml-lib", "test-doc")

    # Same inputs should produce same UUID
    assert uuid1 == uuid2

    # Different inputs should produce different UUID
    uuid3 = deterministic_uuid("xml-lib", "other-doc")
    assert uuid1 != uuid3


def test_validation_result_serialization(validator, tmp_path):
    """Test that validation results can be serialized."""
    xml_file = tmp_path / "test.xml"
    xml_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<document>
  <phases>
    <phase name="begin">
      <payload>Test</payload>
    </phase>
  </phases>
</document>
"""
    )

    result = validator.validate_project(tmp_path)

    # Should produce assertions
    from xml_lib.assertions import AssertionLedger

    ledger = AssertionLedger()
    ledger.add_validation_result(result)

    output_xml = tmp_path / "assertions.xml"
    output_jsonl = tmp_path / "assertions.jsonl"

    ledger.write_xml(output_xml)
    ledger.write_jsonl(output_jsonl)

    assert output_xml.exists()
    assert output_jsonl.exists()
    assert output_xml.stat().st_size > 0
    assert output_jsonl.stat().st_size > 0


def test_minimum_phase_requirement(validator, tmp_path):
    """Test that documents require at least a 'begin' phase."""
    xml_file = tmp_path / "no_begin.xml"
    xml_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<document>
  <phases>
    <phase name="end">
      <payload>No begin phase</payload>
    </phase>
  </phases>
</document>
"""
    )

    result = validator.validate_project(tmp_path)

    # Should have error about missing begin
    # (either from Schematron or guardrails)
    assert not result.is_valid or len(result.warnings) > 0
