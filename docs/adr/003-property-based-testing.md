# ADR 003: Hypothesis for Property-Based Testing

**Status:** Accepted

**Date:** 2025-11-10

## Context

Traditional example-based testing validates specific inputs but may miss edge cases. For a governance platform that must handle arbitrary XML documents, we need to verify that validation rules hold across a wide range of inputs.

### Challenges with Example-Based Testing

1. **Limited Coverage**: Only tests cases developers think of
2. **Edge Cases**: Hard to manually enumerate all boundary conditions
3. **Regression Blind Spots**: New features may break untested scenarios
4. **Maintenance Burden**: Large test suites with duplicated logic

### Requirements

We need a testing approach that:
- Automatically generates diverse test inputs
- Explores edge cases systematically
- Shrinks failing cases to minimal counterexamples
- Verifies properties rather than specific outputs
- Integrates with pytest infrastructure
- Maintains deterministic test suite (reproducible failures)

## Decision

We will adopt **Hypothesis** as our property-based testing framework for all validation rules and core algorithms.

### What is Property-Based Testing?

Instead of testing specific examples:
```python
def test_checksum_length():
    assert len(sha256("hello")) == 64
    assert len(sha256("world")) == 64
```

We test **properties** that should hold for **all** inputs:
```python
@given(st.binary())
def test_checksum_length_property(content):
    assert len(sha256(content)) == 64
```

### Architecture

**Test Organization**:
```
tests/
├── test_property_based.py      # Main property-based tests
├── test_validator.py           # Example-based validator tests
├── test_formal_verification.py # Verification tests
└── test_guardrails.py          # Guardrail tests
```

**Custom Strategies** (`tests/test_property_based.py`):
```python
@st.composite
def xml_element_name(draw):
    """Generate valid XML element names."""
    ...

@st.composite
def lifecycle_document(draw):
    """Generate valid lifecycle documents."""
    ...

@st.composite
def iso_timestamp(draw):
    """Generate valid ISO timestamps."""
    ...
```

### Property Categories

We test these property categories:

#### 1. Invariants (Always True)

```python
@given(st.binary())
def test_content_hash_deterministic(content):
    """Property: Same content always produces same hash."""
    hash1 = sha256(content)
    hash2 = sha256(content)
    assert hash1 == hash2
```

#### 2. Round-trip Properties

```python
@given(xml_document())
def test_parse_serialize_roundtrip(xml_content):
    """Property: Parse → Serialize → Parse should be identity."""
    doc1 = parse(xml_content)
    serialized = serialize(doc1)
    doc2 = parse(serialized)
    assert equivalent(doc1, doc2)
```

#### 3. Oracle Properties

```python
@given(st.lists(st.integers()))
def test_temporal_monotonicity(timestamps):
    """Property: Sorted timestamps maintain order."""
    sorted_ts = sorted(timestamps)
    for i in range(1, len(sorted_ts)):
        assert sorted_ts[i] >= sorted_ts[i-1]
```

#### 4. Consistency Properties

```python
@given(lifecycle_document())
def test_lifecycle_structure(xml_content):
    """Property: All lifecycle docs have required structure."""
    doc = parse(xml_content)
    assert doc.tag == "document"
    assert doc.find("phases") is not None
```

### Integration with pytest

Hypothesis integrates seamlessly:

```bash
# Run all tests (including property-based)
pytest tests/

# Run only property-based tests
pytest tests/test_property_based.py

# Run with more examples (for CI)
pytest tests/ --hypothesis-profile=ci

# Debug a specific failure
pytest tests/ --hypothesis-seed=12345
```

### Configuration

`pytest.ini`:
```ini
[pytest]
hypothesis_profile = default

[hypothesis:default]
max_examples = 50
deadline = None

[hypothesis:ci]
max_examples = 200
deadline = 1000

[hypothesis:debug]
max_examples = 10
verbosity = debug
```

## Alternatives Considered

### QuickCheck (Haskell)

**Pros**: Original property-based testing framework
**Cons**: Requires Haskell, not Python-native
**Verdict**: Wrong language

### ScalaCheck

**Pros**: Mature, good JVM integration
**Cons**: Requires Scala/JVM
**Verdict**: Wrong ecosystem

