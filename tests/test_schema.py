"""Tests for schema module."""

from xml_lib import schema


def test_schema_validator_creation():
    """Test creating a schema validator."""
    validator = schema.SchemaValidator()
    assert validator is not None
    assert validator.xsd_cache is not None
    assert validator.rng_cache is not None
