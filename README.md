# XML-Lib

[![CI](https://github.com/farukalpay/xml-lib/actions/workflows/ci.yml/badge.svg)](https://github.com/farukalpay/xml-lib/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/farukalpay/xml-lib/branch/main/graph/badge.svg)](https://codecov.io/gh/farukalpay/xml-lib)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**XML-Lib** is a comprehensive XML-Lifecycle Validator & Publisher with enterprise-grade validation, publishing, and governance capabilities.

## Features

🚀 **NEW: Interactive Developer Experience** — Modern CLI with interactive shell, autocomplete, watch mode, and enhanced output. [See Interactive Guide →](docs/INTERACTIVE_GUIDE.md)

🔄 **Pipeline Automation** — Declarative XML workflows with chaining, error recovery, and rollback. [See Pipeline Guide →](docs/PIPELINE_GUIDE.md)

🔍 **Relax NG + Schematron Validation** — Validates XML documents against lifecycle schemas with cross-file constraints (IDs, checksums, temporal monotonicity)

📊 **Rule Engine** — Compiles guardrails from XML into executable checks with full provenance tracking (who/when/why)

🔐 **Signed Assertion Ledger** — Cryptographically signed validation results in XML + JSON Lines for CI/CD

💾 **Content-Addressed Storage** — Deterministic UUIDs and SHA-256 content addressing for deduplication

📝 **XSLT 3.0 Publisher** — Renders XML to beautiful HTML documentation with automatic index generation

📑 **OOXML Composer** — Generates PowerPoint presentations from XML with slide masters, tables, and citations

🐘 **PHP Page Generator** — Converts XML to production-ready PHP 8.1+ pages with XXE protection, context-aware escaping, and semantic HTML5

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

# JSON output for CI/CD
xml-lib diff example_document.xml example_amphibians.xml --format json
```

### 6. Lint XML Files (2 minutes) ✨ NEW

```bash
# Lint XML files for formatting and security
xml-lib lint .

# Output as JSON for CI/CD pipelines
xml-lib lint . --format json

# Treat warnings as failures
xml-lib lint . --fail-level warning

# Check for specific issues
xml-lib lint . --no-check-attribute-order  # Skip attribute order checking
```

**What gets checked:**
- ✅ Indentation consistency (configurable, default 2 spaces)
- ✅ Alphabetical attribute ordering
- ✅ XXE vulnerabilities (external entities)
- ✅ Trailing whitespace and line length
- ✅ Missing final newlines

### 7. Pipeline Automation (2 minutes) ✨ NEW

Chain XML operations (validate → transform → output) with error recovery:

```bash
# Run a pre-built pipeline template
xml-lib pipeline run templates/pipelines/soap-validation.yaml input.xml

# List available templates
xml-lib pipeline list

# Preview pipeline stages (dry-run)
xml-lib pipeline dry-run templates/pipelines/rss-feed.yaml feed.xml

# Use in CI/CD
xml-lib pipeline run templates/pipelines/ci-validation.yaml *.xml
```

**Available Templates:**
- 📧 **SOAP Validation** - SOAP envelope validation and enrichment
- 📰 **RSS Feed** - RSS 2.0 validation and publishing
- ⚙️ **Config Validation** - Configuration file management
- 🔄 **Schema Migration** - XML schema version migration
- 🔍 **CI/CD Validation** - Comprehensive quality checks

**Create Your Own Pipeline:**

```yaml
# my-pipeline.yaml
name: validate_and_publish
error_strategy: fail_fast
rollback_enabled: true

stages:
  - type: validate
    name: check_xml
    schemas_dir: schemas
    strict: true

  - type: transform
    name: enrich
    transform: transforms/add-metadata.xsl

  - type: output
    name: generate_report
    format: html
    output_path: out/report.html
```

```bash
xml-lib pipeline run my-pipeline.yaml input.xml
```

**Learn More:** [Pipeline Guide](docs/PIPELINE_GUIDE.md) | [Examples](examples/pipelines/)

### 8. Interactive Shell & Watch Mode (3 minutes) ✨ NEW

Experience modern CLI with autocomplete, watch mode, and enhanced output:

```bash
# Launch interactive shell
xml-lib shell

# Inside shell - use Tab for completion
xml-lib> validate data.xml --schema schema.xsd
✅ Validation passed (0.23s)

xml-lib> config set aliases.v "validate --schema schema.xsd"
✅ Set alias: v = validate --schema schema.xsd

xml-lib> v data.xml  # Use alias
✅ Validation passed

xml-lib> exit
```

**Watch Mode** - Auto-execute on file changes:

```bash
# Watch all XML files and validate on save
xml-lib watch "*.xml" --command "validate {file} --schema schema.xsd"

# You'll see:
👀 Watching: *.xml
📝 Command: validate {file} --schema schema.xsd
Press Ctrl+C to stop

# When you edit a file:
[12:34:56] Change detected: data.xml
✅ Command completed (0.15s)
```

**Configuration** - Customize your workflow:

```bash
# Create aliases for common commands
xml-lib config set aliases.v "validate --schema schema.xsd"
xml-lib config set aliases.p "pipeline run"

# Customize output
xml-lib config set output.emoji true
xml-lib config set watch.debounce_seconds 1.0

# View configuration
xml-lib config show
```

**Shell Completions** - Tab completion in your terminal:

```bash
# Install completions for Bash/Zsh
./scripts/install_completions.sh

# Then enjoy Tab completion:
xml-lib val<Tab>              # Completes to: validate
xml-lib validate da<Tab>      # Completes to: data.xml
xml-lib pipeline <Tab>        # Shows: run  list  dry-run
```

**Features:**
- ✨ Interactive REPL with Tab completion
- 📝 Watch mode for auto-validation
- 🎨 Rich terminal output with colors and progress bars
- ⚙️ Persistent configuration and aliases
- 📋 Command history across sessions
- 🚀 Bash/Zsh shell completions

**Learn More:** [Interactive Guide](docs/INTERACTIVE_GUIDE.md) | [Examples](examples/interactive/)

## Programmatic Usage (Python API)

xml-lib provides a clean, well-documented Python API for integrating XML validation, linting, and publishing into your own applications and scripts.

### Quick Start

```python
from xml_lib import quick_validate

# Validate a project with sensible defaults
result = quick_validate("my-xml-project")

if result.is_valid:
    print(f"✓ All {len(result.validated_files)} files are valid!")
else:
    print(f"✗ Found {len(result.errors)} errors:")
    for error in result.errors:
        print(f"  {error.file}:{error.line} - {error.message}")
```

### Common Patterns

**1. Basic Validation**

```python
from xml_lib import validate_xml

result = validate_xml(
    "my-project",
    schemas_dir="schemas",
    guardrails_dir="lib/guardrails",
    enable_streaming=True,  # Efficient for large files
    show_progress=True,     # Show progress indicator
)

print(f"Valid: {result.is_valid}")
print(f"Files: {len(result.validated_files)}")
print(f"Errors: {len(result.errors)}")
```

**2. Batch Processing**

```python
from xml_lib import create_validator
from pathlib import Path

# Create validator once, reuse for multiple projects
validator = create_validator(
    schemas_dir="schemas",
    guardrails_dir="lib/guardrails",
)

# Validate multiple projects efficiently
projects = [Path("project1"), Path("project2"), Path("project3")]
for project in projects:
    result = validator.validate_project(project)
    print(f"{project}: {'✓' if result.is_valid else '✗'}")
```

**3. Linting**

```python
from xml_lib import lint_xml

# Lint for formatting and security issues
result = lint_xml(
    "my-project",
    check_indentation=True,
    check_external_entities=True,  # Check for XXE vulnerabilities
    indent_size=2,
)

print(f"Checked {result.files_checked} files")
print(f"Errors: {result.error_count}, Warnings: {result.warning_count}")

for issue in result.issues:
    print(issue.format_text())
```

**4. Custom Workflows**

```python
from xml_lib import lint_xml, validate_xml

# Stage 1: Lint files
lint_result = lint_xml("project")
if lint_result.has_errors:
    print("✗ Linting failed!")
    exit(1)

# Stage 2: Validate against schemas
validation_result = validate_xml("project", enable_streaming=True)
if not validation_result.is_valid:
    print("✗ Validation failed!")
    exit(1)

# Stage 3: Generate artifacts (only if validation passed)
print("✓ All checks passed - generating artifacts...")
```

### API Reference

The public API includes:

**High-level functions** (recommended for most users):
- `quick_validate()` - Validate with automatic discovery and defaults
- `validate_xml()` - Full control over validation options
- `create_validator()` - Create reusable validator instances
- `lint_xml()` - Lint files for formatting and security
- `publish_html()` - Publish XML to HTML (requires XSLT templates)

**Core classes** (for advanced usage):
- `Validator` - Main validation engine
- `ValidationResult` - Validation results with errors/warnings
- `XMLLinter` - XML linting engine
- `LintResult` - Linting results
- `Publisher` - HTML publishing engine

**For detailed documentation:**

```python
import xml_lib
help(xml_lib)                # Package overview
help(xml_lib.quick_validate) # Function details
help(xml_lib.Validator)      # Class documentation
```

### Examples

See [`examples/programmatic/`](examples/programmatic/) for complete, runnable examples:

1. **[Basic Validation](examples/programmatic/01_basic_validation.py)** - Getting started, error handling, progress indicators
2. **[Batch Processing](examples/programmatic/02_batch_processing.py)** - Validating multiple projects, generating reports
3. **[Custom Workflow](examples/programmatic/03_custom_workflow.py)** - Multi-stage pipeline with conditional logic

Run any example:

```bash
python examples/programmatic/01_basic_validation.py
```

### Installation

```bash
# From PyPI (when published)
pip install xml-lib

# From source
git clone https://github.com/farukalpay/xml-lib.git
cd xml-lib
pip install -e .
```

### Integration Examples

**Pre-commit Hook:**

```python
#!/usr/bin/env python3
from xml_lib import quick_validate
import sys

result = quick_validate(".")
sys.exit(0 if result.is_valid else 1)
```

**pytest Integration:**

```python
def test_xml_files_are_valid():
    from xml_lib import quick_validate
    result = quick_validate(".")
    assert result.is_valid, f"Found {len(result.errors)} errors"
```

**GitHub Actions:**

```yaml
- name: Validate XML
  run: |
    pip install xml-lib
    python -c "from xml_lib import quick_validate; import sys; sys.exit(0 if quick_validate('.').is_valid else 1)"
```

## New Features

### 🚀 Streaming Validation (for Large Files)

Handle large XML files (>10MB) efficiently with streaming validation:

```bash
# Enable streaming validation
xml-lib validate large-project/ --streaming

# Custom threshold (5MB)
xml-lib validate large-project/ --streaming --streaming-threshold 5242880

# With progress indicator
xml-lib validate large-project/ --streaming --progress
```

**Benefits:**
- Memory-efficient processing with iterparse
- Progress tracking for long-running validations
- Graceful fallback when schemas require full tree

### 🔒 Enhanced Security

#### XXE Protection in PHP Generator

The PHP generator now has hardened XXE protection by default:

```bash
# Secure by default - XXE disabled
xml-lib phpify document.xml

# Explicit opt-in for external entities (shows warning)
xml-lib phpify document.xml --allow-xxe  # Only with trusted XML!
```

#### XML Security Linting

Detect security issues in XML files:

```bash
# Scan for XXE vulnerabilities
xml-lib lint . --check-external-entities

# Allow external entities for specific use cases
xml-lib lint . --allow-xxe
```

### 📊 Machine-Readable Output

Get JSON output for CI/CD integration:

```bash
# Validation results as JSON
xml-lib validate . --format json > results.json

# Lint results as JSON
xml-lib lint . --format json > lint.json

# Diff results as JSON
xml-lib diff file1.xml file2.xml --format json > diff.json
```

**Example JSON output:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "files": ["begin.xml", "start.xml"],
  "summary": {
    "error_count": 0,
    "warning_count": 0,
    "file_count": 2
  }
}
```

### 🎯 Flexible Failure Levels

Control when commands should fail:

```bash
# Fail on errors only (default)
xml-lib validate . --fail-level error

# Treat warnings as errors
xml-lib validate . --fail-level warning

# Fail on any issues (lint only)
xml-lib lint . --fail-level info
```

### 🔬 Mathematical Engine & Proof Verification ✨ NEW

Formal verification of guardrail properties using Banach/Hilbert space constructs and fixed-point theory:

```bash
# Validate with engine proof checks
xml-lib validate . --engine-check --engine-dir lib/engine --engine-output out/engine

# Export proofs to JSON for CI/CD
xml-lib engine export --guardrails-dir guardrails --engine-dir lib/engine -o out/engine_export.json
```

**What gets verified:**
- ✅ **Contraction operators**: Proves `‖T(x)−T(y)‖ ≤ q‖x−y‖` with q < 1
- ✅ **Fixed-point convergence**: Verifies unique fixed point exists via Banach theorem
- ✅ **Fejér monotonicity**: Ensures sequence converges to safe set
- ✅ **Energy bounds**: Proves `Σ ‖x_{k+1} - x_k‖² < ∞` (geometric series)
- ✅ **Firmly nonexpansive**: Verifies projection operators satisfy `‖T(x)−T(y)‖² ≤ ⟨T(x)−T(y), x−y⟩`

**Mathematical constructs implemented:**
- **Hilbert spaces** with inner product `⟨·,·⟩` and induced norm
- **Contraction operators** with Lipschitz constant q ∈ [0,1)
- **Projection operators** onto convex feasibility sets
- **Resolvent operators** `J_A = (I + λA)^{-1}` for monotone A
- **Proximal operators** `prox_φ = argmin [φ(z) + ½‖z-x‖²]`
- **Fixed-point iteration** with convergence analysis

**Integration:**
- **Assertion Ledger**: Proof artifacts written to XML + JSONL
- **Telemetry**: Verification metrics sent to telemetry sink
- **Streaming-safe**: Compatible with `--streaming` validation
- **Property tests**: Hypothesis-based invariant verification
- **Microbenchmarks**: Performance tracking for engine operations

**Example output:**
```json
{
  "rule_id": "gr-001",
  "operator_name": "Op_gr-001",
  "fixed_point_converged": true,
  "fixed_point_metrics": {
    "iterations": 42,
    "final_residual": 1.23e-7,
    "energy": 0.456,
    "rate": 0.9,
    "status": "converged"
  },
  "obligations": [
    {
      "obligation_id": "contraction_Op_gr-001",
      "statement": "Operator is contraction with q=0.9",
      "status": "verified"
    }
  ]
}
```

**See:** [ARTIFACTS.md](ARTIFACTS.md#mathematical-engine) for complete schema→engine mapping and examples.

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

### `xml-lib phpify`

Generate production-ready PHP page from XML document.

```bash
xml-lib phpify XML_FILE [OPTIONS]

Options:
  --output, -o PATH       Output PHP file (default: <input-basename>.php)
  --template TYPE         Template to use: default, minimal (default: default)
  --title TEXT            Override document title
  --favicon PATH          Favicon URL or path
  --assets-dir PATH       Assets directory for CSS/images (default: assets)
  --no-toc                Disable table of contents
  --no-css                Disable CSS generation
  --css-path PATH         Custom CSS file path
  --strict                Strict mode (fail on warnings)
  --max-size BYTES        Maximum XML file size in bytes (default: 10MB)
  --schema PATH           Optional Relax NG or Schematron schema for validation
```

**Features:**
- ✅ XXE protection and size/time limits
- ✅ Schema validation (Relax NG/Schematron)
- ✅ Context-aware escaping (HTML, attributes, URLs)
- ✅ Semantic HTML5 with accessibility landmarks
- ✅ Responsive layout with mobile support
- ✅ Automatic table of contents generation
- ✅ PSR-12 compliant PHP code
- ✅ Deterministic output (stable ordering)

**Examples:**

```bash
# Basic usage
xml-lib phpify example_document.xml

# Custom output path
xml-lib phpify example_document.xml -o public/page.php

# Minimal template without TOC
xml-lib phpify example_document.xml --template minimal --no-toc

# With schema validation
xml-lib phpify document.xml --schema schemas/lifecycle.rng --strict

# Custom title and favicon
xml-lib phpify document.xml --title "My Page" --favicon "favicon.ico"
```

**Security Guarantees:**

The `phpify` command implements defense-in-depth security:

1. **XML Parsing Security**
   - XXE (XML External Entity) protection - disabled external entity resolution
   - Size limits - default 10MB, configurable
   - Parse time limits - 30 seconds max
   - No network access during parsing

2. **Output Security**
   - Context-aware escaping:
     - `htmlspecialchars()` for HTML content (ENT_QUOTES | ENT_HTML5)
     - `escape_attr()` for HTML attributes
     - `sanitize_url()` for URLs (blocks javascript:, data:, vbscript:, file:)
   - Template-based generation prevents code injection
   - All user content treated as untrusted

3. **PHP Code Quality**
   - PSR-12 compliant code style
   - Strict typing in helper functions
   - Automatic `php -l` syntax validation
   - No eval() or dynamic code execution

**Generated Files:**

```
out/
├── example_document.php    # Main PHP page with embedded functions
└── assets/
    └── style.css          # Responsive CSS (if not disabled)
```

**Template Options:**

- **default**: Full-featured template with header, footer, TOC, and responsive CSS
- **minimal**: Lightweight template with inline styles, no TOC

**Limitations:**

- Maximum file size: 10MB (configurable with --max-size)
- Parse timeout: 30 seconds
- Generated PHP requires PHP 8.1+ (uses `str_starts_with()`)
- External images are referenced, not embedded

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
