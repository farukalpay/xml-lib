"""Modern CLI with Typer and Rich for xml-lib.

This CLI provides production-grade commands for XML lifecycle management,
guardrails simulation, mathematical engine operations, and documentation generation.
"""

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree

from xml_lib import lifecycle, schema
from xml_lib.engine.fixed_points import FixedPointIterator
from xml_lib.engine.operators import contraction_operator, projection_operator
from xml_lib.engine.proofs import ProofGenerator
from xml_lib.guardrails.checksum import ChecksumValidator
from xml_lib.guardrails.simulator import GuardrailSimulator, State, StateType, Transition
from xml_lib.pptx.builder import PPTXBuilder
from xml_lib.pptx.exporter import HTMLExporter
from xml_lib.pptx.parser import PPTXParser
from xml_lib.transforms.normalize import Normalizer
from xml_lib.types import CommandResult
from xml_lib.utils.logging import get_logger

app = typer.Typer(
    name="xml-lib",
    help="Production-grade XML lifecycle, guardrails, and mathematical engine",
    add_completion=False,
)

# Sub-applications
lifecycle_app = typer.Typer(help="Lifecycle validation and visualization")
guardrails_app = typer.Typer(help="Guardrails simulation and checking")
engine_app = typer.Typer(help="Mathematical engine operations")
pptx_app = typer.Typer(help="PPTX building and export")
schema_app = typer.Typer(help="Schema derivation and validation")
docs_app = typer.Typer(help="Documentation generation")
examples_app = typer.Typer(help="Run example workflows")

app.add_typer(lifecycle_app, name="lifecycle")
app.add_typer(guardrails_app, name="guardrails")
app.add_typer(engine_app, name="engine")
app.add_typer(pptx_app, name="pptx")
app.add_typer(schema_app, name="schema")
app.add_typer(docs_app, name="docs")
app.add_typer(examples_app, name="examples")

console = Console()
logger = get_logger(__name__)


def print_command_result(result: CommandResult, json_output: Optional[Path] = None) -> None:
    """Print command result with rich formatting and optional JSON output."""
    # JSON output
    if json_output:
        json_data = {
            "command": result.command,
            "timestamp": result.timestamp.isoformat(),
            "duration_ms": result.duration_ms,
            "status": result.status,
            "summary": result.summary,
            "errors": result.errors,
            "warnings": result.warnings,
        }
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(json_data, indent=2))
        console.print(f"[dim]JSON output: {json_output}[/dim]")

    # Rich table output
    table = Table(title=f"Command: {result.command}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Status", f"[bold]{result.status}[/bold]")
    table.add_row("Duration", f"{result.duration_ms:.2f}ms")

    for key, value in result.summary.items():
        table.add_row(key.replace("_", " ").title(), str(value))

    console.print(table)

    # Errors and warnings
    if result.errors:
        console.print("\n[bold red]Errors:[/bold red]")
        for error in result.errors:
            console.print(f"  ❌ {error}")

    if result.warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for warning in result.warnings:
            console.print(f"  ⚠️  {warning}")


@lifecycle_app.command("validate")
def lifecycle_validate(
    path: Path = typer.Argument(..., help="Path to lifecycle base directory"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="JSON output file"),
) -> None:
    """Validate lifecycle DAG and phase invariants.

    Checks:
    - DAG acyclicity
    - Phase ordering (begin → start → iteration → end → continuum)
    - Timestamp monotonicity
    - Cross-reference integrity
    """
    start_time = time.time()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Loading lifecycle...", total=None)

        try:
            dag = lifecycle.load_lifecycle(path)
            progress.update(task, description="[cyan]Validating DAG...")

            validation = lifecycle.validate_dag(dag)
            invariants = lifecycle.check_phase_invariants(dag)
            references = lifecycle.verify_references(dag)

            duration = (time.time() - start_time) * 1000

            result = CommandResult(
                command="lifecycle validate",
                timestamp=datetime.now(UTC),
                duration_ms=duration,
                status="success" if validation.is_valid else "failure",
                summary={
                    "phases": len(dag.nodes),
                    "edges": sum(len(v) for v in dag.edges.values()),
                    "invariant_violations": len(invariants),
                    "reference_errors": len(references),
                },
                errors=validation.errors + [inv.description for inv in invariants],
                warnings=validation.warnings,
            )

            print_command_result(result, output)

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(1)


