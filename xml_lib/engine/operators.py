"""Operator implementations for fixed-point theory."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import numpy.typing as npt

from xml_lib.engine.spaces import ConvexSet, HilbertSpace, MathematicalSpace


@dataclass
class Operator(ABC):
    """Abstract operator T: X → X."""

    space: MathematicalSpace
    name: str = "Operator"

    @abstractmethod
    def apply(self, x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Apply operator: T(x)."""
        pass

    def __call__(self, x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Syntactic sugar: T(x)."""
        return self.apply(x)

    def compose(self, other: "Operator") -> "ComposedOperator":
        """Compose operators: (T ∘ S)(x) = T(S(x))."""
        return ComposedOperator(operators=[self, other], space=self.space)

    def lipschitz_constant(
        self,
        sample_points: list[npt.NDArray[np.float64]],
    ) -> float:
        """Estimate Lipschitz constant L from samples."""
        if len(sample_points) < 2:
            return 0.0

        max_ratio = 0.0
        for i in range(len(sample_points)):
            for j in range(i + 1, len(sample_points)):
                x, y = sample_points[i], sample_points[j]
                tx = self.apply(x)
                ty = self.apply(y)

                d_xy = self.space.distance(x, y)
                d_txy = self.space.distance(tx, ty)

                if d_xy > 1e-10:
                    ratio = d_txy / d_xy
                    max_ratio = max(max_ratio, ratio)

        return max_ratio


@dataclass
class LipschitzOperator(Operator):
    """L-Lipschitz operator: ||T(x) - T(y)|| ≤ L ||x - y||."""

    lipschitz_L: float = 1.0

    def apply(self, x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Apply operator: default identity."""
        return x.copy()

    def is_lipschitz(
        self, x: npt.NDArray[np.float64], y: npt.NDArray[np.float64], tol: float = 1e-9
    ) -> bool:
        """Verify Lipschitz condition."""
        d_txy = self.space.distance(self.apply(x), self.apply(y))
        d_xy = self.space.distance(x, y)
        return d_txy <= self.lipschitz_L * d_xy + tol


@dataclass
class NonexpansiveOperator(LipschitzOperator):
    """Nonexpansive operator: ||T(x) - T(y)|| ≤ ||x - y|| (L=1)."""

    def __post_init__(self) -> None:
        """Set L = 1."""
        self.lipschitz_L = 1.0


@dataclass
class ContractionOperator(LipschitzOperator):
    """Contraction operator: ||T(x) - T(y)|| ≤ q ||x - y||, q ∈ [0,1)."""

    contraction_q: float = 0.9

    def __post_init__(self) -> None:
        """Set L = q < 1."""
        if not (0 <= self.contraction_q < 1):
            raise ValueError(f"Contraction constant must be in [0,1): {self.contraction_q}")
        self.lipschitz_L = self.contraction_q

    def apply(self, x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Apply operator: default scaled identity."""
        return self.contraction_q * x

    def is_contraction(
        self, x: npt.NDArray[np.float64], y: npt.NDArray[np.float64], tol: float = 1e-9
    ) -> bool:
        """Verify contraction property."""
        d_txy = self.space.distance(self.apply(x), self.apply(y))
        d_xy = self.space.distance(x, y)
        return d_txy <= self.contraction_q * d_xy + tol


@dataclass
class FirmlyNonexpansiveOperator(NonexpansiveOperator):
    """Firmly nonexpansive: ||T(x)-T(y)||² ≤ <T(x)-T(y), x-y>."""

    def __post_init__(self) -> None:
        """Firmly nonexpansive implies nonexpansive."""
        super().__post_init__()

    def is_firmly_nonexpansive(
        self,
        x: npt.NDArray[np.float64],
        y: npt.NDArray[np.float64],
        tol: float = 1e-9,
    ) -> bool:
        """Verify firmly nonexpansive property (requires Hilbert space)."""
        if not isinstance(self.space, HilbertSpace):
            return False

        tx = self.apply(x)
        ty = self.apply(y)
        diff_t = tx - ty
        diff_x = x - y

        lhs = float(np.dot(diff_t, diff_t))  # ||T(x)-T(y)||²
        rhs = float(np.dot(diff_t, diff_x))  # <T(x)-T(y), x-y>

        return lhs <= rhs + tol


@dataclass
class ProjectionOperator(FirmlyNonexpansiveOperator):
    """Projection onto convex set P_C: firmly nonexpansive."""

    convex_set: ConvexSet | None = None

    def apply(self, x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Project x onto convex set C."""
        # If already in set, return as-is
        if self.convex_set and self.convex_set.contains(x):
            return x.copy()

        # Simple projection: identity for now (override in subclasses)
        return x.copy()


@dataclass
class ResolventOperator(FirmlyNonexpansiveOperator):
    """Resolvent J_A = (I + λA)^{-1} for monotone A."""

    monotone_A: Callable[[npt.NDArray[np.float64]], npt.NDArray[np.float64]] | None = None
    lambda_param: float = 1.0

    def apply(self, x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Compute resolvent (I + λA)^{-1}(x) via fixed-point iteration."""
        if self.monotone_A is None:
            return x.copy()

        # Simple fixed-point iteration: z = x - λA(z)
        z = x.copy()
        for _ in range(10):  # Max 10 iterations
            z_new = x - self.lambda_param * self.monotone_A(z)
            if np.linalg.norm(z_new - z) < 1e-6:
                break
            z = z_new

        return z


@dataclass
class ProximalOperator(FirmlyNonexpansiveOperator):
    """Proximal operator prox_φ = argmin_z [φ(z) + (1/2λ)||z-x||²]."""

    penalty_phi: Callable[[npt.NDArray[np.float64]], float] | None = None
    lambda_param: float = 1.0

    def apply(self, x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Compute proximal operator via gradient descent."""
        if self.penalty_phi is None:
            return x.copy()

        # Simple gradient descent
        z = x.copy()
        step_size = 0.1
        for _ in range(20):
            # Approximate gradient via finite differences
            grad = np.zeros_like(z)
            eps = 1e-6
            for i in range(len(z)):
                z_plus = z.copy()
                z_plus[i] += eps
                grad[i] = (self.penalty_phi(z_plus) - self.penalty_phi(z)) / eps

            # Gradient descent step with proximal term
            z_new = z - step_size * (grad + (z - x) / self.lambda_param)

            if np.linalg.norm(z_new - z) < 1e-6:
                break
            z = z_new

        return z


@dataclass
class ComposedOperator(Operator):
    """Composition of operators: (T₁ ∘ T₂ ∘ ... ∘ Tₙ)(x)."""

    operators: list[Operator] = field(default_factory=list)

    def apply(self, x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Apply operators right-to-left."""
        result = x
        for op in reversed(self.operators):
            result = op.apply(result)
        return result

    def lipschitz_constant_composed(self) -> float:
        """Product of Lipschitz constants."""
        L = 1.0
        for op in self.operators:
            if isinstance(op, LipschitzOperator):
                L *= op.lipschitz_L
        return L


@dataclass
class FunctionOperator(Operator):
    """Operator defined by explicit function."""

    function: Callable[[npt.NDArray[np.float64]], npt.NDArray[np.float64]] = field(
        default=lambda x: x
    )

    def apply(self, x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Apply function."""
        return self.function(x)
