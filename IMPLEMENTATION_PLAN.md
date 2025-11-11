# Production-Grade XML-Lib Implementation Plan

## Executive Summary

Transform xml-lib into a production-grade, typed Python 3.11 library + CLI that operationalizes the canonical XML lifecycle, guardrail subsystem, and mathematical engine.

## Architecture Overview

### Target Package Structure

```
xml_lib/
├── __init__.py              # Package exports
├── lifecycle.py             # DAG traversal and phase validation
├── schema.py                # XSD/RELAX NG derivation and validation
├── cli.py                   # Typer + Rich CLI interface
├── types.py                 # Type definitions and protocols
├── guardrails/
│   ├── __init__.py
│   ├── policy.py           # YAML policy language
│   ├── transpiler.py       # YAML→XSLT transpiler
│   ├── simulator.py        # Finite-state machine simulator
│   └── checksum.py         # Checksum and signoff logic
├── engine/
│   ├── __init__.py
│   ├── operators.py        # Sympy/numpy operators
│   ├── spaces.py           # Hilbert/Banach spaces
│   ├── norms.py            # Norms and projections
│   ├── fixed_points.py     # Fixed-point iteration
│   ├── fejer.py            # Fejér-monotone checks
│   └── proofs.py           # LaTeX/HTML proof generation
├── pptx/
│   ├── __init__.py
│   ├── parser.py           # Parse document/pptx/*.xml
│   ├── builder.py          # Build PPTX via python-pptx
│   └── exporter.py         # Export HTML handouts
├── transforms/
│   ├── __init__.py
│   ├── xslt.py             # XSLT utilities
│   ├── xpath.py            # XPath queries
│   └── normalize.py        # Diff-able normalizations
└── utils/
    ├── __init__.py
    ├── xml_utils.py        # lxml.iterparse streaming
    ├── cache.py            # Schema compilation cache
    └── logging.py          # Structured logging
```

### Retained Modules (Refactor & Enhance)

- `validator.py` → Enhanced in `lifecycle.py` and `schema.py`
- `publisher.py` → Enhanced with new transforms
- `assertions.py` → Keep with enhancements
- `storage.py` → Keep with enhancements
- `telemetry.py` → Keep with structured logging
- `differ.py` → Enhanced in `transforms/`

## Phase 1: Foundation & Infrastructure

### 1.1 Project Configuration (2-3 hours)

**Files to create:**
- `pyproject.toml` - Poetry/uv configuration
- `.python-version` - Python 3.11 specifier
- `ruff.toml` - Ruff configuration
- `mypy.ini` - MyPy strict configuration
- `.pre-commit-config.yaml` - Pre-commit hooks

**Dependencies to add:**
```toml
[tool.poetry.dependencies]
python = "^3.11"
typer = {extras = ["all"], version = "^0.9.0"}
rich = "^13.7.0"
lxml = "^4.9.0"
xmlschema = "^2.5.0"
sympy = "^1.12"
numpy = "^1.26.0"
python-pptx = "^0.6.21"
cryptography = "^41.0.0"
jsonlines = "^4.0.0"
pyyaml = "^6.0"
jinja2 = "^3.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-cov = "^4.1.0"
hypothesis = "^6.92.0"
mypy = "^1.7.0"
ruff = "^0.1.0"
black = "^23.0.0"
pre-commit = "^3.5.0"
mkdocs-material = "^9.5.0"
mkdocstrings = {extras = ["python"], version = "^0.24.0"}
```

### 1.2 Package Restructuring (3-4 hours)

**Tasks:**
1. Move `cli/xml_lib/*` → `xml_lib/`
2. Create new module structure
3. Add `py.typed` marker for type checking
4. Update all imports
5. Add `__all__` exports

### 1.3 Type Infrastructure (2-3 hours)

**Create `xml_lib/types.py`:**
```python
from typing import Protocol, TypedDict, Literal
from pathlib import Path
from dataclasses import dataclass

PhaseType = Literal["begin", "start", "iteration", "end", "continuum"]

@dataclass
class PhaseNode:
    """Node in the lifecycle DAG"""
    phase: PhaseType
    xml_path: Path
    timestamp: str
    dependencies: list[str]
    metadata: dict[str, Any]

class Validator(Protocol):
    """Protocol for validators"""
    def validate(self, doc: Any) -> ValidationResult: ...
```

## Phase 2: Core Modules Implementation

### 2.1 Lifecycle Module (4-5 hours)

**`xml_lib/lifecycle.py`:**
- Load and parse lifecycle XML files
- Build DAG from phase dependencies
- Topological sort validation
- Phase invariant checking
- Cross-reference validation

**Key functions:**
```python
def load_lifecycle(base_path: Path) -> LifecycleDAG: ...
def validate_dag(dag: LifecycleDAG) -> ValidationResult: ...
def check_phase_invariants(dag: LifecycleDAG) -> list[Invariant]: ...
def verify_references(dag: LifecycleDAG) -> list[ReferenceError]: ...
```

