"""Main CLI entry point for xml-lib."""

import json
import sys
from pathlib import Path

import click

from xml_lib.differ import Differ
from xml_lib.linter import XMLLinter
from xml_lib.php.generator import GeneratorConfig, PHPGenerator
from xml_lib.php.ir import IRBuilder
from xml_lib.php.parser import ParseConfig, SecureXMLParser
from xml_lib.pptx_composer import PPTXComposer
from xml_lib.publisher import Publisher
from xml_lib.sanitize import MathPolicy, Sanitizer
from xml_lib.telemetry import TelemetrySink
from xml_lib.validator import Validator


@click.group()
@click.version_option(version="0.1.0")
@click.option(
    "--telemetry",
    type=click.Choice(["file", "sqlite", "postgres", "none"]),
    default="file",
    help="Telemetry sink backend",
)
@click.option("--telemetry-target", help="Telemetry target (file path, db connection)")
@click.pass_context
def main(ctx: click.Context, telemetry: str, telemetry_target: str | None) -> None:
    """XML-Lifecycle Validator & Publisher.

    Validates and publishes XML documents following the canonical lifecycle chain:
    begin → start → iteration → end → continuum
    """
    ctx.ensure_object(dict)

    # Initialize telemetry
    if telemetry != "none":
        ctx.obj["telemetry"] = TelemetrySink.create(
            backend=telemetry, target=telemetry_target or f"out/telemetry.{telemetry}"
        )
    else:
        ctx.obj["telemetry"] = None


@main.command()
@click.argument("project_path", type=click.Path(exists=True))
@click.option("--schemas-dir", default="schemas", help="Directory containing schemas")
@click.option("--guardrails-dir", default="guardrails", help="Directory containing guardrails")
@click.option("--output", "-o", default="out/assertions.xml", help="Output assertions file")
@click.option("--jsonl", default="out/assertions.jsonl", help="JSON Lines output for CI")
@click.option("--strict", is_flag=True, help="Fail on warnings")
@click.option(
    "--math-policy",
    type=click.Choice(["sanitize", "mathml", "skip", "error"]),
    default="sanitize",
    help="Policy for handling mathy XML (default: sanitize)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format (default: text)",
)
@click.option(
    "--fail-level",
    type=click.Choice(["warning", "error"]),
    default="error",
    help="Treat warnings as errors (default: error)",
)
@click.option(
    "--streaming/--no-streaming",
    default=False,
    help="Use streaming validation for large files (default: off)",
)
@click.option(
    "--streaming-threshold",
    type=int,
    default=10 * 1024 * 1024,
    help="File size threshold for streaming in bytes (default: 10MB)",
)
@click.option(
    "--progress/--no-progress",
    default=False,
    help="Show progress indicator (default: off)",
)
@click.pass_context
def validate(
    ctx: click.Context,
    project_path: str,
    schemas_dir: str,
    guardrails_dir: str,
    output: str,
    jsonl: str,
    strict: bool,
    math_policy: str,
    output_format: str,
    fail_level: str,
    streaming: bool,
    streaming_threshold: int,
    progress: bool,
) -> None:
    """Validate XML documents against lifecycle schemas and guardrails.

    Validates the canonical chain (begin → start → iteration → end → continuum)
    using Relax NG + Schematron with cross-file constraints.
    """
    # Handle --strict and --fail-level interaction
    treat_warnings_as_errors = strict or fail_level == "warning"

    if output_format == "text" and not progress:
        click.echo(f"🔍 Validating project: {project_path}")

    policy = MathPolicy(math_policy)
    validator = Validator(
        schemas_dir=Path(schemas_dir),
        guardrails_dir=Path(guardrails_dir),
        telemetry=ctx.obj.get("telemetry"),
        math_policy=policy,
        use_streaming=streaming,
        streaming_threshold_bytes=streaming_threshold,
        show_progress=progress,
    )
    result = validator.validate_project(Path(project_path), math_policy=policy)

    # Write assertions
    validator.write_assertions(result, Path(output), Path(jsonl))

    # Format output
    if output_format == "json":
        output_data = {
            "valid": result.is_valid,
            "errors": [
                {
                    "file": err.file,
                    "line": err.line,
                    "column": err.column,
                    "message": err.message,
                    "type": err.type,
                    "rule": err.rule,
                }
                for err in result.errors
            ],
            "warnings": [
                {
                    "file": warn.file,
                    "line": warn.line,
                    "column": warn.column,
                    "message": warn.message,
                    "type": warn.type,
                    "rule": warn.rule,
                }
                for warn in result.warnings
            ],
            "files": result.validated_files,
            "summary": {
                "error_count": len(result.errors),
                "warning_count": len(result.warnings),
                "file_count": len(result.validated_files),
            },
        }
        click.echo(json.dumps(output_data, indent=2))
    else:
        # Text output
        if result.is_valid:
            click.echo("✅ Validation passed")
        else:
            click.echo(
                f"❌ Validation failed: {len(result.errors)} errors, {len(result.warnings)} warnings"
            )
            for error in result.errors[:10]:  # Show first 10
                click.echo(f"  ERROR: {error}")
            if treat_warnings_as_errors and result.warnings:
                click.echo(f"❌ Treating {len(result.warnings)} warnings as errors")
                for warning in result.warnings[:10]:  # Show first 10
                    click.echo(f"  WARNING: {warning}")

    # Exit code logic
    if result.errors or treat_warnings_as_errors and result.warnings:
        sys.exit(1)
    else:
        sys.exit(0)


