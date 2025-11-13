"""Configuration for mutmut mutation testing.

Run mutation tests with:
    mutmut run --paths-to-mutate=xml_lib/

View results with:
    mutmut results
    mutmut html

Apply a specific mutation to see what changed:
    mutmut apply <id>
"""


def pre_mutation(context):
    """Filter which files and lines to mutate.

    Args:
        context: Mutation context with line, filename, etc.

    Returns:
        True to allow mutation, False to skip
    """
    # Skip test files
    if "test_" in context.filename or "/tests/" in context.filename:
        return False

    # Skip __init__.py files (mostly imports)
    if context.filename.endswith("__init__.py"):
        return False

    # Skip CLI files (hard to mutation test CLIs effectively)
    if "cli.py" in context.filename or "cli_new.py" in context.filename:
        return False

    # Skip generated or vendored code
    if "/vendor/" in context.filename or "/generated/" in context.filename:
        return False

    # Allow mutation for core modules
    return True


# Paths to mutate (can also specify on command line)
paths_to_mutate = [
    "xml_lib/validator.py",
    "xml_lib/sanitize.py",
    "xml_lib/linter.py",
    "xml_lib/publisher.py",
    "xml_lib/schema.py",
    "xml_lib/lifecycle.py",
    "xml_lib/guardrails.py",
]

# Test command (pytest)
runner = "pytest -x --tb=short -q"

# Directories to exclude
exclude_patterns = [
    "tests/",
    "docs/",
    ".venv/",
    "build/",
    "dist/",
]
