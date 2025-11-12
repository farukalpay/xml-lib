"""Property-based tests for engine using Hypothesis."""

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra import numpy as npst

from xml_lib.engine.fixed_points import FixedPointIterator
from xml_lib.engine.operators import (
    ContractionOperator,
    FirmlyNonexpansiveOperator,
    FunctionOperator,
    NonexpansiveOperator,
)
from xml_lib.engine.proofs import ProofEngine
from xml_lib.engine.spaces import HilbertSpace, InnerProduct


@st.composite
def vectors(draw, dim=5):
    """Strategy for generating vectors."""
    return draw(
        npst.arrays(
            dtype=np.float64,
            shape=(dim,),
            elements=st.floats(
                min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False
            ),
        )
    )


@st.composite
def contraction_constants(draw):
    """Strategy for generating contraction constants in [0, 1)."""
    return draw(st.floats(min_value=0.1, max_value=0.99))


class TestSpaceProperties:
    """Test mathematical space properties."""

    def test_hilbert_cauchy_schwarz(self):
        """Property: Cauchy-Schwarz inequality holds."""
        space = HilbertSpace(dimension=5, name="TestH")

        @given(x=vectors(5), y=vectors(5))
        @settings(max_examples=100)
        def check_cauchy_schwarz(x, y):
            # |<x,y>| ≤ ||x|| ||y||
            inner_prod = abs(space.inner_product(x, y))
            norm_prod = space.norm(x) * space.norm(y)
            assert inner_prod <= norm_prod + 1e-9

        check_cauchy_schwarz()

    def test_hilbert_norm_from_inner_product(self):
        """Property: ||x||² = <x, x>."""
        space = HilbertSpace(dimension=5, name="TestH")

        @given(x=vectors(5))
        @settings(max_examples=100)
        def check_norm(x):
            norm_sq = space.norm(x) ** 2
            inner = space.inner_product(x, x)
            assert abs(norm_sq - inner) < 1e-9

        check_norm()

    def test_triangle_inequality(self):
        """Property: ||x + y|| ≤ ||x|| + ||y||."""
        space = HilbertSpace(dimension=5, name="TestH")

        @given(x=vectors(5), y=vectors(5))
        @settings(max_examples=100)
        def check_triangle(x, y):
            lhs = space.norm(x + y)
            rhs = space.norm(x) + space.norm(y)
            assert lhs <= rhs + 1e-9

        check_triangle()


class TestOperatorProperties:
    """Test operator properties."""

    def test_contraction_property(self):
        """Property: Contraction operators satisfy ||T(x)-T(y)|| ≤ q||x-y||."""
        space = HilbertSpace(dimension=5, name="TestH")

        @given(q=contraction_constants(), x=vectors(5), y=vectors(5))
        @settings(max_examples=50)
        def check_contraction(q, x, y):
            operator = ContractionOperator(
                space=space,
                name="TestContraction",
                contraction_q=q,
            )
            # Use scaled identity as concrete implementation
            operator.apply = lambda z: q * z

            tx = operator.apply(x)
            ty = operator.apply(y)

            d_txy = space.distance(tx, ty)
            d_xy = space.distance(x, y)

            if d_xy > 1e-10:
                assert d_txy <= q * d_xy + 1e-9

        check_contraction()

    def test_nonexpansive_property(self):
        """Property: Nonexpansive operators satisfy ||T(x)-T(y)|| ≤ ||x-y||."""
        space = HilbertSpace(dimension=5, name="TestH")

        @given(x=vectors(5), y=vectors(5))
        @settings(max_examples=50)
        def check_nonexpansive(x, y):
            operator = NonexpansiveOperator(
                space=space,
                name="TestNonexpansive",
            )
            # Use 0.99 * identity as concrete implementation
            operator.apply = lambda z: 0.99 * z

            tx = operator.apply(x)
            ty = operator.apply(y)

            d_txy = space.distance(tx, ty)
            d_xy = space.distance(x, y)

            assert d_txy <= d_xy + 1e-9

        check_nonexpansive()

    def test_firmly_nonexpansive_property(self):
        """Property: Firmly nonexpansive operators satisfy ||T(x)-T(y)||² ≤ <T(x)-T(y), x-y>."""
        space = HilbertSpace(dimension=5, name="TestH")

        @given(x=vectors(5), y=vectors(5))
        @settings(max_examples=50)
        def check_fne(x, y):
            operator = FirmlyNonexpansiveOperator(
                space=space,
                name="TestFNE",
            )
            # Use average: T(x) = (x + T_0(x)) / 2 with T_0 = 0.8*I
            operator.apply = lambda z: (z + 0.8 * z) / 2

            if space.distance(x, y) < 1e-10:
                return

            tx = operator.apply(x)
            ty = operator.apply(y)

            diff_t = tx - ty
            diff_x = x - y

            lhs = float(np.dot(diff_t, diff_t))
            rhs = float(np.dot(diff_t, diff_x))

            assert lhs <= rhs + 1e-8

        check_fne()