@main.command()
@click.argument("project_path", type=click.Path(exists=True))
@click.option("--output-dir", "-o", default="out/site", help="Output directory for HTML")
@click.option("--xslt-dir", default="schemas/xslt", help="Directory containing XSLT templates")
@click.option("--strict", is_flag=True, help="Fail fast on XML parse errors")
@click.option(
    "--math-policy",
    type=click.Choice(["sanitize", "mathml", "skip", "error"]),
    default="sanitize",
    help="Policy for handling mathy XML (default: sanitize)",
)
@click.pass_context
def publish(
    ctx: click.Context,
    project_path: str,
    output_dir: str,
    xslt_dir: str,
    strict: bool,
    math_policy: str,
) -> None:
    """Publish XML documents to HTML using XSLT 3.0.

    Renders human-readable documentation to HTML.
    """
    click.echo(f"📝 Publishing project: {project_path}")

    publisher = Publisher(
        xslt_dir=Path(xslt_dir),
        telemetry=ctx.obj.get("telemetry"),
    )

    policy = MathPolicy(math_policy)
    result = publisher.publish(
        Path(project_path), Path(output_dir), strict=strict, math_policy=policy
    )

    if result.success:
        click.echo(f"✅ Published to {output_dir}")
        click.echo(f"   Generated {len(result.files)} files")
        sys.exit(0)
    else:
        click.echo(f"❌ Publishing failed: {result.error}")
        sys.exit(1)


@main.command()
@click.argument("xml_file", type=click.Path(exists=True))
@click.option("--template", help="PowerPoint template file")
@click.option("--output", "-o", required=True, help="Output .pptx file")
@click.pass_context
def render_pptx(
    ctx: click.Context,
    xml_file: str,
    template: str | None,
    output: str,
) -> None:
    """Render XML guidance to PowerPoint presentation.

    Maps XML to .pptx templates with slide masters, tables, and citations.
    """
    click.echo(f"📊 Rendering PowerPoint: {xml_file}")

    composer = PPTXComposer(
        template=Path(template) if template else None,
        telemetry=ctx.obj.get("telemetry"),
    )

    result = composer.render(Path(xml_file), Path(output))

    if result.success:
        click.echo(f"✅ PowerPoint created: {output}")
        click.echo(f"   {result.slide_count} slides, {result.citation_count} citations")
        sys.exit(0)
    else:
        click.echo(f"❌ Rendering failed: {result.error}")
        sys.exit(1)


@main.command()
@click.argument("file1", type=click.Path(exists=True))
@click.argument("file2", type=click.Path(exists=True))
@click.option("--explain", is_flag=True, help="Provide detailed explanations")
@click.option("--schemas-dir", default="schemas", help="Directory containing schemas")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format (default: text)",
)
@click.pass_context
def diff(
    ctx: click.Context,
    file1: str,
    file2: str,
    explain: bool,
    schemas_dir: str,
    output_format: str,
) -> None:
    """Schema-aware structural diff between two XML files.

    Compares XML documents with understanding of lifecycle semantics.
    """
    if output_format == "text":
        click.echo(f"🔎 Comparing: {file1} ↔ {file2}")

    differ = Differ(
        schemas_dir=Path(schemas_dir),
        telemetry=ctx.obj.get("telemetry"),
    )

    result = differ.diff(Path(file1), Path(file2), explain=explain)

    if output_format == "json":
        output_data = {
            "identical": result.identical,
            "difference_count": len(result.differences),
            "differences": [
                {
                    "type": diff.type.value,
                    "path": diff.path,
                    "old_value": diff.old_value,
                    "new_value": diff.new_value,
                    "explanation": diff.explanation,
                }
                for diff in result.differences
            ],
        }
        click.echo(json.dumps(output_data, indent=2))
    else:
        # Text output
        if result.identical:
            click.echo("✅ Files are identical")
        else:
            click.echo(f"📋 Found {len(result.differences)} differences:")
            for diff in result.differences:
                click.echo(f"\n{diff.format(explain=explain)}")

    sys.exit(0 if result.identical else 1)


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--recursive/--no-recursive", default=True, help="Recursively scan directories")
@click.option(
    "--check-indentation/--no-check-indentation",
    default=True,
    help="Check for consistent indentation",
)
@click.option(
    "--check-attribute-order/--no-check-attribute-order",
    default=True,
    help="Check for alphabetically sorted attributes",
)
@click.option(
    "--check-external-entities/--no-check-external-entities",
    default=True,
    help="Check for XXE vulnerabilities",
)
@click.option(
    "--check-formatting/--no-check-formatting",
    default=True,
    help="Check for general formatting issues",
)
@click.option("--indent-size", default=2, type=int, help="Expected indentation size (spaces)")
@click.option(
    "--allow-xxe",
    is_flag=True,
    help="Allow external entities (WARNING: security risk)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format (default: text)",
)
@click.option(
    "--fail-level",
    type=click.Choice(["info", "warning", "error"]),
    default="error",
    help="Minimum level to trigger failure (default: error)",
)
def lint(
    path: str,
    recursive: bool,
    check_indentation: bool,
    check_attribute_order: bool,
    check_external_entities: bool,
    check_formatting: bool,
    indent_size: int,
    allow_xxe: bool,
    output_format: str,
    fail_level: str,
) -> None:
    """Lint XML files for formatting and security issues.

    Checks for:
    - Consistent indentation and formatting
    - Alphabetically ordered attributes
    - External entity declarations (XXE vulnerabilities)
    - Trailing whitespace and line length
    """
    path_obj = Path(path)

    if output_format == "text":
        click.echo(f"🔍 Linting: {path}")

    linter = XMLLinter(
        check_indentation=check_indentation,
        check_attribute_order=check_attribute_order,
        check_external_entities=check_external_entities,
        check_formatting=check_formatting,
        indent_size=indent_size,
        allow_xxe=allow_xxe,
    )

    # Lint file or directory
    if path_obj.is_file():
        result = linter.lint_file(path_obj)
    else:
        result = linter.lint_directory(path_obj, recursive=recursive)

    # Format output
    if output_format == "json":
        output_data = {
            "files_checked": result.files_checked,
            "issues": [issue.to_dict() for issue in result.issues],
            "summary": {
                "error_count": result.error_count,
                "warning_count": result.warning_count,
                "info_count": len(result.issues) - result.error_count - result.warning_count,
            },
        }
        click.echo(json.dumps(output_data, indent=2))
    else:
        # Text output
        if not result.issues:
            click.echo(f"✅ All {result.files_checked} files passed linting")
        else:
            click.echo(
                f"\n📋 Found {len(result.issues)} issues in {result.files_checked} files:"
            )
            click.echo(
                f"   Errors: {result.error_count}, Warnings: {result.warning_count}, Info: {len(result.issues) - result.error_count - result.warning_count}"
            )
            click.echo()

            for issue in result.issues:
                click.echo(issue.format_text())

    # Determine exit code based on fail-level
    should_fail = False
    if fail_level == "error" and result.error_count > 0 or fail_level == "warning" and (result.error_count > 0 or result.warning_count > 0) or fail_level == "info" and len(result.issues) > 0:
        should_fail = True

    sys.exit(1 if should_fail else 0)


