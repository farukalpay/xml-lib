# xml-lib Public API Reference

This document describes the stable public API of xml-lib. All exports listed here are considered stable and safe to use in production code.

## Installation & Import

```python
# Install via pip (when published)
pip install xml-lib

# Import high-level functions (recommended for most users)
from xml_lib import quick_validate, validate_xml, lint_xml, publish_html

# Import classes for advanced usage
from xml_lib import Validator, ValidationResult, XMLLinter, Publisher

# Import enums and configuration types
from xml_lib import MathPolicy, TelemetrySink, FileTelemetrySink
```

## Quick Start

### Validation

The fastest way to validate XML files:

```python
from xml_lib import quick_validate

# Validates all XML files in a project directory
# Auto-discovers schemas/ and lib/guardrails/ directories
result = quick_validate("my-xml-project")

if result.is_valid:
    print(f"✓ All {len(result.validated_files)} files are valid!")
else:
    print(f"✗ Found {len(result.errors)} errors:")
    for error in result.errors:
        print(f"  {error.file}:{error.line} - {error.message}")
```

### Linting

Check for formatting issues and security vulnerabilities:

```python
from xml_lib import lint_xml

result = lint_xml("my-project", check_security=True)

print(f"Checked {result.files_checked} files")
print(f"Errors: {result.error_count}, Warnings: {result.warning_count}")

for issue in result.issues:
    if issue.level.value == "error":
        print(f"  {issue.format_text()}")
```

### Publishing

Transform XML to HTML:

```python
from xml_lib import publish_html

result = publish_html("my-project", "output/html")

if result.success:
    print(f"Published {len(result.files)} files")
else:
    print(f"Publishing failed: {result.error}")
```

## High-Level Functions

These functions provide the simplest interface for common tasks.

### `quick_validate()`

```python
def quick_validate(
    project_path: str | Path,
    *,
    show_progress: bool = False,
) -> ValidationResult
```

**Quick validation with sensible defaults** - the easiest way to get started.

- **Auto-discovers** schemas and guardrails in standard locations
- **Validates all XML files** in the project directory
- **Returns** a `ValidationResult` with errors, warnings, and metadata

**Parameters:**
- `project_path`: Directory containing XML files
- `show_progress`: Show progress indicator (default: False)

**Returns:** `ValidationResult`

**Raises:** `FileNotFoundError` if project_path doesn't exist

---

### `validate_xml()`

```python
def validate_xml(
    project_path: str | Path,
    *,
    schemas_dir: Optional[str | Path] = None,
    guardrails_dir: Optional[str | Path] = None,
    math_policy: MathPolicy = MathPolicy.SANITIZE,
    enable_streaming: bool = True,
    streaming_threshold_mb: int = 10,
    show_progress: bool = False,
    telemetry: Optional[TelemetrySink] = None,
) -> ValidationResult
```

**Full-featured validation with complete control** over all options.

**Parameters:**
- `project_path`: Directory containing XML files
- `schemas_dir`: Directory with .rng and .sch schemas (auto-discovered if None)
- `guardrails_dir`: Directory with guardrail definitions (auto-discovered if None)
- `math_policy`: How to handle mathematical content:
  - `MathPolicy.SANITIZE` (default): Clean problematic content
  - `MathPolicy.SKIP`: Skip files with math
  - `MathPolicy.ERROR`: Raise errors on math content
- `enable_streaming`: Use memory-efficient streaming for large files (default: True)
- `streaming_threshold_mb`: Files larger than this use streaming (default: 10MB)
- `show_progress`: Show progress indicator (default: False)
- `telemetry`: Optional telemetry sink for metrics collection

**Returns:** `ValidationResult`

**Example:**
```python
from xml_lib import validate_xml, MathPolicy

result = validate_xml(
    "my-project",
    schemas_dir="custom/schemas",
    math_policy=MathPolicy.SKIP,
    enable_streaming=True,
    show_progress=True,
)
```

---

### `create_validator()`

```python
def create_validator(
    *,
    schemas_dir: str | Path,
    guardrails_dir: str | Path,
    math_policy: MathPolicy = MathPolicy.SANITIZE,
    enable_streaming: bool = True,
    streaming_threshold_bytes: int = 10 * 1024 * 1024,
    show_progress: bool = False,
    telemetry: Optional[TelemetrySink] = None,
) -> Validator
```

**Create a reusable Validator instance** for validating multiple projects.

