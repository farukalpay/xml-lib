# ADR 001: Z3 SMT Solver for Formal Verification

**Status:** Accepted

**Date:** 2025-11-10

## Context

The XML-Lib governance platform requires formal verification of guardrail properties to ensure mathematical correctness and completeness. The existing proof engine (`lib/engine/*.xml`) provides informal proofs in XML format with axioms, lemmas, and theorems, but lacks automated verification capabilities.

Manual proof verification is:
- Time-consuming and error-prone
- Difficult to maintain as guardrails evolve
- Not scalable for complex properties
- Lacks counterexample generation for invalid properties

We need a solution that can:
1. Automatically verify formal properties of guardrail rules
2. Generate counterexamples when properties don't hold
3. Integrate with existing XML-based proof definitions
4. Support complex logical formulas (quantifiers, implications, etc.)
5. Provide reasonable performance (< 30 seconds per property)

## Decision

We will integrate the **Z3 SMT (Satisfiability Modulo Theories) Solver** as the formal verification engine for the XML-Lib governance platform.

### Architecture

The implementation consists of:

1. **FormalVerificationEngine** (`cli/xml_lib/formal_verification.py`):
   - Parses XML proof definitions into Z3 formulas
   - Maintains axioms, lemmas, and theorems as ProofNode structures
   - Verifies properties using Z3 solver
   - Generates proof trees for visualization

2. **Property Extraction**:
   - Converts guardrail constraints (XPath, regex, temporal) to Z3 formulas
   - Maintains bidirectional mapping between XML rules and Z3 expressions

3. **Verification Workflow**:
   ```
   XML Guardrails → Extract Properties → Convert to Z3 → Verify → Generate Results
   ```

4. **Proof Status Tracking**:
   - `VERIFIED`: Property holds (negation is UNSAT)
   - `FAILED`: Property doesn't hold (counterexample found)
   - `UNKNOWN`: Solver timeout or limitation
   - `TIMEOUT`: Exceeded time limit

### Why Z3?

Alternative SMT solvers considered:
- **CVC5**: Strong for theory reasoning, but less mature Python bindings
- **Yices**: Fast but limited quantifier support
- **Alt-Ergo**: Good for verification, but smaller community
- **MathSAT**: Commercial licensing restrictions

Z3 was chosen because:
1. **Mature Python bindings** (z3-solver package)
2. **Powerful quantifier reasoning** (FORALL, EXISTS)
3. **Rich theory support** (strings, integers, reals, arrays)
4. **Active development** by Microsoft Research
5. **Proven track record** in formal verification tools
6. **MIT license** (permissive open source)

### Integration Points

The formal verification engine integrates with:
- **Guardrail Engine** (`guardrails.py`): Extracts properties from guardrail rules
- **Mathematical Engine** (`lib/engine/*.xml`): Parses axioms and theorems
- **Proof Visualization** (`proof_visualization.py`): Renders verification results

## Consequences

### Positive

✅ **Automated Verification**: Properties are verified automatically without manual proof checking

✅ **Counterexample Generation**: When properties fail, Z3 provides concrete counterexamples for debugging

✅ **Scalability**: Can verify complex properties with nested quantifiers and multiple theories

✅ **Confidence**: Mathematical guarantees that guardrails enforce intended properties

✅ **Documentation**: Proof trees serve as living documentation of correctness

✅ **Regression Prevention**: Automated tests catch when changes break proven properties

### Negative

⚠️ **Solver Dependency**: Adds ~29MB dependency (z3-solver package)

⚠️ **Performance Variability**: Complex properties may timeout (mitigated with 30s default timeout)

⚠️ **Learning Curve**: Team needs familiarity with SMT concepts and Z3 API

⚠️ **Constraint Translation**: Not all guardrail constraints map perfectly to Z3 formulas (XPath, regex require approximation)

### Mitigation Strategies

1. **Timeout Management**: Configurable timeout (default 30s) with UNKNOWN status for timeouts
2. **Incremental Verification**: Cache verification results to avoid re-checking unchanged properties
3. **Constraint Approximation**: Document limitations of XPath/regex to Z3 translation
4. **Team Training**: Include Z3 examples and documentation in ADRs

## Implementation Notes

### Example Usage

```python
from xml_lib.formal_verification import verify_guardrails
from pathlib import Path

# Verify all guardrails
proof_tree, results = verify_guardrails(
    engine_dir=Path("lib/engine"),
    guardrails_dir=Path("guardrails"),
    timeout_ms=30000
)

# Check results
for result in results:
    if result.status == ProofStatus.VERIFIED:
        print(f"✓ {result.property_name}: VERIFIED")
    elif result.status == ProofStatus.FAILED:
        print(f"✗ {result.property_name}: FAILED")
        print(f"  Counterexample: {result.counterexample}")
```

### Future Extensions

1. **Incremental Solving**: Use Z3's push/pop for faster batch verification
2. **Proof Certificates**: Generate machine-checkable proof certificates
3. **Custom Theories**: Add domain-specific theories for XML validation
4. **Optimization**: Use quantifier instantiation heuristics for better performance

## References

- [Z3 Theorem Prover](https://github.com/Z3Prover/z3)
- [SMT-LIB Standard](http://smtlib.cs.uiowa.edu/)
- [Satisfiability Modulo Theories](https://en.wikipedia.org/wiki/Satisfiability_modulo_theories)
- [Formal Methods in Practice](https://www.microsoft.com/en-us/research/publication/formal-methods-practice/)