@main.command()
@click.option("--restore", required=True, help="Sanitized XML file to restore")
@click.option("--mapping", help="Mapping file (auto-detected if not provided)")
@click.option("--output", "-o", required=True, help="Output file for restored XML")
@click.pass_context
def roundtrip(
    ctx: click.Context,
    restore: str,
    mapping: str | None,
    output: str,
) -> None:
    """Restore original mathy markup from sanitized XML.

    Reconstructs the original XML with mathematical symbols in element names
    using the mapping file generated during sanitization.
    """
    click.echo(f"🔄 Restoring: {restore}")

    sanitizer = Sanitizer(Path("out"))

    # Auto-detect mapping file if not provided
    if not mapping:
        restore_path = Path(restore)
        mapping_path = Path("out/mappings") / f"{restore_path.name}.mathmap.jsonl"
        if not mapping_path.exists():
            click.echo(f"❌ Mapping file not found: {mapping_path}")
            sys.exit(1)
    else:
        mapping_path = Path(mapping)

    try:
        sanitizer.restore(Path(restore), mapping_path, Path(output))
        click.echo(f"✅ Restored to {output}")
        sys.exit(0)
    except Exception as e:
        click.echo(f"❌ Restoration failed: {e}")
        sys.exit(1)


@main.command()
@click.argument("xml_file", type=click.Path(exists=True))
@click.option("--output", "-o", help="Output PHP file (default: <input-basename>.php)")
@click.option(
    "--template",
    type=click.Choice(["default", "minimal"]),
    default="default",
    help="Template to use",
)
@click.option("--title", help="Override document title")
@click.option("--favicon", help="Favicon URL or path")
@click.option("--assets-dir", default="assets", help="Assets directory for CSS/images")
@click.option("--no-toc", is_flag=True, help="Disable table of contents")
@click.option("--no-css", is_flag=True, help="Disable CSS generation")
@click.option("--css-path", help="Custom CSS file path")
@click.option("--strict", is_flag=True, help="Strict mode (fail on warnings)")
@click.option(
    "--max-size",
    type=int,
    default=10 * 1024 * 1024,
    help="Maximum XML file size in bytes",
)
@click.option(
    "--schema",
    type=click.Path(exists=True),
    help="Optional Relax NG or Schematron schema for validation",
)
@click.option(
    "--allow-xxe",
    is_flag=True,
    help="Allow external entities (WARNING: security risk, only use with trusted XML)",
)
@click.pass_context
def phpify(
    ctx: click.Context,
    xml_file: str,
    output: str | None,
    template: str,
    title: str | None,
    favicon: str | None,
    assets_dir: str,
    no_toc: bool,
    no_css: bool,
    css_path: str | None,
    strict: bool,
    max_size: int,
    schema: str | None,
    allow_xxe: bool,
) -> None:
    """Generate production-ready PHP page from XML document.

    Implements a secure XML→IR→PHP pipeline with:
    - XXE protection and size/time limits
    - Schema validation (Relax NG/Schematron)
    - Context-aware escaping
    - Semantic HTML5 with accessibility
    - Responsive layout
    """
    click.echo(f"🔧 Generating PHP from: {xml_file}")

    xml_path = Path(xml_file)

    # Determine output path
    if not output:
        output = str(xml_path.stem) + ".php"
    output_path = Path(output)

    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Configure secure parser
        parse_config = ParseConfig(
            max_size_bytes=max_size,
            validate_schema=schema is not None,
            schema_path=Path(schema) if schema else None,
            allow_xxe=allow_xxe,
        )

        # Warn user if XXE is enabled
        if allow_xxe:
            click.echo(
                "  ⚠️  WARNING: External entities (XXE) enabled - only use with trusted XML!"
            )

        # Parse XML securely
        click.echo("  Parsing XML...")
        parser = SecureXMLParser(parse_config)
        root = parser.parse(xml_path)

        # Build intermediate representation
        click.echo("  Building intermediate representation...")
        ir_builder = IRBuilder(strict=strict)
        ir = ir_builder.build(root)

        # Configure generator
        gen_config = GeneratorConfig(
            template=template,
            title=title,
            favicon=favicon,
            assets_dir=assets_dir,
            no_toc=no_toc,
            no_css=no_css,
            css_path=css_path,
        )

        # Generate PHP
        click.echo("  Generating PHP...")
        # Find templates directory (handles both installed and dev modes)
        cli_file = Path(__file__).resolve()
        # Try relative to package first
        templates_dir = cli_file.parent.parent.parent.parent / "templates"
        if not templates_dir.exists():
            # Try from working directory
            templates_dir = Path.cwd() / "templates"
        if not templates_dir.exists():
            raise FileNotFoundError(f"Templates directory not found. Tried: {templates_dir}")

        generator = PHPGenerator(templates_dir, gen_config)
        files = generator.generate(ir, output_basename=xml_path.stem)

        # Write output files
        for file_path, content in files.items():
            # Main PHP file goes to output_path, others go relative to it
            if file_path == f"{xml_path.stem}.php":
                full_path = output_path
            else:
                full_path = output_path.parent / file_path

            full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

            click.echo(f"  ✅ Generated: {full_path}")

        # Lint PHP if php is available
        try:
            import subprocess

            result = subprocess.run(
                ["php", "-l", str(output_path)],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                click.echo("  ✅ PHP syntax valid")
            else:
                click.echo(f"  ⚠️  PHP lint warning: {result.stderr}")
                if strict:
                    sys.exit(1)

        except (FileNotFoundError, subprocess.TimeoutExpired):
            click.echo("  ℹ️  PHP not available for linting")

        click.echo("\n✅ PHP generation complete!")
        click.echo(f"   Main file: {output_path}")
        click.echo(f"   Title: {ir.metadata.title}")
        click.echo(f"   Content elements: {len(ir.content)}")

        if ir.citations:
            click.echo(f"   Citations: {len(ir.citations)}")

        sys.exit(0)

    except Exception as e:
        click.echo(f"\n❌ Generation failed: {e}")
        if strict:
            import traceback

            click.echo(traceback.format_exc())
        sys.exit(1)


@main.group()
def pipeline() -> None:
    """XML Pipeline automation commands.

    Execute declarative XML processing pipelines with validation,
    transformation, and output stages.
    """
    pass


@pipeline.command("run")
@click.argument("pipeline_file", type=click.Path(exists=True))
@click.argument("input_xml", type=click.Path(exists=True))
@click.option("--output-dir", "-o", help="Override output directory")
@click.option("--var", "-v", multiple=True, help="Set variable (KEY=VALUE)")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format (default: text)",
)
@click.option("--verbose", "-V", is_flag=True, help="Verbose output")
@click.pass_context
def pipeline_run(
    ctx: click.Context,
    pipeline_file: str,
    input_xml: str,
    output_dir: str | None,
    var: tuple[str, ...],
    output_format: str,
    verbose: bool,
) -> None:
    """Execute a pipeline from YAML definition.

    \b
    Examples:
        xml-lib pipeline run pipelines/soap.yaml input.xml
        xml-lib pipeline run pipelines/rss.yaml feed.xml -o out/
        xml-lib pipeline run pipelines/ci.yaml data.xml -v ENV=prod
    """
    from xml_lib.pipeline import load_pipeline

    if output_format == "text":
        click.echo(f"🔄 Running pipeline: {pipeline_file}")
        click.echo(f"   Input: {input_xml}")

    # Parse variables from --var options
    variables = {}
    for var_str in var:
        if "=" in var_str:
            key, value = var_str.split("=", 1)
            variables[key] = value
        else:
            click.echo(f"⚠️  Invalid variable format: {var_str} (expected KEY=VALUE)")

    try:
        # Load pipeline from YAML
        pipeline_obj = load_pipeline(Path(pipeline_file))

        # Override variables if provided
        if variables:
            pipeline_obj._loader_variables = variables

        # Execute pipeline
        result = pipeline_obj.execute(input_xml=input_xml)

        # Output results
        if output_format == "json":
            click.echo(json.dumps(result.to_dict(), indent=2))
        else:
            click.echo(f"\n{'=' * 60}")
            click.echo(f"Pipeline: {result.pipeline_name}")
            click.echo(f"Status: {'✅ SUCCESS' if result.success else '❌ FAILED'}")
            click.echo(f"Duration: {result.duration_seconds:.2f}s")
            click.echo(f"Stages executed: {result.stages_executed}")
            click.echo(f"Stages failed: {result.stages_failed}")
            click.echo(f"{'=' * 60}")

            if verbose or not result.success:
                click.echo("\nStage Results:")
                for stage_result in result.context.stage_results:
                    status = "✅" if stage_result.success else "❌"
                    click.echo(
                        f"  {status} {stage_result.stage} "
                        f"({stage_result.duration_seconds:.2f}s)"
                    )
                    if stage_result.error:
                        click.echo(f"     Error: {stage_result.error}")

        # Exit with appropriate code
        sys.exit(0 if result.success else 1)

    except Exception as e:
        click.echo(f"\n❌ Pipeline failed: {e}")
        if verbose:
            import traceback

            click.echo(traceback.format_exc())
        sys.exit(1)


