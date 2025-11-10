"""Formal verification proof engine using Z3 SMT solver.

This module provides automatic generation of formal verification proofs
for all guardrail properties defined in the XML governance platform.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from lxml import etree
from z3 import (
    Bool,
    Int,
    String,
    Solver,
    sat,
    unsat,
    And,
    Or,
    Not,
    Implies,
    ForAll,
    Exists,
    StringVal,
    IntVal,
)


class ProofStatus(Enum):
    """Status of a formal verification proof."""

    VERIFIED = "verified"
    FAILED = "failed"
    UNKNOWN = "unknown"
    TIMEOUT = "timeout"


@dataclass
class GuardrailProperty:
    """A formal property derived from a guardrail rule."""

    id: str
    name: str
    description: str
    formula: Any  # Z3 expression
    constraints: List[Any] = field(default_factory=list)
    invariants: List[Any] = field(default_factory=list)


@dataclass
class ProofResult:
    """Result of formal verification."""

    property_id: str
    property_name: str
    status: ProofStatus
    model: Optional[Dict[str, Any]] = None
    counterexample: Optional[Dict[str, Any]] = None
    proof_steps: List[str] = field(default_factory=list)
    verification_time: float = 0.0


@dataclass
class ProofTree:
    """A proof tree structure for visualization."""

    root: "ProofNode"
    properties: List[GuardrailProperty]
    results: List[ProofResult]


@dataclass
class ProofNode:
    """A node in the proof tree."""

    id: str
    label: str
    type: str  # axiom, lemma, theorem, corollary
    statement: str
    proof_steps: List[str] = field(default_factory=list)
    children: List["ProofNode"] = field(default_factory=list)
    status: ProofStatus = ProofStatus.UNKNOWN
    dependencies: List[str] = field(default_factory=list)


class FormalVerificationEngine:
    """Engine for formal verification of guardrail properties using Z3.

    This engine:
    1. Parses XML proof definitions into Z3 formulas
    2. Automatically generates verification conditions
    3. Proves or refutes properties using SMT solving
    4. Generates proof trees for visualization
    """

    def __init__(self, engine_dir: Path, timeout_ms: int = 30000):
        """Initialize the formal verification engine.

        Args:
            engine_dir: Directory containing mathematical engine XML files
            timeout_ms: Timeout for Z3 solver in milliseconds
        """
        self.engine_dir = engine_dir
        self.timeout_ms = timeout_ms
        self.solver = Solver()
        self.solver.set("timeout", timeout_ms)

        # Storage for parsed elements
        self.axioms: Dict[str, ProofNode] = {}
        self.lemmas: Dict[str, ProofNode] = {}
        self.theorems: Dict[str, ProofNode] = {}
        self.properties: List[GuardrailProperty] = []

        # Parse engine files
        self._parse_engine_files()

    def _parse_engine_files(self) -> None:
        """Parse mathematical engine XML files into proof structures."""
        if not self.engine_dir.exists():
            return

        # Parse axioms
        axioms_file = self.engine_dir / "axioms.xml"
        if axioms_file.exists():
            self._parse_axioms(axioms_file)

        # Parse proof file
        proof_file = self.engine_dir / "proof.xml"
        if proof_file.exists():
            self._parse_proof(proof_file)

    def _parse_axioms(self, axioms_file: Path) -> None:
        """Parse axioms from XML into Z3 formulas."""
        try:
            doc = etree.parse(str(axioms_file))
            root = doc.getroot()

            for axiom in root.xpath("//axiom[@id]"):
                axiom_id = axiom.get("id", "")
                statement_elem = axiom.find("statement")

                if statement_elem is not None:
                    node = ProofNode(
                        id=axiom_id,
                        label=f"Axiom {axiom_id}",
                        type="axiom",
                        statement=statement_elem.text or "",
                        status=ProofStatus.VERIFIED,  # Axioms are assumed true
                    )
                    self.axioms[axiom_id] = node

        except Exception as e:
            print(f"Warning: Failed to parse axioms: {e}")

    def _parse_proof(self, proof_file: Path) -> None:
        """Parse proof file and extract lemmas and theorems."""
        try:
            doc = etree.parse(str(proof_file))
            root = doc.getroot()

            # Parse lemmas
            for lemma in root.xpath("//lemma[@id]"):
                lemma_id = lemma.get("id", "")
                statement_elem = lemma.find("statement")
                proof_elem = lemma.find("proof")

                proof_steps = []
                if proof_elem is not None:
                    steps = proof_elem.findall("step")
                    proof_steps = [step.text or "" for step in steps]

                if statement_elem is not None:
                    node = ProofNode(
                        id=lemma_id,
                        label=f"Lemma {lemma_id}",
                        type="lemma",
                        statement=statement_elem.text or "",
                        proof_steps=proof_steps,
                    )
                    self.lemmas[lemma_id] = node

            # Parse theorems
            for theorem in root.xpath("//theorem[@id]"):
                theorem_id = theorem.get("id", "")
                statement_elem = theorem.find("statement")
                proof_elem = theorem.find("proof")

                proof_steps = []
                dependencies = []
                if proof_elem is not None:
                    steps = proof_elem.findall("step")
                    proof_steps = [step.text or "" for step in steps]

                    # Extract dependencies from proof steps
                    for step in steps:
                        step_text = step.text or ""
                        # Look for references to lemmas/axioms
                        for lemma_id in self.lemmas:
                            if lemma_id in step_text:
                                dependencies.append(lemma_id)
                        for axiom_id in self.axioms:
                            if axiom_id in step_text:
                                dependencies.append(axiom_id)

                if statement_elem is not None:
                    node = ProofNode(
                        id=theorem_id,
                        label=f"Theorem {theorem_id}",
                        type="theorem",
                        statement=statement_elem.text or "",
                        proof_steps=proof_steps,
                        dependencies=list(set(dependencies)),
                    )
                    self.theorems[theorem_id] = node

        except Exception as e:
            print(f"Warning: Failed to parse proof: {e}")

    def verify_guardrail_properties(self, guardrails_dir: Path) -> List[ProofResult]:
        """Verify all guardrail properties using Z3.

        Args:
            guardrails_dir: Directory containing guardrail XML files

        Returns:
            List of proof results for each property
        """
        results = []

        # Extract properties from guardrails
        self.properties = self._extract_properties(guardrails_dir)

        # Verify each property
        for prop in self.properties:
            result = self._verify_property(prop)
            results.append(result)

        return results

    def _extract_properties(self, guardrails_dir: Path) -> List[GuardrailProperty]:
        """Extract formal properties from guardrail XML files."""
        properties: List[GuardrailProperty] = []

        if not guardrails_dir.exists():
            return properties

        for xml_file in guardrails_dir.rglob("*.xml"):
            try:
                doc = etree.parse(str(xml_file))
                root = doc.getroot()

                # Extract guardrail rules
                for guardrail in root.xpath("//guardrail[@id]"):
                    rule_id = guardrail.get("id", "")
                    name_elem = guardrail.find("name")
                    desc_elem = guardrail.find("description")
                    constraint_elem = guardrail.find("constraint")

                    if name_elem is None or constraint_elem is None:
                        continue

                    # Convert constraint to Z3 formula
                    constraint_type = constraint_elem.get("type", "xpath")
                    constraint_text = constraint_elem.text or ""

                    formula = self._constraint_to_z3(constraint_type, constraint_text)

                    prop = GuardrailProperty(
                        id=rule_id,
                        name=name_elem.text or "",
                        description=(
                            desc_elem.text or "" if desc_elem is not None else ""
                        ),
                        formula=formula,
                    )
                    properties.append(prop)

            except Exception as e:
                print(f"Warning: Failed to extract properties from {xml_file}: {e}")

        return properties

    def _constraint_to_z3(self, constraint_type: str, constraint_text: str) -> Any:
        """Convert a constraint to a Z3 formula.

        This is a simplified version - a full implementation would need
        a complete parser for XPath, regex, etc.
        """
        # Create symbolic variables
        doc = String("document")
        valid = Bool("valid")

        if constraint_type == "xpath":
            # For XPath constraints, we create a boolean assertion
            # This is a placeholder - real implementation needs XPath parsing
            return valid

        elif constraint_type == "regex":
            # For regex constraints, use Z3 string operations
            # This is a placeholder
            return valid

        elif constraint_type == "temporal":
            # For temporal constraints, use integer/real variables for time
            t1 = Int("t1")
            t2 = Int("t2")
            return t1 < t2

        else:
            # Default: create a boolean variable
            return valid

    def _verify_property(self, prop: GuardrailProperty) -> ProofResult:
        """Verify a single property using Z3."""
        import time

        start_time = time.time()

        # Create a fresh solver for this property
        solver = Solver()
        solver.set("timeout", self.timeout_ms)

        # Add invariants and constraints
        for invariant in prop.invariants:
            solver.add(invariant)

        for constraint in prop.constraints:
            solver.add(constraint)

        # Try to prove the property (check if negation is UNSAT)
        solver.add(Not(prop.formula))

        check_result = solver.check()
        verification_time = time.time() - start_time

        if check_result == unsat:
            # Property is valid (negation is unsatisfiable)
            return ProofResult(
                property_id=prop.id,
                property_name=prop.name,
                status=ProofStatus.VERIFIED,
                verification_time=verification_time,
                proof_steps=[
                    "Assumed property negation",
                    "Added invariants and constraints",
                    "Checked satisfiability",
                    "Result: UNSAT - property is valid",
                ],
            )

        elif check_result == sat:
            # Property is invalid (counterexample exists)
            model = solver.model()
            counterexample = {str(decl): str(model[decl]) for decl in model.decls()}

            return ProofResult(
                property_id=prop.id,
                property_name=prop.name,
                status=ProofStatus.FAILED,
                counterexample=counterexample,
                verification_time=verification_time,
                proof_steps=[
                    "Assumed property negation",
                    "Added invariants and constraints",
                    "Checked satisfiability",
                    "Result: SAT - counterexample found",
                ],
            )

        else:
            # Unknown (timeout or solver limitation)
            return ProofResult(
                property_id=prop.id,
                property_name=prop.name,
                status=ProofStatus.UNKNOWN,
                verification_time=verification_time,
                proof_steps=[
                    "Assumed property negation",
                    "Added invariants and constraints",
                    "Checked satisfiability",
                    "Result: UNKNOWN - timeout or limitation",
                ],
            )

    def build_proof_tree(self) -> ProofTree:
        """Build a complete proof tree from axioms, lemmas, and theorems.

        Returns:
            ProofTree structure with hierarchical proof organization
        """
        # Create root node
        root = ProofNode(
            id="root",
            label="Guardrail Proof System",
            type="root",
            statement="Complete formal verification of guardrail properties",
        )

        # Add axioms as children of root
        for axiom_id, axiom in self.axioms.items():
            root.children.append(axiom)

        # Build dependency graph for lemmas and theorems
        # Add lemmas that depend on axioms
        for lemma_id, lemma in self.lemmas.items():
            # Check if this lemma depends on axioms
            has_axiom_dep = any(dep in self.axioms for dep in lemma.dependencies)
            if has_axiom_dep or not lemma.dependencies:
                # Find the appropriate parent (axiom or root)
                if lemma.dependencies:
                    parent_id = next(
                        (dep for dep in lemma.dependencies if dep in self.axioms),
                        None,
                    )
                    if parent_id and parent_id in self.axioms:
                        self.axioms[parent_id].children.append(lemma)
                    else:
                        root.children.append(lemma)
                else:
                    root.children.append(lemma)

        # Add theorems based on their dependencies
        for theorem_id, theorem in self.theorems.items():
            if not theorem.dependencies:
                root.children.append(theorem)
            else:
                # Attach to the last dependency (simplified heuristic)
                parent_id = theorem.dependencies[-1]
                if parent_id in self.lemmas:
                    self.lemmas[parent_id].children.append(theorem)
                elif parent_id in self.axioms:
                    self.axioms[parent_id].children.append(theorem)
                else:
                    root.children.append(theorem)

        return ProofTree(
            root=root,
            properties=self.properties,
            results=[],
        )

    def verify_all(self, guardrails_dir: Path) -> Tuple[ProofTree, List[ProofResult]]:
        """Perform complete formal verification and build proof tree.

        Args:
            guardrails_dir: Directory containing guardrail definitions

        Returns:
            Tuple of (proof_tree, verification_results)
        """
        # Verify properties
        results = self.verify_guardrail_properties(guardrails_dir)

        # Build proof tree
        proof_tree = self.build_proof_tree()
        proof_tree.results = results

        # Update proof tree node statuses based on verification
        self._update_proof_tree_status(proof_tree, results)

        return proof_tree, results

    def _update_proof_tree_status(
        self, proof_tree: ProofTree, results: List[ProofResult]
    ) -> None:
        """Update proof tree node statuses based on verification results."""
        # Create a map of property IDs to results
        result_map = {r.property_id: r for r in results}

        # Update lemma and theorem statuses
        for lemma_id, lemma in self.lemmas.items():
            if lemma_id in result_map:
                lemma.status = result_map[lemma_id].status
                lemma.proof_steps = result_map[lemma_id].proof_steps

        for theorem_id, theorem in self.theorems.items():
            if theorem_id in result_map:
                theorem.status = result_map[theorem_id].status
                theorem.proof_steps = result_map[theorem_id].proof_steps


def verify_guardrails(
    engine_dir: Path,
    guardrails_dir: Path,
    timeout_ms: int = 30000,
) -> Tuple[ProofTree, List[ProofResult]]:
    """Convenience function to verify all guardrails.

    Args:
        engine_dir: Directory containing mathematical engine XML files
        guardrails_dir: Directory containing guardrail definitions
        timeout_ms: Timeout for Z3 solver in milliseconds

    Returns:
        Tuple of (proof_tree, verification_results)
    """
    engine = FormalVerificationEngine(engine_dir, timeout_ms)
    return engine.verify_all(guardrails_dir)
