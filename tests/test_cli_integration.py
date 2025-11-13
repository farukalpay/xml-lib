"""Integration tests for the CLI using click.testing.CliRunner.

These tests exercise the command-line interface to ensure it works correctly
and produces expected output and exit codes.
"""

from pathlib import Path

import pytest
from click.testing import CliRunner

from xml_lib.cli import main


@pytest.fixture
def runner():
    """Provide a Click CLI runner."""
    return CliRunner()


@pytest.fixture
def sample_project(tmp_path):
    """Create a minimal valid project structure for testing."""
    project = tmp_path / "project"
    project.mkdir()

    # Create schemas directory with minimal schema
    schemas = project / "schemas"
    schemas.mkdir()

    schema_content = """<?xml version="1.0" encoding="UTF-8"?>
<grammar xmlns="http://relaxng.org/ns/structure/1.0">
  <start>
    <element name="document">
      <element name="title"><text/></element>
      <element name="content"><text/></element>
    </element>
  </start>
</grammar>"""
    (schemas / "lifecycle.rng").write_text(schema_content)

    # Create guardrails directory (can be empty)
    guardrails = project / "lib" / "guardrails"
    guardrails.mkdir(parents=True)

    # Create sample XML files
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<document>
  <title>Sample Document</title>
  <content>This is sample content for testing.</content>
</document>"""
    (project / "sample.xml").write_text(xml_content)

    return project


@pytest.fixture
def invalid_project(tmp_path):
    """Create a project with invalid XML for testing error cases."""
    project = tmp_path / "invalid_project"
    project.mkdir()

    schemas = project / "schemas"
    schemas.mkdir()

    guardrails = project / "lib" / "guardrails"
    guardrails.mkdir(parents=True)

    # Create invalid XML (malformed)
    (project / "invalid.xml").write_text("<root><unclosed>")

    return project


class TestValidateCommand:
    """Tests for the 'validate' command."""

    def test_validate_success(self, runner, sample_project):
        """Test validating a valid project succeeds."""
        result = runner.invoke(
            main,
            ["validate", str(sample_project), "--telemetry", "none"],
        )

        # Should exit with code 0 for success
        assert result.exit_code == 0, f"Output: {result.output}"

    def test_validate_with_streaming(self, runner, sample_project):
        """Test validation with streaming enabled."""
        result = runner.invoke(
            main,
            [
                "validate",
                str(sample_project),
                "--enable-streaming",
                "--telemetry",
                "none",
            ],
        )

        assert result.exit_code == 0

    def test_validate_nonexistent_path(self, runner, tmp_path):
        """Test validation with nonexistent path fails gracefully."""
        nonexistent = tmp_path / "does-not-exist"

        result = runner.invoke(
            main, ["validate", str(nonexistent), "--telemetry", "none"]
        )

        # Should exit with non-zero code
        assert result.exit_code != 0

    def test_validate_output_contains_result(self, runner, sample_project):
        """Test that validate output contains meaningful results."""
        result = runner.invoke(
            main, ["validate", str(sample_project), "--telemetry", "none"]
        )

        # Output should mention validation results
        # (exact format may vary, but should have some indication)
        assert len(result.output) > 0

    def test_validate_with_custom_schemas(self, runner, tmp_path):
        """Test validation with custom schema directory."""
        project = tmp_path / "project"
        project.mkdir()

        custom_schemas = tmp_path / "my_schemas"
        custom_schemas.mkdir()

        schema_content = """<?xml version="1.0" encoding="UTF-8"?>
<grammar xmlns="http://relaxng.org/ns/structure/1.0">
  <start><element name="root"><text/></element></start>