### 2.2 Schema Module (3-4 hours)

**`xml_lib/schema.py`:**
- Derive XSD from example XML documents
- Generate RELAX NG schemas
- Validate using xmlschema library
- Cache compiled schemas

**Key functions:**
```python
def derive_xsd(examples: list[Path], output: Path) -> None: ...
def derive_relaxng(examples: list[Path], output: Path) -> None: ...
def validate_with_schema(xml_path: Path, schema_path: Path) -> ValidationResult: ...
```

### 2.3 Guardrails Module (5-6 hours)

**`xml_lib/guardrails/policy.py`:**
- YAML policy language parser
- Policy validation

**`xml_lib/guardrails/transpiler.py`:**
- YAML → XSLT transpilation
- Template generation

**`xml_lib/guardrails/simulator.py`:**
- Finite-state machine implementation
- State transition validation
- Simulation trace generation

**`xml_lib/guardrails/checksum.py`:**
- SHA-256 checksum generation
- Signoff validation
- Multi-party signature verification

### 2.4 Engine Module (6-8 hours)

**`xml_lib/engine/operators.py`:**
```python
from sympy import Symbol, Matrix, simplify
import numpy as np

class Operator:
    """Mathematical operator representation"""
    def __init__(self, symbolic_form: Any, numeric_impl: Callable): ...
    def apply(self, input: np.ndarray) -> np.ndarray: ...
    def compose(self, other: 'Operator') -> 'Operator': ...
```

**`xml_lib/engine/spaces.py`:**
- Hilbert space definitions
- Banach space operations
- Inner products and norms

**`xml_lib/engine/fixed_points.py`:**
- Fixed-point iteration algorithms
- Convergence testing
- Banach fixed-point theorem implementation

**`xml_lib/engine/proofs.py`:**
- Structured proof representation
- LaTeX proof generation
- HTML proof rendering

### 2.5 PPTX Module (3-4 hours)

**`xml_lib/pptx/parser.py`:**
- Parse `document/pptx/*.xml` build plans
- Extract slide structure

**`xml_lib/pptx/builder.py`:**
- Build PPTX using python-pptx
- Apply templates and themes

**`xml_lib/pptx/exporter.py`:**
- Export to HTML handouts
- Generate slide notes

### 2.6 Transforms Module (3-4 hours)

**`xml_lib/transforms/xslt.py`:**
- XSLT transformation utilities
- Template management

**`xml_lib/transforms/normalize.py`:**
- Canonical XML formatting
- Diff-able output generation

## Phase 3: CLI with Typer + Rich

### 3.1 CLI Implementation (4-5 hours)

**New `xml_lib/cli.py`:**
```python
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

app = typer.Typer()
console = Console()

@app.command()
def lifecycle_validate(
    path: Path = typer.Argument(..., help="Path to lifecycle XML"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
) -> None:
    """Validate lifecycle DAG and phase invariants"""
    with Progress() as progress:
        task = progress.add_task("[cyan]Validating lifecycle...", total=100)
        # Implementation
```

**Subcommands to implement:**
- `xml-lib lifecycle validate`
- `xml-lib lifecycle visualize` (GraphViz DAG output)
- `xml-lib guardrails simulate`
- `xml-lib guardrails check`
- `xml-lib engine prove`
- `xml-lib engine verify`
- `xml-lib pptx build`
- `xml-lib pptx export`
- `xml-lib docs gen`
- `xml-lib examples run`
- `xml-lib schema derive`
- `xml-lib schema validate`

### 3.2 Machine-Readable Output (2 hours)

**JSON Summary Format:**
```json
{
  "command": "lifecycle validate",
  "timestamp": "2025-11-10T14:30:00Z",
  "duration_ms": 1234,
  "status": "success",
  "summary": {
    "phases_validated": 5,
    "references_checked": 42,
    "invariants_verified": 8
  },
  "errors": [],
  "warnings": []
}
```

## Phase 4: Testing & Quality

### 4.1 Property-Based Tests (4-5 hours)

**Create `tests/test_properties.py`:**
```python
from hypothesis import given, strategies as st
from xml_lib.lifecycle import load_lifecycle
from xml_lib.schema import validate_with_schema

@given(st.xml_documents())
def test_schema_roundtrip(xml_doc):
    """Schema validation is idempotent"""
    result1 = validate_with_schema(xml_doc)
    result2 = validate_with_schema(xml_doc)
    assert result1 == result2

@given(st.lifecycles())
def test_dag_invariants(lifecycle):
    """DAG always maintains phase ordering"""
    dag = load_lifecycle(lifecycle)
    assert dag.is_topologically_sorted()
```

### 4.2 Integration Tests (3-4 hours)

**Create `tests/test_integration.py`:**
- Test full example_document.xml flow
- Test example_amphibians.xml flow
- Test artifact generation pipeline

### 4.3 Coverage Target (2-3 hours)

- Configure pytest-cov
- Identify coverage gaps
- Add targeted tests to reach ≥90%

