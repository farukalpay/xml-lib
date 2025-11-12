# Example 1: Basic XML Validation Pipeline

This example demonstrates a simple validation pipeline that checks XML documents against schemas and generates a validation report.

## What This Example Does

1. Validates XML input against RelaxNG schema
2. Checks Schematron business rules
3. Generates an HTML validation report
4. Creates a JSON summary for tooling integration

## Files

- `pipeline.yaml` - Pipeline definition
- `input/sample-valid.xml` - Valid XML document
- `input/sample-invalid.xml` - Invalid XML document (for testing)
- `run.sh` - Script to run the example

## Pipeline Stages

1. **validate_input** - ValidateStage
   - Validates against schemas in `../../schemas/`
   - Strict mode enabled (warnings are errors)

2. **generate_html_report** - OutputStage
   - Creates HTML validation report
   - Output: `output/validation-report.html`

3. **generate_json_summary** - OutputStage
   - Creates JSON summary for CI/CD tools
   - Output: `output/summary.json`

## Running the Example

### Using the script:

```bash
./run.sh
```

### Manually:

```bash
# Validate a valid document
xml-lib pipeline run pipeline.yaml input/sample-valid.xml

# Validate an invalid document (will fail)
xml-lib pipeline run pipeline.yaml input/sample-invalid.xml
```

### Dry run (preview stages):

```bash
xml-lib pipeline dry-run pipeline.yaml input/sample-valid.xml
```

## Expected Output

### For valid XML:

```
🔄 Running pipeline: pipeline.yaml
   Input: input/sample-valid.xml

============================================================
Pipeline: basic_validation
Status: ✅ SUCCESS
Duration: 0.32s
Stages executed: 3
Stages failed: 0
============================================================
```

Files created:
- `output/validation-report.html` - Green checkmark, "All checks passed"
- `output/summary.json` - `{"valid": true, "errors": 0, "warnings": 0}`

### For invalid XML:

```
🔄 Running pipeline: pipeline.yaml
   Input: input/sample-invalid.xml

============================================================
Pipeline: basic_validation
Status: ❌ FAILED
Duration: 0.18s
Stages executed: 1
Stages failed: 1
============================================================

Stage Results:
  ❌ validate_input (0.18s)
     Error: Validation failed: 3 errors
```

## Key Concepts Demonstrated

1. **YAML Pipeline Definition**: Declarative workflow definition
2. **Fail-Fast Error Strategy**: Stop on first validation error
3. **Multiple Output Formats**: HTML for humans, JSON for machines
4. **Schema Validation**: Leveraging xml-lib's validation engine

## Customization

### Change error handling:

```yaml
# Continue even if validation fails (useful for collecting all errors)
error_strategy: continue
```

### Add more output formats:

```yaml
stages:
  # ... existing stages ...

  - type: output
    name: generate_xml_report
    format: xml
    output_path: output/report.xml
```

### Add custom validation logic:

```python
# In custom-validation.py
def custom_check(context):
    # Add your business logic
    tree = context.xml_tree
    if not tree.find(".//required-field"):
        raise ValueError("Missing required field")
    return StageResult(stage="custom_check", success=True)

# Use with CustomStage in Python API
```

## Troubleshooting

### "Pipeline validation failed: Transform file not found"

Make sure you're running from the example directory:

```bash
cd examples/pipelines/01-basic-validation
xml-lib pipeline run pipeline.yaml input/sample-valid.xml
```

### "No module named 'xml_lib'"

Install xml-lib:

```bash
pip install xml-lib
# Or from source:
pip install -e ../../..
```

## Next Steps

- **Example 2**: [Multi-Format Publishing](../02-multi-format-output/) - Transform XML to multiple formats
- **Documentation**: [Pipeline Guide](../../../docs/PIPELINE_GUIDE.md) - Complete guide
- **Templates**: [Pipeline Templates](../../../templates/pipelines/) - Pre-built workflows
