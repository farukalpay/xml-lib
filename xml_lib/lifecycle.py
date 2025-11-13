"""Lifecycle DAG management and validation.

This module handles loading, traversing, and validating the canonical XML lifecycle:
begin → start → iteration → end → continuum
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from lxml import etree

from xml_lib.types import (
    Invariant,
    PhaseNode,
    PhaseType,
    Priority,
    Reference,
    ReferenceError,
    ValidationResult,
)
from xml_lib.utils.logging import get_logger, structured_log
from xml_lib.utils.xml_utils import (
    get_element_checksum,
    get_element_id,
    get_element_timestamp,
    parse_xml,
)

logger = get_logger(__name__)


@dataclass
class LifecycleDAG:
    """Directed acyclic graph representing the lifecycle."""

    nodes: dict[str, PhaseNode] = field(default_factory=dict)
    edges: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    phase_order: list[PhaseType] = field(
        default_factory=lambda: ["begin", "start", "iteration", "end", "continuum"]
    )
    base_path: Path = field(default_factory=Path)

    def add_node(self, node: PhaseNode) -> None:
        """Add a node to the DAG."""
        node_id = node.id or f"{node.phase}_{node.xml_path.stem}"
        self.nodes[node_id] = node

    def add_edge(self, from_id: str, to_id: str) -> None:
        """Add an edge between two nodes."""
        self.edges[from_id].append(to_id)

    def topological_sort(self) -> list[str]:
        """Return nodes in topological order.

        Returns:
            List of node IDs in topological order

        Raises:
            ValueError: If cycle detected
        """
        in_degree = dict.fromkeys(self.nodes, 0)
        for node_id, neighbors in self.edges.items():
            for neighbor in neighbors:
                in_degree[neighbor] = in_degree.get(neighbor, 0) + 1

        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        result = []

        while queue:
            node_id = queue.popleft()
            result.append(node_id)

            for neighbor in self.edges.get(node_id, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self.nodes):
            raise ValueError("Cycle detected in lifecycle DAG")

        return result

    def is_topologically_sorted(self) -> bool:
        """Check if DAG is topologically sorted."""
        try:
            self.topological_sort()
            return True
        except ValueError:
            return False

    def get_node(self, node_id: str) -> PhaseNode | None:
        """Get node by ID."""
        return self.nodes.get(node_id)

    def get_dependencies(self, node_id: str) -> list[str]:
        """Get all dependencies for a node."""
        return self.edges.get(node_id, [])


def load_lifecycle(base_path: Path) -> LifecycleDAG:
    """Load lifecycle XML files into a DAG.

    Args:
        base_path: Base directory containing lib/ folder

    Returns:
        LifecycleDAG representing the lifecycle

    Raises:
        FileNotFoundError: If required lifecycle files missing
    """
    dag = LifecycleDAG(base_path=base_path)
    lib_path = base_path / "lib"

    if not lib_path.exists():
        raise FileNotFoundError(f"Lifecycle directory not found: {lib_path}")

    structured_log(logger, "info", "Loading lifecycle", phase="load")

    # Load each phase file
    phase_files = {
        "begin": lib_path / "begin.xml",
        "start": lib_path / "start.xml",
        "iteration": lib_path / "iteration.xml",
        "end": lib_path / "end.xml",
        "continuum": lib_path / "continuum.xml",
    }

    prev_node_id = None
    for phase, xml_path in phase_files.items():
        if not xml_path.exists():
            logger.warning(f"Phase file not found: {xml_path}")
            continue

        try:
            root = parse_xml(xml_path)
            timestamp_str = get_element_timestamp(root)
            timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now()

            node = PhaseNode(
                phase=phase,  # type: ignore
                xml_path=xml_path,
                timestamp=timestamp,
                id=get_element_id(root),
                checksum=get_element_checksum(root),
            )

            dag.add_node(node)
            node_id = node.id or f"{phase}_{xml_path.stem}"

            # Create edge from previous phase
            if prev_node_id:
                dag.add_edge(prev_node_id, node_id)

            prev_node_id = node_id

            structured_log(
                logger,
                "debug",
                f"Loaded phase: {phase}",
                phase=phase,
                doc_id=node.id,
                path=str(xml_path),
            )

        except etree.XMLSyntaxError as e:
            logger.error(f"Failed to parse {xml_path}: {e}")
            continue

    return dag


def validate_dag(dag: LifecycleDAG) -> ValidationResult:
    """Validate the lifecycle DAG structure.

    Args:
        dag: LifecycleDAG to validate

    Returns:
        ValidationResult with errors and warnings
    """
    errors = []
    warnings = []

    structured_log(logger, "info", "Validating DAG structure")

    # Check for cycles
    if not dag.is_topologically_sorted():
        errors.append("Cycle detected in lifecycle DAG")

    # Check for missing phases
    expected_phases = set(dag.phase_order)
    actual_phases = {node.phase for node in dag.nodes.values()}
    missing_phases = expected_phases - actual_phases

    if missing_phases:
        warnings.append(f"Missing phases: {', '.join(missing_phases)}")

    # Check phase ordering
    phase_positions = {phase: i for i, phase in enumerate(dag.phase_order)}
    sorted_nodes = [dag.nodes[node_id] for node_id in dag.topological_sort()]

    for i in range(len(sorted_nodes) - 1):
        current = sorted_nodes[i]
        next_node = sorted_nodes[i + 1]

        if phase_positions.get(current.phase, -1) > phase_positions.get(next_node.phase, -1):
            errors.append(
                f"Phase ordering violation: {current.phase} should come before {next_node.phase}"
            )

    is_valid = len(errors) == 0

    # Convert string errors to ValidationError objects
    error_objects = [
        ValidationError(
            file="",
            line=None,
            column=None,
            message=err,
            type="error",
            rule="lifecycle-validation",
        )
        for err in errors
    ]

    # Convert string warnings to ValidationError objects
    warning_objects = [
        ValidationError(
            file="",
            line=None,
            column=None,
            message=warn,
            type="warning",
            rule="lifecycle-validation",
        )
        for warn in warnings
    ]

    return ValidationResult(
        is_valid=is_valid,
        errors=error_objects,
        warnings=warning_objects,
    )


def check_phase_invariants(dag: LifecycleDAG) -> list[Invariant]:
    """Check phase-specific invariants.

    Args:
        dag: LifecycleDAG to check

    Returns:
        List of violated invariants
    """
    violated = []

    # Invariant: begin phase must have no dependencies
    begin_nodes = [n for n in dag.nodes.values() if n.phase == "begin"]
    for node in begin_nodes:
        node_id = node.id or f"begin_{node.xml_path.stem}"
        deps = dag.get_dependencies(node_id)
        if deps:
            violated.append(
                Invariant(
                    id="begin_no_deps",
                    description="Begin phase must have no dependencies",
                    check=f"dependencies({node_id}) == []",
                    severity=Priority.CRITICAL,
                )
            )

    # Invariant: timestamps must be monotonically increasing
    sorted_nodes = [dag.nodes[node_id] for node_id in dag.topological_sort()]
    for i in range(len(sorted_nodes) - 1):
        if sorted_nodes[i].timestamp > sorted_nodes[i + 1].timestamp:
            violated.append(
                Invariant(
                    id="timestamp_monotonic",
                    description="Timestamps must increase along lifecycle",
                    check=f"{sorted_nodes[i].phase}.timestamp <= {sorted_nodes[i+1].phase}.timestamp",
                    severity=Priority.HIGH,
                )
            )

    return violated


def verify_references(dag: LifecycleDAG) -> list[ReferenceError]:
    """Verify cross-references between lifecycle documents.

    Args:
        dag: LifecycleDAG to verify

    Returns:
        List of reference errors
    """
    errors = []
    all_ids = {node.id for node in dag.nodes.values() if node.id}

    structured_log(logger, "info", "Verifying cross-references")

    for node_id, node in dag.nodes.items():
        try:
            root = parse_xml(node.xml_path)

            # Find all reference attributes
            for ref_attr in ["ref-begin", "ref-start", "ref-iteration", "ref-end", "ref-continuum"]:
                refs = root.xpath(f"//*[@{ref_attr}]")
                for elem in refs:
                    target_id = elem.get(ref_attr)
                    if target_id and target_id not in all_ids:
                        ref = Reference(
                            source_id=node_id,
                            target_id=target_id or "",
                            reference_type=ref_attr,
                            source_file=node.xml_path,
                        )
                        errors.append(
                            ReferenceError(
                                reference=ref,
                                error=f"Reference to non-existent ID: {target_id}",
                                file_path=node.xml_path,
                            )
                        )

        except etree.XMLSyntaxError as e:
            logger.error(f"Failed to verify references in {node.xml_path}: {e}")

    return errors


def generate_lifecycle_report(dag: LifecycleDAG) -> dict[str, Any]:
    """Generate a comprehensive lifecycle report.

    Args:
        dag: LifecycleDAG to report on

    Returns:
        Report dictionary with validation results
    """
    dag_validation = validate_dag(dag)
    invariant_violations = check_phase_invariants(dag)
    reference_errors = verify_references(dag)

    return {
        "lifecycle": {
            "base_path": str(dag.base_path),
            "phase_count": len(dag.nodes),
            "phases": [node.phase for node in dag.nodes.values()],
        },
        "dag_validation": {
            "is_valid": dag_validation.is_valid,
            "errors": dag_validation.errors,
            "warnings": dag_validation.warnings,
        },
        "invariants": {
            "total_checked": len(check_phase_invariants(dag)) + len(dag.nodes),
            "violations": [
                {"id": inv.id, "description": inv.description, "severity": inv.severity.value}
                for inv in invariant_violations
            ],
        },
        "references": {
            "total_verified": sum(
                len(parse_xml(node.xml_path).xpath("//*[@ref-*]")) for node in dag.nodes.values()
            ),
            "errors": [
                {
                    "source": err.reference.source_id,
                    "target": err.reference.target_id,
                    "error": err.error,
                }
                for err in reference_errors
            ],
        },
    }
