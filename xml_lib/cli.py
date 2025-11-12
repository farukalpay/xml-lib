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


if __name__ == "__main__":
    main()
