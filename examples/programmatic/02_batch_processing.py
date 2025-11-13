#!/usr/bin/env python3
"""Batch XML Processing Example - Validating Multiple Projects

This example shows how to efficiently validate multiple XML projects
in a batch using a reusable Validator instance.

Use Cases:
- CI/CD pipelines validating multiple repositories
- Nightly validation jobs across multiple projects
- Monorepo validation with multiple XML-based services
- Quality assurance workflows

Requirements:
- pip install xml-lib
"""

import sys
from pathlib import Path
from typing import List, Tuple

from xml_lib import ValidationResult, create_validator


def batch_validate(
    projects: List[Path],
    schemas_dir: Path,
    guardrails_dir: Path,
) -> List[Tuple[Path, ValidationResult]]:
    """Validate multiple projects efficiently with a shared validator.

    Args:
        projects: List of project directories to validate
        schemas_dir: Shared schemas directory
        guardrails_dir: Shared guardrails directory

    Returns:
        List of (project_path, result) tuples
    """
    # Create a single validator instance to reuse across all projects
    # This is more efficient than creating a new validator for each project
    validator = create_validator(
        schemas_dir=schemas_dir,
        guardrails_dir=guardrails_dir,
        enable_streaming=True,  # Handle large files efficiently
        show_progress=False,  # Disable for batch mode
    )

    results = []

    print(f"Validating {len(projects)} projects...")
    print()

    for i, project in enumerate(projects, 1):
        print(f"[{i}/{len(projects)}] Validating: {project.name}")

        try:
            result = validator.validate_project(project)
            results.append((project, result))

            status = "✓" if result.is_valid else "✗"
            error_count = len(result.errors)
            file_count = len(result.validated_files)

            print(f"  {status} {file_count} files, {error_count} errors")

        except Exception as e:
            print(f"  ✗ Exception: {e}")
            # Create a failed result
            result = ValidationResult(is_valid=False)
            results.append((project, result))

        print()

    return results


def generate_report(
    results: List[Tuple[Path, ValidationResult]],
    output_file: Path,
) -> None:
    """Generate a validation report for all projects.

    Args:
        results: Validation results from batch_validate
        output_file: Path to write the report
    """
    with output_file.open("w") as f:
        f.write("# XML Validation Report\n\n")

        # Summary
        total = len(results)
        valid = sum(1 for _, r in results if r.is_valid)
        invalid = total - valid

        f.write("## Summary\n\n")
        f.write(f"- **Total projects**: {total}\n")
        f.write(f"- **Valid**: {valid} ✓\n")
        f.write(f"- **Invalid**: {invalid} ✗\n")
        f.write(f"- **Success rate**: {valid/total*100:.1f}%\n\n")

        # Detailed results
        f.write("## Detailed Results\n\n")

        for project, result in results:
            status = "✓ PASS" if result.is_valid else "✗ FAIL"
            f.write(f"### {project.name} - {status}\n\n")

            f.write(f"- Files validated: {len(result.validated_files)}\n")
            f.write(f"- Errors: {len(result.errors)}\n")
            f.write(f"- Warnings: {len(result.warnings)}\n")
            f.write(f"- Timestamp: {result.timestamp}\n")

            if result.errors:
                f.write(f"\n**Errors:**\n\n")
                for error in result.errors[:10]:  # Show first 10
                    f.write(f"- `{error.file}:{error.line or '?'}` - {error.message}\n")
                if len(result.errors) > 10:
                    f.write(f"- ... and {len(result.errors) - 10} more\n")

            f.write("\n")

    print(f"Report written to: {output_file}")


def main() -> None:
    """Run batch validation example."""
    print("=" * 70)
    print("XML-Lib: Batch Processing Example")
    print("=" * 70)
    print()

    # Example setup: Discover multiple projects to validate
    # In real usage, these might come from:
    # - Command-line arguments
    # - Configuration files
    # - Directory scanning
    # - CI/CD environment variables

    # For this example, we'll use the current project and examples
    base_path = Path(".")

    # Find project directories
    # In a real scenario, you might have multiple project directories
    projects = [base_path]

    # Check for example projects
    if (base_path / "examples").exists():
        example_projects = [
            p for p in (base_path / "examples").iterdir()
            if p.is_dir() and not p.name.startswith(".")
        ]
        projects.extend(example_projects[:2])  # Add first 2 example dirs

    # Shared schemas and guardrails
    schemas_dir = base_path / "schemas"
    guardrails_dir = base_path / "lib" / "guardrails"

    # Ensure required directories exist
    if not schemas_dir.exists():
        print(f"⚠ Schemas directory not found: {schemas_dir}")
        print("Creating minimal schemas directory...")
        schemas_dir.mkdir(parents=True)

    if not guardrails_dir.exists():
        print(f"⚠ Guardrails directory not found: {guardrails_dir}")
        print("Creating guardrails directory...")
        guardrails_dir.mkdir(parents=True)

    print(f"Projects to validate: {len(projects)}")
    print(f"Schemas directory: {schemas_dir}")
    print(f"Guardrails directory: {guardrails_dir}")
    print()

    # Run batch validation
    results = batch_validate(projects, schemas_dir, guardrails_dir)

    # Generate summary
    print("=" * 70)
    print("Batch Validation Summary")
    print("=" * 70)

    valid_count = sum(1 for _, r in results if r.is_valid)
    invalid_count = len(results) - valid_count

    print(f"Total projects: {len(results)}")
    print(f"Valid: {valid_count} ✓")
    print(f"Invalid: {invalid_count} ✗")
    print(f"Success rate: {valid_count/len(results)*100:.1f}%")
    print()

    # Generate markdown report
    report_file = Path("validation_report.md")
    generate_report(results, report_file)
    print()

    # Exit with appropriate code
    if invalid_count > 0:
        print("⚠ Some projects failed validation")
        sys.exit(1)
    else:
        print("✓ All projects passed validation")
        sys.exit(0)


if __name__ == "__main__":
    main()
