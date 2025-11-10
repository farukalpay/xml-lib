"""Tests for schema module."""

from pathlib import Path

from xml_lib import schema
from xml_lib.types import ValidationResult


def test_schema_validator_creation():
    """Test creating a schema validator."""
    validator = schema.SchemaValidator()
    assert validator is not None
    assert validator.xsd_cache is not None
    assert validator.rng_cache is not None
