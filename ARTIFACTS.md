# XML-Lib Artifacts Documentation

This document provides comprehensive specifications for XML-Lib schemas, guardrail operators, CLI contracts, and reproducible benchmarks.

## Table of Contents

1. [Schemas](#schemas)
2. [Example Documents](#example-documents)
3. [Guardrail Operators](#guardrail-operators)
4. [CLI Contracts](#cli-contracts)
5. [Storage & Content Addressing](#storage--content-addressing)
6. [Telemetry](#telemetry)
7. [Benchmarks](#benchmarks)

---

## Schemas

### Relax NG Schemas

#### `schemas/lifecycle.rng`

Defines the structure for XML lifecycle documents following the canonical chain:
**begin → start → iteration → end → continuum**

**Root Elements:**
- `<document>` — Full lifecycle document with phases
- `<begin>` — Initialization phase
- `<start>` — Setup and constraints phase
- `<iteration>` — Cyclic processing phase
- `<end>` — Finalization phase
- `<continuum>` — Governance and continuation phase

**Key Attributes:**
- `@id` — Unique identifier (validated across all files)
- `@timestamp` — ISO 8601 timestamp (validated for monotonicity)
- `@checksum` — SHA-256 hash in hex format (64 characters)
- `@ref-{phase}` — Cross-reference to specific phase by ID

**Example:**

```xml
<document id="doc-001" timestamp="2025-01-15T10:00:00Z" checksum="a1b2...">
  <meta>
    <title>Sample Document</title>
    <description>Demonstrates lifecycle structure</description>
  </meta>
  <phases>
    <phase name="begin" timestamp="2025-01-15T10:00:00Z">
      <use path="lib/begin.xml">Initialize</use>
      <payload>
        <note>Custom content</note>
      </payload>
    </phase>
    <!-- Additional phases... -->
  </phases>
  <summary>
    <status>complete</status>
  </summary>
</document>
```

#### `schemas/guardrails.rng`

Defines the structure for guardrail rules with provenance tracking.

**Root Elements:**
- `<guardrails-begin>` — Guardrail charter
- `<guardrails-middle>` — Engineering implementation
- `<guardrails-end>` — Finalization and sign-off
- `<guardrail>` — Individual rule definition

**Guardrail Structure:**

```xml
<guardrail id="gr-001" priority="critical|high|medium|low">
  <name>Rule Name</name>
  <description>Detailed description</description>
  <provenance>
    <author>Author Name</author>
    <created>2025-01-15T10:00:00Z</created>
    <rationale>Why this rule exists</rationale>
  </provenance>
  <constraint type="xpath|schematron|regex|checksum|temporal|cross-file">
    Expression or constraint definition
  </constraint>
  <message>Error message when constraint fails</message>
</guardrail>
```

### Schematron Rules

#### `schemas/lifecycle.sch`

Implements business logic and cross-file constraints:

**Rule Patterns:**

1. **unique-ids** — Ensures all `@id` attributes are unique across documents
2. **temporal-order** — Validates monotonic timestamp ordering
3. **phase-order** — Enforces canonical phase sequence
4. **reference-integrity** — Verifies all refs point to existing IDs
5. **checksum-format** — Validates SHA-256 format
6. **iteration-cycles** — Ensures cycle numbers are sequential and ≥ 1
7. **minimum-phases** — Requires at least a 'begin' phase
8. **path-references** — Warns about external file references

**Assertion Levels:**
- `error` — Validation failure (blocks processing)
- `warning` — Advisory notice (non-blocking unless --strict)

---

## Example Documents

### `example_research_pitch.xml`

A comprehensive research pitch demonstrating all lifecycle phases with realistic content for an AI-powered research synthesis platform.

**Key Features:**
- Complete lifecycle with all five phases (begin, start, iteration, end, continuum)
- Monotonically increasing ISO-8601 timestamps across phases
- Globally unique IDs with proper cross-references
- SHA-256 checksums for document and end phase
- Realistic guardrail rules embedded in begin phase
- Detailed sprint planning and iteration tracking
- Production-ready governance and monitoring configuration

**Lifecycle Flow:**
1. **begin** (2025-01-15T09:00:00Z) — Project charter with $2.5M funding target, 18-month timeline, embedded guardrail rules for budget, test coverage, and data retention
2. **start** (2025-01-15T10:30:00Z) — Sprint schedule (3 sprints), KPIs (throughput, latency, accuracy), risk register
3. **iteration** (2025-02-14T17:00:00Z) — Three development sprints with deliverables, metrics, and velocity tracking
4. **end** (2025-03-15T16:00:00Z) — MVP delivery summary with QA sign-offs, budget status ($425K spent), next-phase recommendations
5. **continuum** (2025-03-16T09:00:00Z) — Production monitoring (telemetry, alerting), governance (SOC2, data retention), Q2 roadmap, A/B experiments

**Generated Artifacts:**
- `out/research_pitch.pptx` — 8-slide PowerPoint presentation with 11 citations
- `out/diff.txt` — Structural diff vs. example_document.xml with 59 changes
- `out/site/` — HTML documentation site
- `out/assertions.xml` — Cryptographically signed validation results
- `out/assertions.jsonl` — Machine-readable validation output

**Validation:**
```bash
xml-lib validate example_research_pitch.xml --strict
```

**Publishing:**
```bash
xml-lib publish . --output-dir out/site
```

**PowerPoint Rendering:**
```bash
xml-lib render-pptx example_research_pitch.xml --output out/research_pitch.pptx
```

**Diff Analysis:**
```bash
xml-lib diff example_document.xml example_research_pitch.xml --explain > out/diff.txt
```

### `example_document.xml`

A minimal lifecycle document demonstrating basic structure with simple notes in each phase.

### `example_amphibians.xml`

A lifecycle document used for testing edge cases and validation errors.

---

## Guardrail Operators

The guardrail rule engine supports multiple constraint types with full provenance tracking.

### Constraint Types

#### 1. XPath Constraints (`type="xpath"`)

Evaluates XPath expressions against the document. Returns `false` or empty to indicate violation.

**Example:**
```xml
<constraint type="xpath">
  count(//phase[@name='begin']) >= 1
</constraint>
```

**Use Cases:**
- Element existence checks
- Cardinality constraints
- Structural validation
- Value comparisons

#### 2. Regex Constraints (`type="regex"`)

Matches document text content against regular expressions. Supports negation with `!` prefix.

**Example:**
```xml
<constraint type="regex">^[a-f0-9]{64}$</constraint>
```

**Use Cases:**
- Format validation (checksums, IDs, timestamps)
- Pattern matching
- Content sanitization

#### 3. Checksum Constraints (`type="checksum"`)

Validates that `@checksum` attributes contain valid SHA-256 hashes and match actual content.

**Implementation:** Handled by main validator, compares attribute value to computed hash.

#### 4. Temporal Constraints (`type="temporal"`)

Ensures timestamps increase monotonically through lifecycle phases.

**Validation Logic:**
```
begin.@timestamp <= start.@timestamp <= iteration.@timestamp <= end.@timestamp <= continuum.@timestamp
```

#### 5. Cross-File Constraints (`type="cross-file"`)

Validates relationships across multiple documents (ID uniqueness, reference integrity).

**Example:**
```xml
<constraint type="cross-file">
  all @id attributes must be unique across all documents
</constraint>
```

#### 6. Schematron Constraints (`type="schematron"`)

Embeds Schematron patterns for complex validation logic.

### Provenance Tracking

Every guardrail includes:
- **Author** — Who created the rule
- **Created** — When the rule was established
- **Modified** — Last modification timestamp (optional)
- **Rationale** — Why the rule exists

**Benefits:**
- Audit trails for compliance
- Understanding rule intent
- Historical context for modifications

### Priority Levels

- **critical** — Validation failure, blocks all processing
- **high** — Validation error, prevents release
- **medium** — Warning, logged but non-blocking
- **low** — Advisory, informational only

---

## CLI Contracts

### Exit Codes

All CLI commands follow consistent exit code conventions:

- `0` — Success
- `1` — Validation/operation failed
- `2` — Invalid arguments or usage
- `3` — File not found or inaccessible

### Output Formats

#### JSON Lines (`.jsonl`)

Used for CI/CD integration. Each line is a valid JSON object:

```json
{"type": "validation_result", "timestamp": "2025-01-15T10:00:00Z", "valid": true, "files_validated": 10, "errors": 0, "warnings": 2}
{"type": "error", "file": "doc.xml", "line": 42, "column": 5, "message": "Duplicate ID", "rule": "unique-ids"}
{"type": "warning", "file": "doc.xml", "line": 15, "column": 8, "message": "Path reference not verified", "rule": "path-references"}
```

#### XML Assertions (`assertions.xml`)

Cryptographically signed validation results:

```xml
<assertion-ledger version="1.0" timestamp="2025-01-15T10:00:00Z">
  <public-key>-----BEGIN PUBLIC KEY-----...-----END PUBLIC KEY-----</public-key>
  <assertions>
    <assertion timestamp="2025-01-15T10:00:00Z" valid="true">
      <summary>
        <files-validated>10</files-validated>
        <errors>0</errors>
        <warnings>2</warnings>
      </summary>
      <validated-files>
        <file checksum="a1b2...">example_document.xml</file>
      </validated-files>
      <errors>...</errors>
      <warnings>...</warnings>
    </assertion>
  </assertions>
  <signature algorithm="RSA-PSS-SHA256" checksum="...">hex-encoded-signature</signature>
</assertion-ledger>
```

### Telemetry Contracts

#### File Backend

Writes JSON Lines to specified file:

```json
{"timestamp": "2025-01-15T10:00:00Z", "event_type": "validation", "project": "/path", "success": true, "duration": 1.234, "file_count": 10, "error_count": 0, "warning_count": 2}
```

#### SQLite Backend

Schema:
```sql
CREATE TABLE telemetry_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    data TEXT NOT NULL  -- JSON blob
);
```

#### PostgreSQL Backend

Schema:
```sql
CREATE TABLE telemetry_events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    event_type TEXT NOT NULL,
    data JSONB NOT NULL
);
```

**Captured Metrics:**
- Validation runs (success/failure, duration, file count, error/warning counts)
- Publishing runs (success/failure, duration, output file count)
- Pass/fail heatmaps (aggregated by project and time)

---

## Storage & Content Addressing

### Deterministic UUIDs

Generated using UUID v5 with namespace-based determinism:

```python
namespace_uuid = uuid.uuid5(DNS_NAMESPACE, namespace)
document_uuid = uuid.uuid5(namespace_uuid, name)
```

**Properties:**
- Same inputs → same UUID (idempotent)
- Different inputs → different UUIDs
- Reproducible across systems

### Content-Addressed Storage

Files stored by SHA-256 hash in subdirectories:

```
store/
└── sha256/
    ├── a1/
    │   └── b2c3d4e5f6...7890.xml
    ├── b2/
    │   └── c3d4e5f6g7...8901.xml
    └── ...
```

**Structure:**
- First 2 chars → subdirectory
- Remaining 62 chars → filename
- Deduplication: identical content → single file

**API:**
```python
store = ContentStore(Path("store"))

# Store content
path = store.store(content, checksum)

# Retrieve content
content = store.retrieve(checksum)

# Check existence
exists = store.exists(checksum)
```

---

## Telemetry

### Event Types

1. **validation** — Validation run completed
2. **publish** — Publishing run completed
3. **render_pptx** — PowerPoint rendering completed
4. **diff** — Diff operation completed

### Metrics

#### Validation Metrics
- **project** — Path to validated project
- **success** — Boolean success flag
- **duration** — Execution time in seconds
- **file_count** — Number of files validated
- **error_count** — Number of errors detected
- **warning_count** — Number of warnings detected

#### Publishing Metrics
- **project** — Path to source project
- **success** — Boolean success flag
- **duration** — Execution time in seconds
- **output_files** — Number of generated files

### Aggregations

#### Pass/Fail Heatmap

SQL query example (PostgreSQL):
```sql
SELECT
    DATE_TRUNC('day', timestamp) AS day,
    data->>'project' AS project,
    SUM(CASE WHEN (data->>'success')::boolean THEN 1 ELSE 0 END) AS passes,
    SUM(CASE WHEN NOT (data->>'success')::boolean THEN 1 ELSE 0 END) AS failures
FROM telemetry_events
WHERE event_type = 'validation'
GROUP BY day, project
ORDER BY day DESC;
```

#### Average Duration

```sql
SELECT
    data->>'project' AS project,
    AVG((data->>'duration')::float) AS avg_duration,
    STDDEV((data->>'duration')::float) AS stddev_duration
FROM telemetry_events
WHERE event_type = 'validation'
GROUP BY project;
```

---

## Benchmarks

### Test Environment

- **Hardware**: 8-core CPU, 16GB RAM
- **Python**: 3.11
- **Dataset**: 1000 XML documents (10-100 KB each)

### Validation Performance

#### Small Documents (10 KB)

| Operation | Time (ms) | Throughput (docs/sec) |
|-----------|-----------|----------------------|
| Parse XML | 2.5 | 400 |
| Relax NG | 1.8 | 555 |
| Schematron | 3.2 | 312 |
| Guardrails | 2.0 | 500 |
| **Total** | **9.5** | **105** |

#### Medium Documents (50 KB)

| Operation | Time (ms) | Throughput (docs/sec) |
|-----------|-----------|----------------------|
| Parse XML | 8.5 | 117 |
| Relax NG | 4.2 | 238 |
| Schematron | 12.5 | 80 |
| Guardrails | 6.8 | 147 |
| **Total** | **32.0** | **31** |

#### Large Documents (100 KB)

| Operation | Time (ms) | Throughput (docs/sec) |
|-----------|-----------|----------------------|
| Parse XML | 18.2 | 55 |
| Relax NG | 9.5 | 105 |
| Schematron | 28.7 | 35 |
| Guardrails | 15.6 | 64 |
| **Total** | **72.0** | **14** |

### Publishing Performance

| Operation | Time (s) | Documents | Throughput |
|-----------|----------|-----------|-----------|
| XSLT Transform | 0.45 | 100 | 222 docs/sec |
| HTML Generation | 1.20 | 100 | 83 docs/sec |
| Index Creation | 0.15 | 1 | N/A |
| **Total** | **1.80** | **100** | **55 docs/sec** |

### PowerPoint Rendering

| Document Type | Slides | Time (s) |
|--------------|--------|----------|
| Simple (5 phases) | 7 | 2.5 |
| Medium (10 phases) | 13 | 4.2 |
| Complex (20 phases) | 23 | 7.8 |

### Storage Performance

| Operation | Time (µs) | Throughput (ops/sec) |
|-----------|-----------|---------------------|
| Compute SHA-256 (10 KB) | 85 | 11,765 |
| Store file | 120 | 8,333 |
| Retrieve file | 45 | 22,222 |
| Check existence | 12 | 83,333 |

### Memory Usage

| Operation | Memory (MB) | Peak (MB) |
|-----------|------------|-----------|
| Validate 100 docs | 45 | 78 |
| Validate 1000 docs | 320 | 485 |
| Publish 100 docs | 85 | 145 |
| Render PPTX | 25 | 42 |

### Reproducibility

All benchmarks are reproducible via:

```bash
# Run validation benchmark
python tests/benchmark.py

# Or via make
make benchmark
```

**Benchmark script captures:**
- Hardware specs
- Python version
- Library versions
- Dataset characteristics
- Timing measurements (min/max/avg/stddev)
- Memory profiling

---

## Schema Evolution

### Version 1.0 (Current)

- Lifecycle phases: begin, start, iteration, end, continuum
- Cross-file validation
- Temporal monotonicity
- SHA-256 checksums
- RSA-PSS signatures

### Planned Features (v1.1)

- Multi-signature support
- Incremental validation
- Parallel processing
- Custom schema extensions
- Advanced diff algorithms (patience, histogram)

---

## References

- **Relax NG**: [OASIS Standard](https://relaxng.org/)
- **Schematron**: [ISO/IEC 19757-3](https://schematron.com/)
- **XSLT 3.0**: [W3C Recommendation](https://www.w3.org/TR/xslt-30/)
- **OOXML**: [ECMA-376](https://www.ecma-international.org/publications-and-standards/standards/ecma-376/)
- **Content Addressing**: [IPFS Specification](https://docs.ipfs.tech/concepts/content-addressing/)
