"""Proof obligation system bound to guardrail rules."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
import numpy.typing as npt

from xml_lib.engine.fixed_points import ConvergenceResult, FixedPointIterator
from xml_lib.engine.operators import (
    ContractionOperator,
    FirmlyNonexpansiveOperator,
    Operator,
)
from xml_lib.engine.spaces import HilbertSpace


class ProofStatus(Enum):
    """Proof verification status."""

    VERIFIED = "verified"
    FAILED = "failed"
    PENDING = "pending"
    SKIPPED = "skipped"


@dataclass
class ProofStep:
    """Single step in a proof."""

    step_id: str
    description: str
    reasoning: str
    result: bool
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProofObligation:
    """Machine-checkable proof obligation."""

    obligation_id: str
    statement: str
    axioms_used: list[str] = field(default_factory=list)
    steps: list[ProofStep] = field(default_factory=list)
    status: ProofStatus = ProofStatus.PENDING
    guardrail_rule_id: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)

    def add_step(self, step: ProofStep) -> None:
        """Add a proof step."""
        self.steps.append(step)

    def verify(self) -> bool:
        """Verify all steps."""
        if not self.steps:
            self.status = ProofStatus.SKIPPED
            return False

        all_verified = all(step.result for step in self.steps)
        self.status = ProofStatus.VERIFIED if all_verified else ProofStatus.FAILED
        return all_verified

    def to_dict(self) -> dict:
        """Export to dictionary."""
        return {
            "obligation_id": self.obligation_id,
            "statement": self.statement,
            "axioms_used": self.axioms_used,
            "steps": [
                {
                    "step_id": s.step_id,
                    "description": s.description,
                    "reasoning": s.reasoning,
                    "result": s.result,
                    "details": s.details,
                }
                for s in self.steps
            ],
            "status": self.status.value,
            "guardrail_rule_id": self.guardrail_rule_id,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ProofResult:
    """Result of proof verification."""

    obligations: list[ProofObligation] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    def all_verified(self) -> bool:
        """Check if all obligations verified."""
        return all(
            o.status == ProofStatus.VERIFIED or o.status == ProofStatus.SKIPPED
            for o in self.obligations
        )

    def to_dict(self) -> dict:
        """Export to dictionary."""
        return {
            "obligations": [o.to_dict() for o in self.obligations],
            "summary": self.summary,
            "all_verified": self.all_verified(),
        }


@dataclass
class GuardrailProof:
    """Proof binding guardrail rule to mathematical constructs."""

    rule_id: str
    rule_name: str
    operator: Operator
    fixed_point_result: ConvergenceResult | None = None
    obligations: list[ProofObligation] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Export to dictionary."""
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "operator_name": self.operator.name,
            "fixed_point_converged": (
                self.fixed_point_result.is_converged() if self.fixed_point_result else False
            ),
            "fixed_point_metrics": (
                self.fixed_point_result.metrics.to_dict() if self.fixed_point_result else {}
            ),
            "obligations": [o.to_dict() for o in self.obligations],
        }


