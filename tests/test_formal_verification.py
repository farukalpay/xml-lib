"""Tests for formal verification proof engine."""

import tempfile
from pathlib import Path

import pytest
from lxml import etree

from xml_lib.formal_verification import (
    FormalVerificationEngine,
    GuardrailProperty,
    ProofNode,
    ProofResult,
    ProofStatus,
    ProofTree,
    verify_guardrails,
)


class TestProofNode:
    """Tests for ProofNode dataclass."""

    def test_create_proof_node(self):
        """Test creating a proof node."""
        node = ProofNode(
            id="test1",
            label="Test Node",
            type="axiom",
            statement="Test statement",
        )

        assert node.id == "test1"
        assert node.label == "Test Node"
        assert node.type == "axiom"
        assert node.statement == "Test statement"
        assert node.children == []
        assert node.status == ProofStatus.UNKNOWN

    def test_proof_node_with_children(self):
        """Test proof node with child nodes."""
        parent = ProofNode(
            id="parent",
            label="Parent",
            type="theorem",
            statement="Parent statement",
        )

        child1 = ProofNode(
            id="child1",
            label="Child 1",
            type="lemma",
            statement="Child 1 statement",
        )

        child2 = ProofNode(
            id="child2",
            label="Child 2",
            type="lemma",
            statement="Child 2 statement",
        )

        parent.children = [child1, child2]

        assert len(parent.children) == 2
        assert parent.children[0].id == "child1"
        assert parent.children[1].id == "child2"

    def test_proof_node_dependencies(self):
        """Test proof node with dependencies."""
        node = ProofNode(
            id="theorem1",
            label="Theorem 1",
            type="theorem",
            statement="Test theorem",
            dependencies=["L1", "L2", "A1"],
        )

        assert len(node.dependencies) == 3
        assert "L1" in node.dependencies
        assert "A1" in node.dependencies


class TestFormalVerificationEngine:
    """Tests for FormalVerificationEngine."""

    @pytest.fixture
    def temp_engine_dir(self):
        """Create temporary directory with test engine files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine_dir = Path(tmpdir) / "engine"
            engine_dir.mkdir()

            # Create test axioms file
            axioms_xml = """<?xml version="1.0" encoding="UTF-8"?>
<axioms>
  <axiom id="A1">
    <statement>FORALL x, P(x) IMPLIES Q(x)</statement>
  </axiom>
  <axiom id="A2">
    <statement>FORALL x, Q(x) IMPLIES R(x)</statement>
  </axiom>
</axioms>"""
            (engine_dir / "axioms.xml").write_text(axioms_xml)

            # Create test proof file
            proof_xml = """<?xml version="1.0" encoding="UTF-8"?>
<guardrail-proof>
  <lemma id="L1">
    <statement>FORALL x, P(x) IMPLIES R(x)</statement>
    <proof>
      <step>From A1 obtain Q(x)</step>
      <step>Apply A2 to derive R(x)</step>
    </proof>
  </lemma>
  <theorem id="T1">
    <statement>Complete guardrail compliance</statement>
    <proof>
      <step>Apply L1 to all states</step>
      <step>Therefore all states comply</step>
    </proof>
  </theorem>
</guardrail-proof>"""
            (engine_dir / "proof.xml").write_text(proof_xml)

            yield engine_dir

    def test_engine_initialization(self, temp_engine_dir):
        """Test engine initialization."""
        engine = FormalVerificationEngine(temp_engine_dir)

        assert engine.engine_dir == temp_engine_dir
        assert len(engine.axioms) == 2
        assert len(engine.lemmas) == 1
        assert len(engine.theorems) == 1

    def test_parse_axioms(self, temp_engine_dir):
        """Test parsing axioms from XML."""
        engine = FormalVerificationEngine(temp_engine_dir)

        assert "A1" in engine.axioms
        assert "A2" in engine.axioms

        axiom1 = engine.axioms["A1"]
        assert axiom1.type == "axiom"
        assert axiom1.status == ProofStatus.VERIFIED
        assert "P(x) IMPLIES Q(x)" in axiom1.statement

    def test_parse_lemmas(self, temp_engine_dir):
        """Test parsing lemmas from proof file."""
        engine = FormalVerificationEngine(temp_engine_dir)

        assert "L1" in engine.lemmas

        lemma1 = engine.lemmas["L1"]
        assert lemma1.type == "lemma"
        assert "P(x) IMPLIES R(x)" in lemma1.statement
        assert len(lemma1.proof_steps) == 2

    def test_parse_theorems(self, temp_engine_dir):
        """Test parsing theorems from proof file."""
        engine = FormalVerificationEngine(temp_engine_dir)

        assert "T1" in engine.theorems

        theorem1 = engine.theorems["T1"]
        assert theorem1.type == "theorem"
        assert "compliance" in theorem1.statement.lower()
        assert len(theorem1.proof_steps) == 2

    def test_build_proof_tree(self, temp_engine_dir):
        """Test building proof tree from parsed elements."""
        engine = FormalVerificationEngine(temp_engine_dir)
        proof_tree = engine.build_proof_tree()

        assert proof_tree.root is not None
        assert proof_tree.root.id == "root"
        assert len(proof_tree.root.children) > 0

    def test_extract_properties_from_guardrails(self, temp_engine_dir):
        """Test extracting properties from guardrail files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            guardrails_dir = Path(tmpdir) / "guardrails"
            guardrails_dir.mkdir()

            # Create test guardrail file
            guardrail_xml = """<?xml version="1.0" encoding="UTF-8"?>
<guardrails>
  <guardrail id="GR1" priority="high">
    <name>ID Uniqueness</name>
    <description>All IDs must be unique</description>
    <constraint type="xpath">count(//*[@id]) = count(distinct-values(//*/@id))</constraint>
  </guardrail>
</guardrails>"""
            (guardrails_dir / "test.xml").write_text(guardrail_xml)

            engine = FormalVerificationEngine(temp_engine_dir)
            properties = engine._extract_properties(guardrails_dir)

            assert len(properties) == 1
            assert properties[0].id == "GR1"
            assert properties[0].name == "ID Uniqueness"

    def test_verify_property(self, temp_engine_dir):
        """Test verifying a single property."""
        from z3 import Bool

        engine = FormalVerificationEngine(temp_engine_dir)

        # Create a simple tautology property
        prop = GuardrailProperty(
            id="test_prop",
            name="Test Property",
            description="Test description",
            formula=Bool("valid"),  # Simple boolean
        )

        result = engine._verify_property(prop)

        assert result.property_id == "test_prop"
        assert result.property_name == "Test Property"
        assert isinstance(result.verification_time, float)

    def test_verify_guardrails_integration(self, temp_engine_dir):
        """Test complete guardrail verification workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            guardrails_dir = Path(tmpdir) / "guardrails"
            guardrails_dir.mkdir()

            # Create minimal guardrail
            guardrail_xml = """<?xml version="1.0" encoding="UTF-8"?>
