# ADR 004: Test Coverage Strategy for Phase 1

**Status:** Accepted

**Date:** 2025-11-10

## Context

Phase 1 of the XML governance platform introduces significant new functionality:
- Z3 formal verification engine
- Proof tree visualization
- Property-based testing framework

We need a comprehensive testing strategy that:
1. Achieves 95%+ code coverage
2. Validates correctness of critical paths
3. Prevents regressions as the platform evolves
4. Maintains test suite maintainability
5. Supports continuous integration

### Current State

The project has existing tests:
- `test_validator.py` - Core validation tests
- `test_guardrails.py` - Guardrail engine tests
- `test_publisher.py` - Publishing tests
- `test_properties.py` - Existing property tests
- `test_pptx.py` - PowerPoint generation tests
- `test_phpify.py` - PHP generation tests

### Requirements

- **Coverage Target**: 95%+ line coverage for new modules
- **Test Types**: Unit, integration, property-based, and end-to-end
- **Performance**: Full suite should run in < 2 minutes
- **Maintainability**: Tests should be readable and easy to update
- **CI Integration**: Automated coverage reporting in GitHub Actions

## Decision

We will implement a **comprehensive multi-layered testing strategy** with distinct test categories and coverage requirements.

### Test Pyramid

```
         /\
        /E2E\         End-to-End Tests (5%)
       /------\       - Full workflow tests
      /        \      - Integration scenarios
     /Integration\    Integration Tests (15%)
    /------------\    - Multi-module interactions
   /              \   - File I/O
  /   Unit Tests   \  Unit Tests (50%)
 /------------------\ - Module isolation
/                    \ - Pure functions
--------------------
    Property-Based    Property-Based Tests (30%)
    - Invariants
    - Round-trip
    - Oracle properties
```

### Coverage Targets by Module

| Module | Coverage Target | Rationale |
|--------|----------------|-----------|
| `formal_verification.py` | 95% | Critical for correctness |
| `proof_visualization.py` | 90% | Multiple rendering paths |
| `validator.py` | 95% | Core validation logic |
| `guardrails.py` | 95% | Security-critical |
| `storage.py` | 95% | Data integrity |
| `publisher.py` | 85% | Complex XSLT paths |
| `pptx_composer.py` | 80% | External library integration |

### Test File Organization

```
tests/
├── test_formal_verification.py       # Unit tests for Z3 engine
├── test_proof_visualization.py       # Visualization tests
├── test_property_based.py            # Property-based tests
├── test_guardrails_comprehensive.py  # Extended guardrail tests
├── test_validator.py                 # Core validator tests
├── test_integration.py               # Integration tests
└── fixtures/                         # Test data
    ├── valid_lifecycle.xml
    ├── invalid_amphibians.xml
    └── guardrails/
```

### Test Categories

#### 1. Unit Tests

**Focus**: Individual functions and classes in isolation

**Tools**: pytest, unittest.mock

**Example**:
```python
def test_parse_axiom():
    """Test parsing a single axiom from XML."""
    engine = FormalVerificationEngine(engine_dir)
    assert "A1" in engine.axioms
    assert engine.axioms["A1"].type == "axiom"
```

**Coverage Target**: 95% of critical paths

#### 2. Integration Tests

**Focus**: Multi-module interactions and file I/O

**Tools**: pytest, tempfile, fixtures

**Example**:
```python
def test_end_to_end_verification():
    """Test complete verification workflow."""
    proof_tree, results = verify_guardrails(
        engine_dir, guardrails_dir
    )
    assert len(results) > 0
    visualizer = ProofTreeVisualizer(proof_tree)
    visualizer.render_graphviz(output_path)
    assert output_path.exists()
```

**Coverage Target**: 90% of integration paths

#### 3. Property-Based Tests

**Focus**: Invariants that must hold for all inputs

**Tools**: Hypothesis

**Example**:
```python
@given(st.binary())
def test_hash_determinism(content):
    """Property: Hash is deterministic."""
    assert sha256(content) == sha256(content)
```

**Coverage Target**: 100% of critical invariants

#### 4. End-to-End Tests

**Focus**: Complete workflows from user perspective

**Tools**: pytest, fixtures

**Example**:
```python
def test_complete_workflow():
    """Test full governance workflow."""
    # 1. Validate documents
    validator.validate_project(project_path)

    # 2. Verify guardrails
    proof_tree, results = verify_guardrails(...)

    # 3. Generate visualizations
    visualizer.render_all(...)

    # All steps should succeed
    assert all(r.status == VERIFIED for r in results)
```

**Coverage Target**: 100% of documented workflows

### Coverage Measurement

#### Tools

- **pytest-cov**: Coverage measurement during test execution
- **coverage.py**: Underlying coverage engine
- **Codecov**: Coverage tracking and reporting

#### Configuration

`pytest.ini`:
```ini
[pytest]
addopts =
    --cov=cli/xml_lib
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml
    --cov-fail-under=95
```

#### CI Integration

`.github/workflows/ci.yml`:
```yaml
- name: Run tests with coverage
  run: |
    pytest --cov=cli/xml_lib --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
    fail_ci_if_error: true
```