Use this when you need to validate multiple projects with the same configuration.

**Returns:** `Validator` instance

**Example:**
```python
from xml_lib import create_validator
from pathlib import Path

# Create validator once
validator = create_validator(
    schemas_dir="schemas",
    guardrails_dir="lib/guardrails",
    enable_streaming=True,
)

# Validate multiple projects
for project in ["project1", "project2", "project3"]:
    result = validator.validate_project(Path(project))
    print(f"{project}: {'✓' if result.is_valid else '✗'}")
```

---

### `lint_xml()`

```python
def lint_xml(
    path: str | Path,
    *,
    check_indentation: bool = True,
    check_attribute_order: bool = True,
    check_external_entities: bool = True,
    check_formatting: bool = True,
    indent_size: int = 2,
    allow_xxe: bool = False,
) -> LintResult
```

**Lint XML files for formatting and security issues.**

Checks for:
- Inconsistent indentation
- XXE (XML External Entity) vulnerabilities
- Attribute ordering
- Other formatting best practices

**Parameters:**
- `path`: File or directory to lint
- `check_indentation`: Check consistent indentation (default: True)
- `check_attribute_order`: Check alphabetical attribute order (default: True)
- `check_external_entities`: Check for XXE vulnerabilities (default: True)
- `check_formatting`: Check general formatting (default: True)
- `indent_size`: Expected spaces for indentation (default: 2)
- `allow_xxe`: Allow external entities - False for security (default: False)

**Returns:** `LintResult`

---

### `publish_html()`

```python
def publish_html(
    project_path: str | Path,
    output_dir: str | Path,
    *,
    xslt_dir: Optional[str | Path] = None,
    telemetry: Optional[TelemetrySink] = None,
) -> PublishResult
```

**Publish XML documents to HTML** using XSLT 3.0 transformation.

**Parameters:**
- `project_path`: Directory containing XML files
- `output_dir`: Directory where HTML files will be written
- `xslt_dir`: Directory with XSLT templates (auto-discovered if None)
- `telemetry`: Optional telemetry sink

**Returns:** `PublishResult`

## Core Classes

For advanced usage that requires more control.

### `Validator`

Main validation class.

```python
class Validator:
    def __init__(
        self,
        schemas_dir: Path,
        guardrails_dir: Path,
        telemetry: TelemetrySink | None = None,
        math_policy: MathPolicy = MathPolicy.SANITIZE,
        use_streaming: bool = False,
        streaming_threshold_bytes: int = 10 * 1024 * 1024,
        show_progress: bool = False,
    )

    def validate_project(self, project_path: Path) -> ValidationResult
    def validate_file(self, file_path: Path) -> ValidationResult
```

**Methods:**
- `validate_project(project_path)`: Validate all XML files in a directory
- `validate_file(file_path)`: Validate a single XML file

---

### `ValidationResult`

Result type for validation operations (dataclass).

```python
@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[ValidationError]
    warnings: list[ValidationError]
    validated_files: list[str]
    checksums: dict[str, str]
    timestamp: datetime
    used_streaming: bool
```

**Attributes:**
- `is_valid`: True if validation passed without errors
- `errors`: List of validation errors
- `warnings`: List of non-fatal warnings
- `validated_files`: Paths of validated files
- `checksums`: SHA-256 checksums of validated files
- `timestamp`: When validation was performed
- `used_streaming`: Whether streaming was used

---

### `ValidationError`

Individual validation error (dataclass).

```python
@dataclass
class ValidationError:
    file: str
    line: int | None
    column: int | None
    message: str
    type: str  # 'error' or 'warning'
    rule: str | None
```

---

### `XMLLinter`

XML linter for formatting and security checks.

```python
class XMLLinter:
    def __init__(
        self,
        check_indentation: bool = True,
        check_attribute_order: bool = True,
        check_external_entities: bool = True,
        check_formatting: bool = True,
        indent_size: int = 2,
        allow_xxe: bool = False,
    )

    def lint_file(self, file_path: Path) -> LintResult
    def lint_directory(self, dir_path: Path) -> LintResult
```

---

### `LintResult`

Result of linting operations (dataclass).

```python
@dataclass
class LintResult:
    issues: list[LintIssue]
    files_checked: int
    error_count: int
    warning_count: int
    has_errors: bool
```

---

### `LintIssue`

Individual lint issue (dataclass).