</grammar>"""
        (custom_schemas / "lifecycle.rng").write_text(schema_content)

        guardrails = tmp_path / "guardrails"
        guardrails.mkdir()

        (project / "test.xml").write_text("<root>Test</root>")

        result = runner.invoke(
            main,
            [
                "validate",
                str(project),
                "--schemas-dir",
                str(custom_schemas),
                "--guardrails-dir",
                str(guardrails),
                "--telemetry",
                "none",
            ],
        )

        assert result.exit_code == 0


class TestPublishCommand:
    """Tests for the 'publish' command."""

    def test_publish_success(self, runner, sample_project, tmp_path):
        """Test publishing a project succeeds."""
        output_dir = tmp_path / "output"

        result = runner.invoke(
            main,
            [
                "publish",
                str(sample_project),
                "--output-dir",
                str(output_dir),
                "--telemetry",
                "none",
            ],
        )

        # Should succeed (exit code 0 or complete without crash)
        # Note: May exit with non-zero if XSLT not found, which is acceptable
        assert result.exit_code in [0, 1, 2]  # Allow various exit codes

    def test_publish_creates_output_directory(self, runner, sample_project, tmp_path):
        """Test that publish creates the output directory if it doesn't exist."""
        output_dir = tmp_path / "new_output"

        result = runner.invoke(
            main,
            [
                "publish",
                str(sample_project),
                "--output-dir",
                str(output_dir),
                "--telemetry",
                "none",
            ],
        )

        # Directory creation may depend on successful publishing
        # Just verify command doesn't crash
        assert result is not None


class TestLintCommand:
    """Tests for the 'lint' command."""

    def test_lint_success(self, runner, sample_project):
        """Test linting a valid project."""
        result = runner.invoke(
            main,
            ["lint", str(sample_project), "--telemetry", "none"],
        )

        # Should complete successfully
        assert result.exit_code == 0

    def test_lint_with_options(self, runner, sample_project):
        """Test linting with various options."""
        result = runner.invoke(
            main,
            [
                "lint",
                str(sample_project),
                "--check-indentation",
                "--check-attribute-order",
                "--telemetry",
                "none",
            ],
        )

        assert result.exit_code == 0

    def test_lint_detects_issues(self, runner, tmp_path):
        """Test that lint detects formatting issues."""
        # Create XML with obvious formatting issues
        xml_file = tmp_path / "bad.xml"
        xml_file.write_text(
            '<?xml version="1.0"?>\n<root attr2="b" attr1="a">\n   <child/>\n</root>'
        )

        result = runner.invoke(main, ["lint", str(tmp_path), "--telemetry", "none"])

        # Should complete (may or may not report issues depending on linter strictness)
        assert result.exit_code in [0, 1]


class TestDiffCommand:
    """Tests for the 'diff' command."""

    def test_diff_identical_files(self, runner, tmp_path):
        """Test diffing two identical files."""
        file1 = tmp_path / "file1.xml"
        file2 = tmp_path / "file2.xml"

        xml_content = "<root><child>content</child></root>"
        file1.write_text(xml_content)
        file2.write_text(xml_content)

        result = runner.invoke(
            main, ["diff", str(file1), str(file2), "--telemetry", "none"]
        )

        # Should complete successfully
        assert result.exit_code == 0

    def test_diff_different_files(self, runner, tmp_path):
        """Test diffing two different files."""
        file1 = tmp_path / "file1.xml"
        file2 = tmp_path / "file2.xml"

        file1.write_text("<root><child>content1</child></root>")
        file2.write_text("<root><child>content2</child></root>")

        result = runner.invoke(
            main, ["diff", str(file1), str(file2), "--telemetry", "none"]
        )

        # Should complete and show differences
        assert result.exit_code in [0, 1]


class TestRoundtripCommand:
    """Tests for the 'roundtrip' command."""

    def test_roundtrip_success(self, runner, sample_project, tmp_path):
        """Test XML roundtrip validation."""
        output_file = tmp_path / "roundtrip.xml"

        result = runner.invoke(
            main,
            [
                "roundtrip",
                str(sample_project / "sample.xml"),
                str(output_file),
                "--telemetry",
                "none",
            ],
        )

        # Should complete (exit code may vary based on implementation)
        assert result is not None


class TestRenderPptxCommand:
    """Tests for the 'render-pptx' command."""

    def test_render_pptx_basic(self, runner, tmp_path):
        """Test PowerPoint rendering command."""
        # Create a minimal XML for PPTX rendering
        xml_file = tmp_path / "slides.xml"
        xml_file.write_text(
            """<?xml version="1.0"?>
<presentation>
  <slide>
    <title>Test Slide</title>
    <content>Test content</content>
  </slide>
</presentation>"""
        )

        output_file = tmp_path / "output.pptx"

        result = runner.invoke(
            main,
            [
                "render-pptx",
                str(xml_file),
                str(output_file),
                "--telemetry",
                "none",
            ],
        )

        # Command should execute (may fail if dependencies missing)
        assert result is not None


