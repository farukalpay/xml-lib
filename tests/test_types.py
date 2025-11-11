"""Tests for type definitions."""

from datetime import datetime
from pathlib import Path

from xml_lib.types import (
    CommandResult,
    Invariant,
    PhaseNode,
    Priority,
    Reference,
    ValidationResult,
)


def test_phase_node_creation():
    """Test creating a PhaseNode."""
    node = PhaseNode(
        phase="begin",
        xml_path=Path("lib/begin.xml"),
        timestamp=datetime.now(),
        id="test-id",
    )

    assert node.phase == "begin"
    assert node.id == "test-id"


def test_validation_result_creation():
    """Test creating a ValidationResult."""
    result = ValidationResult(
        is_valid=True,
        errors=[],
        warnings=["test warning"],
    )

    assert result.is_valid
    assert len(result.warnings) == 1


def test_command_result_creation():
    """Test creating a CommandResult."""
    result = CommandResult(
        command="test",
        timestamp=datetime.now(),
        duration_ms=100.0,
        status="success",
    )

    assert result.status == "success"
    assert result.duration_ms == 100.0


def test_invariant_creation():
    """Test creating an Invariant."""
    inv = Invariant(
        id="test-inv",
        description="Test invariant",
        check="some_check",
        severity=Priority.HIGH,
    )

    assert inv.id == "test-inv"
    assert inv.severity == Priority.HIGH


def test_reference_creation():
    """Test creating a Reference."""
    ref = Reference(
        source_id="src",
        target_id="tgt",
        reference_type="ref-begin",
        source_file=Path("test.xml"),
    )

    assert ref.source_id == "src"
    assert ref.target_id == "tgt"