@pipeline.command("list")
@click.option("--templates-dir", default="templates/pipelines", help="Templates directory")
def pipeline_list(templates_dir: str) -> None:
    """List available pipeline templates.

    Shows all pre-built pipeline templates with descriptions.
    """
    import yaml

    templates_path = Path(templates_dir)

    if not templates_path.exists():
        click.echo(f"❌ Templates directory not found: {templates_dir}")
        sys.exit(1)

    click.echo("📋 Available Pipeline Templates:\n")

    yaml_files = sorted(templates_path.glob("*.yaml"))
    if not yaml_files:
        click.echo(f"   No templates found in {templates_dir}")
        sys.exit(0)

    for yaml_file in yaml_files:
        try:
            with open(yaml_file) as f:
                config = yaml.safe_load(f)

            name = config.get("name", yaml_file.stem)
            description = config.get("description", "No description")
            stage_count = len(config.get("stages", []))

            click.echo(f"  • {yaml_file.name}")
            click.echo(f"    Name: {name}")
            click.echo(f"    Description: {description}")
            click.echo(f"    Stages: {stage_count}")
            click.echo()

        except Exception as e:
            click.echo(f"  • {yaml_file.name} (error loading: {e})")
            click.echo()


@pipeline.command("dry-run")
@click.argument("pipeline_file", type=click.Path(exists=True))
@click.argument("input_xml", type=click.Path(exists=True))
def pipeline_dry_run(pipeline_file: str, input_xml: str) -> None:
    """Show pipeline stages without executing.

    Useful for previewing what a pipeline will do before running it.

    \b
    Example:
        xml-lib pipeline dry-run pipelines/soap.yaml input.xml
    """
    from xml_lib.pipeline import load_pipeline

    click.echo(f"🔍 Dry run: {pipeline_file}\n")

    try:
        pipeline_obj = load_pipeline(Path(pipeline_file))

        click.echo(f"Pipeline: {pipeline_obj.name}")
        click.echo(f"Error Strategy: {pipeline_obj.error_strategy.value}")
        click.echo(f"Rollback: {'Enabled' if pipeline_obj.rollback_enabled else 'Disabled'}")
        click.echo(f"\nStages ({len(pipeline_obj.stages)}):\n")

        for i, stage in enumerate(pipeline_obj.stages, 1):
            click.echo(f"  {i}. {stage.name} ({stage.__class__.__name__})")

        click.echo(f"\n✅ Pipeline is valid")
        sys.exit(0)

    except Exception as e:
        click.echo(f"\n❌ Pipeline validation failed: {e}")
        sys.exit(1)


