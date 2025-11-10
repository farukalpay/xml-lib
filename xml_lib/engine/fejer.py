"""Fejér-monotone sequence analysis."""

import numpy as np


def check_fejer_monotonicity(
    sequence: list[np.ndarray], reference: np.ndarray
) -> dict[str, bool | float]:
    """Check Fejér monotonicity of sequence.

    A sequence {x_n} is Fejér-monotone with respect to a set C if
    ||x_{n+1} - p|| ≤ ||x_n - p|| for all p ∈ C and n.

    Args:
        sequence: Sequence of vectors
        reference: Reference point (typically fixed point)

    Returns:
        Dictionary with monotonicity check results
    """
    if len(sequence) < 2:
        return {"is_fejer_monotone": True, "max_increase": 0.0}

    distances = [float(np.linalg.norm(x - reference)) for x in sequence]
    increases = [distances[i + 1] - distances[i] for i in range(len(distances) - 1)]

    is_monotone = all(inc <= 0 for inc in increases)
    max_increase = max(increases) if increases else 0.0

    return {
        "is_fejer_monotone": is_monotone,
        "max_increase": max_increase,
        "distances": distances,
        "increases": increases,
    }
