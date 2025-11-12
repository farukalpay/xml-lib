# XML Pipeline Automation - Design Document

## Overview

The XML Pipeline system provides a declarative, composable framework for chaining XML operations (validation, transformation, output) with built-in error recovery, rollback, and templating.

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Pipeline                                 │
│  - stages: List[Stage]                                      │
│  - context: PipelineContext                                 │
│  - error_strategy: ErrorStrategy                           │
│  - rollback_enabled: bool                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ contains
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Stage (Abstract)                        │
│  + execute(context) -> StageResult                          │
│  + rollback(context) -> None                                │
│  + validate_input(context) -> bool                          │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┬──────────────┐
        │                   │                   │              │
┌───────▼────────┐  ┌──────▼─────────┐  ┌─────▼──────┐  ┌───▼────────┐
│ ValidateStage  │  │ TransformStage │  │OutputStage │  │CustomStage │
│ - schemas      │  │ - xslt/python  │  │ - format   │  │ - function │
│ - guardrails   │  │ - params       │  │ - target   │  │ - rollback │
│ - strict       │  │                │  │            │  │            │
└────────────────┘  └────────────────┘  └────────────┘  └────────────┘
```

### Pipeline Context

```python
@dataclass
class PipelineContext:
    """Execution context passed between stages."""

    # Current XML data
    xml_data: str
    xml_tree: Optional[etree._Element] = None

    # File paths
    input_path: Optional[Path] = None
    output_path: Optional[Path] = None
    working_dir: Path = field(default_factory=lambda: Path.cwd())

    # State tracking
    stage_results: List[StageResult] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)

    # Rollback state
    snapshots: List[Tuple[str, str]] = field(default_factory=list)  # (stage_name, xml_data)

    # Metadata
    start_time: datetime = field(default_factory=datetime.now)
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
```

### Error Strategies

```python
class ErrorStrategy(Enum):
    """Error handling strategies."""
    FAIL_FAST = "fail_fast"           # Stop on first error
    CONTINUE = "continue"              # Log error, continue pipeline
    ROLLBACK = "rollback"              # Rollback to last snapshot
    RETRY = "retry"                    # Retry stage with exponential backoff
    SKIP = "skip"                      # Skip failed stage, continue
```

### Stage Types

#### 1. ValidateStage

```python
class ValidateStage(Stage):
    """Validates XML against schemas and guardrails."""

    def __init__(
        self,
        schemas_dir: Optional[Path] = None,
        guardrails_dir: Optional[Path] = None,
        strict: bool = True,
        streaming: bool = False,
        name: Optional[str] = None
    ):
        ...

    def execute(self, context: PipelineContext) -> StageResult:
        # Use existing validator.py
        from xml_lib.validator import Validator
        validator = Validator(schemas_dir, guardrails_dir)
        result = validator.validate(context.xml_tree)
        return StageResult(
            stage=self.name,
            success=result.success,
            data=context.xml_data,
            metadata=result.to_dict()
        )
```

#### 2. TransformStage

```python
class TransformStage(Stage):
    """Transforms XML using XSLT or Python functions."""

    def __init__(
        self,
        transform: Union[Path, Callable],
        params: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None
    ):
        ...

    def execute(self, context: PipelineContext) -> StageResult:
        if isinstance(self.transform, Path):
            # XSLT transformation
            xslt_tree = etree.parse(str(self.transform))
            transform = etree.XSLT(xslt_tree)
            result_tree = transform(context.xml_tree, **self.params)
            transformed = str(result_tree)
        else:
            # Python function
            transformed = self.transform(context.xml_data, context)

        context.xml_data = transformed
        context.xml_tree = etree.fromstring(transformed.encode())
        return StageResult(stage=self.name, success=True, data=transformed)
