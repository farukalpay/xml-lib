"""Interactive REPL shell for xml-lib.

Provides an interactive command-line interface with tab completion, command
history, syntax highlighting, and multi-line input support.
"""

import shlex
import sys
from pathlib import Path
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from pygments.lexers.shell import BashLexer

from xml_lib.interactive.completer import XmlLibCompleter
from xml_lib.interactive.config import Config, get_config
from xml_lib.interactive.output import get_formatter


class XmlLibShell:
    """Interactive shell for xml-lib with autocomplete and history."""

    # Built-in shell commands
    BUILTIN_COMMANDS = {"help", "exit", "quit", "clear", "history", "config"}

    def __init__(self, config: Config | None = None):
        """Initialize interactive shell.

        Args:
            config: Optional configuration object. Uses global config if None.
        """
        self.config = config or get_config()
        self.formatter = get_formatter()
        self.running = True

        # Setup history file
        history_file = self.config.get_config_dir() / "history"
        history_file.parent.mkdir(parents=True, exist_ok=True)

        # Create prompt session
        self.session = PromptSession(
            history=FileHistory(str(history_file)),
            completer=XmlLibCompleter(),
            lexer=PygmentsLexer(BashLexer) if self.config.shell.multiline else None,
            style=self._get_style(),
            auto_suggest=(
                AutoSuggestFromHistory() if self.config.shell.auto_suggest else None
            ),
            complete_while_typing=self.config.shell.complete_while_typing,
            vi_mode=self.config.shell.vi_mode,
            multiline=False,  # Single line for now, can be extended
            key_bindings=self._create_key_bindings(),
        )

    def _get_style(self) -> Style:
        """Get prompt_toolkit style.

        Returns:
            Style object for prompt customization
        """
        return Style.from_dict(
            {
                "prompt": "cyan bold",
                "": "#ffffff",
            }
        )

    def _create_key_bindings(self) -> KeyBindings:
        """Create custom key bindings.

        Returns:
            KeyBindings object with custom bindings
        """
        kb = KeyBindings()

        # Ctrl+C: Clear current input
        @kb.add("c-c")
        def _(event):
            event.app.current_buffer.reset()

        # Ctrl+D: Exit if buffer is empty
        @kb.add("c-d")
        def _(event):
            if not event.app.current_buffer.text:
                event.app.exit()

        return kb

    def run(self) -> int:
        """Run the interactive shell loop.

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        # Print welcome banner
        self.formatter.print_banner()

        while self.running:
            try:
                # Get input
                text = self.session.prompt(
                    self.config.shell.prompt,
                    default="",
                )

                # Process command
                if text.strip():
                    self._execute_command(text.strip())

            except KeyboardInterrupt:
                # Ctrl+C: Clear line and continue
                continue

            except EOFError:
                # Ctrl+D: Exit gracefully
                break

            except Exception as e:
                self.formatter.print_error(f"Unexpected error: {e}")
                if self.config.output.verbose:
                    import traceback

                    traceback.print_exc()

        # Goodbye message
        icon = "👋 " if self.config.output.emoji else ""
        self.formatter.console.print(f"\n{icon}Goodbye!", style="bold cyan")
        return 0

    def _execute_command(self, text: str) -> None:
        """Parse and execute a command.

        Args:
            text: Command text to execute
        """
        try:
            # Parse command line
            args = shlex.split(text)
        except ValueError as e:
            self.formatter.print_error(f"Parse error: {e}")
            return

        if not args:
            return

        command = args[0]

        # Check for aliases
        if command in self.config.aliases.aliases:
            alias_expansion = self.config.aliases.aliases[command]
            try:
                expanded_args = shlex.split(alias_expansion) + args[1:]
                args = expanded_args
                command = args[0]
            except ValueError as e:
                self.formatter.print_error(f"Alias expansion error: {e}")
                return

        # Handle built-in commands
        if command in self.BUILTIN_COMMANDS:
            self._execute_builtin(command, args[1:])
            return

        # Execute through CLI
        self._execute_cli_command(args)

    def _execute_builtin(self, command: str, args: list[str]) -> None:
        """Execute a built-in shell command.

        Args:
            command: Built-in command name
            args: Command arguments
        """
        if command == "help":
            self._show_help()
        elif command in ("exit", "quit"):
            self.running = False
        elif command == "clear":
            self.formatter.clear_terminal()
        elif command == "history":
            self._show_history()
        elif command == "config":
            self._handle_config_command(args)

    def _execute_cli_command(self, args: list[str]) -> None:
        """Execute a CLI command.

        Args:
            args: Command arguments (including command name)
        """
        try:
            # Import the CLI main function
            from xml_lib.cli import main

            # Preserve original sys.argv
            original_argv = sys.argv

            try:
                # Set sys.argv for Click
                sys.argv = ["xml-lib"] + args

                # Execute command
                # We need to catch SystemExit since Click calls sys.exit()
                try:
                    main(standalone_mode=False)
                except SystemExit as e:
                    # Non-zero exit code indicates error
                    if e.code != 0:
                        self.formatter.print_error(
                            f"Command failed with exit code {e.code}"
                        )
                except Exception as e:
                    self.formatter.print_error(f"Command error: {e}")
                    if self.config.output.verbose:
                        import traceback

                        traceback.print_exc()

            finally:
                # Restore original sys.argv
                sys.argv = original_argv

        except ImportError as e:
            self.formatter.print_error(f"Failed to import CLI: {e}")

    def _show_help(self) -> None:
        """Show help message with available commands."""
        help_text = """
