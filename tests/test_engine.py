"""Unit tests for engine module."""

import numpy as np
import pytest

from xml_lib.engine.fixed_points import (
    BoundedEnergyChecker,
    FejerMonotoneSequence,
    FixedPointIterator,
)
from xml_lib.engine.operators import (
    ComposedOperator,
    ContractionOperator,
    FirmlyNonexpansiveOperator,
    FunctionOperator,
    NonexpansiveOperator,
    ProjectionOperator,
)
from xml_lib.engine.proofs import ProofEngine
from xml_lib.engine.spaces import ConvexSet, HilbertSpace, InnerProduct


class TestInnerProduct:
    """Test inner product functionality."""

    def test_euclidean_inner_product(self):
        """Test Euclidean inner product."""
        ip = InnerProduct.euclidean()
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([4.0, 5.0, 6.0])

        result = ip(x, y)
        expected = 1 * 4 + 2 * 5 + 3 * 6  # 32
        assert abs(result - expected) < 1e-9

    def test_induced_norm(self):
        """Test induced norm from inner product."""
        ip = InnerProduct.euclidean()
        x = np.array([3.0, 4.0])

        norm = ip.norm(x)
        expected = 5.0  # sqrt(9 + 16)
        assert abs(norm - expected) < 1e-9


class TestHilbertSpace:
    """Test Hilbert space functionality."""

    def test_cauchy_schwarz(self):
        """Test Cauchy-Schwarz inequality."""
        space = HilbertSpace(dimension=3, name="H")
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([4.0, 5.0, 6.0])

        assert space.cauchy_schwarz_holds(x, y)

    def test_orthogonality(self):
        """Test orthogonality check."""
        space = HilbertSpace(dimension=2, name="H")
        x = np.array([1.0, 0.0])
        y = np.array([0.0, 1.0])

        assert space.orthogonal(x, y)

    def test_gram_schmidt(self):
        """Test Gram-Schmidt orthonormalization."""
        space = HilbertSpace(dimension=3, name="H")
        vectors = [
            np.array([1.0, 1.0, 0.0]),
            np.array([1.0, 0.0, 1.0]),
            np.array([0.0, 1.0, 1.0]),
        ]

        orthonormal = space.gram_schmidt(vectors)

        # Check orthonormality
        for i, e_i in enumerate(orthonormal):
            # Check norm
            assert abs(space.norm(e_i) - 1.0) < 1e-9

            # Check orthogonality with others
            for j, e_j in enumerate(orthonormal):
                if i != j:
                    assert space.orthogonal(e_i, e_j, tol=1e-9)


class TestContractionOperator:
    """Test contraction operator."""

    def test_contraction_property(self):
        """Test contraction property."""
        space = HilbertSpace(dimension=3, name="H")
        operator = ContractionOperator(
            space=space,
            name="TestContraction",
            contraction_q=0.8,
        )
        # Concrete implementation: scaled identity
        operator.apply = lambda x: 0.8 * x

        x = np.array([1.0, 2.0, 3.0])
        y = np.array([4.0, 5.0, 6.0])

        assert operator.is_contraction(x, y)

    def test_contraction_constant_bounds(self):
        """Test that contraction constant must be in [0, 1)."""
        space = HilbertSpace(dimension=3, name="H")

        with pytest.raises(ValueError):
            ContractionOperator(
                space=space,
                name="Invalid",
                contraction_q=1.5,  # Invalid
            )


class TestFixedPointIteration:
    """Test fixed-point iteration."""

    def test_simple_contraction_converges(self):
        """Test that simple contraction converges."""
        space = HilbertSpace(dimension=3, name="H")
        operator = ContractionOperator(
            space=space,
            name="SimpleContraction",
            contraction_q=0.5,
        )
        # Converges to origin
        operator.apply = lambda x: 0.5 * x

        iterator = FixedPointIterator(
            operator=operator,
            max_iterations=100,
            tolerance=1e-6,
        )

        x0 = np.array([1.0, 2.0, 3.0])
        result = iterator.iterate(x0)

        assert result.is_converged()
        assert np.linalg.norm(result.fixed_point) < 0.01

    def test_energy_bounded(self):
        """Test that energy is bounded for contractions."""
        space = HilbertSpace(dimension=3, name="H")
        operator = ContractionOperator(
            space=space,
            name="Contraction",
            contraction_q=0.9,
        )
        operator.apply = lambda x: 0.9 * x

        iterator = FixedPointIterator(
            operator=operator,
            max_iterations=100,
            tolerance=1e-6,
        )

        x0 = np.array([1.0, 2.0, 3.0])
        result = iterator.iterate(x0)

        assert result.metrics.energy < 1e6