@pipeline.command("validate")
@click.argument("pipeline_file", type=click.Path(exists=True))
def pipeline_validate(pipeline_file: str) -> None:
    """Validate pipeline YAML definition.

    Checks that the pipeline definition is valid and all referenced
    files (schemas, transforms, templates) exist.

    \b
    Example:
        xml-lib pipeline validate pipelines/soap.yaml
    """
    from xml_lib.pipeline import load_pipeline

    click.echo(f"🔍 Validating: {pipeline_file}")

    try:
        pipeline_obj = load_pipeline(Path(pipeline_file))

        click.echo(f"✅ Pipeline definition is valid")
        click.echo(f"   Name: {pipeline_obj.name}")
        click.echo(f"   Stages: {len(pipeline_obj.stages)}")
        sys.exit(0)

    except Exception as e:
        click.echo(f"❌ Validation failed: {e}")
        sys.exit(1)


@main.group()
def stream() -> None:
    """Streaming XML validation for large files.

    Process enterprise-scale XML files (1GB-10GB+) with constant memory usage.
    Supports checkpointing, resume, and performance benchmarking.
    """
    pass


@stream.command("validate")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--schema", type=click.Path(exists=True), help="XSD schema file for validation")
@click.option(
    "--checkpoint-interval",
    type=int,
    default=100,
    help="Save checkpoint every N MB (0 = disabled)",
)
@click.option(
    "--checkpoint-dir",
    type=click.Path(),
    default=".checkpoints",
    help="Directory for checkpoint files",
)
@click.option("--resume-from", type=click.Path(exists=True), help="Resume from checkpoint file")
@click.option("--track-memory/--no-track-memory", default=True, help="Track memory usage")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def stream_validate(
    file_path: str,
    schema: str | None,
    checkpoint_interval: int,
    checkpoint_dir: str,
    resume_from: str | None,
    track_memory: bool,
    output_format: str,
) -> None:
    """Validate large XML files using streaming.

    Processes files with constant memory usage (~50MB), suitable for
    files that are too large for DOM parsing.

    \b
    Examples:
        # Validate 5GB file with checkpoints every 100MB
        xml-lib stream validate huge.xml --checkpoint-interval 100

        # Validate with XSD schema
        xml-lib stream validate data.xml --schema schema.xsd

        # Resume from checkpoint
        xml-lib stream validate data.xml --resume-from .checkpoints/data_checkpoint_5.json
    """
    from xml_lib.streaming import StreamingValidator

    if output_format == "text":
        click.echo(f"🔍 Streaming validation: {file_path}")
        if schema:
            click.echo(f"   Schema: {schema}")
        if resume_from:
            click.echo(f"   Resuming from: {resume_from}")

    try:
        validator = StreamingValidator(schema_path=schema)

        result = validator.validate_stream(
            file_path=file_path,
            checkpoint_interval_mb=checkpoint_interval,
            checkpoint_dir=Path(checkpoint_dir) if checkpoint_dir else None,
            resume_from=Path(resume_from) if resume_from else None,
            track_memory=track_memory,
        )

        if output_format == "json":
            import json

            output_data = {
                "valid": result.is_valid,
                "errors": [
                    {
                        "message": err.message,
                        "line": err.line_number,
                        "column": err.column_number,
                        "element": err.element_name,
                        "type": err.error_type,
                    }
                    for err in result.errors
                ],
                "warnings": [
                    {
                        "message": warn.message,
                        "line": warn.line_number,
                        "column": warn.column_number,
                        "element": warn.element_name,
                    }
                    for warn in result.warnings
                ],
                "statistics": {
                    "elements_validated": result.elements_validated,
                    "bytes_processed": result.bytes_processed,
                    "duration_seconds": result.duration_seconds,
                    "throughput_mbps": result.throughput_mbps,
                    "peak_memory_mb": result.peak_memory_mb,
                    "checkpoint_count": result.checkpoint_count,
                },
            }
            click.echo(json.dumps(output_data, indent=2))
        else:
            click.echo("\n" + result.format_summary())

        sys.exit(0 if result.is_valid else 1)

    except Exception as e:
        click.echo(f"\n❌ Validation failed: {e}")
        sys.exit(1)


