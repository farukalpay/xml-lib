"""Tests for engine wrapper integration."""

import json
import tempfile
from pathlib import Path

import pytest

from xml_lib.engine_wrapper import EngineWrapper
from xml_lib.guardrails import GuardrailRule


class TestEngineWrapper:
    """Tests for EngineWrapper class."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for engine and output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            engine_dir = tmpdir / "engine"
            engine_dir.mkdir()
            output_dir = tmpdir / "output"
            output_dir.mkdir()

            # Create basic engine spec
            engine_spec = '''<?xml version="1.0" encoding="UTF-8"?>
<engine-spec>
  <spaces>
    <hilbert name="DefaultH" dimension="10"/>
  </spaces>
  <operators>
    <contraction name="T1" q="0.9"/>
  </operators>
</engine-spec>'''
            (engine_dir / "spec.xml").write_text(engine_spec)

            yield engine_dir, output_dir

    def test_create_engine_wrapper(self, temp_dirs):
        """Test creating engine wrapper."""
        engine_dir, output_dir = temp_dirs
        wrapper = EngineWrapper(engine_dir, output_dir)

        assert wrapper.engine_dir == engine_dir
        assert wrapper.output_dir == output_dir
        assert wrapper.parser is not None
        assert wrapper.proof_engine is not None
        assert wrapper.integration is not None

    def test_engine_wrapper_creates_output_dir(self):
        """Test that wrapper creates output directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            engine_dir = tmpdir / "engine"
            engine_dir.mkdir()
            output_dir = tmpdir / "output" / "nested"

            wrapper = EngineWrapper(engine_dir, output_dir)

            assert output_dir.exists()

    def test_run_engine_checks_empty_rules(self, temp_dirs):
        """Test running engine checks with no rules."""
        engine_dir, output_dir = temp_dirs
        wrapper = EngineWrapper(engine_dir, output_dir)

        proofs, proof_result, metrics = wrapper.run_engine_checks([])

        assert len(proofs) == 0
        assert metrics.guardrail_count == 0

    def test_run_engine_checks_single_rule(self, temp_dirs):
        """Test running engine checks with single rule."""
        engine_dir, output_dir = temp_dirs
        wrapper = EngineWrapper(engine_dir, output_dir)

        rule = GuardrailRule(
            id="TEST1",
            name="Test Rule",
            description="Test rule for engine",
            priority="high",
            constraint_type="xpath",
            constraint="//test",
            message="Test message",
            provenance={"author": "Test"},
        )

        proofs, proof_result, metrics = wrapper.run_engine_checks([rule])

        assert len(proofs) == 1
        assert proofs[0].rule_id == "TEST1"
        assert proofs[0].rule_name == "Test Rule"
        assert metrics.guardrail_count == 1

    def test_run_engine_checks_multiple_rules(self, temp_dirs):
        """Test running engine checks with multiple rules."""
        engine_dir, output_dir = temp_dirs
        wrapper = EngineWrapper(engine_dir, output_dir)

        rules = [
            GuardrailRule(
                id=f"RULE{i}",
                name=f"Rule {i}",
                description=f"Test rule {i}",
                priority="medium",
                constraint_type="xpath",
                constraint=f"//element{i}",
                message=None,
                provenance={},
            )
            for i in range(3)
        ]

        proofs, proof_result, metrics = wrapper.run_engine_checks(rules)

        assert len(proofs) == 3
        assert metrics.guardrail_count == 3

    def test_run_engine_checks_generates_proofs(self, temp_dirs):
        """Test that engine checks generate proof obligations."""
        engine_dir, output_dir = temp_dirs
        wrapper = EngineWrapper(engine_dir, output_dir)

        rule = GuardrailRule(
            id="GR1",
            name="Guardrail 1",
            description="Test",
            priority="high",
            constraint_type="xpath",
            constraint="//test",
            message=None,
            provenance={},
        )

        proofs, proof_result, metrics = wrapper.run_engine_checks([rule])

        assert proof_result is not None
        assert isinstance(proof_result.summary, dict)

    def test_run_engine_checks_metrics_structure(self, temp_dirs):
        """Test metrics structure from engine checks."""
        engine_dir, output_dir = temp_dirs
        wrapper = EngineWrapper(engine_dir, output_dir)

        rules = [
            GuardrailRule(
                id="GR1",
                name="Test",
                description="Test",
                priority="high",
                constraint_type="xpath",
                constraint="//test",
                message=None,
                provenance={},
            )
        ]

        proofs, proof_result, metrics = wrapper.run_engine_checks(rules)

        assert hasattr(metrics, "guardrail_count")
        assert hasattr(metrics, "proof_count")
        assert hasattr(metrics, "verified_count")
        assert hasattr(metrics, "failed_count")
        assert hasattr(metrics, "convergence_metrics")

    def test_write_outputs_creates_files(self, temp_dirs):
        """Test that write_outputs creates all output files."""
        engine_dir, output_dir = temp_dirs
        wrapper = EngineWrapper(engine_dir, output_dir)

        rule = GuardrailRule(
            id="GR1",
            name="Test Rule",
            description="Test",
            priority="high",
            constraint_type="xpath",
            constraint="//test",
            message=None,
            provenance={},
        )

        proofs, proof_result, metrics = wrapper.run_engine_checks([rule])
        output_files = wrapper.write_outputs(proofs, proof_result, metrics)

        assert "xml" in output_files
        assert "jsonl" in output_files
        assert "metrics" in output_files
        assert "artifact" in output_files

        # Check files exist
        assert output_files["xml"].exists()
        assert output_files["jsonl"].exists()
        assert output_files["metrics"].exists()
        assert output_files["artifact"].exists()

    def test_write_outputs_xml_format(self, temp_dirs):
        """Test XML output format."""
        engine_dir, output_dir = temp_dirs
        wrapper = EngineWrapper(engine_dir, output_dir)

        rule = GuardrailRule(
            id="GR1",
            name="Test Rule",
            description="Test",
            priority="high",
            constraint_type="xpath",
            constraint="//test",
            message=None,
            provenance={},
        )

        proofs, proof_result, metrics = wrapper.run_engine_checks([rule])
        output_files = wrapper.write_outputs(proofs, proof_result, metrics)

        xml_content = output_files["xml"].read_text()
        assert "engine-proof-ledger" in xml_content
        assert "GR1" in xml_content
        assert "Test Rule" in xml_content

    def test_write_outputs_jsonl_format(self, temp_dirs):
        """Test JSONL output format."""
        engine_dir, output_dir = temp_dirs
        wrapper = EngineWrapper(engine_dir, output_dir)

        rule = GuardrailRule(
            id="GR1",
            name="Test Rule",
            description="Test",
            priority="high",
            constraint_type="xpath",
            constraint="//test",
            message=None,
            provenance={},
        )

        proofs, proof_result, metrics = wrapper.run_engine_checks([rule])
        output_files = wrapper.write_outputs(proofs, proof_result, metrics)

        jsonl_content = output_files["jsonl"].read_text()
        lines = jsonl_content.strip().split("\n")
        assert len(lines) >= 1

        record = json.loads(lines[0])
        assert "rule_id" in record
        assert record["rule_id"] == "GR1"

    def test_write_outputs_metrics_json_format(self, temp_dirs):
        """Test metrics JSON output format."""
        engine_dir, output_dir = temp_dirs
        wrapper = EngineWrapper(engine_dir, output_dir)

        rule = GuardrailRule(
            id="GR1",
            name="Test",
            description="Test",
            priority="high",
            constraint_type="xpath",
            constraint="//test",
            message=None,
            provenance={},
        )

        proofs, proof_result, metrics = wrapper.run_engine_checks([rule])
        output_files = wrapper.write_outputs(proofs, proof_result, metrics)

        metrics_content = output_files["metrics"].read_text()
        metrics_data = json.loads(metrics_content)

        assert "guardrail_count" in metrics_data
        assert metrics_data["guardrail_count"] == 1

    def test_write_outputs_artifact_format(self, temp_dirs):
        """Test artifact JSON output format."""
        engine_dir, output_dir = temp_dirs
        wrapper = EngineWrapper(engine_dir, output_dir)

        rule = GuardrailRule(
            id="GR1",
            name="Test",
            description="Test",
            priority="high",
            constraint_type="xpath",
            constraint="//test",
            message=None,
            provenance={},
        )

        proofs, proof_result, metrics = wrapper.run_engine_checks([rule])
        output_files = wrapper.write_outputs(proofs, proof_result, metrics)

        artifact_content = output_files["artifact"].read_text()
        artifact_data = json.loads(artifact_content)

        assert "timestamp" in artifact_data or "proofs" in artifact_data

    def test_export_proofs_json(self, temp_dirs):
        """Test export_proofs_json method."""
        engine_dir, output_dir = temp_dirs
        wrapper = EngineWrapper(engine_dir, output_dir)

        rule = GuardrailRule(
            id="GR1",
            name="Test Rule",
            description="Test",
            priority="high",
            constraint_type="xpath",
            constraint="//test",
            message=None,
            provenance={},
        )

        proofs, proof_result, metrics = wrapper.run_engine_checks([rule])
        export_data = wrapper.export_proofs_json(proofs, proof_result, metrics)

        assert "proofs" in export_data
        assert "proof_result" in export_data
        assert "metrics" in export_data
        assert "checksum" in export_data

        assert len(export_data["proofs"]) == 1
        assert export_data["proofs"][0]["rule_id"] == "GR1"

    def test_export_proofs_json_multiple_rules(self, temp_dirs):
        """Test export with multiple rules."""
        engine_dir, output_dir = temp_dirs
        wrapper = EngineWrapper(engine_dir, output_dir)

        rules = [
            GuardrailRule(
                id=f"GR{i}",
                name=f"Rule {i}",
                description="Test",
                priority="medium",
                constraint_type="xpath",
                constraint="//test",
                message=None,
                provenance={},
            )
            for i in range(5)
        ]

        proofs, proof_result, metrics = wrapper.run_engine_checks(rules)
        export_data = wrapper.export_proofs_json(proofs, proof_result, metrics)

        assert len(export_data["proofs"]) == 5
        assert export_data["metrics"]["guardrail_count"] == 5

    def test_checksum_determinism(self, temp_dirs):
        """Test that checksum is deterministic for same proofs."""
        engine_dir, output_dir = temp_dirs
        wrapper = EngineWrapper(engine_dir, output_dir)

        rule = GuardrailRule(
            id="GR1",
            name="Test",
            description="Test",
            priority="high",
            constraint_type="xpath",
            constraint="//test",
            message=None,
            provenance={},
        )

        # Note: This test checks determinism within same proof objects
        # The actual iteration may vary due to randomness in initial state
        proofs1, proof_result1, metrics1 = wrapper.run_engine_checks([rule])
        export1 = wrapper.export_proofs_json(proofs1, proof_result1, metrics1)

        # Generate checksum should be consistent for same proofs
        checksum1 = export1["checksum"]
        checksum2 = wrapper.integration.generate_checksum(proofs1)

        assert checksum1 == checksum2


