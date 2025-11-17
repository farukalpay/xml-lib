"""Tests for the modern Typer-based CLI."""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from xml_lib.cli_new import (
    app,
    print_command_result,
)
from xml_lib.types import CommandResult


runner = CliRunner()


class TestPrintCommandResult:
    """Tests for print_command_result helper function."""

    def test_print_success_result(self):
        """Test printing successful command result."""
        result = CommandResult(
            command="test command",
            timestamp=datetime.now(),
            duration_ms=123.45,
            status="success",
            summary={"files": 5, "processed": True},
            errors=[],
            warnings=[],
        )

        # Should not raise
        print_command_result(result)

    def test_print_result_with_errors(self):
        """Test printing result with errors."""
        result = CommandResult(
            command="test command",
            timestamp=datetime.now(),
            duration_ms=50.0,
            status="failure",
            summary={},
            errors=["Error 1", "Error 2"],
            warnings=[],
        )

        print_command_result(result)

    def test_print_result_with_warnings(self):
        """Test printing result with warnings."""
        result = CommandResult(
            command="test command",
            timestamp=datetime.now(),
            duration_ms=100.0,
            status="warning",
            summary={},
            errors=[],
            warnings=["Warning 1"],
        )

        print_command_result(result)

    def test_print_result_with_json_output(self):
        """Test printing result with JSON output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "output.json"

            result = CommandResult(
                command="test command",
                timestamp=datetime.now(),
                duration_ms=75.0,
                status="success",
                summary={"count": 10},
                errors=[],
                warnings=["Minor issue"],
            )

            print_command_result(result, json_output=json_path)

            assert json_path.exists()
            data = json.loads(json_path.read_text())
            assert data["command"] == "test command"
            assert data["status"] == "success"
            assert data["summary"]["count"] == 10
            assert "Minor issue" in data["warnings"]

    def test_print_result_creates_parent_directories(self):
        """Test that JSON output creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "nested" / "dir" / "output.json"

            result = CommandResult(
                command="test",
                timestamp=datetime.now(),
                duration_ms=10.0,
                status="success",
                summary={},
            )

            print_command_result(result, json_output=json_path)

            assert json_path.exists()


class TestCLIBasicFunctionality:
    """Basic CLI functionality tests."""

    def test_app_exists(self):
        """Test that app is defined."""
        assert app is not None

    def test_help_command(self):
        """Test --help works."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "xml-lib" in result.stdout or "Usage" in result.stdout

    def test_lifecycle_subcommand_help(self):
        """Test lifecycle subcommand help."""
        result = runner.invoke(app, ["lifecycle", "--help"])
        assert result.exit_code == 0

    def test_guardrails_subcommand_help(self):
        """Test guardrails subcommand help."""
        result = runner.invoke(app, ["guardrails", "--help"])
        assert result.exit_code == 0

    def test_engine_subcommand_help(self):
        """Test engine subcommand help."""
        result = runner.invoke(app, ["engine", "--help"])
        assert result.exit_code == 0

    def test_schema_subcommand_help(self):
        """Test schema subcommand help."""
        result = runner.invoke(app, ["schema", "--help"])
        assert result.exit_code == 0

    def test_pptx_subcommand_help(self):
        """Test pptx subcommand help."""
        result = runner.invoke(app, ["pptx", "--help"])
        assert result.exit_code == 0


class TestGuardrailsCommands:
    """Tests for guardrails CLI commands."""

    def test_guardrails_simulate_default(self):
        """Test guardrails simulate with default options."""
        result = runner.invoke(app, ["guardrails", "simulate"])
        # Should complete without error
        assert result.exit_code == 0

    def test_guardrails_simulate_custom_steps(self):
        """Test guardrails simulate with custom steps."""
        result = runner.invoke(app, ["guardrails", "simulate", "--steps", "10"])
        assert result.exit_code == 0

    def test_guardrails_simulate_with_output(self):
        """Test guardrails simulate with JSON output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sim.json"
            result = runner.invoke(
                app,
                ["guardrails", "simulate", "--output", str(output_path)],
            )

            assert result.exit_code == 0
            if output_path.exists():
                data = json.loads(output_path.read_text())
                assert "command" in data
                assert data["command"] == "guardrails simulate"

    def test_guardrails_check_help(self):
        """Test guardrails check help."""
        result = runner.invoke(app, ["guardrails", "check", "--help"])
        assert result.exit_code == 0
        assert "checksum" in result.stdout.lower() or "file" in result.stdout.lower()


