"""Enhanced output formatting with colors, progress bars, and pretty printing.

Provides rich terminal output for validation results, errors, and progress
indication. Respects NO_COLOR environment variable and configuration settings.
"""

import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from xml_lib.interactive.config import get_config


@dataclass
class ValidationError:
    """Validation error details."""

    message: str
    line: int | None = None
    column: int | None = None
    context: str | None = None
    file_path: str | None = None


@dataclass
class ValidationResult:
    """Validation result container."""

    success: bool
    duration: float
    errors: list[ValidationError] = None
    warnings: list[ValidationError] = None
    elements_validated: int = 0
    file_path: str | None = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class OutputFormatter:
    """Handles formatted output to terminal."""

    def __init__(self, force_color: bool | None = None):
        """Initialize output formatter.

        Args:
            force_color: Override color detection. None uses config and env.
        """
        config = get_config()

        # Respect NO_COLOR environment variable
        no_color = os.environ.get("NO_COLOR")
        if no_color is not None:
            use_color = False
        elif force_color is not None:
            use_color = force_color
        else:
            use_color = config.output.colors

        self.console = Console(force_terminal=use_color if use_color else None)
        self.config = config
        self.use_emoji = config.output.emoji and not no_color

    def print_banner(self) -> None:
        """Print welcome banner for interactive shell."""
        banner_text = """
╔═══════════════════════════════════════════════════════════╗
║                    XML-LIB Interactive                    ║
║            Modern XML Toolkit for DevOps & CI/CD          ║
╚═══════════════════════════════════════════════════════════╝

Type 'help' for commands, 'exit' or Ctrl+D to quit.
"""
        if self.use_emoji:
            banner_text = "🚀 " + banner_text.strip()

        self.console.print(banner_text, style="bold cyan")

    def print_success(self, message: str) -> None:
        """Print success message."""
        icon = "✅ " if self.use_emoji else ""
        self.console.print(f"{icon}{message}", style="bold green")

    def print_error(self, message: str) -> None:
        """Print error message."""
        icon = "❌ " if self.use_emoji else ""
        self.console.print(f"{icon}{message}", style="bold red")

    def print_warning(self, message: str) -> None:
        """Print warning message."""
        icon = "⚠️  " if self.use_emoji else ""
        self.console.print(f"{icon}{message}", style="bold yellow")

    def print_info(self, message: str) -> None:
        """Print info message."""
        icon = "ℹ️  " if self.use_emoji else ""
        self.console.print(f"{icon}{message}", style="cyan")

    def print_header(self, text: str) -> None:
        """Print section header."""
        self.console.print(f"\n{text}", style="bold underline")

    def print_timestamp(self) -> None:
        """Print current timestamp."""
        now = datetime.now().strftime("%H:%M:%S")
        icon = "🕐 " if self.use_emoji else ""
        self.console.print(f"{icon}[{now}]", style="dim")

    def print_validation_result(self, result: ValidationResult) -> None:
        """Pretty-print validation results with statistics and errors.

        Args:
            result: ValidationResult object with details.
        """
        # Header panel
        if result.success:
            header_text = "Validation Passed"
            header_style = "bold white on green"
            icon = "✅ " if self.use_emoji else ""
        else:
            header_text = "Validation Failed"
            header_style = "bold white on red"
            icon = "❌ " if self.use_emoji else ""

        if result.file_path:
            header_text += f"\nFile: {result.file_path}"

        self.console.print(Panel(f"{icon}{header_text}", style=header_style))

        # Statistics table
        table = Table(show_header=True, header_style="bold cyan", box=None)
        table.add_column("Metric", style="dim", width=20)
        table.add_column("Value", width=30)

        if self.config.output.show_timing:
            table.add_row("Duration", f"{result.duration:.3f}s")

        if result.elements_validated > 0:
            table.add_row("Elements", str(result.elements_validated))

        error_count = len(result.errors)
        warning_count = len(result.warnings)

        if error_count == 0:
            table.add_row("Errors", "[green]0[/green]")
        else:
            table.add_row("Errors", f"[red]{error_count}[/red]")

        if warning_count == 0:
            table.add_row("Warnings", "[green]0[/green]")
        else:
            table.add_row("Warnings", f"[yellow]{warning_count}[/yellow]")

        self.console.print(table)

        # Error details
        if result.errors:
            self.console.print("\n[bold red]Errors:[/bold red]")
            max_errors = self.config.output.max_error_lines
            errors_to_show = result.errors[:max_errors]

            for i, error in enumerate(errors_to_show, 1):
                self._print_error_detail(i, error)

            if len(result.errors) > max_errors:
                remaining = len(result.errors) - max_errors
                self.console.print(
                    f"\n[dim]... and {remaining} more error(s)[/dim]"
                )

        # Warning details
        if result.warnings:
            self.console.print("\n[bold yellow]Warnings:[/bold yellow]")
            max_warnings = self.config.output.max_error_lines
            warnings_to_show = result.warnings[:max_warnings]

            for i, warning in enumerate(warnings_to_show, 1):
                self._print_error_detail(i, warning, is_warning=True)

            if len(result.warnings) > max_warnings:
                remaining = len(result.warnings) - max_warnings
                self.console.print(
                    f"\n[dim]... and {remaining} more warning(s)[/dim]"
                )

    def _print_error_detail(
        self, index: int, error: ValidationError, is_warning: bool = False
    ) -> None:
        """Print detailed error information."""
        style = "yellow" if is_warning else "red"
        icon = "⚠️" if (is_warning and self.use_emoji) else ("❌" if self.use_emoji else "")

        # Error message
        msg = f"  {icon} {index}. [{style}]{error.message}[/{style}]"
        self.console.print(msg)

        # Location info
        location_parts = []
        if error.file_path:
            location_parts.append(f"File: {error.file_path}")
        if error.line is not None:
            location_parts.append(f"Line {error.line}")
        if error.column is not None:
            location_parts.append(f"Column {error.column}")

        if location_parts:
            self.console.print(f"     [dim]{', '.join(location_parts)}[/dim]")

        # Context if available
        if error.context:
            syntax = Syntax(
                error.context,
                "xml",
                line_numbers=True,
                theme="monokai",
                start_line=max(1, (error.line or 1) - 2),
            )
            self.console.print(syntax)

    def create_progress(self, description: str = "Processing") -> "ProgressContext":
        """Create a progress bar context manager.

        Args:
            description: Description text for the progress bar.

        Returns:
            ProgressContext object to use as context manager.
        """
        return ProgressContext(self.console, description, self.config.output.progress_bars)

    def clear_terminal(self) -> None:
        """Clear the terminal screen."""
        if sys.platform == "win32":
            os.system("cls")
        else:
            os.system("clear")

    def print_file_change(self, filepath: str) -> None:
        """Print file change notification."""
        icon = "📝 " if self.use_emoji else ""
        self.console.print(f"\n{icon}Change detected: [cyan]{filepath}[/cyan]")
        self.print_timestamp()

    def print_watch_start(self, pattern: str, command: str) -> None:
        """Print watch mode start message."""
        icon = "👀 " if self.use_emoji else ""
        self.console.print(f"{icon}Watching: [cyan]{pattern}[/cyan]")

        icon = "📝 " if self.use_emoji else ""
        self.console.print(f"{icon}Command: [yellow]{command}[/yellow]")

        self.console.print("[dim]Press Ctrl+C to stop[/dim]\n")

    def print_watch_stop(self) -> None:
        """Print watch mode stop message."""
        icon = "👋 " if self.use_emoji else ""
        self.console.print(f"\n{icon}Stopped watching", style="yellow")

    def print_table(self, title: str, headers: list[str], rows: list[list[str]]) -> None:
        """Print a formatted table.

        Args:
            title: Table title
            headers: List of column headers
            rows: List of row data (each row is a list of strings)
        """
        table = Table(title=title, show_header=True, header_style="bold cyan")

        for header in headers:
            table.add_column(header)

        for row in rows:
            table.add_row(*row)

        self.console.print(table)

    def print_config(self, config_dict: dict[str, Any]) -> None:
        """Print configuration in a formatted table.

        Args:
            config_dict: Dictionary of configuration key-value pairs
        """
        table = Table(
            title="Configuration",
            show_header=True,
            header_style="bold cyan",
            box=None,
        )
        table.add_column("Setting", style="cyan", width=30)
        table.add_column("Value", width=40)

        for key, value in sorted(config_dict.items()):
            if isinstance(value, dict):
                # Flatten nested dicts
                for sub_key, sub_value in value.items():
                    table.add_row(f"{key}.{sub_key}", str(sub_value))
            else:
                table.add_row(key, str(value))

        self.console.print(table)


