"""Norms and inner products."""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np


@dataclass
class Norm:
    """Norm definition."""

    name: str
    func: Callable[[np.ndarray], float]

    def __call__(self, x: np.ndarray) -> float:
        """Compute norm."""
        return self.func(x)


@dataclass
class InnerProduct:
    """Inner product definition."""

    name: str
    func: Callable[[np.ndarray, np.ndarray], float]

    def __call__(self, x: np.ndarray, y: np.ndarray) -> float:
        """Compute inner product."""
        return self.func(x, y)


# Standard norms
L2_NORM = Norm(name="L²", func=lambda x: float(np.linalg.norm(x, ord=2)))
L1_NORM = Norm(name="L¹", func=lambda x: float(np.linalg.norm(x, ord=1)))
LINF_NORM = Norm(name="L∞", func=lambda x: float(np.linalg.norm(x, ord=np.inf)))

# Standard inner product
STANDARD_INNER_PRODUCT = InnerProduct(
    name="⟨·,·⟩",
    func=lambda x, y: float(np.dot(x, y)),
)
