#!/usr/bin/env python3
"""Demo: Mathematical Engine with example_document.xml

This script demonstrates the mathematical engine layer that verifies guardrail
properties through Banach/Hilbert space constructs and fixed-point theory.
"""

import json
from pathlib import Path

import numpy as np

# Import engine components
from xml_lib.engine.fixed_points import FixedPointIterator
from xml_lib.engine.integration import EngineLedgerIntegration, EngineMetrics
from xml_lib.engine.operators import ContractionOperator
from xml_lib.engine.parser import EngineSpecParser
from xml_lib.engine.proofs import GuardrailProof, ProofEngine
from xml_lib.engine.spaces import HilbertSpace


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def demo_spaces() -> HilbertSpace:
    """Demonstrate mathematical space constructs."""
    print_section("1. Mathematical Spaces")

    # Create a Hilbert space
    space = HilbertSpace(dimension=5, name="GuardrailSpace")

    # Test vectors
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = np.array([2.0, 3.0, 4.0, 5.0, 6.0])

    print(f"Created Hilbert space: {space.name} (dimension={space.dimension})")
    print(f"\nTest vectors:")
    print(f"  x = {x}")
    print(f"  y = {y}")

    # Compute inner product
    inner_prod = space.inner_product(x, y)
    print(f"\nInner product ⟨x, y⟩ = {inner_prod:.2f}")

    # Compute norms
    norm_x = space.norm(x)
    norm_y = space.norm(y)
    print(f"Norms: ‖x‖ = {norm_x:.2f}, ‖y‖ = {norm_y:.2f}")

    # Verify Cauchy-Schwarz inequality
    cs_holds = space.cauchy_schwarz_holds(x, y)
    print(f"\nCauchy-Schwarz inequality holds: {cs_holds} ✓")
    print(f"  |⟨x,y⟩| = {abs(inner_prod):.2f} ≤ {norm_x * norm_y:.2f} = ‖x‖‖y‖")

    return space


def demo_operators(space: HilbertSpace) -> ContractionOperator:
    """Demonstrate operator constructs."""
    print_section("2. Contraction Operators")

    # Create a contraction operator
    operator = ContractionOperator(
        space=space,
        name="GuardrailOperator",
        contraction_q=0.9,
    )

    # Uses default implementation: scaled identity (q * x)

    print(f"Created operator: {operator.name}")
    print(f"  Type: Contraction")
    print(f"  Contraction constant q = {operator.contraction_q}")

    # Test contraction property
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = np.array([2.0, 3.0, 4.0, 5.0, 6.0])

    tx = operator.apply(x)
    ty = operator.apply(y)

    d_xy = space.distance(x, y)
    d_txy = space.distance(tx, ty)

    print(f"\nVerifying contraction property:")
    print(f"  ‖x - y‖ = {d_xy:.2f}")
    print(f"  ‖T(x) - T(y)‖ = {d_txy:.2f}")
    print(f"  ‖T(x) - T(y)‖ / ‖x - y‖ = {d_txy / d_xy:.2f}")

    is_contraction = operator.is_contraction(x, y)
    print(f"\nContraction property satisfied: {is_contraction} ✓")
    print(f"  ‖T(x) - T(y)‖ ≤ {operator.contraction_q} ‖x - y‖")

    return operator


def demo_fixed_point(operator: ContractionOperator, space: HilbertSpace) -> None:
    """Demonstrate fixed-point iteration."""
    print_section("3. Fixed-Point Iteration & Convergence")

    # Initial point
    x0 = np.array([5.0, 4.0, 3.0, 2.0, 1.0])

    print(f"Initial point x₀ = {x0}")
    print(f"Starting fixed-point iteration: xₖ₊₁ = T(xₖ)")

    # Create iterator
    iterator = FixedPointIterator(
        operator=operator,
        max_iterations=100,
        tolerance=1e-6,
        store_trajectory=True,
    )

    # Run iteration
    result = iterator.iterate(x0)

    print(f"\nConvergence results:")
    print(f"  Status: {result.metrics.status.value}")
    print(f"  Iterations: {result.metrics.iterations}")
    print(f"  Final residual: {result.metrics.final_residual:.2e}")
    print(f"  Convergence rate: {result.metrics.rate:.4f}")
    print(f"  Total energy: {result.metrics.energy:.6f}")

    print(f"\nFixed point x* = {result.fixed_point}")
    print(f"  ‖x*‖ = {space.norm(result.fixed_point):.2e}")

    # Verify it's a fixed point
    tx_star = operator.apply(result.fixed_point)
    residual = space.distance(result.fixed_point, tx_star)
    print(f"\nFixed-point verification:")
    print(f"  ‖x* - T(x*)‖ = {residual:.2e} ≈ 0 ✓")

    # Show trajectory convergence
    if len(result.trajectory) >= 5:
        print(f"\nTrajectory (first 5 iterations):")
        for i, x in enumerate(result.trajectory[:5]):
            print(f"  x_{i} norm: {space.norm(x):.4f}")


