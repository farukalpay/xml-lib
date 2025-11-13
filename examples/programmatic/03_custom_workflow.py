#!/usr/bin/env python3
"""Custom Workflow Example - Integrating xml-lib into Your Pipeline

This example demonstrates how to integrate xml-lib into a custom workflow
with validation, linting, and conditional publishing based on results.

Use Cases:
- Documentation build pipelines
- Automated quality checks with custom logic
- Multi-stage validation workflows
- Integration with existing tooling

Requirements:
- pip install xml-lib
"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional

from xml_lib import lint_xml, validate_xml
from xml_lib.linter import LintLevel


class XMLWorkflow:
    """Custom XML processing workflow with validation, linting, and publishing."""

    def __init__(
        self,
        project_path: Path,
        schemas_dir: Path,
        guardrails_dir: Path,
        strict_mode: bool = False,
    ):
        """Initialize workflow.

        Args:
            project_path: Project directory to process
            schemas_dir: Schemas directory
            guardrails_dir: Guardrails directory
            strict_mode: Whether to treat warnings as errors
        """
        self.project_path = project_path
        self.schemas_dir = schemas_dir
        self.guardrails_dir = guardrails_dir
        self.strict_mode = strict_mode
        self.results: Dict[str, any] = {}

    def run(self) -> bool:
        """Execute the complete workflow.

        Returns:
            True if workflow completed successfully, False otherwise
        """
        print("=" * 70)
        print("XML Processing Workflow")
        print("=" * 70)
        print(f"Project: {self.project_path}")
        print(f"Strict mode: {self.strict_mode}")
        print()

        # Stage 1: Lint files for formatting and security
        if not self._stage_lint():
            return False

        # Stage 2: Validate against schemas and guardrails
        if not self._stage_validate():
            return False

        # Stage 3: Generate artifacts (if validation passed)
        self._stage_generate_artifacts()

        # Stage 4: Create summary report
        self._stage_create_report()

        print()
        print("=" * 70)
        print("Workflow completed successfully!")
        print("=" * 70)

        return True

    def _stage_lint(self) -> bool:
        """Stage 1: Lint XML files for issues."""
        print("Stage 1: Linting XML files")
        print("-" * 70)

        result = lint_xml(
            self.project_path,
            check_indentation=True,
            check_attribute_order=True,
            check_external_entities=True,
            indent_size=2,
        )

        self.results["lint"] = {
            "files_checked": result.files_checked,
            "error_count": result.error_count,
            "warning_count": result.warning_count,
        }

        print(f"Files checked: {result.files_checked}")
        print(f"Errors: {result.error_count}")
        print(f"Warnings: {result.warning_count}")

        # Show issues grouped by severity
        if result.issues:
            print("\nIssues found:")
            for level in [LintLevel.ERROR, LintLevel.WARNING, LintLevel.INFO]:
                issues = [i for i in result.issues if i.level == level]
                if issues:
                    print(f"\n  {level.value.upper()}S:")
                    for issue in issues[:5]:  # Show first 5
                        print(f"    {issue.format_text()}")
                    if len(issues) > 5:
                        print(f"    ... and {len(issues) - 5} more")

        # Determine if we should continue
        has_blockers = result.has_errors or (self.strict_mode and result.warning_count > 0)

        if has_blockers:
            print("\n✗ Linting failed - workflow stopped")
            return False
        else:
            print("\n✓ Linting passed")
            return True

    def _stage_validate(self) -> bool:
        """Stage 2: Validate XML files."""
        print("\nStage 2: Validating XML files")
        print("-" * 70)

        result = validate_xml(
            self.project_path,
            schemas_dir=self.schemas_dir,
            guardrails_dir=self.guardrails_dir,
            enable_streaming=True,
            show_progress=False,
        )

        self.results["validation"] = {
            "is_valid": result.is_valid,
            "error_count": len(result.errors),
            "warning_count": len(result.warnings),
            "validated_files": len(result.validated_files),
            "used_streaming": result.used_streaming,
        }

        print(f"Files validated: {len(result.validated_files)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Warnings: {len(result.warnings)}")
        print(f"Streaming: {'Yes' if result.used_streaming else 'No'}")

        # Show validation errors
        if result.errors:
            print("\nValidation errors:")
            for error in result.errors[:5]:
                print(f"  {error.file}:{error.line or '?'}")
                print(f"    {error.message}")
                print(f"    [Rule: {error.rule}]")
            if len(result.errors) > 5:
                print(f"  ... and {len(result.errors) - 5} more")

        if not result.is_valid:
            print("\n✗ Validation failed - workflow stopped")
            return False
        else:
            print("\n✓ Validation passed")
            return True

    def _stage_generate_artifacts(self) -> None:
        """Stage 3: Generate build artifacts."""
        print("\nStage 3: Generating artifacts")
        print("-" * 70)

        # In a real workflow, you might:
        # - Publish HTML documentation
        # - Generate PHP pages
        # - Create PowerPoint presentations
        # - Export to other formats

        artifacts_dir = self.project_path / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)

        # Example: Create a validation stamp file
        stamp_file = artifacts_dir / "validation_stamp.txt"
        stamp_file.write_text(f"Validated successfully at {self.results.get('validation', {}).get('timestamp', 'unknown')}\n")

        print(f"✓ Artifacts generated in: {artifacts_dir}")

        self.results["artifacts"] = {
            "directory": str(artifacts_dir),
            "files": [str(stamp_file)],
        }

    def _stage_create_report(self) -> None:
        """Stage 4: Create summary report."""
        print("\nStage 4: Creating summary report")
        print("-" * 70)

        report_file = self.project_path / "workflow_report.json"

        report = {
            "project": str(self.project_path),
            "strict_mode": self.strict_mode,
            "results": self.results,
        }

        report_file.write_text(json.dumps(report, indent=2))

        print(f"✓ Report saved to: {report_file}")


def main() -> None:
    """Run custom workflow example."""
    # Configuration
    project_path = Path(".")
    schemas_dir = project_path / "schemas"
    guardrails_dir = project_path / "lib" / "guardrails"

    # Ensure directories exist
    schemas_dir.mkdir(exist_ok=True)
    guardrails_dir.mkdir(parents=True, exist_ok=True)

    # Create and run workflow
    workflow = XMLWorkflow(
        project_path=project_path,
        schemas_dir=schemas_dir,
        guardrails_dir=guardrails_dir,
        strict_mode=False,  # Set to True to treat warnings as errors
    )

    success = workflow.run()

    # Exit with appropriate code
    import sys
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
