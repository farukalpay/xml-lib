"""Tests for validator handling of math symbols in XML."""

import pytest
from pathlib import Path
from xml_lib.validator import Validator
from xml_lib.sanitize import MathPolicy


def test_validator_sanitize_policy_succeeds(tmp_path):
    """Test that validator succeeds with sanitize policy on mathy XML."""
    # Create a file with invalid element name
    xml_file = tmp_path / "mathy.xml"
    xml_file.write_text('<?xml version="1.0"?>\n<document><×>content</×></document>')

    validator = Validator(
        schemas_dir=Path("schemas"),
        guardrails_dir=Path("guardrails"),
        telemetry=None,
    )

    result = validator.validate_project(tmp_path, math_policy=MathPolicy.SANITIZE)

    # Should succeed (with schema warnings perhaps, but parseable)
    assert len(result.validated_files) == 1


def test_validator_error_policy_fails(tmp_path):
    """Test that validator fails with error policy on mathy XML."""
    # Create a file with invalid element name
    xml_file = tmp_path / "mathy.xml"
    xml_file.write_text('<?xml version="1.0"?>\n<document><×>content</×></document>')

    validator = Validator(
        schemas_dir=Path("schemas"),
        guardrails_dir=Path("guardrails"),
        telemetry=None,
    )

    result = validator.validate_project(tmp_path, math_policy=MathPolicy.ERROR)

    # Should fail to parse
    assert not result.is_valid
    assert len(result.errors) > 0
    assert any("xml-syntax" in err.rule for err in result.errors)


def test_validator_skip_policy_warns(tmp_path):
    """Test that validator warns with skip policy on mathy XML."""
    # Create a file with invalid element name
    xml_file = tmp_path / "mathy.xml"
    xml_file.write_text('<?xml version="1.0"?>\n<document><×>content</×></document>')

    validator = Validator(
        schemas_dir=Path("schemas"),
        guardrails_dir=Path("guardrails"),
        telemetry=None,
    )

    result = validator.validate_project(tmp_path, math_policy=MathPolicy.SKIP)

    # Should have warning but continue
    assert len(result.warnings) > 0
    assert len(result.validated_files) == 0  # File was skipped
