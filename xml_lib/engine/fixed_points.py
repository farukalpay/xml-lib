"""Fixed-point iteration algorithms."""

from dataclasses import dataclass, field
from typing import Callable

import numpy as np


@dataclass
class ConvergenceResult:
    """Result of fixed-point iteration."""

    converged: bool
    fixed_point: np.ndarray | None
    iterations: int
    error: float
    trace: list[np.ndarray] = field(default_factory=list)


class FixedPointIterator:
    """Fixed-point iteration solver."""

    def __init__(
        self,
        operator: Callable[[np.ndarray], np.ndarray],
        tolerance: float = 1e-6,
        max_iterations: int = 1000,
    ):
        """Initialize fixed-point iterator.

        Args:
            operator: Contraction operator T
            tolerance: Convergence tolerance
            max_iterations: Maximum iterations
        """
        self.operator = operator
        self.tolerance = tolerance
        self.max_iterations = max_iterations

    def iterate(self, x0: np.ndarray, record_trace: bool = False) -> ConvergenceResult:
        """Run fixed-point iteration.

        Args:
            x0: Initial point
            record_trace: Record iteration trace

        Returns:
            ConvergenceResult
        """
        x = x0.copy()
        trace = [x.copy()] if record_trace else []

        for i in range(self.max_iterations):
            x_next = self.operator(x)
            error = float(np.linalg.norm(x_next - x))

            if record_trace:
                trace.append(x_next.copy())

            if error < self.tolerance:
                return ConvergenceResult(
                    converged=True,
                    fixed_point=x_next,
                    iterations=i + 1,
                    error=error,
                    trace=trace,
                )

            x = x_next

        return ConvergenceResult(
            converged=False,
            fixed_point=x,
            iterations=self.max_iterations,
            error=float(np.linalg.norm(self.operator(x) - x)),
            trace=trace,
        )


def is_fejer_monotone(sequence: list[np.ndarray], fixed_point: np.ndarray) -> bool:
    """Check if sequence is Fejér-monotone.

    Args:
        sequence: Sequence of iterates
        fixed_point: Fixed point

    Returns:
        True if Fejér-monotone
    """
    if len(sequence) < 2:
        return True

    distances = [float(np.linalg.norm(x - fixed_point)) for x in sequence]

    for i in range(len(distances) - 1):
        if distances[i + 1] > distances[i]:
            return False

    return True