<guardrails>
  <guardrail id="GR1" priority="medium">
    <name>Test Rule</name>
    <description>Test</description>
    <constraint type="xpath">//test</constraint>
  </guardrail>
</guardrails>"""
            (guardrails_dir / "test.xml").write_text(guardrail_xml)

            proof_tree, results = verify_guardrails(
                temp_engine_dir,
                guardrails_dir,
                timeout_ms=5000,
            )

            assert proof_tree is not None
            assert isinstance(results, list)


class TestProofTree:
    """Tests for ProofTree structure."""

    def test_create_proof_tree(self):
        """Test creating a proof tree."""
        root = ProofNode(
            id="root",
            label="Root",
            type="root",
            statement="Root statement",
        )

        tree = ProofTree(
            root=root,
            properties=[],
            results=[],
        )

        assert tree.root == root
        assert tree.properties == []
        assert tree.results == []

    def test_proof_tree_with_properties_and_results(self):
        """Test proof tree with properties and results."""
        root = ProofNode(
            id="root",
            label="Root",
            type="root",
            statement="Root statement",
        )

        prop = GuardrailProperty(
            id="prop1",
            name="Property 1",
            description="Test property",
            formula=None,
        )

        result = ProofResult(
            property_id="prop1",
            property_name="Property 1",
            status=ProofStatus.VERIFIED,
        )

        tree = ProofTree(
            root=root,
            properties=[prop],
            results=[result],
        )

        assert len(tree.properties) == 1
        assert len(tree.results) == 1
        assert tree.results[0].status == ProofStatus.VERIFIED


class TestProofStatus:
    """Tests for ProofStatus enum."""

    def test_proof_status_values(self):
        """Test proof status enum values."""
        assert ProofStatus.VERIFIED.value == "verified"
        assert ProofStatus.FAILED.value == "failed"
        assert ProofStatus.UNKNOWN.value == "unknown"
        assert ProofStatus.TIMEOUT.value == "timeout"

    def test_proof_status_comparison(self):
        """Test proof status can be compared."""
        status1 = ProofStatus.VERIFIED
        status2 = ProofStatus.VERIFIED
        status3 = ProofStatus.FAILED

        assert status1 == status2
        assert status1 != status3


class TestGuardrailProperty:
    """Tests for GuardrailProperty dataclass."""

    def test_create_guardrail_property(self):
        """Test creating a guardrail property."""
        from z3 import Bool

        formula = Bool("test")

        prop = GuardrailProperty(
            id="prop1",
            name="Test Property",
            description="Test description",
            formula=formula,
        )

        assert prop.id == "prop1"
        assert prop.name == "Test Property"
        assert prop.description == "Test description"
        assert prop.formula == formula
        assert prop.constraints == []
        assert prop.invariants == []

    def test_property_with_constraints_and_invariants(self):
        """Test property with constraints and invariants."""
        from z3 import Bool

        formula = Bool("test")
        constraint1 = Bool("c1")
        invariant1 = Bool("i1")

        prop = GuardrailProperty(
            id="prop1",
            name="Test Property",
            description="Test description",
            formula=formula,
            constraints=[constraint1],
            invariants=[invariant1],
        )

        assert len(prop.constraints) == 1
        assert len(prop.invariants) == 1


class TestProofResult:
    """Tests for ProofResult dataclass."""

    def test_create_proof_result_verified(self):
        """Test creating a verified proof result."""
        result = ProofResult(
            property_id="prop1",
            property_name="Test Property",
            status=ProofStatus.VERIFIED,
            proof_steps=["Step 1", "Step 2"],
        )

        assert result.property_id == "prop1"
        assert result.status == ProofStatus.VERIFIED
        assert len(result.proof_steps) == 2
        assert result.counterexample is None

    def test_create_proof_result_failed(self):
        """Test creating a failed proof result with counterexample."""
        counterexample = {"x": "5", "y": "10"}

        result = ProofResult(
            property_id="prop1",
            property_name="Test Property",
            status=ProofStatus.FAILED,
            counterexample=counterexample,
        )

        assert result.status == ProofStatus.FAILED
        assert result.counterexample == counterexample
        assert "x" in result.counterexample

    def test_proof_result_with_model(self):
        """Test proof result with Z3 model."""
        model_data = {"var1": "value1", "var2": "value2"}

        result = ProofResult(
            property_id="prop1",
            property_name="Test Property",
            status=ProofStatus.VERIFIED,
            model=model_data,
        )

        assert result.model == model_data
        assert "var1" in result.model