@stream.command("benchmark")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Save results to JSON file")
@click.option("--dom/--no-dom", default=True, help="Include DOM method in comparison")
@click.option(
    "--streaming/--no-streaming", default=True, help="Include streaming method in comparison"
)
def stream_benchmark(
    file_path: str,
    output: str | None,
    dom: bool,
    streaming: bool,
) -> None:
    """Benchmark streaming vs DOM validation performance.

    Compares processing time, memory usage, and throughput between
    DOM and streaming methods.

    \b
    Examples:
        # Benchmark single file
        xml-lib stream benchmark test_100mb.xml

        # Save results to JSON
        xml-lib stream benchmark test_100mb.xml --output results.json

        # Compare only streaming (skip DOM)
        xml-lib stream benchmark huge_5gb.xml --no-dom
    """
    from xml_lib.streaming import BenchmarkRunner

    click.echo(f"🔬 Benchmarking: {file_path}")

    try:
        runner = BenchmarkRunner()
        result = runner.run_benchmark(
            file_path=file_path, include_dom=dom, include_streaming=streaming
        )

        # Display report
        click.echo(result.format_report())

        # Save to JSON if requested
        if output:
            import json

            with open(output, "w") as f:
                json.dump(result.to_dict(), f, indent=2)
            click.echo(f"\n✅ Results saved to {output}")

        sys.exit(0)

    except Exception as e:
        click.echo(f"\n❌ Benchmark failed: {e}")
        sys.exit(1)