### Exclusions

Some code paths are intentionally excluded from coverage:

```python
# .coveragerc
[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
```

### Coverage Gaps Strategy

When coverage falls below 95%:

1. **Identify Gaps**: Use coverage report to find uncovered lines
2. **Assess Criticality**: Prioritize critical paths
3. **Add Tests**: Write targeted tests for gaps
4. **Document Exceptions**: Justify any intentional exclusions

## Alternatives Considered

### 100% Coverage Requirement

**Pros**: Maximum confidence
**Cons**: Diminishing returns, maintenance burden
**Verdict**: 95% is more practical

### No Coverage Requirement

**Pros**: Faster development
**Cons**: Regression risks, quality concerns
**Verdict**: Too risky for governance platform

### Mutation Testing (mutmut, cosmic-ray)

**Pros**: Tests quality of tests
**Cons**: Very slow, complex setup
**Verdict**: Future enhancement, not Phase 1

### Fuzz Testing (atheris, pythonfuzz)

**Pros**: Finds crashes and edge cases
**Cons**: Non-deterministic, hard to reproduce
**Verdict**: Complement to property-based testing

## Consequences

### Positive

✅ **High Confidence**: 95%+ coverage provides strong correctness guarantees

✅ **Regression Prevention**: Comprehensive tests catch breaking changes

✅ **Documentation**: Tests serve as executable specifications

✅ **Refactoring Safety**: High coverage enables confident refactoring

✅ **CI/CD Integration**: Automated coverage reporting catches issues early

✅ **Multiple Perspectives**: Unit + integration + property tests cover different angles

### Negative

⚠️ **Development Time**: Writing comprehensive tests takes time

⚠️ **Maintenance Burden**: Tests need updates when code changes

⚠️ **False Confidence**: High coverage doesn't guarantee correctness

⚠️ **Slow Test Suite**: More tests = longer CI runs

### Mitigation Strategies

1. **Parallel Testing**: Run tests in parallel with `pytest-xdist`
2. **Test Selection**: Use `pytest -k` to run subsets during development
3. **Coverage Caching**: Cache coverage results for unchanged files
4. **Fast/Slow Split**: Mark slow tests with `@pytest.mark.slow`

## Implementation Plan

### Phase 1: Foundation (Completed)

✅ Add pytest-cov to requirements
✅ Configure coverage reporting
✅ Create base test structure

### Phase 2: Core Module Tests (Completed)

✅ `test_formal_verification.py` - 95%+ coverage
✅ `test_proof_visualization.py` - 90%+ coverage
✅ `test_property_based.py` - Property tests
✅ `test_guardrails_comprehensive.py` - Extended tests

### Phase 3: Integration & E2E (In Progress)

- [ ] `test_integration.py` - Cross-module tests
- [ ] `test_end_to_end.py` - Complete workflows
- [ ] Performance benchmarks

### Phase 4: CI/CD (Pending)

- [ ] Update GitHub Actions workflow
- [ ] Add Codecov integration
- [ ] Set up coverage badges

## Best Practices

### 1. Test Naming

```python
# Good: Describes what is tested and expected
def test_parse_axiom_returns_verified_status():
    ...

# Bad: Vague
def test_axiom():
    ...
```

### 2. Arrange-Act-Assert

```python
def test_verify_property():
    # Arrange
    engine = FormalVerificationEngine(engine_dir)
    prop = GuardrailProperty(...)

    # Act
    result = engine._verify_property(prop)

    # Assert
    assert result.status == ProofStatus.VERIFIED
```

### 3. DRY with Fixtures

```python
@pytest.fixture
def proof_tree():
    """Reusable proof tree for tests."""
    return create_test_proof_tree()

def test_visualization(proof_tree):
    # Use fixture
    viz = ProofTreeVisualizer(proof_tree)
    ...
```

### 4. Test Isolation

```python
# Good: Uses tempfile for isolation
def test_with_temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test uses isolated directory
        ...

# Bad: Uses global state
def test_modifies_global():
    global state
    state = "modified"  # Affects other tests
```

## Monitoring and Reporting

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=cli/xml_lib --cov-report=html

# Open in browser
open htmlcov/index.html

# Generate terminal report
pytest --cov=cli/xml_lib --cov-report=term-missing
```

### Coverage Trends

Track coverage over time:
- Use Codecov for historical tracking
- Set up coverage badges in README
- Monitor coverage in pull requests

### Quality Metrics

Beyond coverage percentage:
- **Test Speed**: Full suite < 2 minutes
- **Flakiness**: 0% flaky tests
- **Assertion Density**: Avg 2-3 assertions per test
- **Documentation**: All test modules have docstrings

## Future Enhancements

1. **Mutation Testing**: Verify test suite quality
2. **Performance Profiling**: Identify slow tests
3. **Fuzz Testing**: Generate random inputs for stress testing
4. **Visual Regression**: Screenshot comparison for visualizations
5. **Load Testing**: Verify performance under load

## References

- [pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Test Pyramid](https://martinfowler.com/bliki/TestPyramid.html)
- [Property-Based Testing](https://hypothesis.works/articles/what-is-property-based-testing/)