class TestProofEngine:
    """Test proof engine."""

    def test_contraction_proof(self):
        """Test contraction proof generation."""
        space = HilbertSpace(dimension=3, name="H")
        operator = ContractionOperator(
            space=space,
            name="TestContraction",
            contraction_q=0.9,
        )
        operator.apply = lambda x: 0.9 * x

        proof_engine = ProofEngine()

        samples = [np.random.randn(3) for _ in range(10)]
        proof = proof_engine.prove_contraction(operator, samples, 0.9)

        assert proof.obligation_id is not None
        assert len(proof.steps) > 0

    def test_fixed_point_proof(self):
        """Test fixed-point existence proof."""
        space = HilbertSpace(dimension=3, name="H")
        operator = ContractionOperator(
            space=space,
            name="TestContraction",
            contraction_q=0.8,
        )
        operator.apply = lambda x: 0.8 * x

        proof_engine = ProofEngine()

        x0 = np.array([1.0, 2.0, 3.0])
        proof, result = proof_engine.prove_fixed_point_exists(operator, x0)

        assert proof.obligation_id is not None
        assert result is not None
        assert result.is_converged()

    def test_guardrail_proof(self):
        """Test complete guardrail proof."""
        space = HilbertSpace(dimension=3, name="H")
        operator = ContractionOperator(
            space=space,
            name="GuardrailOp",
            contraction_q=0.9,
        )
        operator.apply = lambda x: 0.9 * x

        proof_engine = ProofEngine()

        x0 = np.array([1.0, 2.0, 3.0])
        samples = [np.random.randn(3) for _ in range(10)]

        guardrail_proof = proof_engine.prove_guardrail_compliance(
            rule_id="test_rule",
            rule_name="Test Rule",
            operator=operator,
            initial_state=x0,
            sample_points=samples,
        )

        assert guardrail_proof.rule_id == "test_rule"
        assert len(guardrail_proof.obligations) > 0


class TestComposedOperator:
    """Test operator composition."""

    def test_composition(self):
        """Test operator composition."""
        space = HilbertSpace(dimension=3, name="H")

        op1 = FunctionOperator(
            space=space,
            name="Op1",
            function=lambda x: 0.8 * x,
        )

        op2 = FunctionOperator(
            space=space,
            name="Op2",
            function=lambda x: 0.9 * x,
        )

        composed = op1.compose(op2)

        x = np.array([1.0, 2.0, 3.0])
        result = composed.apply(x)

        # op1(op2(x)) = 0.8 * (0.9 * x) = 0.72 * x
        expected = 0.72 * x

        assert np.allclose(result, expected)

    def test_lipschitz_constant_composed(self):
        """Test Lipschitz constant of composition."""
        space = HilbertSpace(dimension=3, name="H")

        op1 = ContractionOperator(
            space=space,
            name="Op1",
            contraction_q=0.8,
        )

        op2 = ContractionOperator(
            space=space,
            name="Op2",
            contraction_q=0.9,
        )

        composed = ComposedOperator(
            operators=[op1, op2],
            space=space,
        )

        # L = L1 * L2 = 0.8 * 0.9 = 0.72
        L = composed.lipschitz_constant_composed()
        assert abs(L - 0.72) < 1e-9


class TestFejerMonotone:
    """Test Fejér-monotone sequences."""

    def test_simple_fejer_sequence(self):
        """Test simple Fejér-monotone sequence."""
        space = HilbertSpace(dimension=3, name="H")

        # Convex set: ball around origin
        convex_set = ConvexSet(
            space=space,
            characteristic=lambda x: np.linalg.norm(x) <= 5.0,
            name="Ball",
        )

        fejer = FejerMonotoneSequence(convex_set=convex_set, space=space)

        # Sequence converging to origin
        sequence = [np.array([1.0, 0.0, 0.0]) * (0.9**k) for k in range(10)]

        # Should be Fejér-monotone w.r.t. origin
        result = fejer.verify_convergence(sequence)

        assert result["is_fejer_monotone"]
        assert result["bounded"]


class TestBoundedEnergy:
    """Test bounded energy checker."""

    def test_bounded_energy(self):
        """Test energy computation."""
        checker = BoundedEnergyChecker()

        # Geometric sequence with decreasing steps
        sequence = [np.array([1.0, 0.0]) * (0.9**k) for k in range(20)]

        result = checker.check_bounded_energy(sequence)

        assert result["bounded"]
        assert result["energy"] < 1e6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