@stream.command("generate")
@click.argument("size_mb", type=int)
@click.option("--output", "-o", required=True, type=click.Path(), help="Output file path")
@click.option(
    "--pattern",
    type=click.Choice(["simple", "complex", "nested", "realistic"]),
    default="complex",
    help="XML structure pattern",
)
@click.option(
    "--type",
    "record_type",
    type=click.Choice(["user", "product", "transaction", "log"]),
    help="Generate realistic dataset of specific type",
)
@click.option("--record-count", type=int, help="Number of records (for dataset mode)")
def stream_generate(
    size_mb: int,
    output: str,
    pattern: str,
    record_type: str | None,
    record_count: int | None,
) -> None:
    """Generate test XML files for benchmarking.

    Creates XML files of specified size with various complexity patterns.

    \b
    Examples:
        # Generate 1GB test file
        xml-lib stream generate 1000 --output test_1gb.xml

        # Generate with complex pattern
        xml-lib stream generate 500 --output test_500mb.xml --pattern complex

        # Generate realistic dataset
        xml-lib stream generate 0 --output users.xml --type user --record-count 1000000
    """
    from xml_lib.streaming import TestFileGenerator

    if record_type and record_count:
        # Generate realistic dataset
        click.echo(
            f"📝 Generating realistic dataset: {record_count:,} {record_type} records"
        )

        try:
            generator = TestFileGenerator()
            generator.generate_realistic_dataset(
                output_path=output,
                record_count=record_count,
                record_type=record_type,
            )

            output_path = Path(output)
            file_size_mb = output_path.stat().st_size / 1024 / 1024

            click.echo(f"✅ Generated {output} ({file_size_mb:.1f} MB)")
            sys.exit(0)

        except Exception as e:
            click.echo(f"❌ Generation failed: {e}")
            sys.exit(1)

    else:
        # Generate by size
        click.echo(f"📝 Generating {size_mb}MB test file with {pattern} pattern")

        def progress(current: int, total: int) -> None:
            pct = (current / total) * 100
            mb_current = current / 1024 / 1024
            mb_total = total / 1024 / 1024
            click.echo(
                f"  Progress: {pct:5.1f}% ({mb_current:6.1f} / {mb_total:.1f} MB)",
                nl=False,
            )
            click.echo("\r", nl=False)

        try:
            generator = TestFileGenerator()
            generator.generate(
                output_path=output,
                size_mb=size_mb,
                pattern=pattern,
                progress_callback=progress,
            )

            click.echo(f"\n✅ Generated {output} ({size_mb} MB)")
            sys.exit(0)

        except Exception as e:
            click.echo(f"\n❌ Generation failed: {e}")
            sys.exit(1)


@stream.command("checkpoint")
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--checkpoint-dir",
    type=click.Path(),
    default=".checkpoints",
    help="Checkpoint directory",
)
@click.option("--list", "list_checkpoints", is_flag=True, help="List available checkpoints")
@click.option("--delete", is_flag=True, help="Delete all checkpoints for file")
def stream_checkpoint(
    file_path: str,
    checkpoint_dir: str,
    list_checkpoints: bool,
    delete: bool,
) -> None:
    """Manage validation checkpoints.

    List, inspect, or delete checkpoints for a file.

    \b
    Examples:
        # List checkpoints for file
        xml-lib stream checkpoint data.xml --list

        # Delete all checkpoints
        xml-lib stream checkpoint data.xml --delete
    """
    from xml_lib.streaming import CheckpointManager

    try:
        manager = CheckpointManager(checkpoint_dir=Path(checkpoint_dir))

        if delete:
            count = manager.delete_checkpoints(Path(file_path))
            click.echo(f"✅ Deleted {count} checkpoint(s) for {file_path}")
            sys.exit(0)

        if list_checkpoints:
            output = manager.format_checkpoint_list(Path(file_path))
            click.echo(output)
            sys.exit(0)

        # Default: show checkpoint info
        latest = manager.latest(Path(file_path))
        if latest:
            info = manager.get_checkpoint_info(latest)
            click.echo(f"Latest checkpoint for {file_path}:")
            click.echo(f"  File: {latest}")
            click.echo(f"  Position: {info.get('file_position', 0):,} bytes")
            click.echo(f"  Elements: {info.get('elements_validated', 0):,}")
            click.echo(f"  Timestamp: {info.get('timestamp', 'N/A')}")
        else:
            click.echo(f"No checkpoints found for {file_path}")

        sys.exit(0)

    except Exception as e:
        click.echo(f"❌ Checkpoint operation failed: {e}")
        sys.exit(1)


@main.command()
def shell() -> None:
    """Launch interactive shell with autocomplete and history.

    The interactive shell provides a REPL environment with:
    - Tab completion for commands, files, and flags
    - Command history (persistent across sessions)
    - Syntax highlighting
    - Alias support

    \b
    Examples:
        xml-lib shell

    Inside the shell:
        xml-lib> validate data.xml --schema schema.xsd
        xml-lib> config set aliases.v "validate --schema schema.xsd"
        xml-lib> v data.xml
        xml-lib> exit
    """
    from xml_lib.interactive import launch_shell

    sys.exit(launch_shell())


@main.command()
@click.argument("pattern")
@click.option(
    "--command",
    "-c",
    required=True,
    help="Command to execute (use {file} as placeholder)",
)
@click.option(
    "--path",
    default=".",
    type=click.Path(exists=True),
    help="Base path to watch (default: current directory)",
)
@click.option(
    "--debounce",
    "-d",
    type=float,
    help="Debounce delay in seconds (default: from config)",
)
@click.option(
    "--clear/--no-clear",
    default=None,
    help="Clear terminal on change (default: from config)",
)
@click.option(
    "--recursive/--no-recursive",
    default=True,
    help="Watch subdirectories recursively",
)
def watch(
    pattern: str,
    command: str,
    path: str,
    debounce: float | None,
    clear: bool | None,
    recursive: bool,
) -> None:
    """Watch files for changes and auto-execute commands.

    Monitors files matching PATTERN and executes COMMAND when changes are detected.
    Includes debouncing to avoid rapid re-runs.

    Use {file} in the command string as a placeholder for the changed file path.

    \b
    Examples:
        # Watch all XML files and validate on change
        xml-lib watch "*.xml" --command "validate {file} --schema schema.xsd"

        # Watch specific directory
        xml-lib watch "data/**/*.xml" --command "validate {file}" --path data/

        # Custom debounce delay
        xml-lib watch "*.xml" --command "lint {file}" --debounce 1.0

        # Watch without clearing terminal
        xml-lib watch "*.xml" --command "validate {file}" --no-clear
    """
    from xml_lib.interactive import watch_files

    sys.exit(
        watch_files(
            pattern=pattern,
            command=command,
            path=path,
            recursive=recursive,
            debounce=debounce,
            clear=clear,
        )
    )