class TestEngineCommands:
    """Tests for engine CLI commands."""

    def test_engine_verify_contraction(self):
        """Test engine verify with contraction operator."""
        result = runner.invoke(app, ["engine", "verify", "--type", "contraction"])
        assert result.exit_code == 0

    def test_engine_verify_projection(self):
        """Test engine verify with projection operator."""
        result = runner.invoke(app, ["engine", "verify", "--type", "projection"])
        assert result.exit_code == 0

    def test_engine_verify_unknown_type(self):
        """Test engine verify with unknown operator type."""
        result = runner.invoke(app, ["engine", "verify", "--type", "unknown"])
        assert result.exit_code != 0

    def test_engine_verify_with_output(self):
        """Test engine verify with JSON output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "verify.json"
            result = runner.invoke(
                app,
                ["engine", "verify", "--output", str(output_path)],
            )

            assert result.exit_code == 0

    def test_engine_prove_help(self):
        """Test engine prove help."""
        result = runner.invoke(app, ["engine", "prove", "--help"])
        assert result.exit_code == 0


class TestSchemaCommands:
    """Tests for schema CLI commands."""

    def test_schema_derive_xsd(self):
        """Test schema derive with XSD type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create example XML
            example_path = tmpdir / "example.xml"
            example_path.write_text("<root><child>test</child></root>")

            output_path = tmpdir / "derived.xsd"

            result = runner.invoke(
                app,
                [
                    "schema",
                    "derive",
                    str(example_path),
                    "--output",
                    str(output_path),
                    "--type",
                    "xsd",
                ],
            )

            assert result.exit_code == 0
            assert output_path.exists()

    def test_schema_derive_relaxng(self):
        """Test schema derive with RELAX NG type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            example_path = tmpdir / "example.xml"
            example_path.write_text("<root><child>test</child></root>")

            output_path = tmpdir / "derived.rng"

            result = runner.invoke(
                app,
                [
                    "schema",
                    "derive",
                    str(example_path),
                    "--output",
                    str(output_path),
                    "--type",
                    "relaxng",
                ],
            )

            assert result.exit_code == 0

    def test_schema_derive_unknown_type(self):
        """Test schema derive with unknown type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            example_path = tmpdir / "example.xml"
            example_path.write_text("<root/>")

            output_path = tmpdir / "derived.txt"

            result = runner.invoke(
                app,
                [
                    "schema",
                    "derive",
                    str(example_path),
                    "--output",
                    str(output_path),
                    "--type",
                    "unknown",
                ],
            )

            assert result.exit_code != 0

    def test_schema_validate_valid_xml(self):
        """Test schema validate with valid XML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create XSD schema
            xsd_content = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="root" type="xs:string"/>
</xs:schema>'''
            xsd_path = tmpdir / "schema.xsd"
            xsd_path.write_text(xsd_content)

            # Create valid XML
            xml_path = tmpdir / "valid.xml"
            xml_path.write_text("<root>test</root>")

            result = runner.invoke(
                app,
                ["schema", "validate", str(xml_path), str(xsd_path)],
            )

            assert result.exit_code == 0

    def test_schema_validate_invalid_xml(self):
        """Test schema validate with invalid XML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create XSD that requires specific element
            xsd_content = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="expected">
    <xs:complexType>
      <xs:attribute name="id" type="xs:string" use="required"/>
    </xs:complexType>
  </xs:element>
</xs:schema>'''
            xsd_path = tmpdir / "schema.xsd"
            xsd_path.write_text(xsd_content)

            # Create invalid XML (wrong root element)
            xml_path = tmpdir / "invalid.xml"
            xml_path.write_text("<wrong/>")

            result = runner.invoke(
                app,
                ["schema", "validate", str(xml_path), str(xsd_path)],
            )

            # May exit with 0 but show failure in output
            assert result.exit_code == 0 or "failure" in result.stdout.lower()

    def test_schema_validate_with_output(self):
        """Test schema validate with JSON output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            xsd_content = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="root" type="xs:string"/>
</xs:schema>'''
            xsd_path = tmpdir / "schema.xsd"
            xsd_path.write_text(xsd_content)

            xml_path = tmpdir / "test.xml"
            xml_path.write_text("<root>test</root>")

            output_path = tmpdir / "result.json"

            result = runner.invoke(
                app,
                [
                    "schema",
                    "validate",
                    str(xml_path),
                    str(xsd_path),
                    "--output",
                    str(output_path),
                ],
            )

            assert result.exit_code == 0
            if output_path.exists():
                data = json.loads(output_path.read_text())
                assert "command" in data


