from pathlib import Path

from xml_lib.guardrails import GuardrailEngine
from xml_lib.validator import Validator


def test_validator_private_shim_available():
    validator = Validator(
        schemas_dir=Path("schemas"),
        guardrails_dir=Path("guardrails"),
        telemetry=None,
    )
    assert hasattr(validator, "_validate_file")


def test_guardrail_private_shim_available():
    engine = GuardrailEngine(guardrails_dir=Path("guardrails"))
    assert hasattr(engine, "_load_guardrails")