```python
@dataclass
class LintIssue:
    level: LintLevel
    file: Path
    line: int
    column: int | None
    message: str
    rule: str

    def format_text(self) -> str
```

---

### `LintLevel`

Severity levels for lint issues (enum).

```python
class LintLevel(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
```

---

### `Publisher`

HTML publisher using XSLT transformation.

```python
class Publisher:
    def __init__(
        self,
        xslt_dir: Path,
        telemetry: TelemetrySink | None = None,
    )

    def publish_project(self, project_path: Path, output_dir: Path) -> PublishResult
    def publish_file(self, xml_file: Path, output_file: Path) -> PublishResult
```

---

### `PublishResult`

Result of publishing operations (dataclass).

```python
@dataclass
class PublishResult:
    success: bool
    files: list[Path]
    error: str | None
```

## Enums and Types

### `MathPolicy`

Policy for handling mathematical XML content.

```python
class MathPolicy(str, Enum):
    SANITIZE = "sanitize"  # Clean problematic content (recommended)
    SKIP = "skip"          # Skip files with math content
    ERROR = "error"        # Raise errors on math content
```

**Example:**
```python
from xml_lib import validate_xml, MathPolicy

result = validate_xml("project", math_policy=MathPolicy.SKIP)
```

---

### `TelemetrySink`

Abstract base for telemetry backends.

```python
class TelemetrySink(Protocol):
    def log_validation(
        self,
        project_name: str,
        success: bool,
        duration_ms: float,
        file_count: int,
        error_count: int,
        warning_count: int,
    ) -> None

    def log_publish(
        self,
        project_name: str,
        success: bool,
        duration_ms: float,
        output_files: int,
    ) -> None

    def log_event(self, event_type: str, data: dict) -> None
```

---

### `FileTelemetrySink`

File-based telemetry backend (JSON Lines format).

```python
class FileTelemetrySink(TelemetrySink):
    def __init__(self, file_path: Path)
```

**Example:**
```python
from xml_lib import validate_xml, FileTelemetrySink
from pathlib import Path

telemetry = FileTelemetrySink(Path("metrics.jsonl"))
result = validate_xml("project", telemetry=telemetry)
```

## Pipeline Automation

For batch processing workflows (optional module).

```python
from xml_lib import PipelineEngine, load_pipeline

# Load pipeline from YAML
pipeline = load_pipeline("templates/ci-validation.yaml")

# Execute with context
engine = PipelineEngine()
result = engine.execute(pipeline, {"input_dir": "project"})
```

See [PIPELINE_GUIDE.md](PIPELINE_GUIDE.md) for details.

## CLI Usage

All functionality is also available via command-line:

```bash
# Validate XML files
xml-lib validate my-project

# Lint for issues
xml-lib lint my-project

# Publish to HTML
xml-lib publish my-project --output-dir output/

# Interactive shell
xml-lib shell

# Pipeline execution
xml-lib pipeline run templates/ci-validation.yaml
```

## Error Handling

The library uses **result objects** (ValidationResult, LintResult, PublishResult) to report per-file issues, and **exceptions** only for "cannot even start" conditions like missing files or misconfiguration.

```python
from xml_lib import quick_validate, FileNotFoundError

try:
    result = quick_validate("nonexistent")
except FileNotFoundError as e:
    print(f"Project not found: {e}")

result = quick_validate("project")

# Errors are in result.errors, not raised as exceptions
if not result.is_valid:
    for error in result.errors:
        print(f"{error.file}:{error.line} - {error.message}")
```

## Type Stability Guarantees

All types in the public API (`ValidationResult`, `ValidationError`, `LintResult`, etc.) are considered stable. The library includes tests to ensure these types don't change unexpectedly:

```python
# These assertions are tested in tests/test_api.py
assert hasattr(ValidationResult, 'is_valid')
assert hasattr(ValidationResult, 'errors')
assert hasattr(ValidationError, 'file')
assert hasattr(ValidationError, 'line')
```

## Next Steps

- See [README.md](../README.md) for overview and examples
- See [PIPELINE_GUIDE.md](PIPELINE_GUIDE.md) for automation
- See [STREAMING_GUIDE.md](STREAMING_GUIDE.md) for large file handling
- See [INTERACTIVE_GUIDE.md](INTERACTIVE_GUIDE.md) for the REPL shell

---

**Version:** 0.1.0
**Last Updated:** 2025-11-13
