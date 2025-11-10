"""Tests for proof tree visualization."""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest
import networkx as nx

from xml_lib.formal_verification import (
    ProofNode,
    ProofResult,
    ProofStatus,
    ProofTree,
    GuardrailProperty,
)
from xml_lib.proof_visualization import ProofTreeVisualizer


# Check if Graphviz is available
def is_graphviz_available():
    """Check if Graphviz dot executable is available."""
    try:
        subprocess.run(
            ["dot", "-V"], capture_output=True, check=True, timeout=5
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


graphviz_available = is_graphviz_available()
skip_if_no_graphviz = pytest.mark.skipif(
    not graphviz_available,
    reason="Graphviz not installed (required for rendering tests)"
)


class TestProofTreeVisualizer:
    """Tests for ProofTreeVisualizer class."""

    @pytest.fixture
    def simple_proof_tree(self):
        """Create a simple proof tree for testing."""
        root = ProofNode(
            id="root",
            label="Proof System",
            type="root",
            statement="Complete proof system",
        )

        axiom1 = ProofNode(
            id="A1",
            label="Axiom 1",
            type="axiom",
            statement="Basic axiom 1",
            status=ProofStatus.VERIFIED,
        )

        axiom2 = ProofNode(
            id="A2",
            label="Axiom 2",
            type="axiom",
            statement="Basic axiom 2",
            status=ProofStatus.VERIFIED,
        )

        lemma1 = ProofNode(
            id="L1",
            label="Lemma 1",
            type="lemma",
            statement="Derived lemma",
            status=ProofStatus.VERIFIED,
            proof_steps=["Apply A1", "Apply A2", "Conclude"],
        )

        theorem1 = ProofNode(
            id="T1",
            label="Theorem 1",
            type="theorem",
            statement="Main theorem",
            status=ProofStatus.VERIFIED,
            dependencies=["L1"],
        )

        # Build tree structure
        root.children = [axiom1, axiom2]
        axiom1.children = [lemma1]
        lemma1.children = [theorem1]

        return ProofTree(
            root=root,
            properties=[],
            results=[],
        )

    @pytest.fixture
    def complex_proof_tree(self):
        """Create a more complex proof tree with multiple levels."""
        root = ProofNode(
            id="root",
            label="Guardrail Proof System",
            type="root",
            statement="Complete guardrail verification",
        )

        # Create axioms
        axioms = []
        for i in range(1, 4):
            axiom = ProofNode(
                id=f"A{i}",
                label=f"Axiom {i}",
                type="axiom",
                statement=f"Axiom {i} statement",
                status=ProofStatus.VERIFIED,
            )
            axioms.append(axiom)
            root.children.append(axiom)

        # Create lemmas
        lemmas = []
        for i in range(1, 3):
            lemma = ProofNode(
                id=f"L{i}",
                label=f"Lemma {i}",
                type="lemma",
                statement=f"Lemma {i} statement",
                status=ProofStatus.VERIFIED,
                proof_steps=[f"Step 1 for L{i}", f"Step 2 for L{i}"],
            )
            lemmas.append(lemma)
            axioms[i - 1].children.append(lemma)

        # Create theorem
        theorem = ProofNode(
            id="T1",
            label="Main Theorem",
            type="theorem",
            statement="Main theorem statement",
            status=ProofStatus.VERIFIED,
            dependencies=["L1", "L2"],
        )
        lemmas[0].children.append(theorem)

        return ProofTree(
            root=root,
            properties=[],
            results=[],
        )

    def test_visualizer_initialization(self, simple_proof_tree):
        """Test initializing visualizer with a proof tree."""
        viz = ProofTreeVisualizer(simple_proof_tree)

        assert viz.proof_tree == simple_proof_tree
        assert isinstance(viz.graph, nx.DiGraph)
        assert len(viz.graph.nodes()) > 0

    def test_build_networkx_graph(self, simple_proof_tree):
        """Test building NetworkX graph from proof tree."""
        viz = ProofTreeVisualizer(simple_proof_tree)

        # Check that all nodes are in the graph
        assert "root" in viz.graph.nodes()
        assert "A1" in viz.graph.nodes()
        assert "A2" in viz.graph.nodes()
        assert "L1" in viz.graph.nodes()
        assert "T1" in viz.graph.nodes()

        # Check edges
        assert viz.graph.has_edge("root", "A1")
        assert viz.graph.has_edge("root", "A2")
        assert viz.graph.has_edge("A1", "L1")
        assert viz.graph.has_edge("L1", "T1")

    def test_graph_node_attributes(self, simple_proof_tree):
        """Test that graph nodes have correct attributes."""
        viz = ProofTreeVisualizer(simple_proof_tree)

        a1_data = viz.graph.nodes["A1"]
        assert a1_data["label"] == "Axiom 1"
        assert a1_data["type"] == "axiom"
        assert a1_data["status"] == ProofStatus.VERIFIED.value

        l1_data = viz.graph.nodes["L1"]
        assert l1_data["label"] == "Lemma 1"
        assert l1_data["type"] == "lemma"
        assert len(l1_data["proof_steps"]) == 3

    @skip_if_no_graphviz
    def test_render_graphviz_svg(self, simple_proof_tree):
        """Test rendering proof tree as SVG using Graphviz."""
        viz = ProofTreeVisualizer(simple_proof_tree)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "proof_tree.svg"
            result_path = viz.render_graphviz(output_path, format="svg")

            assert result_path.exists()
            assert result_path.suffix == ".svg"

            # Check that file has content
            content = result_path.read_text()
            assert len(content) > 0
            assert "<?xml" in content  # SVG header

    @skip_if_no_graphviz
    def test_render_graphviz_pdf(self, simple_proof_tree):
        """Test rendering proof tree as PDF using Graphviz."""
        viz = ProofTreeVisualizer(simple_proof_tree)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "proof_tree.pdf"
            result_path = viz.render_graphviz(output_path, format="pdf")

            assert result_path.exists()
            assert result_path.suffix == ".pdf"

            # Check that file has content (PDF magic number)
            content = result_path.read_bytes()
            assert content.startswith(b"%PDF")

    def test_render_interactive_plotly(self, simple_proof_tree):
        """Test rendering interactive proof tree using Plotly."""
        viz = ProofTreeVisualizer(simple_proof_tree)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "proof_tree.html"
            result_path = viz.render_interactive_plotly(output_path)

            assert result_path.exists()
            assert result_path.suffix == ".html"

            # Check that file has content
            content = result_path.read_text()
            assert len(content) > 0
            assert "plotly" in content.lower()
            assert "<html>" in content.lower()

    def test_hierarchical_layout(self, simple_proof_tree):
        """Test hierarchical layout computation."""
        viz = ProofTreeVisualizer(simple_proof_tree)
        pos = viz._hierarchical_layout()

        # Check that all nodes have positions
        assert "root" in pos
        assert "A1" in pos
        assert "L1" in pos

        # Check that positions are tuples of (x, y)
        for node_id, position in pos.items():
            assert isinstance(position, tuple)
            assert len(position) == 2
            assert isinstance(position[0], (int, float))
            assert isinstance(position[1], (int, float))

        # Check that root is at top (y = 0)
        assert pos["root"][1] == 0

        # Check that children are below parents
        assert pos["A1"][1] < pos["root"][1]
        assert pos["L1"][1] < pos["A1"][1]

    def test_hierarchical_layout_complex(self, complex_proof_tree):
        """Test hierarchical layout with complex tree."""
        viz = ProofTreeVisualizer(complex_proof_tree)
        pos = viz._hierarchical_layout()

        # All nodes should have positions
        assert len(pos) == len(viz.graph.nodes())

        # Root should be at level 0
        assert pos["root"][1] == 0

        # Axioms should be at level -1
        for i in range(1, 4):
            axiom_id = f"A{i}"
            assert pos[axiom_id][1] == -1

    def test_generate_proof_report(self, simple_proof_tree):
        """Test generating HTML proof report."""
        viz = ProofTreeVisualizer(simple_proof_tree)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.html"
            result_path = viz.generate_proof_report(output_path)

            assert result_path.exists()
            assert result_path.suffix == ".html"

            # Check content
            content = result_path.read_text()
            assert "Formal Verification Proof Report" in content
            assert "Axiom" in content
            assert "Lemma" in content
            assert "Theorem" in content

    def test_report_contains_statistics(self, complex_proof_tree):
        """Test that report contains verification statistics."""
        viz = ProofTreeVisualizer(complex_proof_tree)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.html"
            result_path = viz.generate_proof_report(output_path)

            content = result_path.read_text()

            # Should contain stat cards
            assert "Total Proof Elements" in content
            assert "Verified" in content

    def test_export_json(self, simple_proof_tree):
        """Test exporting proof tree as JSON."""
        viz = ProofTreeVisualizer(simple_proof_tree)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "proof_tree.json"
            result_path = viz.export_json(output_path)

            assert result_path.exists()
            assert result_path.suffix == ".json"

            # Load and validate JSON
            with open(result_path) as f:
                data = json.load(f)

            assert "nodes" in data
            assert "edges" in data
            assert "results" in data

            # Check nodes
            assert "root" in data["nodes"]
            assert "A1" in data["nodes"]

            # Check edges
            assert len(data["edges"]) > 0

    def test_json_contains_complete_node_data(self, simple_proof_tree):
        """Test that JSON export contains complete node data."""
        viz = ProofTreeVisualizer(simple_proof_tree)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "proof_tree.json"
            viz.export_json(output_path)

            with open(output_path) as f:
                data = json.load(f)

            # Check A1 node data
            a1_data = data["nodes"]["A1"]
            assert a1_data["id"] == "A1"
            assert a1_data["label"] == "Axiom 1"
            assert a1_data["type"] == "axiom"
            assert a1_data["status"] == ProofStatus.VERIFIED.value

            # Check L1 node data
            l1_data = data["nodes"]["L1"]
            assert len(l1_data["proof_steps"]) == 3

    def test_visualize_tree_with_failed_proof(self):
        """Test visualizing tree with failed proof elements."""
        root = ProofNode(
            id="root",
            label="Proof System",
            type="root",
            statement="Test system",
        )

        failed_lemma = ProofNode(
            id="L1",
            label="Failed Lemma",
            type="lemma",
            statement="This lemma fails",
            status=ProofStatus.FAILED,
        )

        root.children = [failed_lemma]

        tree = ProofTree(root=root, properties=[], results=[])
        viz = ProofTreeVisualizer(tree)

        # Should handle failed status correctly
        assert "L1" in viz.graph.nodes()
        assert viz.graph.nodes["L1"]["status"] == ProofStatus.FAILED.value

    def test_visualize_tree_with_unknown_status(self):
        """Test visualizing tree with unknown proof status."""
        root = ProofNode(
            id="root",
            label="Proof System",
            type="root",
            statement="Test system",
        )

        unknown_theorem = ProofNode(
            id="T1",
            label="Unknown Theorem",
            type="theorem",
            statement="Status unknown",
            status=ProofStatus.UNKNOWN,
        )

        root.children = [unknown_theorem]

        tree = ProofTree(root=root, properties=[], results=[])
        viz = ProofTreeVisualizer(tree)

        assert "T1" in viz.graph.nodes()
        assert viz.graph.nodes["T1"]["status"] == ProofStatus.UNKNOWN.value

    def test_empty_proof_tree(self):
        """Test handling empty proof tree."""
        root = ProofNode(
            id="root",
            label="Empty Root",
            type="root",
            statement="Empty tree",
        )

        tree = ProofTree(root=root, properties=[], results=[])
        viz = ProofTreeVisualizer(tree)

        # Should only have root node
        assert len(viz.graph.nodes()) == 1
        assert "root" in viz.graph.nodes()
        assert len(viz.graph.edges()) == 0

    def test_proof_tree_with_results(self, simple_proof_tree):
        """Test proof tree visualization with verification results."""
        result1 = ProofResult(
            property_id="prop1",
            property_name="Property 1",
            status=ProofStatus.VERIFIED,
        )

        result2 = ProofResult(
            property_id="prop2",
            property_name="Property 2",
            status=ProofStatus.FAILED,
            counterexample={"x": "5"},
        )

        simple_proof_tree.results = [result1, result2]

        viz = ProofTreeVisualizer(simple_proof_tree)

        # Export to JSON and check results are included
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "proof_tree.json"
            viz.export_json(output_path)

            with open(output_path) as f:
                data = json.load(f)

            assert len(data["results"]) == 2
            assert data["results"][0]["property_id"] == "prop1"
            # Status is stored as enum value in string form
            assert data["results"][1]["status"] in ["failed", "ProofStatus.FAILED"]
