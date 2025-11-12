"""Mathematical space definitions for the engine."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import numpy.typing as npt


@dataclass
class InnerProduct:
    """Inner product structure for Hilbert spaces."""

    compute: Callable[[npt.NDArray[np.float64], npt.NDArray[np.float64]], float]

    def __call__(self, x: npt.NDArray[np.float64], y: npt.NDArray[np.float64]) -> float:
        """Compute inner product <x, y>."""
        return self.compute(x, y)

    @staticmethod
    def euclidean() -> "InnerProduct":
        """Standard Euclidean inner product."""
        return InnerProduct(compute=lambda x, y: float(np.dot(x, y)))

    def norm(self, x: npt.NDArray[np.float64]) -> float:
        """Induced norm: ||x|| = sqrt(<x, x>)."""
        return np.sqrt(max(0.0, self.compute(x, x)))


@dataclass
class MathematicalSpace(ABC):
    """Abstract base for mathematical spaces."""

    dimension: int
    name: str = "UnnamedSpace"
    properties: dict[str, Any] = field(default_factory=dict)

    @abstractmethod
    def contains(self, point: npt.NDArray[np.float64]) -> bool:
        """Check if point is in the space."""
        pass

    @abstractmethod
    def distance(self, x: npt.NDArray[np.float64], y: npt.NDArray[np.float64]) -> float:
        """Compute distance d(x, y)."""
        pass


@dataclass
class MetricSpace(MathematicalSpace):
    """Metric space (U, d) with distance function."""

    metric: Callable[[npt.NDArray[np.float64], npt.NDArray[np.float64]], float] = field(
        default=lambda x, y: float(np.linalg.norm(x - y))
    )
    is_complete: bool = False

    def contains(self, point: npt.NDArray[np.float64]) -> bool:
        """Check point dimensionality."""
        return point.shape[0] == self.dimension

    def distance(self, x: npt.NDArray[np.float64], y: npt.NDArray[np.float64]) -> float:
        """Compute metric distance."""
        return self.metric(x, y)

    def is_cauchy(self, sequence: list[npt.NDArray[np.float64]], epsilon: float = 1e-6) -> bool:
        """Check if sequence is Cauchy."""
        if len(sequence) < 2:
            return True
        n = len(sequence)
        for i in range(max(0, n - 10), n):
            for j in range(i + 1, n):
                if self.distance(sequence[i], sequence[j]) > epsilon:
                    return False
        return True


@dataclass
class NormedSpace(MetricSpace):
    """Normed space (B, ||·||) with norm-induced metric."""

    norm: Callable[[npt.NDArray[np.float64]], float] = field(
        default=lambda x: float(np.linalg.norm(x))
    )

    def __post_init__(self) -> None:
        """Set metric from norm."""
        self.metric = lambda x, y: self.norm(x - y)

    def ball(
        self, center: npt.NDArray[np.float64], radius: float
    ) -> Callable[[npt.NDArray[np.float64]], bool]:
        """Return characteristic function of open ball."""
        return lambda x: self.norm(x - center) < radius


@dataclass
class BanachSpace(NormedSpace):
    """Banach space: complete normed vector space."""

    def __post_init__(self) -> None:
        """Mark as complete."""
        super().__post_init__()
        self.is_complete = True


@dataclass
class HilbertSpace(BanachSpace):
    """Hilbert space H with inner product <·,·>."""

    inner_product: InnerProduct = field(default_factory=InnerProduct.euclidean)

    def __post_init__(self) -> None:
        """Set norm from inner product."""
        self.norm = lambda x: self.inner_product.norm(x)
        super().__post_init__()

    def orthogonal(
        self, x: npt.NDArray[np.float64], y: npt.NDArray[np.float64], tol: float = 1e-9
    ) -> bool:
        """Check if x ⊥ y."""
        return abs(self.inner_product(x, y)) < tol

    def gram_schmidt(self, vectors: list[npt.NDArray[np.float64]]) -> list[npt.NDArray[np.float64]]:
        """Gram-Schmidt orthonormalization."""
        if not vectors:
            return []

        result: list[npt.NDArray[np.float64]] = []
        for v in vectors:
            # Subtract projections onto existing orthonormal vectors
            u = v.copy()
            for e in result:
                u = u - self.inner_product(v, e) * e

            # Normalize
            norm_u = self.norm(u)
            if norm_u > 1e-10:
                result.append(u / norm_u)

        return result

    def project_onto_subspace(
        self, x: npt.NDArray[np.float64], basis: list[npt.NDArray[np.float64]]
    ) -> npt.NDArray[np.float64]:
        """Project x onto subspace spanned by orthonormal basis."""
        projection = np.zeros_like(x)
        for e in basis:
            projection += self.inner_product(x, e) * e
        return projection

    def cauchy_schwarz_holds(
        self,
        x: npt.NDArray[np.float64],
        y: npt.NDArray[np.float64],
        tol: float = 1e-9,
    ) -> bool:
        """Verify Cauchy-Schwarz: |<x,y>| ≤ ||x|| ||y||."""
        lhs = abs(self.inner_product(x, y))
        rhs = self.norm(x) * self.norm(y)
        return lhs <= rhs + tol


@dataclass
class ConvexSet:
    """Convex set C in a space."""

    space: MathematicalSpace
    characteristic: Callable[[npt.NDArray[np.float64]], bool]
    name: str = "ConvexSet"

    def contains(self, point: npt.NDArray[np.float64]) -> bool:
        """Check if point ∈ C."""
        return self.characteristic(point)

    def is_convex_combination(
        self,
        x: npt.NDArray[np.float64],
        y: npt.NDArray[np.float64],
        lambda_val: float,
        tol: float = 1e-9,
    ) -> bool:
        """Check if λx + (1-λ)y ∈ C for λ ∈ [0,1]."""
        if not (0 <= lambda_val <= 1):
            return False
        z = lambda_val * x + (1 - lambda_val) * y
        return self.contains(z)

    @staticmethod
    def halfspace(
        normal: npt.NDArray[np.float64], offset: float, space: MathematicalSpace
    ) -> "ConvexSet":
        """Halfspace {x : <normal, x> ≤ offset}."""
        return ConvexSet(
            space=space,
            characteristic=lambda x: float(np.dot(normal, x)) <= offset,
            name=f"Halfspace_{offset}",
        )

    @staticmethod
    def intersection(sets: list["ConvexSet"], space: MathematicalSpace) -> "ConvexSet":
        """Intersection of convex sets (convex)."""
        return ConvexSet(
            space=space,
            characteristic=lambda x: all(s.contains(x) for s in sets),
            name="Intersection",
        )