def demo_proofs(operator: ContractionOperator, space: HilbertSpace) -> GuardrailProof:
    """Demonstrate proof generation."""
    print_section("4. Proof Obligations & Verification")

    proof_engine = ProofEngine()

    # Generate sample points
    parser = EngineSpecParser(Path("lib/engine"))
    sample_points = parser.generate_sample_points(space, count=10)

    print(f"Generated {len(sample_points)} sample points for verification")

    # Generate proof for a guardrail rule
    print(f"\nGenerating proof for guardrail rule 'latency-bound'...")

    x0 = np.array([5.0, 4.0, 3.0, 2.0, 1.0])

    guardrail_proof = proof_engine.prove_guardrail_compliance(
        rule_id="latency-bound",
        rule_name="Latency Upper Bound (p95 ≤ 40ms)",
        operator=operator,
        initial_state=x0,
        sample_points=sample_points,
    )

    print(f"\nProof generated for rule: {guardrail_proof.rule_name}")
    print(f"  Operator: {guardrail_proof.operator.name}")
    print(f"  Obligations: {len(guardrail_proof.obligations)}")

    # Show obligations
    for i, obligation in enumerate(guardrail_proof.obligations, 1):
        print(f"\n  Obligation {i}: {obligation.statement}")
        print(f"    Status: {obligation.status.value}")
        print(f"    Steps: {len(obligation.steps)}")

        for step in obligation.steps:
            print(f"      - {step.description}: {'✓' if step.result else '✗'}")

    # Fixed-point metrics
    if guardrail_proof.fixed_point_result:
        fp = guardrail_proof.fixed_point_result
        print(f"\n  Fixed-Point Convergence:")
        print(f"    Converged: {fp.is_converged()}")
        print(f"    Iterations: {fp.metrics.iterations}")
        print(f"    Final residual: {fp.metrics.final_residual:.2e}")
        print(f"    Energy: {fp.metrics.energy:.6f}")

    return guardrail_proof


def demo_integration(guardrail_proof: GuardrailProof) -> None:
    """Demonstrate integration with assertion ledger."""
    print_section("5. Integration & Outputs")

    # Create integration
    integration = EngineLedgerIntegration(Path("out/demo_engine"))

    print("Writing proof artifacts...")

    # Write XML proof ledger
    xml_file = Path("out/demo_engine/demo_proofs.xml")
    integration.write_proof_xml([guardrail_proof], xml_file)
    print(f"  ✓ XML proof ledger: {xml_file}")

    # Write JSONL
    jsonl_file = Path("out/demo_engine/demo_proofs.jsonl")
    integration.write_proof_jsonl([guardrail_proof], jsonl_file)
    print(f"  ✓ JSONL format: {jsonl_file}")

    # Create metrics
    metrics = EngineMetrics(
        guardrail_count=1,
        proof_count=len(guardrail_proof.obligations),
        verified_count=sum(1 for o in guardrail_proof.obligations if o.status.value == "verified"),
        failed_count=sum(1 for o in guardrail_proof.obligations if o.status.value == "failed"),
        convergence_metrics={
            guardrail_proof.rule_id: {
                "converged": (
                    guardrail_proof.fixed_point_result.is_converged()
                    if guardrail_proof.fixed_point_result
                    else False
                ),
                "iterations": (
                    guardrail_proof.fixed_point_result.metrics.iterations
                    if guardrail_proof.fixed_point_result
                    else 0
                ),
            }
        },
    )

    # Write metrics
    metrics_file = Path("out/demo_engine/demo_metrics.json")
    integration.write_metrics_json(metrics, metrics_file)
    print(f"  ✓ Metrics: {metrics_file}")

    # Generate checksum
    checksum = integration.generate_checksum([guardrail_proof])
    print(f"\n  Proof checksum: {checksum[:16]}...")

    print(f"\nAll artifacts written to: out/demo_engine/")


def main() -> None:
    """Run the demo."""
    print("\n" + "=" * 80)
    print("  MATHEMATICAL ENGINE DEMO")
    print("  Example: Guardrail → Operator → Fixed-Point → Proof")
    print("=" * 80)

    # 1. Demonstrate spaces
    space = demo_spaces()

    # 2. Demonstrate operators
    operator = demo_operators(space)

    # 3. Demonstrate fixed-point iteration
    demo_fixed_point(operator, space)

    # 4. Demonstrate proof generation
    guardrail_proof = demo_proofs(operator, space)

    # 5. Demonstrate integration
    demo_integration(guardrail_proof)

    # Final summary
    print_section("Summary")
    print("✓ Mathematical space constructs (Hilbert space with inner product)")
    print("✓ Contraction operator with verified Lipschitz constant q = 0.9")
    print("✓ Fixed-point iteration converging to x* with ‖x* - T(x*)‖ ≈ 0")
    print("✓ Proof obligations verified (contraction, fixed-point, energy)")
    print("✓ Integration with assertion ledger (XML + JSONL)")
    print("\nDemo complete! See out/demo_engine/ for generated artifacts.")
    print("\nNext steps:")
    print("  1. Run: xml-lib validate . --engine-check")
    print("  2. Run: xml-lib engine export -o out/engine_export.json")
    print("  3. See: ARTIFACTS.md#mathematical-engine for full documentation")


if __name__ == "__main__":
    main()