```

#### 3. OutputStage

```python
class OutputStage(Stage):
    """Outputs XML to various formats."""

    def __init__(
        self,
        format: str,  # 'html', 'pptx', 'php', 'json', 'xml'
        output_path: Path,
        template: Optional[Path] = None,
        name: Optional[str] = None
    ):
        ...

    def execute(self, context: PipelineContext) -> StageResult:
        # Use existing publishers
        if self.format == 'html':
            from xml_lib.publisher import publish
            publish(context.xml_tree, output_path, template)
        elif self.format == 'pptx':
            from xml_lib.pptx_composer import compose_pptx
            compose_pptx(context.xml_tree, output_path)
        # ...etc
```

#### 4. CustomStage

```python
class CustomStage(Stage):
    """User-defined stage with custom logic."""

    def __init__(
        self,
        function: Callable[[PipelineContext], StageResult],
        rollback_function: Optional[Callable] = None,
        name: Optional[str] = None
    ):
        ...
```

### Pipeline Definition

#### Programmatic API

```python
from xml_lib.pipeline import Pipeline, ValidateStage, TransformStage, OutputStage

pipeline = Pipeline(
    name="soap_validation",
    error_strategy=ErrorStrategy.ROLLBACK,
    rollback_enabled=True
)

pipeline.add_stage(
    ValidateStage(
        schemas_dir=Path("schemas/soap"),
        strict=True,
        name="validate_soap"
    )
)

pipeline.add_stage(
    TransformStage(
        transform=Path("transforms/enrich_soap.xsl"),
        params={"timestamp": datetime.now().isoformat()},
        name="enrich"
    )
)

pipeline.add_stage(
    ValidateStage(
        schemas_dir=Path("schemas/soap"),
        name="validate_enriched"
    )
)

pipeline.add_stage(
    OutputStage(
        format="html",
        output_path=Path("out/soap_report.html"),
        name="generate_report"
    )
)

# Execute
result = pipeline.execute(input_xml="data/soap_request.xml")
```

#### Declarative YAML

```yaml
name: soap_validation
description: Validate and enrich SOAP messages
error_strategy: rollback
rollback_enabled: true

stages:
  - type: validate
    name: validate_soap
    schemas_dir: schemas/soap
    strict: true

  - type: transform
    name: enrich
    transform: transforms/enrich_soap.xsl
    params:
      timestamp: "${NOW}"
      version: "1.0"

  - type: validate
    name: validate_enriched
    schemas_dir: schemas/soap

  - type: output
    name: generate_report
    format: html
    output_path: out/soap_report.html

variables:
  NOW: "{{ datetime.now().isoformat() }}"
```

### Pipeline Templates

Pre-built templates for common use cases:

1. **SOAP Pipeline** (`templates/soap.yaml`)
   - Validate SOAP envelope
   - Extract body
   - Transform to internal format
   - Validate transformed
   - Generate response

2. **RSS Feed Pipeline** (`templates/rss.yaml`)
   - Validate RSS 2.0 schema
   - Transform dates to ISO format
   - Add channel metadata
   - Validate enriched feed
   - Output to multiple formats

3. **Config File Pipeline** (`templates/config.yaml`)
   - Validate against schema
   - Resolve includes/imports
   - Apply environment-specific overrides
   - Validate merged config
   - Output to deployment format

4. **Migration Pipeline** (`templates/migration.yaml`)
   - Validate source schema
   - Transform to target schema
   - Validate target schema
   - Generate diff report
   - Archive original

5. **CI/CD Validation** (`templates/ci.yaml`)
   - Pre-commit validation
   - Schema compatibility check
   - Security linting (XXE, external entities)
   - Generate quality report
   - Update metrics

## Error Recovery & Rollback

### Snapshot System

```python
class Pipeline:
    def _create_snapshot(self, context: PipelineContext, stage_name: str):
        """Create a snapshot before executing a stage."""
        if self.rollback_enabled:
            context.snapshots.append((stage_name, context.xml_data))

    def _rollback_to_stage(self, context: PipelineContext, stage_name: str):
        """Rollback to a specific stage's snapshot."""
        for i, (name, data) in enumerate(reversed(context.snapshots)):
            if name == stage_name:
                context.xml_data = data
                context.xml_tree = etree.fromstring(data.encode())
                # Remove subsequent snapshots
                context.snapshots = context.snapshots[:-(i+1)]
                return True
        return False

    def _execute_with_recovery(self, stage: Stage, context: PipelineContext):
        """Execute stage with error recovery."""
        self._create_snapshot(context, stage.name)

        try:
            result = stage.execute(context)
            context.stage_results.append(result)
            return result

        except Exception as e:
            if self.error_strategy == ErrorStrategy.FAIL_FAST:
                raise

            elif self.error_strategy == ErrorStrategy.ROLLBACK:
                self._rollback_to_stage(context, stage.name)
                raise PipelineError(f"Stage {stage.name} failed, rolled back")

            elif self.error_strategy == ErrorStrategy.RETRY:
                return self._retry_stage(stage, context)

            elif self.error_strategy == ErrorStrategy.SKIP:
                result = StageResult(
                    stage=stage.name,
                    success=False,
                    error=str(e),
                    data=context.xml_data
                )
                context.stage_results.append(result)
                return result

            elif self.error_strategy == ErrorStrategy.CONTINUE:
                logging.error(f"Stage {stage.name} failed: {e}")
                result = StageResult(
                    stage=stage.name,
                    success=False,
                    error=str(e),
                    data=context.xml_data
                )
                context.stage_results.append(result)
                return result
