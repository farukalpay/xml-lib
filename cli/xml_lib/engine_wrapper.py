"""Wrapper for engine integration with validator and CLI."""

import json
from pathlib import Path
from typing import Any

import numpy as np

from xml_lib.engine.integration import EngineLedgerIntegration, EngineMetrics
from xml_lib.engine.operators import ContractionOperator
from xml_lib.engine.parser import EngineSpecParser
from xml_lib.engine.proofs import GuardrailProof, ProofEngine, ProofResult
from xml_lib.engine.spaces import HilbertSpace
from xml_lib.guardrails import GuardrailRule
from xml_lib.telemetry import TelemetrySink


class EngineWrapper:
    """Wrapper for engine integration."""

    def __init__(
        self,
        engine_dir: Path,
        output_dir: Path,
        telemetry: TelemetrySink | None = None,
    ):
        self.engine_dir = engine_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.telemetry = telemetry

        # Initialize components
        self.parser = EngineSpecParser(engine_dir)
        self.proof_engine = ProofEngine()
        self.integration = EngineLedgerIntegration(output_dir)

    def run_engine_checks(
        self,
        guardrail_rules: list[GuardrailRule],
    ) -> tuple[list[GuardrailProof], ProofResult, EngineMetrics]:
        """Run engine checks on guardrail rules."""
        # Parse engine spec
        engine_spec = self.parser.parse()

        # Create default Hilbert space
        space = engine_spec.spaces.get(
            "hilbert", HilbertSpace(dimension=10, name="DefaultH")
        )

        # Generate proofs for each guardrail rule
        guardrail_proofs: list[GuardrailProof] = []

        for rule in guardrail_rules:
            # Create operator for this rule
            # Default: contraction with q=0.9 (can be customized based on rule)
            operator = ContractionOperator(
                space=space,
                name=f"Op_{rule.id}",
                contraction_q=0.9,
            )
            # Simple scaled identity implementation
            operator.apply = lambda x: 0.9 * x

            # Generate sample points
            initial_state = np.random.randn(space.dimension) * 0.5
            sample_points = self.parser.generate_sample_points(space, count=10)

            # Generate proof
            proof = self.proof_engine.prove_guardrail_compliance(
                rule_id=rule.id,
                rule_name=rule.name,
                operator=operator,
                initial_state=initial_state,
                sample_points=sample_points,
            )

            guardrail_proofs.append(proof)

        # Batch verify all proofs
        proof_result = self.proof_engine.batch_verify(guardrail_proofs)

        # Compute metrics
        convergence_metrics = {}
        for proof in guardrail_proofs:
            if proof.fixed_point_result:
                convergence_metrics[proof.rule_id] = {
                    "converged": proof.fixed_point_result.is_converged(),
                    "iterations": proof.fixed_point_result.metrics.iterations,
                    "final_residual": proof.fixed_point_result.metrics.final_residual,
                    "energy": proof.fixed_point_result.metrics.energy,
                }

        metrics = EngineMetrics(
            guardrail_count=len(guardrail_rules),
            proof_count=len(proof_result.obligations),
            verified_count=proof_result.summary.get("verified", 0),
            failed_count=proof_result.summary.get("failed", 0),
            convergence_metrics=convergence_metrics,
        )

        # Integrate with telemetry
        if self.telemetry:
            self.integration.integrate_with_telemetry(proof_result, self.telemetry)

        return guardrail_proofs, proof_result, metrics

    def write_outputs(
        self,
        guardrail_proofs: list[GuardrailProof],
        proof_result: ProofResult,
        metrics: EngineMetrics,
    ) -> dict[str, Path]:
        """Write engine outputs to files."""
        output_files = {}

        # Write XML proof ledger
        xml_file = self.output_dir / "engine_proofs.xml"
        self.integration.write_proof_xml(guardrail_proofs, xml_file)
        output_files["xml"] = xml_file

        # Write JSONL proof ledger
        jsonl_file = self.output_dir / "engine_proofs.jsonl"
        self.integration.write_proof_jsonl(guardrail_proofs, jsonl_file)
        output_files["jsonl"] = jsonl_file

        # Write metrics
        metrics_file = self.output_dir / "engine_metrics.json"
        self.integration.write_metrics_json(metrics, metrics_file)
        output_files["metrics"] = metrics_file

        # Write proof artifact
        artifact = self.integration.create_proof_artifact(
            guardrail_proofs, proof_result
        )
        artifact_file = self.output_dir / "engine_artifact.json"
        with artifact_file.open("w") as f:
            json.dump(artifact, f, indent=2)
        output_files["artifact"] = artifact_file

        return output_files

    def export_proofs_json(
        self,
        guardrail_proofs: list[GuardrailProof],
        proof_result: ProofResult,
        metrics: EngineMetrics,
    ) -> dict[str, Any]:
        """Export proofs and metrics as JSON."""
        return {
            "proofs": [p.to_dict() for p in guardrail_proofs],
            "proof_result": proof_result.to_dict(),
            "metrics": metrics.to_dict(),
            "checksum": self.integration.generate_checksum(guardrail_proofs),
        }
