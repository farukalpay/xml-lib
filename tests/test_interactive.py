"""Tests for interactive features (shell, watch, config, output)."""

import tempfile
from pathlib import Path

import pytest

from xml_lib.interactive import Config, OutputFormatter, ValidationError, ValidationResult


class TestConfig:
    """Test configuration management."""

    def test_default_config(self):
        """Test default configuration values."""
        config = Config()

        assert config.output.colors is True
        assert config.output.emoji is True
        assert config.output.verbose is False
        assert config.watch.debounce_seconds == 0.5
        assert config.shell.prompt == "xml-lib> "

    def test_config_get_set(self):
        """Test getting and setting configuration values."""
        config = Config()

        # Test get
        assert config.get("output.colors") is True
        assert config.get("shell.prompt") == "xml-lib> "

        # Test set
        assert config.set("output.colors", False) is True
        assert config.get("output.colors") is False

        assert config.set("shell.prompt", ">>> ") is True
        assert config.get("shell.prompt") == ">>> "

    def test_config_aliases(self):
        """Test alias configuration."""
        config = Config()

        # Set alias
        config.aliases.set("v", "validate --schema schema.xsd")
        assert config.aliases.get("v") == "validate --schema schema.xsd"

        # Remove alias
        assert config.aliases.remove("v") is True
        assert config.aliases.get("v") is None

    def test_config_save_load(self):
        """Test saving and loading configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"

            # Create and save config
            config1 = Config()
            config1.set("output.emoji", False)
            config1.aliases.set("v", "validate")
            config1.save(config_file)

            # Load config
            config2 = Config.load(config_file)
            assert config2.get("output.emoji") is False
            assert config2.aliases.get("v") == "validate"

    def test_config_reset(self):
        """Test resetting configuration to defaults."""
        config = Config()

        # Modify config
        config.set("output.emoji", False)
        config.aliases.set("test", "test command")

        # Reset
        config.reset()

        # Check defaults restored
        assert config.get("output.emoji") is True
        assert len(config.aliases.aliases) == 0


class TestOutputFormatter:
    """Test output formatting."""

    def test_formatter_creation(self):
        """Test creating output formatter."""
        formatter = OutputFormatter(force_color=False)
        assert formatter is not None
        assert formatter.console is not None

    def test_validation_result_success(self):
        """Test formatting successful validation result."""
        formatter = OutputFormatter(force_color=False)

        result = ValidationResult(
            success=True,
            duration=0.234,
            elements_validated=100,
            file_path="test.xml",
        )

        # Should not raise exception
        formatter.print_validation_result(result)

    def test_validation_result_with_errors(self):
        """Test formatting validation result with errors."""
        formatter = OutputFormatter(force_color=False)

        errors = [
            ValidationError(
                message="Invalid element 'foo'",
                line=10,
                column=5,
                file_path="test.xml",
            ),
            ValidationError(
                message="Missing attribute 'id'",
                line=15,
                column=3,
                file_path="test.xml",
            ),
        ]

        result = ValidationResult(
            success=False,
            duration=0.123,
            errors=errors,
            elements_validated=50,
            file_path="test.xml",
        )

        # Should not raise exception
        formatter.print_validation_result(result)

    def test_validation_result_with_warnings(self):
        """Test formatting validation result with warnings."""
        formatter = OutputFormatter(force_color=False)

        warnings = [
            ValidationError(
                message="Deprecated element 'old-tag'",
                line=20,
                column=8,
            ),
        ]

        result = ValidationResult(
            success=True,
            duration=0.156,
            warnings=warnings,
            elements_validated=75,
        )

        # Should not raise exception
        formatter.print_validation_result(result)

    def test_progress_context(self):
        """Test progress bar context manager."""
        formatter = OutputFormatter(force_color=False)

        with formatter.create_progress("Testing") as progress:
            assert progress is not None
            progress.update(10)
            progress.set_total(100)
            assert progress.elapsed() >= 0

    def test_messages(self):
        """Test various message types."""
        formatter = OutputFormatter(force_color=False)

        # Should not raise exceptions
        formatter.print_success("Success message")
        formatter.print_error("Error message")
        formatter.print_warning("Warning message")
        formatter.print_info("Info message")
        formatter.print_header("Header")


class TestCompleter:
    """Test command completion."""

    def test_completer_import(self):
        """Test importing completer."""
        from xml_lib.interactive.completer import XmlLibCompleter

        completer = XmlLibCompleter()
        assert completer is not None

    def test_completer_commands(self):
        """Test command suggestions."""
        from xml_lib.interactive.completer import XmlLibCompleter

        completer = XmlLibCompleter()
        assert "validate" in completer.COMMANDS
        assert "pipeline" in completer.COMMANDS
        assert "watch" in completer.COMMANDS
        assert "config" in completer.COMMANDS
        assert "shell" in completer.COMMANDS

    def test_completer_subcommands(self):
        """Test subcommand suggestions."""
        from xml_lib.interactive.completer import XmlLibCompleter

        completer = XmlLibCompleter()
        assert "run" in completer.SUBCOMMANDS["pipeline"]
        assert "validate" in completer.SUBCOMMANDS["stream"]
        assert "show" in completer.SUBCOMMANDS["config"]


class TestWatcher:
    """Test file watching functionality."""

    def test_watcher_import(self):
        """Test importing watcher."""
        from xml_lib.interactive.watcher import FileWatcherService, XmlFileWatcher

        assert FileWatcherService is not None
        assert XmlFileWatcher is not None

    def test_watcher_creation(self):
        """Test creating file watcher."""
        from xml_lib.interactive.watcher import XmlFileWatcher

        watcher = XmlFileWatcher(
            pattern="*.xml",
            command="validate {file}",
            debounce_sec=0.5,
        )

        assert watcher.pattern == "*.xml"
        assert watcher.command == "validate {file}"
        assert watcher.debounce_sec == 0.5

    def test_watcher_pattern_matching(self):
        """Test file pattern matching."""
        from xml_lib.interactive.watcher import XmlFileWatcher

        watcher = XmlFileWatcher(
            pattern="*.xml",
            command="validate {file}",
        )

        assert watcher._matches_pattern("test.xml") is True
        assert watcher._matches_pattern("test.txt") is False
        assert watcher._matches_pattern("data/test.xml") is True


class TestShell:
    """Test interactive shell."""

    def test_shell_import(self):
        """Test importing shell."""
        from xml_lib.interactive.shell import XmlLibShell

        assert XmlLibShell is not None

    def test_shell_creation(self):
        """Test creating shell instance."""
        from xml_lib.interactive.shell import XmlLibShell

        shell = XmlLibShell()
        assert shell is not None
        assert shell.config is not None
        assert shell.formatter is not None

    def test_shell_builtin_commands(self):
        """Test built-in commands."""
        from xml_lib.interactive.shell import XmlLibShell

        shell = XmlLibShell()
        assert "help" in shell.BUILTIN_COMMANDS
        assert "exit" in shell.BUILTIN_COMMANDS
        assert "config" in shell.BUILTIN_COMMANDS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