class TestFixedPointProperties:
    """Test fixed-point iteration properties."""

    def test_contraction_converges(self):
        """Property: Contraction operators have unique fixed point."""
        space = HilbertSpace(dimension=5, name="TestH")

        @given(q=contraction_constants(), x0=vectors(5))
        @settings(max_examples=20, deadline=None)
        def check_convergence(q, x0):
            operator = ContractionOperator(
                space=space,
                name="TestContraction",
                contraction_q=q,
            )
            # Scaled identity converges to origin
            operator.apply = lambda z: q * z

            iterator = FixedPointIterator(
                operator=operator,
                max_iterations=500,
                tolerance=1e-5,
            )

            result = iterator.iterate(x0)

            # Should converge
            assert result.is_converged() or result.metrics.final_residual < 1e-4

        check_convergence()

    def test_energy_bounded_for_contractions(self):
        """Property: Energy Σ||x_{k+1}-x_k||² is bounded for contractions."""
        space = HilbertSpace(dimension=5, name="TestH")

        @given(q=contraction_constants(), x0=vectors(5))
        @settings(max_examples=20, deadline=None)
        def check_energy(q, x0):
            operator = ContractionOperator(
                space=space,
                name="TestContraction",
                contraction_q=q,
            )
            operator.apply = lambda z: q * z

            iterator = FixedPointIterator(
                operator=operator,
                max_iterations=500,
                tolerance=1e-5,
            )

            result = iterator.iterate(x0)

            # Energy should be bounded
            assert result.metrics.energy < 1e6

        check_energy()


class TestProofEngineProperties:
    """Test proof engine properties."""

    def test_contraction_proof_sound(self):
        """Property: Contraction proofs are sound."""
        space = HilbertSpace(dimension=5, name="TestH")
        proof_engine = ProofEngine()

        @given(q=contraction_constants())
        @settings(max_examples=10, deadline=None)
        def check_proof_soundness(q):
            operator = ContractionOperator(
                space=space,
                name="TestContraction",
                contraction_q=q,
            )
            operator.apply = lambda z: q * z

            # Generate sample points
            np.random.seed(42)
            samples = [np.random.randn(5) for _ in range(10)]

            # Generate proof
            proof = proof_engine.prove_contraction(operator, samples, q)

            # If proof verifies, operator should satisfy contraction
            if proof.status.value == "verified":
                for i in range(len(samples)):
                    for j in range(i + 1, len(samples)):
                        x, y = samples[i], samples[j]
                        d_xy = space.distance(x, y)
                        if d_xy > 1e-10:
                            d_txy = space.distance(operator.apply(x), operator.apply(y))
                            assert d_txy <= q * d_xy + 0.02  # tolerance

        check_proof_soundness()


class TestAxiomPreservation:
    """Test that axioms are preserved through operations."""

    def test_composition_lipschitz_constant(self):
        """Property: Composition of Lipschitz operators has product of constants."""
        space = HilbertSpace(dimension=5, name="TestH")

        @given(q1=contraction_constants(), q2=contraction_constants())
        @settings(max_examples=20)
        def check_composition(q1, q2):
            op1 = FunctionOperator(
                space=space, name="Op1", function=lambda x: q1 * x
            )
            op2 = FunctionOperator(
                space=space, name="Op2", function=lambda x: q2 * x
            )

            composed = op1.compose(op2)

            # Expected Lipschitz constant: q1 * q2
            expected_L = q1 * q2

            # Test on sample points
            np.random.seed(42)
            samples = [np.random.randn(5) for _ in range(5)]

            observed_L = composed.lipschitz_constant(samples)

            # Should be close to expected
            assert abs(observed_L - expected_L) < 0.1

        check_composition()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
