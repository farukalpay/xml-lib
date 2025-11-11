"""XML-Lib: Production-grade XML lifecycle, guardrails, and mathematical engine."""

__version__ = "0.1.0"

# Using old Click-based CLI for backward compatibility with existing workflows
# New Typer CLI available in cli_new.py for future migration
from xml_lib.cli import main as app

__all__ = ["app", "__version__"]