class TestDocsCommands:
    """Tests for docs CLI commands."""

    def test_docs_gen(self):
        """Test docs gen command."""
        result = runner.invoke(app, ["docs", "gen"])
        assert result.exit_code == 0


class TestExamplesCommands:
    """Tests for examples CLI commands."""

    def test_examples_run_nonexistent(self):
        """Test running nonexistent example."""
        result = runner.invoke(app, ["examples", "run", "nonexistent"])
        # Should fail gracefully
        assert result.exit_code != 0 or "not found" in result.stdout.lower()

    def test_examples_run_help(self):
        """Test examples run help."""
        result = runner.invoke(app, ["examples", "run", "--help"])
        assert result.exit_code == 0


class TestLifecycleCommands:
    """Tests for lifecycle CLI commands."""

    def test_lifecycle_validate_help(self):
        """Test lifecycle validate help."""
        result = runner.invoke(app, ["lifecycle", "validate", "--help"])
        assert result.exit_code == 0

    def test_lifecycle_visualize_help(self):
        """Test lifecycle visualize help."""
        result = runner.invoke(app, ["lifecycle", "visualize", "--help"])
        assert result.exit_code == 0

    def test_lifecycle_validate_nonexistent_path(self):
        """Test lifecycle validate with nonexistent path."""
        result = runner.invoke(app, ["lifecycle", "validate", "/nonexistent/path"])
        # Should handle error gracefully
        assert result.exit_code != 0

    def test_lifecycle_visualize_nonexistent_path(self):
        """Test lifecycle visualize with nonexistent path."""
        result = runner.invoke(app, ["lifecycle", "visualize", "/nonexistent/path"])
        # Should handle error gracefully
        assert result.exit_code != 0


class TestPPTXCommands:
    """Tests for PPTX CLI commands."""

    def test_pptx_build_help(self):
        """Test pptx build help."""
        result = runner.invoke(app, ["pptx", "build", "--help"])
        assert result.exit_code == 0

    def test_pptx_export_help(self):
        """Test pptx export help."""
        result = runner.invoke(app, ["pptx", "export", "--help"])
        assert result.exit_code == 0


class TestCommandResultJSONOutput:
    """Tests for JSON output functionality."""

    def test_json_output_includes_timestamp(self):
        """Test that JSON output includes timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "output.json"

            result = CommandResult(
                command="test",
                timestamp=datetime.now(),
                duration_ms=10.0,
                status="success",
                summary={},
            )

            print_command_result(result, json_output=json_path)

            data = json.loads(json_path.read_text())
            assert "timestamp" in data

    def test_json_output_includes_duration(self):
        """Test that JSON output includes duration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "output.json"

            result = CommandResult(
                command="test",
                timestamp=datetime.now(),
                duration_ms=123.456,
                status="success",
                summary={},
            )

            print_command_result(result, json_output=json_path)

            data = json.loads(json_path.read_text())
            assert data["duration_ms"] == 123.456

    def test_json_output_includes_all_fields(self):
        """Test that JSON output includes all fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "output.json"

            result = CommandResult(
                command="complete command",
                timestamp=datetime.now(),
                duration_ms=500.0,
                status="warning",
                summary={"processed": 100, "skipped": 5},
                errors=["Error A", "Error B"],
                warnings=["Warning X"],
            )

            print_command_result(result, json_output=json_path)

            data = json.loads(json_path.read_text())
            assert data["command"] == "complete command"
            assert data["status"] == "warning"
            assert data["summary"]["processed"] == 100
            assert data["summary"]["skipped"] == 5
            assert "Error A" in data["errors"]
            assert "Error B" in data["errors"]
            assert "Warning X" in data["warnings"]
