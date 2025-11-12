"""Fixed-point iteration and convergence analysis."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import numpy as np
import numpy.typing as npt

from xml_lib.engine.operators import Operator
from xml_lib.engine.spaces import ConvexSet, MathematicalSpace


class ConvergenceStatus(Enum):
    """Convergence status."""

    CONVERGED = "converged"
    MAX_ITERATIONS = "max_iterations"
    DIVERGED = "diverged"
    UNKNOWN = "unknown"


@dataclass
class ConvergenceMetrics:
    """Metrics for convergence analysis."""

    iterations: int
    final_residual: float
    residual_history: list[float] = field(default_factory=list)
    energy: float = 0.0  # Σ ||x_{k+1} - x_k||²
    rate: float = 0.0  # Estimated convergence rate
    status: ConvergenceStatus = ConvergenceStatus.UNKNOWN
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Export to dictionary."""
        return {
            "iterations": self.iterations,
            "final_residual": self.final_residual,
            "residual_history": self.residual_history,
            "energy": self.energy,
            "rate": self.rate,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ConvergenceResult:
    """Result of fixed-point iteration."""

    fixed_point: npt.NDArray[np.float64]
    metrics: ConvergenceMetrics
    trajectory: list[npt.NDArray[np.float64]] = field(default_factory=list)

    def is_converged(self) -> bool:
        """Check if converged."""
        return self.metrics.status == ConvergenceStatus.CONVERGED

    def to_dict(self) -> dict:
        """Export to dictionary."""
        return {
            "fixed_point": self.fixed_point.tolist(),
            "metrics": self.metrics.to_dict(),
            "trajectory_length": len(self.trajectory),
        }


@dataclass
class FixedPointIterator:
    """Fixed-point iteration engine."""

    operator: Operator
    max_iterations: int = 1000
    tolerance: float = 1e-6
    store_trajectory: bool = False

    def iterate(
        self,
        x0: npt.NDArray[np.float64],
    ) -> ConvergenceResult:
        """Run fixed-point iteration: x_{k+1} = T(x_k)."""
        x = x0.copy()
        trajectory: list[npt.NDArray[np.float64]] = []
        residual_history: list[float] = []
        energy = 0.0

        if self.store_trajectory:
            trajectory.append(x.copy())

        for k in range(self.max_iterations):
            x_next = self.operator.apply(x)

            # Compute residual ||x_{k+1} - x_k||
            residual = float(np.linalg.norm(x_next - x))
            residual_history.append(residual)

            # Accumulate energy
            energy += residual**2

            if self.store_trajectory:
                trajectory.append(x_next.copy())

            # Check convergence
            if residual < self.tolerance:
                metrics = ConvergenceMetrics(
                    iterations=k + 1,
                    final_residual=residual,
                    residual_history=residual_history,
                    energy=energy,
                    rate=self._estimate_rate(residual_history),
                    status=ConvergenceStatus.CONVERGED,
                )
                return ConvergenceResult(
                    fixed_point=x_next,
                    metrics=metrics,
                    trajectory=trajectory,
                )

            x = x_next

        # Did not converge
        final_residual = residual_history[-1] if residual_history else float("inf")
        metrics = ConvergenceMetrics(
            iterations=self.max_iterations,
            final_residual=final_residual,
            residual_history=residual_history,
            energy=energy,
            rate=self._estimate_rate(residual_history),
            status=ConvergenceStatus.MAX_ITERATIONS,
        )
        return ConvergenceResult(
            fixed_point=x,
            metrics=metrics,
            trajectory=trajectory,
        )

    def _estimate_rate(self, residuals: list[float]) -> float:
        """Estimate convergence rate q from residuals."""
        if len(residuals) < 2:
            return 0.0

        # Estimate q from consecutive residuals: r_{k+1} / r_k ≈ q
        ratios = []
        for i in range(len(residuals) - 1):
            if residuals[i] > 1e-10:
                ratios.append(residuals[i + 1] / residuals[i])

        return float(np.mean(ratios)) if ratios else 0.0

    def banach_fixed_point_theorem(
        self,
        contraction_constant: float,
        x0: npt.NDArray[np.float64],
        x1: npt.NDArray[np.float64],
    ) -> dict:
        """Banach fixed-point theorem: estimate ||x* - x_n||."""
        if contraction_constant >= 1.0:
            return {"error": "Not a contraction"}

        d0 = float(np.linalg.norm(x1 - x0))
        return {
            "theorem": "Banach fixed-point",
            "contraction_q": contraction_constant,
            "initial_distance": d0,
            "error_bound_formula": "q^n / (1 - q) * d(x1, x0)",
            "error_bound_at_10": (contraction_constant**10 / (1 - contraction_constant) * d0),
            "error_bound_at_100": (contraction_constant**100 / (1 - contraction_constant) * d0),
        }


@dataclass
class FejerMonotoneSequence:
    """Fejér-monotone sequence with respect to a set."""

    convex_set: ConvexSet
    space: MathematicalSpace

    def is_fejer_monotone(
        self,
        sequence: list[npt.NDArray[np.float64]],
        tolerance: float = 1e-9,
    ) -> bool:
        """Check if sequence is Fejér-monotone w.r.t. C.

        For all x* ∈ C: ||x_{k+1} - x*|| ≤ ||x_k - x*||
        """
        if len(sequence) < 2:
            return True

        # Sample points in C (simplified: check against center/origin)
        # In practice, should check against multiple points in C
        test_points = [np.zeros(self.space.dimension)]

        for x_star in test_points:
            if not self.convex_set.contains(x_star):
                continue

            for k in range(len(sequence) - 1):
                d_k = self.space.distance(sequence[k], x_star)
                d_kp1 = self.space.distance(sequence[k + 1], x_star)

                if d_kp1 > d_k + tolerance:
                    return False

        return True

    def verify_convergence(
        self,
        sequence: list[npt.NDArray[np.float64]],
    ) -> dict:
        """Verify Fejér-monotone convergence properties."""
        if not sequence:
            return {"valid": False, "reason": "Empty sequence"}

        is_fejer = self.is_fejer_monotone(sequence)

        # Check if sequence is bounded
        norms = [float(np.linalg.norm(x)) for x in sequence]
        max_norm = max(norms)

        # Check if sequence converges
        if len(sequence) >= 2:
            final_distance = self.space.distance(sequence[-1], sequence[-2])
        else:
            final_distance = float("inf")

        return {
            "is_fejer_monotone": is_fejer,
            "sequence_length": len(sequence),
            "max_norm": max_norm,
            "final_step_distance": final_distance,
            "bounded": max_norm < 1e6,
        }


@dataclass
class BoundedEnergyChecker:
    """Check bounded energy: Σ ||x_{k+1} - x_k||² < ∞."""

    def check_bounded_energy(
        self,
        sequence: list[npt.NDArray[np.float64]],
    ) -> dict:
        """Compute total energy and check convergence."""
        if len(sequence) < 2:
            return {"energy": 0.0, "bounded": True}

        energy = 0.0
        step_norms = []

        for k in range(len(sequence) - 1):
            step = float(np.linalg.norm(sequence[k + 1] - sequence[k]))
            energy += step**2
            step_norms.append(step)

        return {
            "energy": energy,
            "bounded": energy < 1e6,
            "steps": len(step_norms),
            "max_step": max(step_norms) if step_norms else 0.0,
            "min_step": min(step_norms) if step_norms else 0.0,
            "step_norms": step_norms[-10:],  # Last 10 steps
        }
