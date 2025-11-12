# XML Pipeline Automation - User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Core Concepts](#core-concepts)
4. [Pipeline Stages](#pipeline-stages)
5. [Error Handling](#error-handling)
6. [Templates](#templates)
7. [Advanced Usage](#advanced-usage)
8. [Performance](#performance)
9. [Best Practices](#best-practices)

## Introduction

XML Pipeline Automation provides a declarative framework for chaining XML operations (validation, transformation, output) with built-in error recovery, rollback, and state management.

### Key Features

- **Declarative Pipelines**: Define workflows in YAML or programmatically in Python
- **Error Recovery**: Multiple strategies (fail-fast, continue, rollback, retry, skip)
- **Rollback Support**: Automatic state snapshots and restoration
- **Template Library**: Pre-built pipelines for common use cases (SOAP, RSS, CI/CD)
- **Extensible**: Custom stages with Python functions
- **Production-Ready**: Comprehensive error handling, logging, and monitoring

### When to Use Pipelines

- **Multi-Stage Validation**: Validate → Transform → Re-validate workflows
- **Data Migration**: Legacy XML schema migration with rollback
- **CI/CD Integration**: Automated validation and quality checks
- **API Processing**: SOAP/REST XML message transformation
- **Report Generation**: XML → Multiple output formats (HTML, PDF, JSON)

## Quick Start

### Installation

```bash
pip install xml-lib
```

### Your First Pipeline

Create a simple pipeline that validates XML and outputs HTML:

**1. Create `my_pipeline.yaml`:**

```yaml
name: simple_validation
description: Validate XML and generate report
error_strategy: fail_fast
rollback_enabled: true

stages:
  - type: validate
    name: validate_input
    schemas_dir: schemas
    strict: true

  - type: output
    name: generate_report
    format: html
    output_path: out/report.html
```

**2. Run the pipeline:**

```bash
xml-lib pipeline run my_pipeline.yaml input.xml
```

**3. View results:**

```
🔄 Running pipeline: my_pipeline.yaml
   Input: input.xml

============================================================
Pipeline: simple_validation
Status: ✅ SUCCESS
Duration: 0.45s
Stages executed: 2
Stages failed: 0
============================================================
```

## Core Concepts

### Pipeline

A Pipeline orchestrates the execution of multiple stages. Each pipeline has:

- **Name**: Identifier for logging and reporting
- **Error Strategy**: How to handle stage failures
- **Rollback Support**: Whether to create state snapshots
- **Stages**: Ordered list of operations to perform

### Stage

A Stage represents a discrete operation (validation, transformation, output). Stages:

- Execute sequentially in order
- Receive and modify the pipeline context
- Return results indicating success/failure
- Can be rolled back if errors occur

### Context

PipelineContext carries state between stages:

- **XML Data**: Current XML document (string and parsed tree)
- **File Paths**: Input/output file locations
- **Variables**: Key-value store for sharing data
- **Results**: History of stage executions
- **Snapshots**: State backups for rollback

## Pipeline Stages

### ValidateStage

Validates XML against schemas and guardrails.

**YAML:**

```yaml
stages:
  - type: validate
    name: validate_xml
    schemas_dir: schemas
    guardrails_dir: guardrails
    strict: true
    streaming: false
    streaming_threshold: 10485760  # 10MB
```

**Python:**

```python
from xml_lib.pipeline import Pipeline, ValidateStage
from pathlib import Path

pipeline = Pipeline(name="validate")
pipeline.add_stage(ValidateStage(
    schemas_dir=Path("schemas"),
    guardrails_dir=Path("guardrails"),
    strict=True
))
```

**Parameters:**
- `schemas_dir`: Directory containing RelaxNG/Schematron schemas
- `guardrails_dir`: Directory containing custom validation rules
- `strict`: Treat warnings as errors (default: true)
- `streaming`: Force streaming mode for large files (default: false)
- `streaming_threshold`: Auto-enable streaming above this size (default: 10MB)

### TransformStage

Transforms XML using XSLT stylesheets or Python functions.

**XSLT Transformation:**

```yaml
stages:
  - type: transform
    name: enrich
    transform: transforms/add-metadata.xsl
    params:
      timestamp: "2024-01-01T00:00:00"
      version: "1.0"
```

**Python Function:**

```python
from xml_lib.pipeline import TransformStage

def add_timestamp(xml_data, context):
    return xml_data.replace(
        "</root>",
        f"<timestamp>{context.get_variable('now')}</timestamp></root>"
    )

pipeline.add_stage(TransformStage(
    transform=add_timestamp,
    name="add_timestamp"
))
```

**Parameters:**
- `transform`: Path to XSLT file or Python callable
- `params`: Dictionary of parameters to pass to XSLT
- `name`: Stage identifier

### OutputStage

Outputs XML to various formats.

**Supported Formats:**
- `xml`: Pretty-printed XML
- `html`: HTML documentation (via XSLT publisher)
- `pptx`: PowerPoint presentation
- `php`: PHP pages with XXE protection
- `json`: JSON metadata (context dump)
- `assertions`: Signed assertion ledger

**Example:**

```yaml
stages:
  - type: output
    name: write_html
    format: html
    output_path: out/report.html
    template: templates/custom.xsl
    options:
      title: "Validation Report"
```

```python
from xml_lib.pipeline import OutputStage

pipeline.add_stage(OutputStage(
    format="html",
    output_path=Path("out/report.html"),
    template=Path("templates/custom.xsl"),
    options={"title": "Report"}
))
```

### CustomStage

Execute custom Python logic within the pipeline.

**Python:**

```python
from xml_lib.pipeline import CustomStage, StageResult

def analyze_xml(context):
    element_count = len(context.xml_tree.findall(".//*"))
    context.set_variable("element_count", element_count)

    return StageResult(
        stage="analyze",
        success=True,
        metadata={"count": element_count}
    )

pipeline.add_stage(CustomStage(
    function=analyze_xml,
    name="analyze_structure"
))
```

**With Rollback:**

```python
def modify_xml(context):
    context.set_variable("backup", context.xml_data)
    context.xml_data = context.xml_data.upper()
    return StageResult(stage="modify", success=True)

def rollback_modification(context):
    context.xml_data = context.get_variable("backup")

pipeline.add_stage(CustomStage(
    function=modify_xml,
    rollback_function=rollback_modification,
    name="modify_with_rollback"
))
```

## Error Handling

### Error Strategies

Control how pipelines handle stage failures:

#### 1. FAIL_FAST (default)

Stop execution on first error.

```yaml
error_strategy: fail_fast
```

**Use when:** Production workflows where any failure should stop processing.

#### 2. CONTINUE

Log errors but continue executing all stages.

```yaml
error_strategy: continue
```

**Use when:** Collecting all validation issues for reporting.

#### 3. ROLLBACK

Rollback to last snapshot and stop.

```yaml
error_strategy: rollback
```

**Use when:** Data modifications must be atomic (all-or-nothing).

#### 4. RETRY

Retry failed stage with exponential backoff.

```yaml
error_strategy: retry
```

**Use when:** Transient failures are expected (network issues, resource contention).

#### 5. SKIP

Skip failed stage and continue.

```yaml
error_strategy: skip
```

**Use when:** Optional stages that shouldn't block the pipeline.

### Rollback Mechanism

Enable rollback to create automatic state snapshots:

```yaml
rollback_enabled: true
max_snapshots: 100  # Limit memory usage
```

**How it works:**

1. Before each stage, pipeline saves XML state
2. If stage fails and `error_strategy: rollback`, restore previous state
3. Snapshots are limited to `max_snapshots` (oldest discarded)

**Example:**

```python
pipeline = Pipeline(
    name="safe_transform",
    error_strategy=ErrorStrategy.ROLLBACK,
    rollback_enabled=True
)

pipeline.add_stage(TransformStage(...))  # Creates snapshot
pipeline.add_stage(ValidateStage(...))   # Creates snapshot
# If validation fails, XML reverts to pre-transform state
```

## Templates

Pre-built pipelines for common use cases.

### Available Templates

List all templates:

```bash
xml-lib pipeline list
```

### SOAP Validation

Validate and enrich SOAP messages.

```bash
xml-lib pipeline run templates/pipelines/soap-validation.yaml soap-message.xml
```

**Features:**
- Envelope structure validation
- Metadata enrichment (timestamps, versions)
- Re-validation of enriched message
- HTML report generation
- Assertion ledger for audit trails

### RSS Feed Processing

Validate and publish RSS 2.0 feeds.

```bash
xml-lib pipeline run templates/pipelines/rss-feed.yaml feed.xml
```

**Features:**
- RSS 2.0 schema validation
- Date normalization (ISO 8601)
- Channel metadata enrichment
- Multi-format output (XML, HTML, JSON)

### Configuration Validation

Validate XML configs with environment overrides.

```bash
ENV=production xml-lib pipeline run templates/pipelines/config-validation.yaml config.xml
```

**Features:**
- Base configuration validation
- Include resolution (XInclude)
- Environment-specific overrides
- Security linting (XXE detection)
- Deployment format generation

### Schema Migration

Migrate XML documents between schema versions.

```bash
xml-lib pipeline run templates/pipelines/schema-migration.yaml legacy-data.xml
```

**Features:**
- Source schema validation
- Data quality pre-checks
- Schema transformation
- Target schema validation
- Diff report generation
- Full audit trail

### CI/CD Validation

Comprehensive validation for continuous integration.

```bash
COMMIT_SHA=$GITHUB_SHA xml-lib pipeline run templates/pipelines/ci-validation.yaml changed-files.xml
```

**Features:**
- Schema validation
- Compatibility checking
- Security linting
- Quality metrics
- Performance analysis
- JSON metrics for tooling

## Advanced Usage

### Programmatic API

Build pipelines in Python for maximum flexibility:

```python
from xml_lib.pipeline import (
    Pipeline,
    ValidateStage,
    TransformStage,
    OutputStage,
    CustomStage,
    ErrorStrategy
)
from pathlib import Path

# Create pipeline
pipeline = Pipeline(
    name="advanced_pipeline",
    error_strategy=ErrorStrategy.ROLLBACK,
    rollback_enabled=True,
    max_snapshots=50
)

# Add stages
pipeline.add_stage(ValidateStage(
    schemas_dir=Path("schemas"),
    strict=True
))

pipeline.add_stage(TransformStage(
    transform=Path("transforms/enrich.xsl"),
    params={"version": "2.0"}
))

def custom_check(context):
    # Custom business logic
    if not context.xml_tree.find(".//required-field"):
        raise ValueError("Missing required field")
    return StageResult(stage="custom_check", success=True)

pipeline.add_stage(CustomStage(
    function=custom_check,
    name="business_rules"
))

pipeline.add_stage(OutputStage(
    format="html",
    output_path=Path("out/report.html")
))

# Execute
result = pipeline.execute(input_xml="data.xml")

# Check results
if result.success:
    print(f"✅ Pipeline succeeded in {result.duration_seconds:.2f}s")
    for stage_result in result.context.stage_results:
        print(f"  - {stage_result.stage}: {stage_result.duration_seconds:.2f}s")
else:
    print(f"❌ Pipeline failed: {result.error}")
```

### Variables and Templating

Use variables to make pipelines reusable:

```yaml
variables:
  timestamp: "{{ datetime.now().isoformat() }}"
  environment: "${ENV}"  # From environment variable
  version: "1.0"

stages:
  - type: transform
    name: add_metadata
    transform: transforms/metadata.xsl
    params:
      timestamp: "${timestamp}"
      env: "${environment}"
      version: "${version}"
```

### CLI Variable Override

Override variables at runtime:

```bash
xml-lib pipeline run pipeline.yaml input.xml \
  -v timestamp=$(date -Iseconds) \
  -v environment=production \
  -v version=2.0
```

### Dry Run

Preview pipeline stages without executing:

```bash
xml-lib pipeline dry-run pipeline.yaml input.xml
```

Output:

```
🔍 Dry run: pipeline.yaml

Pipeline: my_pipeline
Error Strategy: rollback
Rollback: Enabled

Stages (4):

  1. validate_input (ValidateStage)
  2. enrich (TransformStage)
  3. validate_enriched (ValidateStage)
  4. generate_report (OutputStage)

✅ Pipeline is valid
```

### Pipeline Validation

Validate YAML definition before execution:

```bash
xml-lib pipeline validate pipeline.yaml
```

## Performance

### Streaming Mode

For large XML files (>10MB), use streaming validation:

```yaml
stages:
  - type: validate
    name: validate_large_file
    streaming: true
    streaming_threshold: 5242880  # 5MB
```

**Benefits:**
- Constant memory usage regardless of file size
- Processes files >1GB efficiently
- Automatic activation above threshold

### Snapshot Management

Limit snapshot history for long pipelines:

```yaml
rollback_enabled: true
max_snapshots: 50  # Keep last 50 snapshots only
```

**Memory formula:** ~`(avg_xml_size × max_snapshots)` bytes

### Pipeline Parallelization

Currently stages execute sequentially. For parallel processing, use multiple pipeline instances:

```python
from concurrent.futures import ThreadPoolExecutor

files = ["file1.xml", "file2.xml", "file3.xml"]

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(pipeline.execute, input_xml=f)
        for f in files
    ]
    results = [f.result() for f in futures]
```

## Best Practices

### 1. Use Descriptive Stage Names

**❌ Bad:**

```yaml
stages:
  - type: validate
    name: v1
  - type: transform
    name: t1
```

**✅ Good:**

```yaml
stages:
  - type: validate
    name: validate_soap_envelope
  - type: transform
    name: add_processing_metadata
```

### 2. Choose Appropriate Error Strategies

| Use Case | Strategy | Rollback |
|----------|----------|----------|
| Production data processing | `fail_fast` | ✅ Yes |
| CI/CD validation | `continue` | ❌ No |
| Data migration | `rollback` | ✅ Yes |
| Flaky network operations | `retry` | ✅ Yes |
| Optional enrichment | `skip` | ❌ No |

### 3. Validate Early and Often

```yaml
stages:
  - type: validate
    name: validate_input
    strict: true

  - type: transform
    name: enrich

  - type: validate
    name: validate_output
    strict: true  # Catch transform errors early
```

### 4. Use Templates as Starting Points

Don't reinvent the wheel - customize existing templates:

```bash
cp templates/pipelines/soap-validation.yaml my-custom-soap.yaml
# Edit my-custom-soap.yaml
xml-lib pipeline run my-custom-soap.yaml input.xml
```

### 5. Test Pipelines with Dry Run

Always dry-run before production:

```bash
# Development
xml-lib pipeline dry-run pipeline.yaml test-data.xml

# Production
xml-lib pipeline run pipeline.yaml production-data.xml
```

### 6. Monitor and Log

Enable verbose logging for debugging:

```bash
xml-lib pipeline run pipeline.yaml input.xml --verbose
```

Output:

```
🔄 Running pipeline: pipeline.yaml
   Input: input.xml

Stage Results:
  ✅ validate_input (0.23s)
  ✅ transform_data (0.45s)
  ❌ validate_output (0.12s)
     Error: Validation failed: 2 errors
```

### 7. Version Control Pipelines

Store pipeline definitions in git alongside code:

```
myproject/
├── src/
├── tests/
├── pipelines/
│   ├── development.yaml
│   ├── staging.yaml
│   └── production.yaml
├── schemas/
└── transforms/
```

### 8. Document Custom Stages

Add clear docstrings to custom functions:

```python
def calculate_metrics(context):
    """Calculate XML complexity metrics.

    Metrics:
    - element_count: Total number of elements
    - max_depth: Maximum nesting depth
    - attribute_count: Total attributes

    Sets variables: metrics_json
    """
    tree = context.xml_tree
    # ... implementation ...
```

---

## Next Steps

- **Tutorial**: Follow the [Pipeline Tutorial](PIPELINE_TUTORIAL.md) for hands-on examples
- **Examples**: Explore [example projects](../examples/pipelines/)
- **API Reference**: See [Pipeline API docs](api/pipeline.md)
- **Contributing**: Add your own [pipeline templates](../CONTRIBUTING.md)

## Support

- **Issues**: [GitHub Issues](https://github.com/farukalpay/xml-lib/issues)
- **Discussions**: [GitHub Discussions](https://github.com/farukalpay/xml-lib/discussions)
- **Documentation**: [https://xml-lib.readthedocs.io](https://xml-lib.readthedocs.io)