class ProgressContext:
    """Context manager for progress bars."""

    def __init__(self, console: Console, description: str, enabled: bool = True):
        """Initialize progress context.

        Args:
            console: Rich console instance
            description: Progress description text
            enabled: Whether progress bar is enabled
        """
        self.console = console
        self.description = description
        self.enabled = enabled
        self.progress: Progress | None = None
        self.task_id: TaskID | None = None
        self.start_time = 0.0

    def __enter__(self) -> "ProgressContext":
        """Enter context and create progress bar."""
        self.start_time = time.time()

        if self.enabled:
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=self.console,
            )
            self.progress.__enter__()
            self.task_id = self.progress.add_task(self.description, total=100)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and cleanup progress bar."""
        if self.progress:
            self.progress.__exit__(exc_type, exc_val, exc_tb)

    def update(self, advance: float = 1.0, description: str | None = None) -> None:
        """Update progress.

        Args:
            advance: Amount to advance progress
            description: Optional new description
        """
        if self.progress and self.task_id is not None:
            kwargs = {"advance": advance}
            if description:
                kwargs["description"] = description
            self.progress.update(self.task_id, **kwargs)

    def set_total(self, total: int) -> None:
        """Set total progress amount.

        Args:
            total: Total progress amount
        """
        if self.progress and self.task_id is not None:
            self.progress.update(self.task_id, total=total)

    def elapsed(self) -> float:
        """Get elapsed time in seconds.

        Returns:
            Elapsed time since context was entered.
        """
        return time.time() - self.start_time


# Global formatter instance
_global_formatter: OutputFormatter | None = None


def get_formatter() -> OutputFormatter:
    """Get the global output formatter instance.

    Returns:
        Global OutputFormatter object.
    """
    global _global_formatter
    if _global_formatter is None:
        _global_formatter = OutputFormatter()
    return _global_formatter


def reset_formatter() -> None:
    """Reset the global formatter (useful for testing)."""
    global _global_formatter
    _global_formatter = None
