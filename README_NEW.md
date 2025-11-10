# XML-Lib: Production-Grade XML Lifecycle & Mathematical Engine

[![CI](https://github.com/farukalpay/xml-lib/actions/workflows/ci.yml/badge.svg)](https://github.com/farukalpay/xml-lib/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**XML-Lib** is a production-grade, typed Python 3.11+ library and CLI that operationalizes the canonical XML lifecycle, guardrail subsystem, and mathematical engine (Hilbert/Banach spaces, fixed-point theory, and formal proofs).

## ✨ Features

🔄 **Lifecycle DAG Management** — Load, validate, and traverse XML lifecycle phases (begin → start → iteration → end → continuum) with topological checking and phase invariants

📊 **Schema Derivation** — Automatically derive XSD/RELAX NG schemas from example XML documents and validate with caching

🛡️ **Guardrails Subsystem** — YAML policy language → XSLT transpiler, finite-state simulators, cryptographic checksums, and multi-party signoff logic

🧮 **Mathematical Engine** — Sympy/numpy operators, Hilbert/Banach spaces, fixed-point iteration, Fejér-monotone checks, and LaTeX/HTML proof generation

📑 **PPTX Integration** — Parse build plans from `document/pptx/*.xml`, build presentations via python-pptx, export HTML handouts

🔀 **XSLT + XPath Transforms** — Round-tripping, diff-able normalizations, and transformation pipelines

⚡ **Performance** — Stream-parse large XML with `lxml.iterparse`, cache schema compilations, deterministic I/O

📏 **Quality Gates** — Machine-readable JSON summaries + pretty Rich tables, structured logs (ISO timestamps, phases, doc IDs)

## 🚀 Quick Start (1 minute)

### Installation

```bash
# Clone the repository
git clone https://github.com/farukalpay/xml-lib.git
cd xml-lib

# Install with Poetry (recommended)
poetry install

# Or with pip
pip install -e .
```

### Basic Usage

```bash
# Validate lifecycle DAG
xml-lib lifecycle validate . --output artifacts/lifecycle-report.json

# Visualize lifecycle as tree
xml-lib lifecycle visualize .

# Simulate guardrail FSM
xml-lib guardrails simulate --steps 5

# Verify mathematical operator
xml-lib engine verify --type contraction

# Build PPTX from XML
xml-lib pptx build document/pptx/workflows.xml -o artifacts/workflows.pptx

# Derive schema from examples
xml-lib schema derive example_document.xml example_amphibians.xml -o schemas/derived.rng

# Run full example pipeline
xml-lib examples run document
```

## 📋 CLI Commands

### Lifecycle

```bash
# Validate lifecycle DAG and phase invariants
xml-lib lifecycle validate PATH [--output FILE]

# Visualize lifecycle as tree
xml-lib lifecycle visualize PATH [--output FILE]
```

**What gets validated:**
- ✅ DAG acyclicity
- ✅ Phase ordering (begin → start → iteration → end → continuum)
- ✅ Timestamp monotonicity
- ✅ Cross-reference integrity
- ✅ ID uniqueness

### Guardrails

```bash
# Simulate finite-state machine
xml-lib guardrails simulate [--steps N] [--output FILE]

# Verify file checksum
xml-lib guardrails check FILE --checksum HASH [--output FILE]
```

### Engine

```bash
# Generate proof from XML specification
xml-lib engine prove XML_FILE [--output FILE] [--format latex|html]

# Verify operator properties (fixed points, Fejér monotonicity)
xml-lib engine verify [--type contraction|projection] [--output FILE]
```

### PPTX

```bash
# Build PowerPoint from XML build plan
xml-lib pptx build XML_FILE --output FILE [--template FILE]

# Export PowerPoint to HTML handout
xml-lib pptx export PPTX_FILE --output FILE
```

### Schema

```bash
# Derive schema from example documents
xml-lib schema derive FILE... --output FILE [--type xsd|relaxng]

# Validate XML against schema
xml-lib schema validate XML_FILE SCHEMA_FILE [--output FILE]
```

### Examples

```bash
# Run example through full pipeline
xml-lib examples run EXAMPLE [--output DIR]
```

## 🏗️ Architecture

```
xml-lib/
├── xml_lib/                      # Main package
│   ├── lifecycle.py              # DAG traversal, phase validation
│   ├── schema.py                 # XSD/RELAX NG derivation & validation
│   ├── cli_new.py                # Typer + Rich CLI
│   ├── types.py                  # Type definitions & protocols
│   ├── guardrails/               # Policy enforcement
│   │   ├── policy.py             # YAML policy language
│   │   ├── transpiler.py         # YAML → XSLT
│   │   ├── simulator.py          # FSM simulator
│   │   └── checksum.py           # Checksum & signoff
│   ├── engine/                   # Mathematical engine
│   │   ├── operators.py          # Sympy/numpy operators
│   │   ├── spaces.py             # Hilbert/Banach spaces
│   │   ├── norms.py              # Norms & inner products
│   │   ├── fixed_points.py       # Fixed-point iteration
│   │   ├── fejer.py              # Fejér-monotone checks
│   │   └── proofs.py             # Proof generation
│   ├── pptx/                     # PPTX subsystem
│   │   ├── parser.py             # Parse build plans
│   │   ├── builder.py            # Build via python-pptx
│   │   └── exporter.py           # Export HTML
│   ├── transforms/               # XML transforms
│   │   ├── xslt.py               # XSLT utilities
│   │   ├── xpath.py              # XPath queries
│   │   └── normalize.py          # Normalization
│   └── utils/                    # Utilities
│       ├── xml_utils.py          # lxml streaming
│       ├── cache.py              # Schema cache
│       └── logging.py            # Structured logging
├── lib/                          # Canonical lifecycle
│   ├── begin.xml → continuum.xml
│   ├── guardrails/               # Enforcement specs
│   └── engine/                   # Mathematical specs
├── schemas/                      # XSD/RELAX NG schemas
├── tests/                        # Comprehensive tests
└── docs/                         # MkDocs documentation
```

## 📖 Documentation

- **[Implementation Plan](IMPLEMENTATION_PLAN.md)** — Detailed development roadmap
- **[System Contracts](CONTRACTS.md)** — Invariants, guarantees, and quality gates
- **[Artifacts Spec](ARTIFACTS.md)** — Detailed artifact specifications

## 🔬 Mathematical Engine

The engine implements:

- **Operators**: Contraction operators, projection operators, composition
- **Spaces**: Hilbert spaces (L²), Banach spaces (Lᵖ)
- **Fixed Points**: Banach fixed-point theorem, convergence testing
- **Fejér Monotonicity**: Sequence analysis, monotonicity checking
- **Proofs**: Structured proof generation (LaTeX/HTML)

### Example: Fixed-Point Iteration

```python
from xml_lib.engine.operators import contraction_operator
from xml_lib.engine.fixed_points import FixedPointIterator
import numpy as np

# Create contraction operator with constant 0.8
op = contraction_operator("T", 0.8)

# Run fixed-point iteration
iterator = FixedPointIterator(op.apply, tolerance=1e-6)
result = iterator.iterate(np.array([1.0, 2.0]))

print(f"Converged: {result.converged}")
print(f"Fixed point: {result.fixed_point}")
print(f"Iterations: {result.iterations}")
```

## 🛡️ Guardrails Subsystem

### YAML Policy Language

```yaml
name: lifecycle-integrity
version: 1.0
rules:
  - id: gr-001
    name: Phase Ordering
    description: Ensure phases follow canonical order
    type: xpath
    constraint: "count(//phase[@name='begin']) = 1"
    priority: critical
    message: "Begin phase must appear exactly once"
```

### Finite-State Machine Simulation

```python
from xml_lib.guardrails.simulator import GuardrailSimulator, State, Transition

sim = GuardrailSimulator()
sim.add_state(State("initial", StateType.INITIAL))
sim.add_state(State("checking", StateType.CHECKING))
sim.add_state(State("passed", StateType.PASSED))

sim.add_transition(Transition("initial", "checking", "True"))
sim.add_transition(Transition("checking", "passed", "valid == True"))

result = sim.simulate([{"valid": True}])
print(f"Success: {result.success}, Trace: {result.trace}")
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=xml_lib --cov-report=html

# Run property tests
pytest -m property

# Run benchmarks
pytest --benchmark-only
```

### Property-Based Tests (Hypothesis)

```python
from hypothesis import given, strategies as st
from xml_lib.schema import validate_with_schema

@given(st.xml_documents())
def test_validation_idempotence(xml_doc):
    """Schema validation is idempotent."""
    result1 = validate_with_schema(xml_doc)
    result2 = validate_with_schema(xml_doc)
    assert result1 == result2
```

## ⚙️ Configuration

### pyproject.toml

```toml
[tool.poetry]
name = "xml-lib"
version = "0.1.0"
python = "^3.11"

[tool.poetry.dependencies]
typer = {extras = ["all"], version = "^0.9.0"}
rich = "^13.7.0"
lxml = "^5.0.0"
xmlschema = "^2.5.0"
sympy = "^1.12"
numpy = "^1.26.0"
# ... (see pyproject.toml for complete list)

[tool.mypy]
strict = true

[tool.ruff]
line-length = 100
select = ["E", "W", "F", "I", "B", "C4", "UP", "ARG", "SIM"]
```

## 🤝 Contributing

See [CONTRACTS.md](CONTRACTS.md) for system invariants and PR checklist.

**PR Checklist:**
- [ ] Touched phase → updated proof → tests → docs
- [ ] All tests pass (`pytest`)
- [ ] Coverage ≥90% (`pytest --cov`)
- [ ] Mypy strict passes (`mypy xml_lib`)
- [ ] Ruff linting passes (`ruff check xml_lib`)
- [ ] Black formatting applied (`black xml_lib`)
- [ ] CONTRACTS.md updated if invariants changed

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Repository**: [github.com/farukalpay/xml-lib](https://github.com/farukalpay/xml-lib)
- **Issues**: [GitHub Issues](https://github.com/farukalpay/xml-lib/issues)
- **Discussions**: [GitHub Discussions](https://github.com/farukalpay/xml-lib/discussions)

---

Built with ❤️ using Python 3.11+, Typer, Rich, lxml, sympy, numpy, and python-pptx.