@lifecycle_app.command("visualize")
def lifecycle_visualize(
    path: Path = typer.Argument(..., help="Path to lifecycle base directory"),
    output: Path = typer.Option(
        Path("artifacts/lifecycle.txt"), "--output", "-o", help="Output file"
    ),
) -> None:
    """Visualize lifecycle DAG as a tree."""
    try:
        dag = lifecycle.load_lifecycle(path)

        tree = Tree(f"[bold]Lifecycle DAG[/bold] ({len(dag.nodes)} phases)")

        sorted_nodes = dag.topological_sort()
        for node_id in sorted_nodes:
            node = dag.get_node(node_id)
            if node:
                branch = tree.add(
                    f"[cyan]{node.phase}[/cyan] ({node.timestamp.strftime('%Y-%m-%d')})"
                )
                deps = dag.get_dependencies(node_id)
                if deps:
                    branch.add(f"[dim]Dependencies: {', '.join(deps)}[/dim]")

        console.print(tree)

        # Save to file
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w") as f:
            console.print(tree, file=f)
        console.print(f"\n[dim]Saved to: {output}[/dim]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@guardrails_app.command("simulate")
def guardrails_simulate(
    steps: int = typer.Option(5, "--steps", "-n", help="Number of simulation steps"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="JSON output file"),
) -> None:
    """Simulate guardrail finite-state machine."""
    start_time = time.time()

    console.print("[bold]Guardrail FSM Simulation[/bold]\n")

    # Create simple FSM
    sim = GuardrailSimulator()
    sim.add_state(State("initial", StateType.INITIAL))
    sim.add_state(State("checking", StateType.CHECKING))
    sim.add_state(State("passed", StateType.PASSED))
    sim.add_state(State("failed", StateType.FAILED))

    sim.add_transition(Transition("initial", "checking", "True"))
    sim.add_transition(Transition("checking", "passed", "valid == True"))
    sim.add_transition(Transition("checking", "failed", "valid == False"))

    # Simulate
    inputs = [{"valid": True} for _ in range(steps)]
    result = sim.simulate(inputs)

    duration = (time.time() - start_time) * 1000

    # Display trace
    console.print("[cyan]Simulation Trace:[/cyan]")
    for i, state in enumerate(result.trace):
        console.print(f"  Step {i}: [bold]{state}[/bold]")

    cmd_result = CommandResult(
        command="guardrails simulate",
        timestamp=datetime.now(UTC),
        duration_ms=duration,
        status="success" if result.success else "failure",
        summary={
            "steps": len(result.trace),
            "final_state": result.final_state,
            "success": result.success,
        },
        errors=result.errors,
    )

    print_command_result(cmd_result, output)


@guardrails_app.command("check")
def guardrails_check(
    file: Path = typer.Argument(..., help="File to check"),
    checksum: str = typer.Option(..., "--checksum", "-c", help="Expected checksum"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="JSON output file"),
) -> None:
    """Verify file checksum."""
    start_time = time.time()

    validator = ChecksumValidator()
    result = validator.validate_checksum(file, checksum)

    duration = (time.time() - start_time) * 1000

    cmd_result = CommandResult(
        command="guardrails check",
        timestamp=datetime.now(UTC),
        duration_ms=duration,
        status="success" if result.is_valid else "failure",
        summary={
            "file": str(file),
            "algorithm": result.metadata.get("algorithm", "sha256"),
            "valid": result.is_valid,
        },
        errors=result.errors,
    )

    print_command_result(cmd_result, output)


@engine_app.command("prove")
def engine_prove(
    xml_path: Path = typer.Argument(..., help="Path to proof XML specification"),
    output: Path = typer.Option(
        Path("artifacts/proof.tex"), "--output", "-o", help="Output proof file"
    ),
    format: str = typer.Option("latex", "--format", "-f", help="Output format (latex or html)"),
) -> None:
    """Generate mathematical proof from XML specification."""
    start_time = time.time()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("[cyan]Generating proof...", total=None)

        generator = ProofGenerator()
        proof = generator.generate_from_xml(xml_path)
        generator.export_proof(proof, output, format=format)

        duration = (time.time() - start_time) * 1000

    console.print(f"[green]✓[/green] Proof generated: {output}")

    result = CommandResult(
        command="engine prove",
        timestamp=datetime.now(UTC),
        duration_ms=duration,
        status="success",
        summary={
            "output_file": str(output),
            "format": format,
            "steps": len(proof.steps),
        },
    )

    print_command_result(result)


@engine_app.command("verify")
def engine_verify(
    operator_type: str = typer.Option("contraction", "--type", "-t", help="Operator type"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="JSON output file"),
) -> None:
    """Verify operator properties (fixed points, Fejér monotonicity)."""
    import numpy as np

    start_time = time.time()

    console.print(f"[bold]Verifying {operator_type} operator[/bold]\n")

    # Create operator
    if operator_type == "contraction":
        op = contraction_operator("T", 0.8)
    elif operator_type == "projection":
        op = projection_operator("P", 2)
    else:
        console.print(f"[red]Unknown operator type: {operator_type}[/red]")
        raise typer.Exit(1)

    # Run fixed-point iteration
    iterator = FixedPointIterator(
        operator=op, tolerance=1e-6, max_iterations=100, store_trajectory=True
    )
    x0 = np.array([1.0, 2.0])

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("[cyan]Running fixed-point iteration...", total=None)
        fp_result = iterator.iterate(x0)

    duration = (time.time() - start_time) * 1000

    # Display results
    console.print(f"[cyan]Converged:[/cyan] {fp_result.is_converged()}")
    console.print(f"[cyan]Iterations:[/cyan] {fp_result.metrics.iterations}")
    console.print(f"[cyan]Final error:[/cyan] {fp_result.metrics.final_residual:.2e}")

    if fp_result.fixed_point is not None:
        console.print(f"[cyan]Fixed point:[/cyan] {fp_result.fixed_point}")

    result = CommandResult(
        command="engine verify",
        timestamp=datetime.now(UTC),
        duration_ms=duration,
        status="success" if fp_result.is_converged() else "failure",
        summary={
            "operator_type": operator_type,
            "converged": fp_result.is_converged(),
            "iterations": fp_result.metrics.iterations,
            "error": fp_result.metrics.final_residual,
        },
    )

    print_command_result(result, output)


@pptx_app.command("build")
def pptx_build(
    xml_path: Path = typer.Argument(..., help="Path to PPTX build plan XML"),
    output: Path = typer.Option(..., "--output", "-o", help="Output .pptx file"),
    template: Optional[Path] = typer.Option(None, "--template", "-t", help="Template .pptx file"),
) -> None:
    """Build PowerPoint presentation from XML build plan."""
    start_time = time.time()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Parsing build plan...", total=None)

        parser = PPTXParser()
        plan = parser.parse(xml_path)

        progress.update(task, description="[cyan]Building presentation...")
        builder = PPTXBuilder(template_path=template)
        result = builder.build(plan, output)

        (time.time() - start_time) * 1000

    if result.success:
        console.print(f"[green]✓[/green] Presentation built: {output}")
        console.print(f"  Slides: {result.slide_count}")
    else:
        console.print(f"[red]✗[/red] Build failed: {result.error}")
        raise typer.Exit(1)


@pptx_app.command("export")
def pptx_export(
    pptx_path: Path = typer.Argument(..., help="Path to .pptx file"),
    output: Path = typer.Option(..., "--output", "-o", help="Output .html file"),
) -> None:
    """Export PowerPoint to HTML handout."""
    start_time = time.time()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("[cyan]Exporting to HTML...", total=None)

        exporter = HTMLExporter()
        success = exporter.export(pptx_path, output)

        (time.time() - start_time) * 1000

    if success:
        console.print(f"[green]✓[/green] Exported to: {output}")
    else:
        console.print("[red]✗[/red] Export failed")
        raise typer.Exit(1)


@schema_app.command("derive")
def schema_derive(
    example_files: str = typer.Argument(..., help="Example XML files (comma-separated)"),
    output: Path = typer.Option(..., "--output", "-o", help="Output schema file"),
    schema_type: str = typer.Option("relaxng", "--type", "-t", help="Schema type (xsd or relaxng)"),
) -> None:
    """Derive schema from example XML documents."""
    start_time = time.time()

    # Parse comma-separated file paths
    examples = [Path(p.strip()) for p in example_files.split(",")]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(f"[cyan]Deriving {schema_type} schema...", total=None)

        if schema_type == "xsd":
            schema.derive_xsd_from_examples(examples, output)
        elif schema_type == "relaxng":
            schema.derive_relaxng_from_examples(examples, output)
        else:
            console.print(f"[red]Unknown schema type: {schema_type}[/red]")
            raise typer.Exit(1)

        (time.time() - start_time) * 1000

    console.print(f"[green]✓[/green] Schema derived: {output}")


@schema_app.command("validate")
def schema_validate_cmd(
    xml_path: Path = typer.Argument(..., help="XML file to validate"),
    schema_path: Path = typer.Argument(..., help="Schema file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="JSON output file"),
) -> None:
    """Validate XML document against schema."""
    start_time = time.time()

    result = schema.validate_with_schema(xml_path, schema_path)

    duration = (time.time() - start_time) * 1000

    cmd_result = CommandResult(
        command="schema validate",
        timestamp=datetime.now(UTC),
        duration_ms=duration,
        status="success" if result.is_valid else "failure",
        summary={
            "xml_file": str(xml_path),
            "schema_file": str(schema_path),
            "valid": result.is_valid,
        },
        errors=result.errors,
    )

    print_command_result(cmd_result, output)


@docs_app.command("gen")
def docs_gen(
    source_dir: Path = typer.Option(Path("."), "--source", "-s", help="Source directory"),
    output_dir: Path = typer.Option(
        Path("artifacts/docs"), "--output", "-o", help="Output directory"
    ),
) -> None:
    """Generate documentation from lifecycle and guardrails."""
    console.print("[bold]Documentation generation[/bold]")
    console.print(f"  Source: {source_dir}")
    console.print(f"  Output: {output_dir}")
    console.print("\n[dim]Documentation generation not yet implemented[/dim]")


@examples_app.command("run")
def examples_run(
    example: str = typer.Argument("document", help="Example to run (document or amphibians)"),
    output_dir: Path = typer.Option(
        Path("artifacts"), "--output", "-o", help="Output directory for artifacts"
    ),
) -> None:
    """Run example workflows through full pipeline."""
    start_time = time.time()

    example_file = Path(f"example_{example}.xml")
    if not example_file.exists():
        console.print(f"[red]Example file not found: {example_file}[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Running example: {example}[/bold]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Normalize
        task = progress.add_task("[cyan]Normalizing XML...", total=None)
        normalizer = Normalizer()
        normalized_path = output_dir / example / "normalized.xml"
        normalizer.normalize(example_file, normalized_path)

        # Validate checksum
        progress.update(task, description="[cyan]Computing checksum...")
        validator = ChecksumValidator()
        checksum = validator.compute_checksum(normalized_path)

        duration = (time.time() - start_time) * 1000

    console.print("[green]✓[/green] Example processed")
    console.print(f"  Normalized: {normalized_path}")
    console.print(f"  Checksum: {checksum[:16]}...")
    console.print(f"  Duration: {duration:.2f}ms")


if __name__ == "__main__":
    app()