@main.group()
def config() -> None:
    """Manage xml-lib configuration.

    Configure aliases, watch mode settings, output formatting, and shell behavior.
    Configuration is stored in ~/.xml-lib/config.yaml (or $XDG_CONFIG_HOME/xml-lib).
    """
    pass


@config.command("show")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "yaml", "json"]),
    default="text",
    help="Output format",
)
def config_show(output_format: str) -> None:
    """Show current configuration.

    \b
    Examples:
        xml-lib config show
        xml-lib config show --format yaml
        xml-lib config show --format json
    """
    from xml_lib.interactive import get_config

    cfg = get_config()

    if output_format == "yaml":
        import yaml

        config_file = cfg.get_config_file()
        if config_file.exists():
            with open(config_file) as f:
                click.echo(f.read())
        else:
            click.echo("# No configuration file found (using defaults)")

    elif output_format == "json":
        import json

        data = {
            "aliases": cfg.aliases.aliases,
            "watch": {
                "debounce_seconds": cfg.watch.debounce_seconds,
                "notify": cfg.watch.notify,
                "clear_on_change": cfg.watch.clear_on_change,
                "ignore_patterns": cfg.watch.ignore_patterns,
            },
            "output": {
                "colors": cfg.output.colors,
                "emoji": cfg.output.emoji,
                "verbose": cfg.output.verbose,
                "show_timing": cfg.output.show_timing,
                "progress_bars": cfg.output.progress_bars,
            },
            "shell": {
                "prompt": cfg.shell.prompt,
                "history_size": cfg.shell.history_size,
                "multiline": cfg.shell.multiline,
                "vi_mode": cfg.shell.vi_mode,
            },
        }
        click.echo(json.dumps(data, indent=2))

    else:  # text
        from xml_lib.interactive import get_formatter

        formatter = get_formatter()

        config_dict = {
            "aliases": cfg.aliases.aliases if cfg.aliases.aliases else "(none)",
            "watch.debounce_seconds": cfg.watch.debounce_seconds,
            "watch.notify": cfg.watch.notify,
            "watch.clear_on_change": cfg.watch.clear_on_change,
            "output.colors": cfg.output.colors,
            "output.emoji": cfg.output.emoji,
            "output.verbose": cfg.output.verbose,
            "output.show_timing": cfg.output.show_timing,
            "shell.prompt": repr(cfg.shell.prompt),
            "shell.history_size": cfg.shell.history_size,
            "shell.vi_mode": cfg.shell.vi_mode,
        }

        formatter.print_config(config_dict)


@config.command("get")
@click.argument("key")
def config_get(key: str) -> None:
    """Get a configuration value.

    \b
    Examples:
        xml-lib config get output.colors
        xml-lib config get shell.prompt
        xml-lib config get aliases.v
    """
    from xml_lib.interactive import get_config

    cfg = get_config()

    # Special handling for aliases
    if key.startswith("aliases."):
        alias_name = key.split(".", 1)[1]
        value = cfg.aliases.get(alias_name)
    else:
        value = cfg.get(key)

    if value is not None:
        click.echo(value)
    else:
        click.echo(f"Error: Configuration key not found: {key}", err=True)
        sys.exit(1)


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set a configuration value.

    \b
    Examples:
        xml-lib config set output.emoji false
        xml-lib config set shell.prompt ">>> "
        xml-lib config set aliases.v "validate --schema schema.xsd"
        xml-lib config set watch.debounce_seconds 1.0
    """
    from xml_lib.interactive import get_config

    cfg = get_config()

    # Special handling for aliases
    if key.startswith("aliases."):
        alias_name = key.split(".", 1)[1]
        cfg.aliases.set(alias_name, value)
        cfg.save()
        click.echo(f"✅ Set alias: {alias_name} = {value}")
        return

    # Set regular config value
    success = cfg.set(key, value)
    if success:
        cfg.save()
        click.echo(f"✅ Set {key} = {value}")
    else:
        click.echo(f"❌ Error: Invalid configuration key: {key}", err=True)
        click.echo("Use 'xml-lib config show' to see available settings", err=True)
        sys.exit(1)


@config.command("reset")
@click.option(
    "--confirm",
    is_flag=True,
    help="Confirm reset without prompting",
)
def config_reset(confirm: bool) -> None:
    """Reset configuration to defaults.

    \b
    Examples:
        xml-lib config reset --confirm
    """
    from xml_lib.interactive import get_config

    if not confirm:
        click.confirm(
            "This will reset all configuration to defaults. Continue?",
            abort=True,
        )

    cfg = get_config()
    cfg.reset()
    cfg.save()
    click.echo("✅ Configuration reset to defaults")


if __name__ == "__main__":
    main()