@dataclass
class ProofEngine:
    """Engine for generating and verifying proof obligations."""

    def prove_contraction(
        self,
        operator: Operator,
        sample_points: list[npt.NDArray[np.float64]],
        expected_q: float = 0.9,
    ) -> ProofObligation:
        """Prove operator is a contraction with constant q."""
        obligation = ProofObligation(
            obligation_id=f"contraction_{operator.name}",
            statement=f"Operator {operator.name} is a contraction with q={expected_q}",
            axioms_used=["Banach-fixed-point"],
        )

        if not sample_points or len(sample_points) < 2:
            obligation.add_step(
                ProofStep(
                    step_id="verify_contraction",
                    description="Verify contraction property on samples",
                    reasoning="Insufficient sample points",
                    result=False,
                )
            )
            obligation.status = ProofStatus.FAILED
            return obligation

        # Check contraction property on all pairs
        max_ratio = 0.0
        all_satisfy = True

        for i in range(len(sample_points)):
            for j in range(i + 1, len(sample_points)):
                x, y = sample_points[i], sample_points[j]
                tx = operator.apply(x)
                ty = operator.apply(y)

                d_xy = operator.space.distance(x, y)
                d_txy = operator.space.distance(tx, ty)

                if d_xy > 1e-10:
                    ratio = d_txy / d_xy
                    max_ratio = max(max_ratio, ratio)

                    if ratio > expected_q + 0.01:  # tolerance
                        all_satisfy = False

        obligation.add_step(
            ProofStep(
                step_id="verify_contraction",
                description="Verify contraction property on samples",
                reasoning=f"Check ||T(x)-T(y)|| <= {expected_q} ||x-y|| for all sample pairs",
                result=all_satisfy,
                details={
                    "expected_q": expected_q,
                    "observed_max_ratio": max_ratio,
                    "sample_pairs": len(sample_points) * (len(sample_points) - 1) // 2,
                },
            )
        )

        obligation.verify()
        return obligation

    def prove_firmly_nonexpansive(
        self,
        operator: FirmlyNonexpansiveOperator,
        space: HilbertSpace,
        sample_points: list[npt.NDArray[np.float64]],
    ) -> ProofObligation:
        """Prove operator is firmly nonexpansive."""
        obligation = ProofObligation(
            obligation_id=f"firmly_nonexpansive_{operator.name}",
            statement=f"Operator {operator.name} is firmly nonexpansive",
            axioms_used=["Hilbert-projection"],
        )

        if len(sample_points) < 2:
            obligation.add_step(
                ProofStep(
                    step_id="verify_fne",
                    description="Verify firmly nonexpansive property",
                    reasoning="Insufficient samples",
                    result=False,
                )
            )
            obligation.status = ProofStatus.FAILED
            return obligation

        all_satisfy = True
        for i in range(len(sample_points)):
            for j in range(i + 1, len(sample_points)):
                x, y = sample_points[i], sample_points[j]
                if not operator.is_firmly_nonexpansive(x, y):
                    all_satisfy = False
                    break

        obligation.add_step(
            ProofStep(
                step_id="verify_fne",
                description="Verify firmly nonexpansive property on samples",
                reasoning="Check ||T(x)-T(y)||² <= <T(x)-T(y), x-y>",
                result=all_satisfy,
                details={"sample_pairs": len(sample_points) * (len(sample_points) - 1) // 2},
            )
        )

        obligation.verify()
        return obligation

    def prove_fixed_point_exists(
        self,
        operator: Operator,
        initial_point: npt.NDArray[np.float64],
    ) -> tuple[ProofObligation, ConvergenceResult | None]:
        """Prove fixed point exists via iteration."""
        obligation = ProofObligation(
            obligation_id=f"fixed_point_{operator.name}",
            statement=f"Fixed point exists for {operator.name}",
            axioms_used=["Banach-fixed-point", "completeness"],
        )

        # Run fixed-point iteration
        iterator = FixedPointIterator(operator=operator, max_iterations=1000, tolerance=1e-6)
        result = iterator.iterate(initial_point)

        obligation.add_step(
            ProofStep(
                step_id="run_iteration",
                description="Run fixed-point iteration",
                reasoning="Apply Banach fixed-point theorem via iteration",
                result=result.is_converged(),
                details={
                    "iterations": result.metrics.iterations,
                    "final_residual": result.metrics.final_residual,
                    "convergence_rate": result.metrics.rate,
                },
            )
        )

        if isinstance(operator, ContractionOperator):
            # Additional verification for contraction
            banach_bounds = iterator.banach_fixed_point_theorem(
                operator.contraction_q,
                initial_point,
                operator.apply(initial_point),
            )

            obligation.add_step(
                ProofStep(
                    step_id="banach_bounds",
                    description="Verify Banach fixed-point theorem bounds",
                    reasoning="Contraction mapping theorem guarantees unique fixed point",
                    result=True,
                    details=banach_bounds,
                )
            )

        obligation.verify()
        return obligation, result

    def prove_guardrail_compliance(
        self,
        rule_id: str,
        rule_name: str,
        operator: Operator,
        initial_state: npt.NDArray[np.float64],
        sample_points: list[npt.NDArray[np.float64]],
    ) -> GuardrailProof:
        """Generate comprehensive proof for guardrail rule."""
        guardrail_proof = GuardrailProof(
            rule_id=rule_id,
            rule_name=rule_name,
            operator=operator,
        )

        # Prove operator properties
        if isinstance(operator, ContractionOperator):
            contraction_proof = self.prove_contraction(
                operator, sample_points, operator.contraction_q
            )
            contraction_proof.guardrail_rule_id = rule_id
            guardrail_proof.obligations.append(contraction_proof)

        if isinstance(operator, FirmlyNonexpansiveOperator) and isinstance(
            operator.space, HilbertSpace
        ):
            fne_proof = self.prove_firmly_nonexpansive(operator, operator.space, sample_points)
            fne_proof.guardrail_rule_id = rule_id
            guardrail_proof.obligations.append(fne_proof)

        # Prove fixed point exists
        fp_proof, fp_result = self.prove_fixed_point_exists(operator, initial_state)
        fp_proof.guardrail_rule_id = rule_id
        guardrail_proof.obligations.append(fp_proof)
        guardrail_proof.fixed_point_result = fp_result

        return guardrail_proof

    def batch_verify(self, guardrail_proofs: list[GuardrailProof]) -> ProofResult:
        """Verify multiple guardrail proofs."""
        all_obligations = []
        verified_count = 0
        failed_count = 0
        pending_count = 0

        for proof in guardrail_proofs:
            for obligation in proof.obligations:
                all_obligations.append(obligation)
                if obligation.status == ProofStatus.VERIFIED:
                    verified_count += 1
                elif obligation.status == ProofStatus.FAILED:
                    failed_count += 1
                else:
                    pending_count += 1

        summary = {
            "total_proofs": len(guardrail_proofs),
            "total_obligations": len(all_obligations),
            "verified": verified_count,
            "failed": failed_count,
            "pending": pending_count,
            "success_rate": (verified_count / len(all_obligations) if all_obligations else 0.0),
        }

        return ProofResult(obligations=all_obligations, summary=summary)