class TestEngineWrapperWithTelemetry:
    """Tests for engine wrapper with telemetry integration."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            engine_dir = tmpdir / "engine"
            engine_dir.mkdir()
            output_dir = tmpdir / "output"
            output_dir.mkdir()

            # Create basic engine spec
            engine_spec = '''<?xml version="1.0" encoding="UTF-8"?>
<engine-spec>
  <spaces>
    <hilbert name="DefaultH" dimension="10"/>
  </spaces>
</engine-spec>'''
            (engine_dir / "spec.xml").write_text(engine_spec)

            yield engine_dir, output_dir

    def test_engine_wrapper_without_telemetry(self, temp_dirs):
        """Test engine wrapper works without telemetry."""
        engine_dir, output_dir = temp_dirs
        wrapper = EngineWrapper(engine_dir, output_dir, telemetry=None)

        assert wrapper.telemetry is None

        rule = GuardrailRule(
            id="GR1",
            name="Test",
            description="Test",
            priority="high",
            constraint_type="xpath",
            constraint="//test",
            message=None,
            provenance={},
        )

        # Should work without telemetry
        proofs, proof_result, metrics = wrapper.run_engine_checks([rule])
        assert len(proofs) == 1


class TestEngineWrapperEdgeCases:
    """Tests for edge cases and error handling."""

    def test_wrapper_with_nonexistent_engine_dir(self):
        """Test wrapper with nonexistent engine directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            engine_dir = tmpdir / "nonexistent"
            output_dir = tmpdir / "output"

            # Should not crash on creation
            wrapper = EngineWrapper(engine_dir, output_dir)
            assert wrapper is not None

    def test_run_checks_with_high_priority_rules(self):
        """Test running checks with different priority levels."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            engine_dir = tmpdir / "engine"
            engine_dir.mkdir()
            output_dir = tmpdir / "output"

            # Create engine spec
            engine_spec = '''<?xml version="1.0" encoding="UTF-8"?>
<engine-spec>
  <spaces>
    <hilbert name="DefaultH" dimension="10"/>
  </spaces>
</engine-spec>'''
            (engine_dir / "spec.xml").write_text(engine_spec)

            wrapper = EngineWrapper(engine_dir, output_dir)

            rules = [
                GuardrailRule(
                    id="CRITICAL1",
                    name="Critical Rule",
                    description="Critical",
                    priority="critical",
                    constraint_type="xpath",
                    constraint="//test",
                    message=None,
                    provenance={},
                ),
                GuardrailRule(
                    id="LOW1",
                    name="Low Rule",
                    description="Low",
                    priority="low",
                    constraint_type="xpath",
                    constraint="//test",
                    message=None,
                    provenance={},
                ),
            ]

            proofs, proof_result, metrics = wrapper.run_engine_checks(rules)

            assert len(proofs) == 2
            assert any(p.rule_id == "CRITICAL1" for p in proofs)
            assert any(p.rule_id == "LOW1" for p in proofs)

    def test_write_outputs_empty_proofs(self):
        """Test writing outputs with no proofs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            engine_dir = tmpdir / "engine"
            engine_dir.mkdir()
            output_dir = tmpdir / "output"

            # Create engine spec
            engine_spec = '''<?xml version="1.0" encoding="UTF-8"?>
<engine-spec>
  <spaces>
    <hilbert name="DefaultH" dimension="10"/>
  </spaces>
</engine-spec>'''
            (engine_dir / "spec.xml").write_text(engine_spec)

            wrapper = EngineWrapper(engine_dir, output_dir)

            proofs, proof_result, metrics = wrapper.run_engine_checks([])
            output_files = wrapper.write_outputs(proofs, proof_result, metrics)

            # Should still create files
            assert output_files["xml"].exists()
            assert output_files["jsonl"].exists()
            assert output_files["metrics"].exists()

    def test_export_proofs_json_structure(self):
        """Test JSON export structure is complete."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            engine_dir = tmpdir / "engine"
            engine_dir.mkdir()
            output_dir = tmpdir / "output"

            engine_spec = '''<?xml version="1.0" encoding="UTF-8"?>
<engine-spec>
  <spaces>
    <hilbert name="DefaultH" dimension="10"/>
  </spaces>
</engine-spec>'''
            (engine_dir / "spec.xml").write_text(engine_spec)

            wrapper = EngineWrapper(engine_dir, output_dir)

            rule = GuardrailRule(
                id="GR1",
                name="Test Rule",
                description="Test description",
                priority="high",
                constraint_type="xpath",
                constraint="//element",
                message="Test message",
                provenance={"author": "Test Author"},
            )

            proofs, proof_result, metrics = wrapper.run_engine_checks([rule])
            export = wrapper.export_proofs_json(proofs, proof_result, metrics)

            # Verify complete structure
            assert isinstance(export["proofs"], list)
            assert isinstance(export["proof_result"], dict)
            assert isinstance(export["metrics"], dict)
            assert isinstance(export["checksum"], str)

            # Check proof structure
            if len(export["proofs"]) > 0:
                proof_data = export["proofs"][0]
                assert "rule_id" in proof_data
                assert "rule_name" in proof_data
                assert "operator_name" in proof_data
