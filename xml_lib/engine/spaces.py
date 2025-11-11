"""Hilbert and Banach space definitions."""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np


@dataclass
class HilbertSpace:
    """Hilbert space with inner product."""

    name: str
    dimension: int | None = None
    inner_product: Callable[[np.ndarray, np.ndarray], float] | None = None

    def inner(self, x: np.ndarray, y: np.ndarray) -> float:
        """Compute inner product.

        Args:
            x, y: Vectors

        Returns:
            Inner product value
        """
        if self.inner_product:
            return self.inner_product(x, y)
        else:
            # Default: standard inner product
            return float(np.dot(x, y))

    def norm(self, x: np.ndarray) -> float:
        """Compute norm from inner product.

        Args:
            x: Vector

        Returns:
            Norm value
        """
        return np.sqrt(self.inner(x, x))


@dataclass
class BanachSpace:
    """Banach space with norm."""

    name: str
    dimension: int | None = None
    norm_func: Callable[[np.ndarray], float] | None = None

    def norm(self, x: np.ndarray) -> float:
        """Compute norm.

        Args:
            x: Vector

        Returns:
            Norm value
        """
        if self.norm_func:
            return self.norm_func(x)
        else:
            # Default: L2 norm
            return float(np.linalg.norm(x))


def l2_space(name: str = "L²") -> HilbertSpace:
    """Create L² Hilbert space.

    Args:
        name: Space name

    Returns:
        L² Hilbert space
    """
    return HilbertSpace(
        name=name,
        inner_product=lambda x, y: float(np.dot(x, y)),
    )


def lp_space(p: int, name: str | None = None) -> BanachSpace:
    """Create Lᵖ Banach space.

    Args:
        p: p-norm parameter
        name: Space name

    Returns:
        Lᵖ Banach space
    """
    return BanachSpace(
        name=name or f"L^{p}",
        norm_func=lambda x: float(np.linalg.norm(x, ord=p)),
    )