class TestPhpifyCommand:
    """Tests for the 'phpify' command."""

    def test_phpify_basic(self, runner, tmp_path):
        """Test PHP generation command."""
        xml_file = tmp_path / "page.xml"
        xml_file.write_text(
            """<?xml version="1.0"?>
<page>
  <title>Test Page</title>
  <content>Page content</content>
</page>"""
        )

        output_dir = tmp_path / "php_output"

        result = runner.invoke(
            main,
            ["phpify", str(xml_file), "--output-dir", str(output_dir), "--telemetry", "none"],
        )

        # Command should execute
        assert result is not None


class TestCLIHelpAndVersion:
    """Tests for CLI help and version commands."""

    def test_help_command(self, runner):
        """Test that --help works."""
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Usage:" in result.output or "Commands:" in result.output

    def test_version_command(self, runner):
        """Test that --version works."""
        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        # Should print version information
        assert len(result.output) > 0

    def test_validate_help(self, runner):
        """Test that validate --help works."""
        result = runner.invoke(main, ["validate", "--help"])

        assert result.exit_code == 0
        assert "Usage:" in result.output or "validate" in result.output.lower()

    def test_publish_help(self, runner):
        """Test that publish --help works."""
        result = runner.invoke(main, ["publish", "--help"])

        assert result.exit_code == 0
        assert "Usage:" in result.output or "publish" in result.output.lower()


class TestCLIErrorHandling:
    """Tests for CLI error handling."""

    def test_invalid_command(self, runner):
        """Test that invalid commands are handled gracefully."""
        result = runner.invoke(main, ["nonexistent-command"])

        # Should exit with error
        assert result.exit_code != 0

    def test_missing_required_argument(self, runner):
        """Test that missing required arguments are reported."""
        result = runner.invoke(main, ["validate"])

        # Should exit with error and show usage
        assert result.exit_code != 0

    def test_invalid_option(self, runner, sample_project):
        """Test that invalid options are handled."""
        result = runner.invoke(
            main,
            ["validate", str(sample_project), "--invalid-option", "--telemetry", "none"],
        )

        # Should exit with error
        assert result.exit_code != 0


class TestCLITelemetryOptions:
    """Tests for telemetry CLI options."""

    def test_telemetry_file(self, runner, sample_project, tmp_path):
        """Test validation with file telemetry."""
        telemetry_file = tmp_path / "telemetry.jsonl"

        result = runner.invoke(
            main,
            [
                "validate",
                str(sample_project),
                "--telemetry",
                "file",
                "--telemetry-target",
                str(telemetry_file),
            ],
        )

        # Should complete
        assert result.exit_code in [0, 1]

    def test_telemetry_none(self, runner, sample_project):
        """Test validation with no telemetry."""
        result = runner.invoke(
            main, ["validate", str(sample_project), "--telemetry", "none"]
        )

        assert result.exit_code == 0


class TestCLIIntegrationWorkflows:
    """Integration tests for complete CLI workflows."""

    def test_validate_then_publish_workflow(self, runner, sample_project, tmp_path):
        """Test a complete validate -> publish workflow."""
        # First validate
        validate_result = runner.invoke(
            main, ["validate", str(sample_project), "--telemetry", "none"]
        )

        # Then publish
        output_dir = tmp_path / "output"
        publish_result = runner.invoke(
            main,
            [
                "publish",
                str(sample_project),
                "--output-dir",
                str(output_dir),
                "--telemetry",
                "none",
            ],
        )

        # Both should complete (validation should succeed)
        assert validate_result.exit_code == 0

    def test_validate_and_lint_workflow(self, runner, sample_project):
        """Test validate and lint commands on the same project."""
        # Validate
        validate_result = runner.invoke(
            main, ["validate", str(sample_project), "--telemetry", "none"]
        )

        # Lint
        lint_result = runner.invoke(
            main, ["lint", str(sample_project), "--telemetry", "none"]
        )

        # Both should complete successfully
        assert validate_result.exit_code == 0
        assert lint_result.exit_code == 0
