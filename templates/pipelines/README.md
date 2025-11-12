# XML Pipeline Templates

This directory contains pre-built pipeline templates for common XML processing workflows. These templates can be used as-is or customized for your specific needs.

## Available Templates

### 1. SOAP Validation (`soap-validation.yaml`)

Validates and enriches SOAP messages with metadata tracking.

**Use Cases:**
- SOAP API testing
- Message validation in integration workflows
- Adding processing metadata to SOAP envelopes

**Stages:**
1. Validate SOAP envelope structure
2. Enrich with metadata (timestamp, version, processor)
3. Re-validate enriched message
4. Generate HTML report
5. Generate JSON assertions ledger

**Usage:**
```bash
xml-lib pipeline run templates/pipelines/soap-validation.yaml soap-message.xml
```

### 2. RSS Feed Processing (`rss-feed.yaml`)

Validates, enriches, and publishes RSS 2.0 feeds to multiple formats.

**Use Cases:**
- RSS feed validation
- Feed normalization (date formats, metadata)
- Multi-format publishing (XML, HTML, JSON)

**Stages:**
1. Validate RSS 2.0 schema
2. Normalize date formats to ISO 8601
3. Add channel metadata
4. Re-validate enriched feed
5. Output to XML (clean, formatted)
6. Output to HTML (human-readable)
7. Output to JSON (API format)

**Usage:**
```bash
xml-lib pipeline run templates/pipelines/rss-feed.yaml feed.xml
```

### 3. Configuration Validation (`config-validation.yaml`)

Validates XML configuration files, resolves includes, and applies environment-specific overrides.

**Use Cases:**
- Application configuration management
- Environment-specific config deployment
- Configuration security auditing

**Stages:**
1. Validate base configuration schema
2. Resolve includes and imports
3. Apply environment-specific overrides
4. Validate merged configuration
5. Security lint (XXE, sensitive data)
6. Output final configuration (XML)
7. Output deployment format (JSON)
8. Generate configuration report

**Usage:**
```bash
ENV=production xml-lib pipeline run templates/pipelines/config-validation.yaml config.xml
```

### 4. Schema Migration (`schema-migration.yaml`)

Migrates XML documents from legacy schema to new schema version with full audit trail.

**Use Cases:**
- Schema version upgrades
- Legacy data migration
- Data modernization projects

**Stages:**
1. Validate source schema compliance
2. Pre-migration data quality checks
3. Transform to target schema
4. Validate target schema compliance
5. Data integrity verification
6. Output migrated XML
7. Generate migration diff report
8. Generate audit trail

**Usage:**
```bash
xml-lib pipeline run templates/pipelines/schema-migration.yaml legacy-data.xml
```

### 5. CI/CD Validation (`ci-validation.yaml`)

Comprehensive validation for CI/CD pipelines with quality metrics and reporting.

**Use Cases:**
- Pre-commit validation
- GitHub Actions / GitLab CI integration
- Continuous quality monitoring

**Stages:**
1. Schema validation
2. Schema compatibility check
3. Security linting (XXE, external entities)
4. Code quality checks
5. Performance analysis
6. Generate quality report (HTML)
7. Generate metrics (JSON)
8. Generate assertions ledger

**Usage:**
```bash
# In CI/CD environment
COMMIT_SHA=$GITHUB_SHA BRANCH_NAME=$GITHUB_REF xml-lib pipeline run \
  templates/pipelines/ci-validation.yaml changed-files.xml
```

## Customizing Templates

### 1. Copy and Modify

```bash
cp templates/pipelines/soap-validation.yaml my-custom-pipeline.yaml
# Edit my-custom-pipeline.yaml
xml-lib pipeline run my-custom-pipeline.yaml input.xml
```

### 2. Override Variables

Use environment variables to override template variables:

```bash
ENV=staging TIMESTAMP=$(date -Iseconds) xml-lib pipeline run \
  templates/pipelines/config-validation.yaml config.xml
```

### 3. Extend with Custom Stages

Add custom validation rules, transforms, or outputs:

```yaml
stages:
  # ... existing stages ...

  - type: validate
    name: custom_business_rules
    schemas_dir: my-schemas
    guardrails_dir: my-guardrails
    strict: true
```

## Pipeline Configuration Reference

### Error Strategies

- `fail_fast` - Stop on first error (default)
- `continue` - Log errors but continue pipeline
- `rollback` - Rollback to last snapshot on error
- `retry` - Retry failed stage with exponential backoff
- `skip` - Skip failed stage and continue

### Stage Types

#### `validate`
```yaml
- type: validate
  name: my_validation
  schemas_dir: schemas
  guardrails_dir: guardrails
  strict: true
  streaming: false
  streaming_threshold: 10485760  # 10MB
```

#### `transform`
```yaml
- type: transform
  name: my_transform
  transform: transforms/my-transform.xsl
  params:
    param1: value1
    param2: value2
```

#### `output`
```yaml
- type: output
  name: my_output
  format: html  # html, pptx, php, json, xml, assertions
  output_path: out/result.html
  template: templates/my-template.xsl
  options:
    option1: value1
```

### Variables

Use variables to make pipelines reusable:

```yaml
variables:
  timestamp: "{{ datetime.now().isoformat() }}"
  environment: "${ENV}"  # From environment variable
  version: "1.0"

stages:
  - type: transform
    name: add_metadata
    params:
      timestamp: "${timestamp}"
      env: "${environment}"
```

## Integration Examples

### GitHub Actions

```yaml
name: Validate XML
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install xml-lib
      - run: |
          xml-lib pipeline run templates/pipelines/ci-validation.yaml \
            $(git diff --name-only --diff-filter=AM origin/main | grep '.xml$')
        env:
          COMMIT_SHA: ${{ github.sha }}
          BRANCH_NAME: ${{ github.ref_name }}
          BUILD_NUMBER: ${{ github.run_number }}
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: validate-xml
        name: Validate XML files
        entry: xml-lib pipeline run templates/pipelines/ci-validation.yaml
        language: system
        files: \.xml$
```

### GitLab CI

```yaml
# .gitlab-ci.yml
validate-xml:
  stage: test
  script:
    - pip install xml-lib
    - xml-lib pipeline run templates/pipelines/ci-validation.yaml *.xml
  artifacts:
    reports:
      junit: out/ci/quality-report.xml
    paths:
      - out/ci/
```

## Performance Tips

1. **Enable Streaming** for large files (>10MB):
   ```yaml
   streaming: true
   streaming_threshold: 5242880  # 5MB
   ```

2. **Limit Snapshots** for long pipelines:
   ```yaml
   max_snapshots: 50
   ```

3. **Use `continue` Strategy** for parallel validation:
   ```yaml
   error_strategy: continue
   ```

4. **Disable Rollback** for read-only pipelines:
   ```yaml
   rollback_enabled: false
   ```

## Troubleshooting

### Pipeline Fails at Stage

Check stage output in the error message. Use dry-run to preview stages:

```bash
xml-lib pipeline dry-run templates/pipelines/my-pipeline.yaml input.xml
```

### Variable Not Resolved

Ensure environment variables are exported:

```bash
export ENV=production
xml-lib pipeline run templates/pipelines/config-validation.yaml config.xml
```

### Transform File Not Found

Paths in YAML are relative to the pipeline file directory. Use absolute paths if needed:

```yaml
transform: /absolute/path/to/transform.xsl
```

## Contributing

Have a useful pipeline template? Submit a PR with:

1. YAML pipeline definition
2. Example input/output
3. Documentation of use cases
4. Integration examples

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.
