# Migration Guide

This document describes changes that may affect existing users and how to migrate to newer versions.

## Unreleased → Current

### Summary
This release focuses on developer experience, performance, and security hardening. **No breaking changes** to existing APIs or CLI commands. All new features are opt-in.

### New CLI Commands

#### `xml-lib lint` (New)
Lint XML files for formatting and security issues.

```bash
# Lint a single file
xml-lib lint path/to/file.xml

# Lint a directory recursively
xml-lib lint path/to/directory/

# Output as JSON for CI/CD
xml-lib lint . --format json

# Treat warnings as failures
xml-lib lint . --fail-level warning
```

**Common use cases:**
- Pre-commit hooks: `xml-lib lint . --fail-level warning`
- CI/CD pipelines: `xml-lib lint . --format json --fail-level error`
- Local development: `xml-lib lint . --no-check-attribute-order`

### Enhanced Existing Commands

#### `xml-lib validate` (Enhanced)

**New options:**
```bash
# Get machine-readable JSON output
xml-lib validate project/ --format json

# Treat warnings as errors
xml-lib validate project/ --fail-level warning

# Enable streaming for large files
xml-lib validate project/ --streaming --streaming-threshold 5242880  # 5MB

# Show progress indicator
xml-lib validate project/ --progress
```

**Migration notes:**
- Default behavior unchanged - all new options are opt-in
- `--strict` flag still works (equivalent to `--fail-level warning`)
- JSON format includes all validation details for programmatic access

#### `xml-lib diff` (Enhanced)

**New options:**
```bash
# Get JSON output for automated processing
xml-lib diff file1.xml file2.xml --format json
```

**Migration notes:**
- Text output format unchanged
- JSON output adds machine-readable format without affecting text mode

#### `xml-lib phpify` (Enhanced)

**New option:**
```bash
# Explicitly allow external entities (security risk!)
xml-lib phpify input.xml --allow-xxe
```

**IMPORTANT SECURITY NOTE:**
The `--allow-xxe` flag is **OFF by default**. This is intentional and recommended.

**If you were relying on external entity resolution:**
1. Review if you actually need external entities
2. If yes, add `--allow-xxe` flag explicitly
3. Only use with trusted XML sources
4. Consider alternative approaches that don't require external entities

```bash
# Old behavior (if you need XXE)
xml-lib phpify input.xml

# New behavior (explicit opt-in)
xml-lib phpify input.xml --allow-xxe  # Shows warning
```

### Configuration Changes

#### Validator Class (Python API)

**New optional parameters:**
```python
from xml_lib.validator import Validator

# Enable streaming validation
validator = Validator(
    schemas_dir=Path("schemas"),
    guardrails_dir=Path("guardrails"),
    use_streaming=True,              # New: Enable streaming
    streaming_threshold_bytes=10_000_000,  # New: 10MB threshold
    show_progress=True,               # New: Show progress
)
```

**Migration notes:**
- All parameters are optional with safe defaults
- Existing code continues to work without changes
- `use_streaming=False` by default (opt-in for performance)
- `show_progress=False` by default (opt-in for visibility)

#### ParseConfig Class (Python API)

**New parameter:**
```python
from xml_lib.php.parser import ParseConfig

# Explicitly allow XXE (not recommended)
config = ParseConfig(
    max_size_bytes=10_000_000,
    allow_xxe=True,  # New: Default is False
)
```

**Migration notes:**
- `allow_xxe=False` by default (secure by default)
- If you need external entities, set `allow_xxe=True` explicitly
- Consider security implications before enabling

### Testing and CI/CD Integration

#### New JSON Output Formats

**Validation JSON format:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "files": ["file1.xml", "file2.xml"],
  "summary": {
    "error_count": 0,
    "warning_count": 0,
    "file_count": 2
  }
}
```

**Lint JSON format:**
```json
{
  "files_checked": 5,
  "issues": [
    {
      "level": "warning",
      "message": "Attributes not in alphabetical order",
      "file": "example.xml",
      "line": 3,
      "column": null,
      "rule": "attribute-order"
    }
  ],
  "summary": {
    "error_count": 0,
    "warning_count": 1,
    "info_count": 0
  }
}
```

**Diff JSON format:**
```json
{
  "identical": false,
  "difference_count": 2,
  "differences": [
    {
      "type": "modified",
      "path": "/root/element/@attr",
      "old_value": "old",
      "new_value": "new",
      "explanation": "Attribute 'attr' value changed"
    }
  ]
}
```

#### GitHub Actions Integration

```yaml
# Example: Add linting to CI
- name: Lint XML files
  run: xml-lib lint . --format json --fail-level warning

# Example: Validate with progress
- name: Validate XML
  run: xml-lib validate project/ --format json --progress

# Example: Check for differences
- name: Compare XML files
  run: xml-lib diff before.xml after.xml --format json
```

### Performance Considerations

#### When to Use Streaming

Enable streaming validation (`--streaming`) when:
- XML files are > 10MB (configurable with `--streaming-threshold`)
- Memory usage is a concern
- Processing very large document collections

**Note:** Streaming adds slight overhead for small files, so it's opt-in.

#### When to Show Progress

Enable progress reporting (`--progress`) when:
- Running validation interactively
- Processing many files (>10)
- Long-running validation tasks

**Note:** Progress automatically disabled for non-TTY outputs (pipes, redirects).

### Backward Compatibility

✅ **All existing scripts and integrations continue to work without modification.**

- No breaking changes to CLI commands or flags
- No breaking changes to Python API
- Existing behavior preserved by default
- New features are opt-in via explicit flags

### Deprecation Notice

None. No features have been deprecated in this release.

### Recommended Actions

1. **Add linting to your workflow:**
   ```bash
   xml-lib lint . --fail-level warning
   ```

2. **Use JSON output in CI/CD:**
   ```bash
   xml-lib validate . --format json > validation-results.json
   ```

3. **Review XXE usage:**
   - If you use `phpify` with external entities, add `--allow-xxe` flag
   - Consider if external entities are truly necessary

4. **Try progress reporting:**
   ```bash
   xml-lib validate large-project/ --progress
   ```

5. **Enable streaming for large files:**
   ```bash
   xml-lib validate huge-dataset/ --streaming
   ```

### Getting Help

- Run `xml-lib lint --help` for all linting options
- Run `xml-lib validate --help` for enhanced validation options
- Run `xml-lib phpify --help` for security-related options
- Check the updated README.md for examples and best practices
