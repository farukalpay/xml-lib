"""Main CLI entry point for xml-lib."""

import sys
from pathlib import Path
import click
from typing import Optional

from xml_lib.validator import Validator
from xml_lib.publisher import Publisher
from xml_lib.pptx_composer import PPTXComposer
from xml_lib.differ import Differ
from xml_lib.telemetry import TelemetrySink
from xml_lib.sanitize import MathPolicy, Sanitizer


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
def main(ctx: click.Context, telemetry: str, telemetry_target: Optional[str]) -> None:
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
@click.option(
    "--guardrails-dir", default="guardrails", help="Directory containing guardrails"
)
@click.option(
    "--output", "-o", default="out/assertions.xml", help="Output assertions file"
)
@click.option(
    "--jsonl", default="out/assertions.jsonl", help="JSON Lines output for CI"
)
@click.option("--strict", is_flag=True, help="Fail on warnings")
@click.option(
    "--math-policy",
    type=click.Choice(["sanitize", "mathml", "skip", "error"]),
    default="sanitize",
    help="Policy for handling mathy XML (default: sanitize)",
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
) -> None:
    """Validate XML documents against lifecycle schemas and guardrails.

    Validates the canonical chain (begin → start → iteration → end → continuum)
    using Relax NG + Schematron with cross-file constraints.
    """
    click.echo(f"🔍 Validating project: {project_path}")

    validator = Validator(
        schemas_dir=Path(schemas_dir),
        guardrails_dir=Path(guardrails_dir),
        telemetry=ctx.obj.get("telemetry"),
    )

    policy = MathPolicy(math_policy)
    result = validator.validate_project(Path(project_path), math_policy=policy)

    # Write assertions
    validator.write_assertions(result, Path(output), Path(jsonl))

    if result.is_valid:
        click.echo("✅ Validation passed")
        sys.exit(0)
    else:
        click.echo(
            f"❌ Validation failed: {len(result.errors)} errors, {len(result.warnings)} warnings"
        )
        for error in result.errors[:10]:  # Show first 10
            click.echo(f"  ERROR: {error}")
        if strict and result.warnings:
            click.echo("❌ Strict mode: warnings treated as errors")
            sys.exit(1)
        sys.exit(1 if result.errors else 0)


@main.command()
@click.argument("project_path", type=click.Path(exists=True))
@click.option(
    "--output-dir", "-o", default="out/site", help="Output directory for HTML"
)
@click.option(
    "--xslt-dir", default="schemas/xslt", help="Directory containing XSLT templates"
)
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
    template: Optional[str],
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
@click.pass_context
def diff(
    ctx: click.Context,
    file1: str,
    file2: str,
    explain: bool,
    schemas_dir: str,
) -> None:
    """Schema-aware structural diff between two XML files.

    Compares XML documents with understanding of lifecycle semantics.
    """
    click.echo(f"🔎 Comparing: {file1} ↔ {file2}")

    differ = Differ(
        schemas_dir=Path(schemas_dir),
        telemetry=ctx.obj.get("telemetry"),
    )

    result = differ.diff(Path(file1), Path(file2), explain=explain)

    if result.identical:
        click.echo("✅ Files are identical")
        sys.exit(0)
    else:
        click.echo(f"📋 Found {len(result.differences)} differences:")
        for diff in result.differences:
            click.echo(f"\n{diff.format(explain=explain)}")
        sys.exit(1)


@main.command()
@click.option("--restore", required=True, help="Sanitized XML file to restore")
@click.option("--mapping", help="Mapping file (auto-detected if not provided)")
@click.option("--output", "-o", required=True, help="Output file for restored XML")
@click.pass_context
def roundtrip(
    ctx: click.Context,
    restore: str,
    mapping: Optional[str],
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


if __name__ == "__main__":
    main()