### fast-check (TypeScript/JavaScript)

**Pros**: Good for web projects
**Cons**: Not useful for Python backend
**Verdict**: Wrong language

### PropCheck (Python)

**Pros**: Simple, lightweight
**Cons**: Less mature, smaller community
**Verdict**: Not production-ready

### Why Hypothesis?

1. **Python Native**: First-class Python support
2. **Mature**: Used by major projects (Django, PyPy, NumPy)
3. **Shrinking**: Automatically minimizes failing examples
4. **Strategies**: Rich library of generators
5. **Composable**: Build complex generators from simple ones
6. **pytest Integration**: Works seamlessly with existing tests
7. **Stateful Testing**: Supports stateful system testing
8. **Active Development**: Regular updates and improvements

## Consequences

### Positive

✅ **Better Coverage**: Finds edge cases developers miss

✅ **Automatic Shrinking**: Failing cases reduced to minimal examples

✅ **Self-Documenting**: Properties serve as executable specifications

✅ **Regression Prevention**: Random exploration catches unexpected interactions

✅ **Confidence**: Mathematical properties verified across wide input space

✅ **Cost-Effective**: One property test replaces dozens of example tests

### Negative

⚠️ **Non-Determinism**: Different runs may find different failures (mitigated with `--hypothesis-seed`)

⚠️ **Slower Execution**: Generates many examples (mitigated with configurable example count)

⚠️ **Learning Curve**: Team needs to think in properties, not examples

⚠️ **Debugging Complexity**: Minimal examples may still be complex

### Mitigation Strategies

1. **Seed Control**: Use `--hypothesis-seed` for reproducibility
2. **Profile Configuration**: Fewer examples in development, more in CI
3. **Team Training**: Include property-based testing in onboarding
4. **Hybrid Approach**: Keep critical example-based tests

## Implementation Examples

### XML Validation Properties

```python
@given(simple_xml_document())
def test_well_formed_xml_parses(xml_content):
    """All well-formed XML should parse successfully."""
    doc = etree.fromstring(xml_content.encode())
    assert doc is not None
```

### Content-Addressed Storage Properties

```python
@given(st.binary())
def test_storage_retrieval(content):
    """Stored content can always be retrieved."""
    checksum = sha256(content)
    store.store(content, checksum)
    retrieved = store.retrieve(checksum)
    assert retrieved == content
```

### Guardrail Properties

```python
@given(lifecycle_document())
def test_temporal_ordering_property(xml_content):
    """Lifecycle phases must be temporally ordered."""
    doc = parse(xml_content)
    timestamps = extract_timestamps(doc)
    assert is_monotonic(timestamps)
```

### Formal Verification Properties

```python
@given(proof_tree())
def test_proof_tree_acyclic(tree):
    """Proof trees must never contain cycles."""
    assert is_dag(tree)
    assert no_cycles(tree)
```

## Best Practices

### 1. Start Simple

```python
# Simple property
@given(st.text())
def test_basic_property(text):
    assert len(text) >= 0
```

### 2. Use Assumptions

```python
@given(st.integers())
def test_with_assumption(n):
    assume(n > 0)  # Filter invalid inputs
    assert sqrt(n * n) == n
```

### 3. Compose Strategies

```python
@st.composite
def complex_document(draw):
    title = draw(st.text(min_size=1))
    elements = draw(st.lists(xml_element()))
    return build_document(title, elements)
```

### 4. Test Invariants First

Focus on properties that must **always** hold before testing specific behaviors.

## Future Enhancements

1. **Stateful Testing**: Test guardrail state machine transitions
2. **Custom Shrinking**: Domain-specific minimization strategies
3. **Database Generation**: Generate test database states
4. **Performance Properties**: Verify algorithmic complexity
5. **Concurrency Testing**: Property-based concurrent scenarios

## References

- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Property-Based Testing with PropEr, Erlang, and Elixir](https://propertesting.com/)
- [QuickCheck: A Lightweight Tool for Random Testing](https://www.cs.tufts.edu/~nr/cs257/archive/john-hughes/quick.pdf)
- [How to Specify It! A Guide to Writing Properties of Pure Functions](https://www.dropbox.com/s/tx2b84kae4bw1p4/paper.pdf)