## Phase 5: Documentation

### 5.1 MkDocs Setup (3-4 hours)

**Create `mkdocs.yml`:**
```yaml
site_name: XML-Lib
theme:
  name: material
  palette:
    - scheme: default
      primary: indigo
      accent: indigo
  features:
    - navigation.tabs
    - navigation.sections
    - toc.integrate
    - search.suggest

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            show_source: true

nav:
  - Home: index.md
  - Architecture: architecture.md
  - Lifecycle: lifecycle.md
  - Guardrails: guardrails.md
  - Engine: engine.md
  - API Reference:
    - Lifecycle: api/lifecycle.md
    - Schema: api/schema.md
    - Guardrails: api/guardrails.md
    - Engine: api/engine.md
```

### 5.2 Documentation Content (4-5 hours)

**Create docs:**
- `docs/index.md` - Overview and quickstart
- `docs/architecture.md` - System architecture
- `docs/lifecycle.md` - Lifecycle guide
- `docs/guardrails.md` - Guardrails guide
- `docs/engine.md` - Mathematical engine guide
- `docs/api/` - API reference (auto-generated)

### 5.3 CONTRACTS.md (2 hours)

**Document invariants:**
- Phase ordering constraints
- Reference integrity rules
- Checksum requirements
- Timestamp monotonicity
- Mathematical operator properties

## Phase 6: DevOps & Infrastructure

### 6.1 Devcontainer (1-2 hours)

**Create `.devcontainer/devcontainer.json`:**
```json
{
  "name": "XML-Lib Development",
  "image": "mcr.microsoft.com/devcontainers/python:3.11",
  "features": {
    "ghcr.io/devcontainers/features/git:1": {}
  },
  "postCreateCommand": "poetry install",
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "charliermarsh.ruff"
      ]
    }
  }
}
```

### 6.2 GitHub Actions Enhancement (2-3 hours)

**Update `.github/workflows/ci.yml`:**
- Lint with ruff
- Format check with black
- Type check with mypy --strict
- Test with pytest + coverage
- Build docs
- On tags: publish to PyPI
- Attach built docs and sample artifacts as release assets

### 6.3 Pre-commit Hooks (1 hour)

**Configure `.pre-commit-config.yaml`:**
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

## Phase 7: Examples & Artifacts

### 7.1 Example Pipeline (3-4 hours)

**Create `examples/run_examples.py`:**
```python
def run_example_document():
    """Run example_document.xml through full pipeline"""
    # 1. Validate lifecycle
    # 2. Check guardrails
    # 3. Generate proofs
    # 4. Build PPTX
    # 5. Generate docs
    # Output to artifacts/example_document/{phase}/
```

### 7.2 Artifact Generation (2-3 hours)

**Structure:**
```
artifacts/
├── example_document/
│   ├── begin/
│   │   ├── validated.xml
│   │   └── summary.json
│   ├── start/
│   ├── iteration/
│   ├── end/
│   └── continuum/
└── example_amphibians/
    └── ... (same structure)
```

## Phase 8: Polish & Release

### 8.1 README Update (2 hours)

- Add one-minute quickstart
- Add screenshots of rich output
- Update CLI examples
- Add badges

### 8.2 Performance Optimization (2-3 hours)

- Implement lxml.iterparse for large files
- Add schema compilation cache
- Profile and optimize hot paths

### 8.3 Contributions Guide (1-2 hours)

**Create `CONTRIBUTING.md`:**
- PR checklist
- Development workflow
- Testing requirements

### 8.4 Release v0.1.0 (1 hour)

- Tag release
- Generate changelog
- Push to GitHub
- Publish to PyPI (via CI)

## Timeline Estimate

**Total:** ~70-90 hours of development work

**Phases:**
1. Foundation: 7-10 hours
2. Core Modules: 24-31 hours
3. CLI: 6-7 hours
4. Testing: 9-12 hours
5. Documentation: 9-11 hours
6. DevOps: 4-6 hours
7. Examples: 5-7 hours
8. Polish: 6-8 hours

## Success Criteria

- [x] All existing tests pass
- [ ] ≥90% test coverage
- [ ] MyPy strict passes with no errors
- [ ] All CLI commands work with rich output
- [ ] Examples generate artifacts successfully
- [ ] Documentation builds and is complete
- [ ] CI passes all checks
- [ ] v0.1.0 tag created and pushed

## Migration Strategy

1. **Non-breaking changes first**: Add new modules alongside existing ones
2. **Incremental refactoring**: Move existing code module-by-module
3. **Maintain backward compatibility**: Keep existing CLI working during migration
4. **Test at each step**: Run tests after each module migration
5. **Document changes**: Update CONTRACTS.md as invariants are discovered

## Risk Mitigation

1. **Large scope**: Break into small, tested commits
2. **Breaking changes**: Maintain compatibility layer during migration
3. **Performance regressions**: Benchmark critical paths
4. **Type errors**: Add types incrementally, module by module
