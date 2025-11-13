#!/usr/bin/env python3
"""Basic XML Validation Example - Getting Started with xml-lib

This example demonstrates the simplest way to use xml-lib programmatically
to validate XML files in your Python projects.

Use Cases:
- Quick validation checks in development scripts
- Pre-commit hooks for XML files
- CI/CD integration for XML validation
- Simple command-line tools

Requirements:
- pip install xml-lib
"""

from pathlib import Path

from xml_lib import quick_validate


def main() -> None:
    """Run a basic validation example."""
    print("=" * 70)
    print("XML-Lib: Basic Validation Example")
    print("=" * 70)
    print()

    # Example 1: Quick validation with defaults
    print("Example 1: Quick validation with sensible defaults")
    print("-" * 70)

    # This assumes your project has:
    # - schemas/ directory with .rng and .sch files
    # - lib/guardrails/ directory (can be empty)
    # - XML files to validate

    project_path = Path(".")  # Current directory

    print(f"Validating project: {project_path.absolute()}")
    print()

    result = quick_validate(project_path)

    # Check validation results
    if result.is_valid:
        print("✓ Validation successful!")
        print(f"  - Validated {len(result.validated_files)} files")
        print(f"  - Generated {len(result.checksums)} checksums")

        if result.validated_files:
            print(f"\nValidated files:")
            for file in result.validated_files[:5]:  # Show first 5
                print(f"  - {file}")
            if len(result.validated_files) > 5:
                print(f"  ... and {len(result.validated_files) - 5} more")

    else:
        print("✗ Validation failed!")
        print(f"  - Found {len(result.errors)} errors")
        print(f"  - Found {len(result.warnings)} warnings")

        print("\nErrors:")
        for error in result.errors[:5]:  # Show first 5 errors
            print(f"  {error.file}:{error.line or '?'}")
            print(f"    {error.message}")
            print(f"    [Rule: {error.rule}]")
            print()

        if len(result.errors) > 5:
            print(f"  ... and {len(result.errors) - 5} more errors")

    # Example 2: With progress indicator for large projects
    print()
    print("Example 2: Validation with progress indicator")
    print("-" * 70)

    result = quick_validate(project_path, show_progress=True)

    print(f"Result: {'✓ Valid' if result.is_valid else '✗ Invalid'}")

    # Example 3: Accessing validation metadata
    print()
    print("Example 3: Accessing validation metadata")
    print("-" * 70)

    print(f"Timestamp: {result.timestamp}")
    print(f"Used streaming: {result.used_streaming}")

    if result.checksums:
        print(f"\nFile checksums (SHA-256):")
        for file, checksum in list(result.checksums.items())[:3]:
            print(f"  {Path(file).name}: {checksum[:16]}...")

    print()
    print("=" * 70)
    print("Done! See examples/programmatic/02_batch_processing.py for more.")
    print("=" * 70)


if __name__ == "__main__":
    main()
