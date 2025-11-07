"""Regression test to ensure benchmark shims exist."""

from pathlib import Path
from xml_lib.validator import Validator
from xml_lib.guardrails import GuardrailEngine


def test_validator_has_validate_file_shim():
    """Ensure Validator has _validate_file method for benchmarking."""
    validator = Validator(
        schemas_dir=Path("schemas"),
        guardrails_dir=Path("guardrails"),
        telemetry=None,
    )
    assert hasattr(
        validator, "_validate_file"
    ), "Validator must have _validate_file method"


def test_guardrail_engine_has_load_guardrails_shim():
    """Ensure GuardrailEngine has _load_guardrails method for benchmarking."""
    engine = GuardrailEngine(Path("guardrails"))
    assert hasattr(
        engine, "_load_guardrails"
    ), "GuardrailEngine must have _load_guardrails method"
