# Programmatic XML-Lib Examples

This directory contains practical examples demonstrating how to use xml-lib programmatically in your Python projects.

## Overview

xml-lib provides a clean, well-documented Python API for XML validation, linting, and publishing. These examples show real-world usage patterns that go beyond simple CLI usage.

## Prerequisites

```bash
# Install xml-lib
pip install xml-lib

# Or install from source in development mode
pip install -e .
```

## Examples

### 1. Basic Validation (`01_basic_validation.py`)

**What it demonstrates:**
- Quick validation with sensible defaults
- Error and warning handling
- Progress indicators
- Accessing validation metadata (checksums, timestamps)

**When to use:**
- Development scripts
- Pre-commit hooks
- Simple CI/CD checks
- Learning the basics

**Run it:**
```bash
python examples/programmatic/01_basic_validation.py
```

**Key patterns:**
```python
from xml_lib import quick_validate

# Simplest usage - automatic discovery
result = quick_validate("path/to/project")

if result.is_valid:
    print(f"✓ Validated {len(result.validated_files)} files")
else:
    for error in result.errors:
        print(f"✗ {error.file}:{error.line} - {error.message}")
```

---

### 2. Batch Processing (`02_batch_processing.py`)

**What it demonstrates:**
- Validating multiple projects efficiently
- Reusing validator instances for performance
- Generating validation reports
- Exit code handling for CI/CD

**When to use:**
- CI/CD pipelines with multiple repos
- Nightly validation jobs
- Monorepo validation
- Quality assurance workflows

**Run it:**
```bash
python examples/programmatic/02_batch_processing.py
```

**Key patterns:**
```python
from xml_lib import create_validator

# Create once, reuse many times
validator = create_validator(
    schemas_dir="schemas",
    guardrails_dir="lib/guardrails",
    enable_streaming=True,
)

# Validate multiple projects
for project in projects:
    result = validator.validate_project(project)
    print(f"{project}: {'✓' if result.is_valid else '✗'}")
```

---

### 3. Custom Workflow (`03_custom_workflow.py`)

**What it demonstrates:**
- Multi-stage validation pipeline (lint → validate → artifacts → report)
- Conditional logic based on validation results
- Strict mode (treating warnings as errors)
- Integration with existing tooling

**When to use:**
- Documentation build pipelines
- Custom quality gates
- Integration with other tools
- Complex validation workflows

**Run it:**
```bash
python examples/programmatic/03_custom_workflow.py
```

**Key patterns:**
```python
from xml_lib import lint_xml, validate_xml

# Stage 1: Lint for issues
lint_result = lint_xml("project", check_external_entities=True)
if lint_result.has_errors:
    print("Linting failed!")
    return

# Stage 2: Validate against schemas
validation_result = validate_xml("project", enable_streaming=True)
if not validation_result.is_valid:
    print("Validation failed!")
    return

# Stage 3: Generate artifacts (only if validation passed)
generate_artifacts()
```

---

## Common Patterns

### Quick Start

```python
from xml_lib import quick_validate

result = quick_validate("my-project")
if result.is_valid:
    print("✓ All files valid!")
```

### Full Control

```python
from xml_lib import validate_xml
from xml_lib.sanitize import MathPolicy

result = validate_xml(
    "my-project",
    schemas_dir="custom/schemas",
    guardrails_dir="custom/guardrails",
    math_policy=MathPolicy.SANITIZE,
    enable_streaming=True,
    streaming_threshold_mb=50,
    show_progress=True,
)
```

### Reusable Validator

```python
from xml_lib import create_validator

validator = create_validator(
    schemas_dir="schemas",
    guardrails_dir="lib/guardrails",
)

# Use for multiple projects
for project in ["project1", "project2", "project3"]:
    result = validator.validate_project(Path(project))
    print(f"{project}: {'✓' if result.is_valid else '✗'}")
```

### Linting

```python
from xml_lib import lint_xml

result = lint_xml(
    "project",
    check_indentation=True,
    check_external_entities=True,
    indent_size=2,
)

print(f"Errors: {result.error_count}")
print(f"Warnings: {result.warning_count}")

for issue in result.issues:
    print(issue.format_text())
```

## API Reference

For complete API documentation, use Python's built-in help:

```python
import xml_lib

help(xml_lib)               # Package overview
help(xml_lib.quick_validate)  # Function documentation
help(xml_lib.Validator)       # Class documentation
```

Or access docstrings directly:

```python
from xml_lib import validate_xml
print(validate_xml.__doc__)
```

## Integration Examples

### Pre-commit Hook

```python
#!/usr/bin/env python3
from pathlib import Path
from xml_lib import quick_validate
import sys

result = quick_validate(Path.cwd())
if not result.is_valid:
    print("✗ XML validation failed")
    for error in result.errors:
        print(f"  {error.file}:{error.line} - {error.message}")
    sys.exit(1)

print("✓ All XML files valid")
sys.exit(0)
```

### GitHub Actions

```yaml
- name: Validate XML
  run: |
    pip install xml-lib
    python examples/programmatic/01_basic_validation.py
```

### pytest Integration

```python
import pytest
from xml_lib import quick_validate

def test_xml_files_are_valid():
    """Ensure all XML files in project are valid."""
    result = quick_validate(".")
    assert result.is_valid, f"Found {len(result.errors)} validation errors"
```

## Next Steps

1. **Explore Pipeline Automation**: See `examples/pipelines/` for YAML-based pipeline examples
2. **Interactive Shell**: Try `xml-lib shell` for REPL-based exploration
3. **Streaming for Large Files**: Learn about streaming validation in `docs/STREAMING_GUIDE.md`
4. **Custom Guardrails**: See `lib/guardrails/` for rule definitions

## Support

- **Documentation**: Run `help(xml_lib)` in Python
- **CLI Help**: Run `xml-lib --help`
- **Issues**: https://github.com/farukalpay/xml-lib/issues