```

### Retry Logic

```python
def _retry_stage(
    self,
    stage: Stage,
    context: PipelineContext,
    max_retries: int = 3,
    backoff_factor: float = 2.0
) -> StageResult:
    """Retry stage with exponential backoff."""
    for attempt in range(max_retries):
        try:
            result = stage.execute(context)
            context.stage_results.append(result)
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = backoff_factor ** attempt
            logging.warning(
                f"Stage {stage.name} failed (attempt {attempt + 1}/{max_retries}), "
                f"retrying in {wait_time}s: {e}"
            )
            time.sleep(wait_time)
```

## CLI Integration

```bash
# Execute pipeline from YAML
xml-lib pipeline run templates/soap.yaml input.xml

# Execute with overrides
xml-lib pipeline run templates/soap.yaml input.xml \
  --var "timestamp=$(date -Iseconds)" \
  --output-dir out/

# List available templates
xml-lib pipeline list

# Validate pipeline definition
xml-lib pipeline validate templates/soap.yaml

# Dry run (show stages without executing)
xml-lib pipeline dry-run templates/soap.yaml input.xml

# Watch mode (re-run on file changes)
xml-lib pipeline watch templates/soap.yaml input.xml
```

## Performance Considerations

1. **Streaming Support**: For large files, automatically use streaming validation
2. **Parallel Stages**: Execute independent stages in parallel (future enhancement)
3. **Caching**: Cache parsed schemas and XSLT transforms
4. **Memory Management**: Limit snapshot history, use tempfiles for large intermediates

## Testing Strategy

1. **Unit Tests**: Each stage type, error strategies, rollback
2. **Integration Tests**: Full pipelines with real XML
3. **Property-Based Tests**: Pipeline invariants (idempotency, rollback correctness)
4. **Performance Tests**: Large file handling, memory usage
5. **Template Tests**: All templates work correctly

## Implementation Phases

1. ✅ Design architecture (this document)
2. Core pipeline engine (`xml_lib/pipeline/engine.py`)
3. Stage implementations (`xml_lib/pipeline/stages.py`)
4. YAML loader (`xml_lib/pipeline/loader.py`)
5. CLI commands (`xml_lib/cli.py` additions)
6. Templates (`templates/*.yaml`)
7. Tests (`tests/test_pipeline*.py`)
8. Documentation (`docs/PIPELINE_GUIDE.md`)
9. Examples (`examples/pipelines/`)

## Success Metrics

- ✅ Support chaining 3+ stages
- ✅ Error recovery works for all strategies
- ✅ Rollback restores correct state
- ✅ Templates cover 5+ common use cases
- ✅ >90% test coverage
- ✅ Performance overhead <10% vs direct execution
- ✅ Memory usage stays constant for streaming mode
