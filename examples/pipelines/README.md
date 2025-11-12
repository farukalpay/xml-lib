# Pipeline Examples

Real-world examples demonstrating XML Pipeline Automation features.

## Quick Links

- [Basic Validation](#1-basic-validation)
- [Multi-Format Publishing](#2-multi-format-publishing)
- [Data Migration](#3-data-migration)
- [SOAP API Processing](#4-soap-api-processing)
- [CI/CD Integration](#5-cicd-integration)

## Examples

### 1. Basic Validation

**File:** `01-basic-validation/`

Simple validation pipeline for XML documents.

**Features:**
- Schema validation (Relax NG + Schematron)
- Guardrail rule enforcement
- Error reporting

**Usage:**

```bash
cd 01-basic-validation
xml-lib pipeline run pipeline.yaml sample-input.xml
```

### 2. Multi-Format Publishing

**File:** `02-multi-format-output/`

Transform XML into multiple output formats.

**Features:**
- Single XML source
- Multiple outputs (HTML, JSON, XML)
- Custom XSLT templates
- Report generation

**Usage:**

```bash
cd 02-multi-format-output
xml-lib pipeline run pipeline.yaml document.xml
# Outputs: out/document.html, out/document.json, out/document-clean.xml
```

### 3. Data Migration

**File:** `03-schema-migration/`

Migrate XML documents from legacy schema to new version.

**Features:**
- Pre-migration validation
- XSLT-based transformation
- Post-migration validation
- Rollback on failure
- Diff report generation

**Usage:**

```bash
cd 03-schema-migration
xml-lib pipeline run migrate.yaml legacy-data.xml
# Creates: out/migrated.xml, out/diff-report.html, out/audit.jsonl
```

### 4. SOAP API Processing

**File:** `04-soap-processing/`

Process SOAP messages with validation and enrichment.

**Features:**
- SOAP envelope validation
- WS-Security header verification
- Message enrichment
- Response generation

**Usage:**

```bash
cd 04-soap-processing
xml-lib pipeline run process-request.yaml request.xml
# Creates: out/response.xml, out/audit.jsonl
```

### 5. CI/CD Integration

**File:** `05-ci-integration/`

Automated validation for continuous integration pipelines.

**Features:**
- Pre-commit hooks
- GitHub Actions workflow
- Quality metrics
- Security checks
- JUnit XML reports

**Usage:**

```bash
cd 05-ci-integration

# Run locally
xml-lib pipeline run ci-pipeline.yaml src/**/*.xml

# Install pre-commit hook
cp pre-commit .git/hooks/
chmod +x .git/hooks/pre-commit

# Use in GitHub Actions (see .github/workflows/validate-xml.yml)
```

## Running All Examples

```bash
# From repository root
make examples

# Or manually
for dir in examples/pipelines/*/; do
    cd "$dir"
    if [ -f "run.sh" ]; then
        bash run.sh
    fi
    cd -
done
```

## Creating Your Own Examples

1. Copy an existing example as template
2. Modify `pipeline.yaml` for your use case
3. Add sample input files
4. Test with `xml-lib pipeline dry-run`
5. Document in README.md
6. Submit PR!

## Example Structure

```
example-name/
├── README.md                  # Example documentation
├── pipeline.yaml              # Pipeline definition
├── input/                     # Sample input files
│   └── sample.xml
├── schemas/                   # Validation schemas (if needed)
│   ├── schema.rng
│   └── rules.sch
├── transforms/                # XSLT transforms (if needed)
│   └── transform.xsl
├── templates/                 # Output templates (if needed)
│   └── report.xsl
├── expected-output/           # Expected results for testing
│   └── expected.xml
└── run.sh                     # Run script with explanation
```

## Contributing

Have a useful example? We welcome contributions!

1. Create your example following the structure above
2. Test thoroughly with sample data
3. Document clearly in README.md
4. Submit a pull request

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## Support

- Questions: [GitHub Discussions](https://github.com/farukalpay/xml-lib/discussions)
- Issues: [GitHub Issues](https://github.com/farukalpay/xml-lib/issues)
- Docs: [Pipeline Guide](../../docs/PIPELINE_GUIDE.md)
