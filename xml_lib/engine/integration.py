"""Integration with assertion ledger and telemetry."""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from lxml import etree

from xml_lib.engine.proofs import GuardrailProof, ProofResult

logger = logging.getLogger(__name__)


@dataclass
class EngineMetrics:
    """Metrics for engine execution."""

    guardrail_count: int = 0
    proof_count: int = 0
    verified_count: int = 0
    failed_count: int = 0
    convergence_metrics: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Export to dictionary."""
        return {
            "guardrail_count": self.guardrail_count,
            "proof_count": self.proof_count,
            "verified_count": self.verified_count,
            "failed_count": self.failed_count,
            "convergence_metrics": self.convergence_metrics,
            "timestamp": self.timestamp.isoformat(),
        }


class EngineLedgerIntegration:
    """Integration between engine and assertion ledger."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_proof_xml(
        self,
        guardrail_proofs: list[GuardrailProof],
        output_file: Path,
    ) -> None:
        """Write proofs to XML assertion ledger."""
        output_file.parent.mkdir(parents=True, exist_ok=True)

        root = etree.Element("engine-proof-ledger")
        root.set("version", "1.0")
        root.set("timestamp", datetime.now().isoformat())

        # Add guardrail proofs
        for proof in guardrail_proofs:
            proof_elem = etree.SubElement(root, "guardrail-proof")
            proof_elem.set("rule-id", proof.rule_id)
            proof_elem.set("rule-name", proof.rule_name)

            # Add operator info
            op_elem = etree.SubElement(proof_elem, "operator")
            op_elem.set("name", proof.operator.name)
            op_elem.set("type", proof.operator.__class__.__name__)

            # Add fixed-point result
            if proof.fixed_point_result:
                fp_elem = etree.SubElement(proof_elem, "fixed-point")
                fp_elem.set("converged", str(proof.fixed_point_result.is_converged()))
                fp_elem.set(
                    "iterations",
                    str(proof.fixed_point_result.metrics.iterations),
                )
                fp_elem.set(
                    "final-residual",
                    str(proof.fixed_point_result.metrics.final_residual),
                )
                fp_elem.set("energy", str(proof.fixed_point_result.metrics.energy))

            # Add obligations
            obligations_elem = etree.SubElement(proof_elem, "obligations")
            for obligation in proof.obligations:
                obl_elem = etree.SubElement(obligations_elem, "obligation")
                obl_elem.set("id", obligation.obligation_id)
                obl_elem.set("status", obligation.status.value)

                stmt_elem = etree.SubElement(obl_elem, "statement")
                stmt_elem.text = obligation.statement

                # Add steps
                steps_elem = etree.SubElement(obl_elem, "steps")
                for step in obligation.steps:
                    step_elem = etree.SubElement(steps_elem, "step")
                    step_elem.set("id", step.step_id)
                    step_elem.set("result", str(step.result))
                    step_elem.text = step.description

        # Write to file
        tree = etree.ElementTree(root)
        tree.write(
            str(output_file),
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8",
        )

    def write_proof_jsonl(
        self,
        guardrail_proofs: list[GuardrailProof],
        output_file: Path,
    ) -> None:
        """Write proofs to JSON Lines format."""
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with output_file.open("w") as f:
            for proof in guardrail_proofs:
                record = {
                    "timestamp": datetime.now().isoformat(),
                    "event_type": "guardrail_proof",
                    **proof.to_dict(),
                }
                f.write(json.dumps(record) + "\n")

    def write_metrics_json(
        self,
        metrics: EngineMetrics,
        output_file: Path,
    ) -> None:
        """Write metrics to JSON."""
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with output_file.open("w") as f:
            json.dump(metrics.to_dict(), f, indent=2)

    def generate_checksum(
        self,
        guardrail_proofs: list[GuardrailProof],
    ) -> str:
        """Generate deterministic checksum for proofs."""
        # Sort by rule_id for determinism
        sorted_proofs = sorted(guardrail_proofs, key=lambda p: p.rule_id)

        # Create canonical representation
        canonical = []
        for proof in sorted_proofs:
            canonical.append(f"rule:{proof.rule_id}")
            canonical.append(f"operator:{proof.operator.name}")
            for obligation in proof.obligations:
                canonical.append(f"obligation:{obligation.obligation_id}")
                canonical.append(f"status:{obligation.status.value}")

        text = "|".join(canonical)
        return hashlib.sha256(text.encode()).hexdigest()

    def integrate_with_telemetry(
        self,
        proof_result: ProofResult,
        telemetry_sink: Any,
    ) -> None:
        """Send proof results to telemetry sink."""
        if not hasattr(telemetry_sink, "log_event"):
            return

        try:
            telemetry_sink.log_event(
                "engine_proof_verification",
                total_obligations=proof_result.summary.get("total_obligations", 0),
                verified=proof_result.summary.get("verified", 0),
                failed=proof_result.summary.get("failed", 0),
                success_rate=proof_result.summary.get("success_rate", 0.0),
                all_verified=proof_result.all_verified(),
            )
        except Exception as e:
            logger.warning(f"Telemetry logging failed: {e}")

    def create_proof_artifact(
        self,
        guardrail_proofs: list[GuardrailProof],
        proof_result: ProofResult,
    ) -> dict:
        """Create comprehensive proof artifact."""
        return {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0",
                "checksum": self.generate_checksum(guardrail_proofs),
            },
            "proofs": [p.to_dict() for p in guardrail_proofs],
            "summary": proof_result.summary,
            "all_verified": proof_result.all_verified(),
        }


@dataclass
class StreamingSafeEvaluator:
    """Streaming-safe evaluation hooks for engine."""

    chunk_size: int = 100
    buffer: list[Any] = field(default_factory=list)

    def process_chunk(
        self,
        chunk: list[Any],
        processor: Any,
    ) -> list[Any]:
        """Process a chunk without loading entire dataset."""
        results = []
        for item in chunk:
            try:
                result = processor(item)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})
        return results

    def streaming_proof_verification(
        self,
        guardrail_proofs: list[GuardrailProof],
    ) -> dict:
        """Verify proofs in streaming fashion."""
        verified = 0
        failed = 0

        for i in range(0, len(guardrail_proofs), self.chunk_size):
            chunk = guardrail_proofs[i : i + self.chunk_size]

            for proof in chunk:
                for obligation in proof.obligations:
                    obligation.verify()
                    if obligation.status.value == "verified":
                        verified += 1
                    else:
                        failed += 1

        return {
            "verified": verified,
            "failed": failed,
            "total": verified + failed,
            "streaming_chunks": (len(guardrail_proofs) + self.chunk_size - 1) // self.chunk_size,
        }

    def validate_with_streaming(
        self,
        data_stream: Any,
        validator: Any,
    ) -> dict:
        """Validate data stream without loading all at once."""
        valid_count = 0
        invalid_count = 0

        for chunk in data_stream:
            results = self.process_chunk(chunk, validator)
            valid_count += sum(1 for r in results if r.get("valid", False))
            invalid_count += sum(1 for r in results if not r.get("valid", True))

        return {
            "valid": valid_count,
            "invalid": invalid_count,
            "total": valid_count + invalid_count,
        }
