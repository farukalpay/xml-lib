"""Microbenchmarks for engine performance."""

import numpy as np
import pytest

from xml_lib.engine.fixed_points import FixedPointIterator
from xml_lib.engine.operators import ContractionOperator, FunctionOperator
from xml_lib.engine.parser import EngineSpecParser
from xml_lib.engine.proofs import ProofEngine
from xml_lib.engine.spaces import HilbertSpace


@pytest.fixture
def hilbert_space():
    """Create a Hilbert space for benchmarks."""
    return HilbertSpace(dimension=10, name="BenchmarkH")


@pytest.fixture
def sample_points():
    """Generate sample points."""
    np.random.seed(42)
    return [np.random.randn(10) * 0.5 for _ in range(20)]


class TestSpaceBenchmarks:
    """Benchmark space operations."""

    def test_inner_product_performance(self, benchmark, hilbert_space):
        """Benchmark inner product computation."""
        x = np.random.randn(10)
        y = np.random.randn(10)

        def inner_product():
            return hilbert_space.inner_product(x, y)

        result = benchmark(inner_product)
        assert isinstance(result, float)

    def test_norm_computation_performance(self, benchmark, hilbert_space):
        """Benchmark norm computation."""
        x = np.random.randn(10)

        def compute_norm():
            return hilbert_space.norm(x)

        result = benchmark(compute_norm)
        assert result >= 0

    def test_distance_performance(self, benchmark, hilbert_space):
        """Benchmark distance computation."""
        x = np.random.randn(10)
        y = np.random.randn(10)

        def compute_distance():
            return hilbert_space.distance(x, y)

        result = benchmark(compute_distance)
        assert result >= 0

    def test_gram_schmidt_performance(self, benchmark, hilbert_space):
        """Benchmark Gram-Schmidt orthonormalization."""
        vectors = [np.random.randn(10) for _ in range(5)]

        def orthonormalize():
            return hilbert_space.gram_schmidt(vectors)

        result = benchmark(orthonormalize)
        assert len(result) <= len(vectors)


class TestOperatorBenchmarks:
    """Benchmark operator operations."""

    def test_operator_application_performance(self, benchmark, hilbert_space):
        """Benchmark operator application."""
        operator = FunctionOperator(
            space=hilbert_space,
            name="BenchOp",
            function=lambda x: 0.9 * x,
        )
        x = np.random.randn(10)

        def apply_operator():
            return operator.apply(x)

        result = benchmark(apply_operator)
        assert result.shape == x.shape

    def test_contraction_check_performance(self, benchmark, hilbert_space, sample_points):
        """Benchmark contraction property verification."""
        operator = ContractionOperator(
            space=hilbert_space,
            name="BenchContraction",
            contraction_q=0.9,
        )
        operator.apply = lambda x: 0.9 * x

        x, y = sample_points[0], sample_points[1]

        def check_contraction():
            return operator.is_contraction(x, y)

        result = benchmark(check_contraction)
        assert isinstance(result, bool)

    def test_lipschitz_constant_estimation(self, benchmark, hilbert_space, sample_points):
        """Benchmark Lipschitz constant estimation."""
        operator = FunctionOperator(
            space=hilbert_space,
            name="BenchOp",
            function=lambda x: 0.9 * x,
        )

        def estimate_lipschitz():
            return operator.lipschitz_constant(sample_points[:10])

        result = benchmark(estimate_lipschitz)
        assert result >= 0


class TestFixedPointBenchmarks:
    """Benchmark fixed-point iteration."""

    def test_fixed_point_iteration_performance(self, benchmark, hilbert_space):
        """Benchmark fixed-point iteration."""
        operator = ContractionOperator(
            space=hilbert_space,
            name="BenchContraction",
            contraction_q=0.9,
        )
        operator.apply = lambda x: 0.9 * x

        x0 = np.random.randn(10)

        iterator = FixedPointIterator(
            operator=operator,
            max_iterations=100,
            tolerance=1e-6,
        )

        def iterate():
            return iterator.iterate(x0)

        result = benchmark(iterate)
        assert result.fixed_point is not None

    def test_convergence_analysis_performance(self, benchmark, hilbert_space):
        """Benchmark convergence analysis."""
        operator = ContractionOperator(
            space=hilbert_space,
            name="BenchContraction",
            contraction_q=0.9,
        )
        operator.apply = lambda x: 0.9 * x

        x0 = np.random.randn(10)

        iterator = FixedPointIterator(
            operator=operator,
            max_iterations=100,
            tolerance=1e-6,
            store_trajectory=True,
        )

        def iterate_and_analyze():
            result = iterator.iterate(x0)
            return result.metrics

        metrics = benchmark(iterate_and_analyze)
        assert metrics.iterations > 0


class TestProofEngineBenchmarks:
    """Benchmark proof engine."""

    def test_contraction_proof_performance(self, benchmark, hilbert_space, sample_points):
        """Benchmark contraction proof generation."""
        proof_engine = ProofEngine()
        operator = ContractionOperator(
            space=hilbert_space,
            name="BenchContraction",
            contraction_q=0.9,
        )
        operator.apply = lambda x: 0.9 * x

        def generate_proof():
            return proof_engine.prove_contraction(operator, sample_points[:10], 0.9)

        proof = benchmark(generate_proof)
        assert proof.obligation_id is not None

    def test_fixed_point_proof_performance(self, benchmark, hilbert_space):
        """Benchmark fixed-point existence proof."""
        proof_engine = ProofEngine()
        operator = ContractionOperator(
            space=hilbert_space,
            name="BenchContraction",
            contraction_q=0.9,
        )
        operator.apply = lambda x: 0.9 * x

        x0 = np.random.randn(10)

        def generate_proof():
            return proof_engine.prove_fixed_point_exists(operator, x0)

        proof, result = benchmark(generate_proof)
        assert proof.obligation_id is not None

    def test_guardrail_proof_performance(self, benchmark, hilbert_space, sample_points):
        """Benchmark complete guardrail proof generation."""
        proof_engine = ProofEngine()
        operator = ContractionOperator(
            space=hilbert_space,
            name="BenchContraction",
            contraction_q=0.9,
        )
        operator.apply = lambda x: 0.9 * x

        x0 = np.random.randn(10)

        def generate_guardrail_proof():
            return proof_engine.prove_guardrail_compliance(
                rule_id="bench_rule",
                rule_name="Benchmark Rule",
                operator=operator,
                initial_state=x0,
                sample_points=sample_points[:10],
            )

        proof = benchmark(generate_guardrail_proof)
        assert proof.rule_id == "bench_rule"


class TestParserBenchmarks:
    """Benchmark XML parsing."""

    def test_sample_operator_creation(self, benchmark, hilbert_space):
        """Benchmark operator creation."""
        parser = EngineSpecParser(hilbert_space)

        def create_operator():
            return parser.create_sample_operator("contraction", hilbert_space, q=0.9)

        operator = benchmark(create_operator)
        assert operator is not None

    def test_sample_point_generation(self, benchmark, hilbert_space):
        """Benchmark sample point generation."""
        parser = EngineSpecParser(hilbert_space)

        def generate_points():
            return parser.generate_sample_points(hilbert_space, count=20)

        points = benchmark(generate_points)
        assert len(points) == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])
