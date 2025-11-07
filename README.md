# XML-Lib

[![CI](https://github.com/farukalpay/xml-lib/actions/workflows/ci.yml/badge.svg)](https://github.com/farukalpay/xml-lib/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/farukalpay/xml-lib/branch/main/graph/badge.svg)](https://codecov.io/gh/farukalpay/xml-lib)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**XML-Lib** is a comprehensive XML-Lifecycle Validator & Publisher with enterprise-grade validation, publishing, and governance capabilities.

## Features

🔍 **Relax NG + Schematron Validation** — Validates XML documents against lifecycle schemas with cross-file constraints (IDs, checksums, temporal monotonicity)

📊 **Rule Engine** — Compiles guardrails from XML into executable checks with full provenance tracking (who/when/why)

🔐 **Signed Assertion Ledger** — Cryptographically signed validation results in XML + JSON Lines for CI/CD

💾 **Content-Addressed Storage** — Deterministic UUIDs and SHA-256 content addressing for deduplication

📝 **XSLT 3.0 Publisher** — Renders XML to beautiful HTML documentation with automatic index generation

📑 **OOXML Composer** — Generates PowerPoint presentations from XML with slide masters, tables, and citations

📈 **Pluggable Telemetry** — Captures metrics to file, SQLite, or PostgreSQL with run duration and pass/fail heatmaps

🔀 **Schema-Aware Diff** — Structural XML diffs with semantic explanations

## Quick Start (15 minutes)

### 1. Install (2 minutes)

```bash
# Clone the repository
git clone https://github.com/farukalpay/xml-lib.git
cd xml-lib

# Install dependencies and xml-lib CLI
make install

# Or manually:
pip install -r requirements.txt
pip install -e .
```

### 2. Validate XML Documents (3 minutes)

```bash
# Validate all XML files in the current project
xml-lib validate .

# With strict mode (warnings as errors)
xml-lib validate . --strict

# Output assertions for CI
xml-lib validate . --output out/assertions.xml --jsonl out/assertions.jsonl
```

**What gets validated:**
- ✅ Lifecycle phase ordering (begin → start → iteration → end → continuum)
- ✅ Temporal monotonicity (timestamps must increase)
- ✅ Cross-file ID uniqueness
- ✅ Checksum format (SHA-256)
- ✅ Reference integrity (all refs point to existing IDs)
- ✅ Custom guardrail rules

### 3. Publish Documentation (5 minutes)

```bash
# Generate HTML documentation
xml-lib publish . --output-dir out/site

# Open in browser
open out/site/index.html  # macOS
xdg-open out/site/index.html  # Linux
```

### 4. Generate PowerPoint (2 minutes)

```bash
# Render XML to PowerPoint
xml-lib render-pptx example_document.xml --output out/presentation.pptx

# With custom template
xml-lib render-pptx example_document.xml --template my-template.pptx --output out/presentation.pptx
```

### 5. Compare Documents (3 minutes)

```bash
# Show structural differences
xml-lib diff example_document.xml example_amphibians.xml

# With semantic explanations
xml-lib diff example_document.xml example_amphibians.xml --explain
```

## Repository Contents

XML-Lib contains a canonical XML lifecycle, guardrail subsystem, and mathematical proof engine:

- **Canonical XML lifecycle** (`lib/*.xml`) — Flows from bootstrapping through governance
- **Guardrail subsystem** (`lib/guardrails`) — Charter, middle-phase engineering, and archival handoffs
- **Mathematical engine** (`lib/engine`) — Proves guardrail properties using Banach/Hilbert machinery
- **PPTX documentation** (`document/pptx`) — Presentation engineering pipelines
- **CLI tooling** (`cli/xml_lib`) — Python-based validation and publishing stack

## Repository Layout

```
├── lib
│   ├── begin.xml … continuum.xml        # Primary XML lifecycle
│   ├── guardrails/                      # Guardrail charter → middle → end
│   └── engine/                          # Axioms, operators, proofs, Hilbert stack
├── document/pptx                        # Presentation engineering docs
├── example_document.xml                 # Straightforward lifecycle demo
└── example_amphibians.xml               # Overly engineered amphibian dossier
```

## XML Lifecycle (`lib/*.xml`)

| Phase | Description |
| --- | --- |
| `lib/begin.xml` | Establishes the initial document intent and commentary. |
| `lib/start.xml` | Adds references, XML-engineering guidelines, and sets up iteration rules. |
| `lib/iteration.xml` | Describes per-cycle steps, telegraphs scheduling, and enforces schema contracts. |
| `lib/end.xml` | Aggregates iteration outputs, validates schema/checksum, and archives the final bundle. |
| `lib/continuum.xml` | Extends the lifecycle with governance, telemetry, simulations, policies, and hand-offs. |

These files are intentionally verbose so you can trace how data should flow through each phase. Downstream artifacts (guardrails, proofs, PPTX docs) reference this chain to stay consistent.

## Guardrail Subsystem (`lib/guardrails`)

The guardrail directory mirrors the lifecycle but focuses on enforcement:

1. `begin.xml` – Sets the guardrail charter, scope boundaries, and invariants.
2. `middle.xml` – Performs the heavy engineering lift: fixed-point modeling, policy transpilers, simulators, telemetry routers, validation matrices, and control loops.
3. `end.xml` – Seals the guardrail assets with checksums, artifacts, and multi-role sign-offs.

Each file references the core lifecycle to ensure every policy/enforcement artifact inherits the same intent.

## Mathematical Engine (`lib/engine`)

The engine formalizes guardrail behavior:

- `spaces.xml`, `hilbert.xml`, `operators.xml` – Define the underlying Banach/Hilbert spaces, norms, projections, resolvents, and contraction operators.
- `axioms.xml`, `proof.xml` – Capture the logical foundations and end-to-end proofs tying guardrails-begin → guardrails-middle → guardrails-end.
- `hilbert/` – Contains a blueprint, layered decompositions, operator addenda, fixed-point proofs, and an index for easy navigation.

Use these files to reason about fixed points, Fejér monotone sequences, and energy bounds when evolving the guardrail workflows.

## Presentation Engineering Docs (`document/pptx`)

This folder documents how to analyze, build, or edit PowerPoint decks using XML-Lib tooling:

- `architecture.xml` – Overview of modules (analysis, html builds, OOXML editing, template remix) and dependencies.
- `workflows.xml` – Step-by-step instructions for each workflow, including required commands and example scripts.
- `checks.xml` – Guardrails to keep HTML authoring, validation, and governance aligned with the rest of the repo.

All guidance is freshly written and respects proprietary constraints; use it as a playbook when working with `.pptx` assets.

## Example Documents

- `example_document.xml` – Walks through each lifecycle phase, showing how to combine templates with custom payloads.
- `example_amphibians.xml` – A richly layered scenario (taxonomy, telemetry, governance) that exercises every artifact including guardrails and continuum governance.

Use these as references when crafting new XML bundles or onboarding teammates.

## CLI Reference

### `xml-lib validate`

Validates XML documents against lifecycle schemas and guardrails.

```bash
xml-lib validate PROJECT_PATH [OPTIONS]

Options:
  --schemas-dir PATH      Directory containing schemas (default: schemas)
  --guardrails-dir PATH   Directory containing guardrails (default: guardrails)
  --output, -o PATH       Output assertions file (default: out/assertions.xml)
  --jsonl PATH            JSON Lines output for CI (default: out/assertions.jsonl)
  --strict                Fail on warnings
  --telemetry TYPE        Telemetry backend: file, sqlite, postgres, none
```

### `xml-lib publish`

Publishes XML documents to HTML using XSLT 3.0.

```bash
xml-lib publish PROJECT_PATH [OPTIONS]

Options:
  --output-dir, -o PATH   Output directory (default: out/site)
  --xslt-dir PATH         XSLT templates directory (default: schemas/xslt)
```

### `xml-lib render-pptx`

Renders XML to PowerPoint presentation.

```bash
xml-lib render-pptx XML_FILE [OPTIONS]

Options:
  --template PATH         PowerPoint template file
  --output, -o PATH       Output .pptx file (required)
```

### `xml-lib diff`

Schema-aware structural diff between two XML files.

```bash
xml-lib diff FILE1 FILE2 [OPTIONS]

Options:
  --explain               Provide detailed semantic explanations
  --schemas-dir PATH      Directory containing schemas
```

## Development

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific tests
pytest tests/test_validator.py -v

# Run property-based tests
pytest tests/test_properties.py -v
```

### Code Quality

```bash
# Lint
make lint

# Format
make format

# Type check
make typecheck

# Run all checks
make ci
```

## Working With XML-Lib

1. **Start with the lifecycle** – Read `lib/begin.xml` through `lib/continuum.xml` to understand the canonical flow.
2. **Study guardrails** – Inspect `lib/guardrails/*` and `guardrails/*.xml` to see how policies are compiled into executable checks.
3. **Validate early** – Run `xml-lib validate .` frequently to catch errors early.
4. **Consult the engine** – When modifying guardrails or adding new enforcement logic, update the proofs in `lib/engine` so the math matches.
5. **Leverage PPTX docs** – For presentation work, follow the instructions in `document/pptx` to analyze, build, or remix decks safely.
6. **Reference examples** – Use `example_document.xml` and `example_amphibians.xml` to validate assumptions or prototype new scenarios.

## Architecture

```
xml-lib/
├── cli/xml_lib/              # Python CLI implementation
│   ├── validator.py          # Relax NG + Schematron validator
│   ├── guardrails.py         # Guardrail rule engine
│   ├── publisher.py          # XSLT 3.0 HTML publisher
│   ├── pptx_composer.py      # OOXML PowerPoint composer
│   ├── differ.py             # Schema-aware differ
│   ├── storage.py            # Content-addressed storage
│   ├── assertions.py         # Signed assertion ledger
│   └── telemetry.py          # Pluggable telemetry sink
├── schemas/                  # Relax NG + Schematron schemas
│   ├── lifecycle.rng         # Lifecycle schema
│   ├── lifecycle.sch         # Lifecycle rules
│   ├── guardrails.rng        # Guardrail schema
│   └── xslt/                 # XSLT templates
├── guardrails/               # Executable guardrail rules
│   └── lifecycle-integrity.xml
├── tests/                    # Comprehensive test suite
│   ├── test_validator.py    # Validation tests
│   ├── test_properties.py   # Property-based tests
│   ├── test_publisher.py    # Publishing tests
│   └── fixtures/            # Test fixtures
└── lib/                      # XML lifecycle examples
```

## Contributing

1. **Code style** – Run `make format` before committing
2. **Testing** – Add tests for new features, maintain >90% coverage
3. **XML validation** – Keep XML ASCII-friendly unless a file already uses Unicode
4. **Guardrails** – When touching guardrails, maintain references and update proofs in `lib/engine`
5. **Documentation** – Update `ARTIFACTS.md` when adding features

Pull requests should:
- Explain how they interact with the lifecycle, guardrails, or validation stack
- Include tests with >90% coverage
- Pass all CI checks (`make ci`)

## License

MIT License - see LICENSE file for details

## Links

- 📚 **Documentation**: See `ARTIFACTS.md` for detailed specifications
- 🐛 **Issues**: [GitHub Issues](https://github.com/farukalpay/xml-lib/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/farukalpay/xml-lib/discussions)
