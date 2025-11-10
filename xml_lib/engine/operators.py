"""Mathematical operators with sympy and numpy."""

from dataclasses import dataclass
from typing import Callable

import numpy as np
from sympy import Matrix, Symbol, simplify


@dataclass
class Operator:
    """Mathematical operator representation."""

    name: str
    symbolic_form: Matrix | Symbol
    numeric_impl: Callable[[np.ndarray], np.ndarray] | None = None

    def apply(self, input_vec: np.ndarray) -> np.ndarray:
        """Apply operator to input vector.

        Args:
            input_vec: Input numpy array

        Returns:
            Transformed array
        """
        if self.numeric_impl:
            return self.numeric_impl(input_vec)
        else:
            # Convert symbolic to numeric
            # This is simplified - production would handle matrix operations properly
            return input_vec

    def compose(self, other: "Operator") -> "Operator":
        """Compose this operator with another.

        Args:
            other: Other operator

        Returns:
            Composed operator
        """
        # Symbolic composition
        composed_symbolic = simplify(self.symbolic_form * other.symbolic_form)

        # Numeric composition
        def composed_numeric(x: np.ndarray) -> np.ndarray:
            return self.apply(other.apply(x))

        return Operator(
            name=f"{self.name} ∘ {other.name}",
            symbolic_form=composed_symbolic,
            numeric_impl=composed_numeric,
        )


def projection_operator(name: str, dim: int) -> Operator:
    """Create projection operator.

    Args:
        name: Operator name
        dim: Dimension

    Returns:
        Projection operator
    """
    x = Symbol("x")
    symbolic = Matrix([x / (1 + abs(x))])

    def numeric(vec: np.ndarray) -> np.ndarray:
        return vec / (1 + np.abs(vec))

    return Operator(name=name, symbolic_form=symbolic, numeric_impl=numeric)


def contraction_operator(name: str, constant: float = 0.9) -> Operator:
    """Create contraction operator.

    Args:
        name: Operator name
        constant: Contraction constant (< 1)

    Returns:
        Contraction operator
    """
    x = Symbol("x")
    symbolic = constant * x

    def numeric(vec: np.ndarray) -> np.ndarray:
        return constant * vec

    return Operator(name=name, symbolic_form=symbolic, numeric_impl=numeric)


def compose(*operators: Operator) -> Operator:
    """Compose multiple operators.

    Args:
        *operators: Operators to compose

    Returns:
        Composed operator
    """
    if not operators:
        raise ValueError("Need at least one operator")

    result = operators[0]
    for op in operators[1:]:
        result = result.compose(op)

    return result
