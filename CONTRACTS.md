# XML-Lib System Contracts

This document defines the invariants, contracts, and guarantees maintained by the xml-lib system.

## Table of Contents

1. [Lifecycle Contracts](#lifecycle-contracts)
2. [Guardrail Contracts](#guardrail-contracts)
3. [Engine Contracts](#engine-contracts)
4. [Schema Contracts](#schema-contracts)
5. [PPTX Contracts](#pptx-contracts)
6. [Performance Contracts](#performance-contracts)
7. [Security Contracts](#security-contracts)

---

## Lifecycle Contracts

### Phase Ordering Invariant

**Contract:** The canonical lifecycle must follow strict phase ordering.

```
begin → start → iteration → end → continuum
```

**Guarantees:**
- No cycles in the lifecycle DAG
- Each phase can only reference previous phases
- Topological sort must succeed

**Validation:** `lifecycle.validate_dag()` enforces this invariant

### Timestamp Monotonicity

**Contract:** Timestamps must increase monotonically along the lifecycle.

```
∀ phases p₁, p₂: p₁ →* p₂ ⇒ timestamp(p₁) ≤ timestamp(p₂)
```

**Format:** ISO 8601 UTC timestamps

**Validation:** `lifecycle.check_phase_invariants()` verifies timestamp ordering

### Reference Integrity

**Contract:** All cross-references must point to existing IDs.

**Reference Types:**
- `@ref-begin`: Reference to begin phase
- `@ref-start`: Reference to start phase
- `@ref-iteration`: Reference to iteration phase
- `@ref-end`: Reference to end phase
- `@ref-continuum`: Reference to continuum phase

**Guarantees:**
- No dangling references
- All referenced IDs exist in the lifecycle
- Circular references are detected

**Validation:** `lifecycle.verify_references()` checks all references

### ID Uniqueness

**Contract:** All `@id` attributes must be globally unique across all lifecycle documents.

**Format:** `[a-zA-Z][a-zA-Z0-9_-]*`

**Guarantees:**
- No duplicate IDs
- IDs are stable across runs
- IDs are deterministic

---

## Guardrail Contracts

### Fixed-Point Invariant

**Contract:** Every guardrail must converge to a deterministic control signal.

**Mathematical Form:**
```
∀ guardrail G: ∃ fixed point p: G(p) = p
```

**Guarantees:**
- Finite-state machines are acyclic or have well-defined fixed points
- Policies are deterministic
- No infinite loops in simulation

**Validation:** `guardrails.simulator.simulate()` checks convergence

### Observability Invariant

**Contract:** No guardrail is approved without telemetry hooks.

**Guarantees:**
- Every guardrail emits structured logs
- State transitions are recorded
- Metrics are captured

**Validation:** Enforced at policy creation time

### Checksum Integrity

**Contract:** All signed artifacts must have valid SHA-256 checksums.

**Format:** 64-character hex string

**Guarantees:**
- Checksums are deterministic
- Tampering is detectable
- Content-addressable storage

**Validation:** `guardrails.checksum.validate_checksum()`

### Policy Transpilation

**Contract:** YAML policies must transpile to valid XSLT.

**Guarantees:**
- XSLT is well-formed
- XPath expressions are valid
- Namespaces are preserved

**Validation:** `guardrails.transpiler.transpile_to_xslt()`

---

## Engine Contracts

### Operator Composition

**Contract:** Operator composition is associative.

**Mathematical Form:**
```
(T₁ ∘ T₂) ∘ T₃ = T₁ ∘ (T₂ ∘ T₃)
```

**Guarantees:**
- Composition order doesn't affect result
- Identity operator exists
- Inverse operators are well-defined

**Validation:** Property-based tests verify associativity

### Contraction Property

**Contract:** Contraction operators must have Lipschitz constant < 1.

**Mathematical Form:**
```
‖T(x) - T(y)‖ ≤ q‖x - y‖  where q < 1
```

**Guarantees:**
- Fixed points exist (Banach fixed-point theorem)
- Convergence is guaranteed
- Convergence rate is bounded

**Validation:** `engine.verify_contraction_property()`

### Fejér Monotonicity

**Contract:** Fixed-point iterations must be Fejér-monotone.

**Mathematical Form:**
```
‖x_{n+1} - p*‖ ≤ ‖x_n - p*‖  where p* is the fixed point
```

**Guarantees:**
- Distance to fixed point decreases
- No oscillations
- Convergence is monotonic

**Validation:** `engine.fejer.check_fejer_monotonicity()`

### Proof Soundness

**Contract:** Generated proofs must be logically valid.

**Guarantees:**
- All steps are justified
- References are valid
- Conclusion follows from hypothesis

**Validation:** Human review + automated checks

---

## Schema Contracts

### Schema Derivation Determinism

**Contract:** Schema derivation from examples must be deterministic.

**Guarantees:**
- Same examples → same schema
- Element ordering is preserved
- Attributes are sorted alphabetically

**Validation:** Property-based tests with fixed seeds

### Validation Idempotence

**Contract:** Schema validation is idempotent.

**Mathematical Form:**
```
validate(validate(doc)) = validate(doc)
```

**Guarantees:**
- Validation doesn't modify document
- Results are reproducible
- No side effects

**Validation:** Property tests verify idempotence

### Schema Compatibility

**Contract:** Schemas must be compatible with xmlschema and lxml.

**Guarantees:**
- Valid XSD 1.0 or RELAX NG syntax
- Parseable by standard tools
- No vendor-specific extensions

---

## PPTX Contracts

### Build Plan Validity

**Contract:** Build plans must produce valid .pptx files.

**Guarantees:**
- Output is readable by PowerPoint
- Slides have valid layouts
- No corrupted content

**Validation:** `pptx.builder.build()` returns success/failure

### Template Preservation

**Contract:** Templates must not be modified during build.

**Guarantees:**
- Template file is read-only
- Output is a new file
- Master slides are preserved

### HTML Export Completeness

**Contract:** HTML export must include all slide content.

**Guarantees:**
- No content loss
- Notes are preserved
- Formatting is semantic

---

## Performance Contracts

### Streaming for Large Files

**Contract:** Files > 10MB must use streaming parser.

**Implementation:** `lxml.iterparse` for large XML files

**Guarantees:**
- Memory usage is bounded
- No full document load into RAM
- Elements are cleared after processing

### Schema Compilation Caching

**Contract:** Schemas must be cached after first compilation.

**Guarantees:**
- First use: compile and cache
- Subsequent uses: load from cache
- Cache invalidation on schema change

**Validation:** `utils.cache.SchemaCache` manages lifecycle

### Deterministic I/O

**Contract:** All file I/O must be deterministic.

**Guarantees:**
- Same input → same output
- No timestamps in generated files (except explicit timestamps)
- Stable ordering of elements

---

## Security Contracts

### XXE Protection

**Contract:** All XML parsing must disable external entities.

**Implementation:**
```python
parser = etree.XMLParser(
    resolve_entities=False,
    no_network=True,
)
```

**Guarantees:**
- No external entity resolution
- No network access during parsing
- Protection against XXE attacks

### Input Validation

**Contract:** All user input must be validated before processing.

**Guarantees:**
- File size limits enforced
- Path traversal prevented
- Malicious input rejected

### Checksum Verification

**Contract:** All signed content must be checksum-verified.

**Algorithm:** SHA-256

**Guarantees:**
- Tampering is detected
- Content authenticity
- Non-repudiation

---

## Backward Compatibility

### XML Authority

**Contract:** Existing XML files remain authoritative.

**Guarantees:**
- No semantic changes to XML content
- Only metadata added (IDs, checksums, cross-references)
- Schemas are compatible with existing files

### API Stability

**Contract:** Public API maintains backward compatibility.

**Guarantees:**
- No breaking changes in minor versions
- Deprecation warnings before removal
- Migration guides for major versions

---

## Testing Contracts

### Coverage Requirement

**Contract:** Test coverage must be ≥90%.

**Measured by:** `pytest-cov`

**Guarantees:**
- All public APIs are tested
- Edge cases are covered
- Property tests for invariants

### Property-Based Testing

**Contract:** Critical invariants must have property tests.

**Tools:** Hypothesis

**Properties Tested:**
- Schema validation idempotence
- DAG acyclicity
- Operator associativity
- Checksum determinism

---

## Error Handling Contracts

### Structured Errors

**Contract:** All errors must be structured and actionable.

**Format:**
```json
{
  "error": "ValidationError",
  "message": "Phase ordering violation",
  "file": "lib/begin.xml",
  "line": 42,
  "suggestion": "Ensure begin phase has no dependencies"
}
```

**Guarantees:**
- Errors are machine-readable
- Helpful error messages
- Actionable suggestions

### Graceful Degradation

**Contract:** System must degrade gracefully on errors.

**Guarantees:**
- No data loss
- Partial results when possible
- Clear failure modes

---

## Logging Contracts

### Structured Logging

**Contract:** All logs must be structured JSON.

**Format:**
```json
{
  "timestamp": "2025-11-10T14:30:00Z",
  "level": "INFO",
  "phase": "iteration",
  "doc_id": "doc-001",
  "message": "Phase validated successfully"
}
```

**Guarantees:**
- ISO 8601 timestamps (UTC)
- Phase tracking
- Document ID tracking
- Machine-parseable

### Log Levels

- **DEBUG:** Development diagnostics
- **INFO:** Normal operations
- **WARNING:** Potential issues
- **ERROR:** Recoverable errors
- **CRITICAL:** System failures

---

## Documentation Contracts

### API Documentation

**Contract:** All public APIs must have docstrings.

**Format:** Google-style docstrings

**Guarantees:**
- Parameters documented
- Return types specified
- Examples provided
- Exceptions listed

### User Documentation

**Contract:** All CLI commands must have help text.

**Format:** Rich-formatted help with examples

**Guarantees:**
- Command description
- Argument/option documentation
- Usage examples
- Common pitfalls

---

## Change Management

### PR Checklist

Before merging, ensure:

- [ ] Touched phase → updated proof → tests → docs
- [ ] All tests pass
- [ ] Coverage ≥90%
- [ ] Mypy strict passes
- [ ] Ruff linting passes
- [ ] Black formatting applied
- [ ] CONTRACTS.md updated if invariants changed
- [ ] Breaking changes documented

---

## Version History

- **v0.1.0** (2025-11-10): Initial contract definitions