[bold cyan]XML-LIB Interactive Shell - Available Commands[/bold cyan]

[bold]Main Commands:[/bold]
  validate      Validate XML documents against schemas
  publish       Generate HTML documentation
  render-pptx   Create PowerPoint presentations
  diff          Compare XML documents
  lint          Check XML formatting and security
  pipeline      Run automation pipelines
  stream        Process large XML files
  engine        Mathematical engine operations

[bold]Shell Commands:[/bold]
  help          Show this help message
  config        Manage configuration
  clear         Clear the screen
  history       Show command history
  exit          Exit shell (or press Ctrl+D)
  quit          Exit shell

[bold]Tips:[/bold]
  - Use Tab for command and file completion
  - Use Ctrl+C to cancel current input
  - Use Ctrl+D to exit (when input is empty)
  - Use arrow keys to navigate history
  - Type '<command> --help' for command-specific help

[bold]Examples:[/bold]
  validate data.xml --schema schema.xsd
  pipeline run templates/pipelines/ci-validation.yaml *.xml
  config set output.emoji false
  lint . --format json
"""
        self.formatter.console.print(help_text)

    def _show_history(self) -> None:
        """Show command history."""
        history_file = self.config.get_config_dir() / "history"

        if not history_file.exists():
            self.formatter.print_info("No command history yet")
            return

        try:
            with open(history_file) as f:
                lines = f.readlines()

            if not lines:
                self.formatter.print_info("No command history yet")
                return

            # Show last N commands
            max_history = min(20, len(lines))
            recent = lines[-max_history:]

            self.formatter.console.print("\n[bold]Recent Commands:[/bold]")
            for i, line in enumerate(recent, start=len(lines) - max_history + 1):
                self.formatter.console.print(f"  {i:3d}  {line.rstrip()}")

        except Exception as e:
            self.formatter.print_error(f"Failed to read history: {e}")

    def _handle_config_command(self, args: list[str]) -> None:
        """Handle config subcommands.

        Args:
            args: Config subcommand arguments
        """
        if not args:
            # Show all config
            self._show_config()
            return

        subcommand = args[0]

        if subcommand == "show":
            self._show_config()
        elif subcommand == "get":
            if len(args) < 2:
                self.formatter.print_error("Usage: config get <key>")
                return
            self._get_config_value(args[1])
        elif subcommand == "set":
            if len(args) < 3:
                self.formatter.print_error("Usage: config set <key> <value>")
                return
            self._set_config_value(args[1], args[2])
        elif subcommand == "reset":
            self._reset_config()
        else:
            self.formatter.print_error(f"Unknown config subcommand: {subcommand}")
            self.formatter.print_info(
                "Available: show, get <key>, set <key> <value>, reset"
            )

    def _show_config(self) -> None:
        """Show current configuration."""
        config_dict = {
            "aliases": self.config.aliases.aliases,
            "watch.debounce_seconds": self.config.watch.debounce_seconds,
            "watch.notify": self.config.watch.notify,
            "watch.clear_on_change": self.config.watch.clear_on_change,
            "output.colors": self.config.output.colors,
            "output.emoji": self.config.output.emoji,
            "output.verbose": self.config.output.verbose,
            "output.show_timing": self.config.output.show_timing,
            "shell.prompt": self.config.shell.prompt,
            "shell.history_size": self.config.shell.history_size,
            "shell.vi_mode": self.config.shell.vi_mode,
        }

        self.formatter.print_config(config_dict)

    def _get_config_value(self, key: str) -> None:
        """Get and display a config value.

        Args:
            key: Configuration key
        """
        value = self.config.get(key)
        if value is not None:
            self.formatter.console.print(f"{key} = {value}")
        else:
            self.formatter.print_error(f"Config key not found: {key}")

    def _set_config_value(self, key: str, value: str) -> None:
        """Set a config value.

        Args:
            key: Configuration key
            value: New value
        """
        # Special handling for aliases
        if key.startswith("aliases."):
            alias_name = key.split(".", 1)[1]
            self.config.aliases.set(alias_name, value)
            self.config.save()
            self.formatter.print_success(f"Set alias: {alias_name} = {value}")
            return

        # Set regular config value
        success = self.config.set(key, value)
        if success:
            self.config.save()
            self.formatter.print_success(f"Set {key} = {value}")
        else:
            self.formatter.print_error(f"Invalid config key: {key}")
            self.formatter.print_info(
                "Use 'config show' to see available settings"
            )

    def _reset_config(self) -> None:
        """Reset configuration to defaults."""
        self.config.reset()
        self.config.save()
        self.formatter.print_success("Configuration reset to defaults")


def launch_shell() -> int:
    """Launch the interactive shell.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        shell = XmlLibShell()
        return shell.run()
    except Exception as e:
        print(f"Error: Failed to start shell: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(launch_shell())
