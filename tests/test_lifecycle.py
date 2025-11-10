"""Tests for lifecycle module."""

from pathlib import Path

import pytest

from xml_lib import lifecycle
from xml_lib.types import PhaseNode, ValidationResult


def test_lifecycle_dag_creation():
    """Test creating a basic lifecycle DAG."""
    dag = lifecycle.LifecycleDAG(base_path=Path("."))

    node1 = PhaseNode(
        phase="begin",
        xml_path=Path("lib/begin.xml"),
        timestamp=lifecycle.datetime.now(),
    )
    dag.add_node(node1)

    assert len(dag.nodes) == 1
    assert dag.is_topologically_sorted()


def test_lifecycle_dag_cycle_detection():
    """Test that cycles are detected in DAG."""
    dag = lifecycle.LifecycleDAG(base_path=Path("."))

    # Create nodes
    node1 = PhaseNode(
        phase="begin",
        xml_path=Path("lib/begin.xml"),
        timestamp=lifecycle.datetime.now(),
        id="node1",
    )
    node2 = PhaseNode(
        phase="start",
        xml_path=Path("lib/start.xml"),
        timestamp=lifecycle.datetime.now(),
        id="node2",
    )

    dag.add_node(node1)
    dag.add_node(node2)

    # Create cycle
    dag.add_edge("node1", "node2")
    dag.add_edge("node2", "node1")

    # Should detect cycle
    with pytest.raises(ValueError, match="Cycle detected"):
        dag.topological_sort()


def test_validate_dag():
    """Test DAG validation."""
    dag = lifecycle.LifecycleDAG(base_path=Path("."))

    node = PhaseNode(
        phase="begin",
        xml_path=Path("lib/begin.xml"),
        timestamp=lifecycle.datetime.now(),
        id="begin_node",
    )
    dag.add_node(node)

    result = lifecycle.validate_dag(dag)
    assert isinstance(result, ValidationResult)
    # Should have warnings about missing phases
    assert len(result.warnings) > 0


def test_topological_sort():
    """Test topological sorting of DAG."""
    dag = lifecycle.LifecycleDAG(base_path=Path("."))

    nodes = [
        PhaseNode(
            phase="begin",
            xml_path=Path("lib/begin.xml"),
            timestamp=lifecycle.datetime.now(),
            id="begin",
        ),
        PhaseNode(
            phase="start",
            xml_path=Path("lib/start.xml"),
            timestamp=lifecycle.datetime.now(),
            id="start",
        ),
        PhaseNode(
            phase="end",
            xml_path=Path("lib/end.xml"),
            timestamp=lifecycle.datetime.now(),
            id="end",
        ),
    ]

    for node in nodes:
        dag.add_node(node)

    dag.add_edge("begin", "start")
    dag.add_edge("start", "end")

    sorted_ids = dag.topological_sort()
    assert sorted_ids == ["begin", "start", "end"]
