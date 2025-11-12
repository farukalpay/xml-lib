"""Intelligent autocomplete for xml-lib interactive shell.

Provides context-aware completions for commands, subcommands, flags,
file paths, and configuration options.
"""

import os
from pathlib import Path
from typing import Iterable

from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document

from xml_lib.interactive.config import get_config


class XmlLibCompleter(Completer):
    """Smart autocomplete for xml-lib commands and files."""

    # Main commands
    COMMANDS = [
        "validate",
        "publish",
        "render-pptx",
        "diff",
        "roundtrip",
        "phpify",
        "lint",
        "pipeline",
        "stream",
        "engine",
        "shell",
        "watch",
        "config",
        "help",
        "exit",
        "quit",
        "clear",
    ]

    # Subcommands for each command
    SUBCOMMANDS = {
        "pipeline": ["run", "list", "dry-run", "validate"],
        "stream": ["validate", "generate", "benchmark"],
        "engine": ["export", "visualize"],
        "config": ["show", "set", "get", "reset"],
    }

    # Common flags
    FLAGS = {
        "validate": [
            "--schemas-dir",
            "--guardrails-dir",
            "--output",
            "-o",
            "--jsonl",
            "--strict",
            "--math-policy",
            "--engine-check",
            "--engine-dir",
            "--engine-output",
            "--streaming",
            "--streaming-threshold",
            "--progress",
        ],
        "publish": [
            "--output-dir",
            "-o",
            "--template",
            "--index",
            "--no-index",
        ],
        "render-pptx": [
            "--output",
            "-o",
            "--template",
        ],
        "diff": [
            "--explain",
            "--format",
            "--output",
            "-o",
        ],
        "lint": [
            "--format",
            "--fail-level",
            "--no-check-attribute-order",
            "--no-check-indentation",
            "--no-check-xxe",
        ],
        "pipeline": [
            "--output-dir",
            "-o",
            "--var",
            "-v",
            "--format",
            "--verbose",
            "-V",
        ],
        "stream": [
            "--schema",
            "--checkpoint-interval",
            "--checkpoint-dir",
            "--resume-from",
            "--track-memory",
            "--no-track-memory",
            "--format",
        ],
        "watch": [
            "--command",
            "-c",
            "--debounce",
            "-d",
            "--clear",
            "--no-clear",
        ],
        "config": [],
    }

    # File extensions to complete
    XML_EXTENSIONS = {".xml", ".xsd", ".rng", ".sch"}
    YAML_EXTENSIONS = {".yaml", ".yml"}
    ALL_EXTENSIONS = XML_EXTENSIONS | YAML_EXTENSIONS | {".pptx", ".json"}

    def __init__(self):
        """Initialize completer with config."""
        self.config = get_config()

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        """Generate completions based on current input.

        Args:
            document: Current document/input
            complete_event: Completion event

        Yields:
            Completion objects for suggestions
        """
        text = document.text_before_cursor
        words = text.split()

        # Empty input - suggest commands
        if not words or (len(words) == 1 and not text.endswith(" ")):
            prefix = words[0] if words else ""
            yield from self._complete_commands(prefix)

        # After a command - suggest subcommands, flags, or files
        elif len(words) >= 1:
            command = words[0]
            current_word = words[-1] if words and not text.endswith(" ") else ""

            # Check for aliases first
            if command in self.config.aliases.aliases:
                # Expand alias and re-parse
                alias_expansion = self.config.aliases.aliases[command]
                expanded_words = alias_expansion.split() + words[1:]
                command = expanded_words[0]
                words = expanded_words

            # Subcommand completion
            if len(words) == 1 or (len(words) == 2 and not text.endswith(" ")):
                if command in self.SUBCOMMANDS:
                    prefix = words[1] if len(words) == 2 else ""
                    yield from self._complete_subcommands(command, prefix)

            # Flag completion (words starting with -)
            if current_word.startswith("-"):
                yield from self._complete_flags(command, current_word)

            # File path completion
            elif not current_word.startswith("-"):
                # Determine what file types to suggest based on command
                extensions = self._get_relevant_extensions(command, words)
                yield from self._complete_file_paths(current_word, extensions)

    def _complete_commands(self, prefix: str) -> Iterable[Completion]:
        """Complete command names.

        Args:
            prefix: Current input prefix

        Yields:
            Command completions
        """
        for cmd in self.COMMANDS:
            if cmd.startswith(prefix):
                yield Completion(
                    cmd,
                    start_position=-len(prefix),
                    display_meta=self._get_command_description(cmd),
                )

        # Add aliases
        for alias in self.config.aliases.aliases:
            if alias.startswith(prefix):
                expansion = self.config.aliases.aliases[alias]
                yield Completion(
                    alias,
                    start_position=-len(prefix),
                    display_meta=f"alias: {expansion}",
                )

    def _complete_subcommands(
        self, command: str, prefix: str
    ) -> Iterable[Completion]:
        """Complete subcommand names.

        Args:
            command: Parent command
            prefix: Current input prefix

        Yields:
            Subcommand completions
        """
        if command in self.SUBCOMMANDS:
            for subcmd in self.SUBCOMMANDS[command]:
                if subcmd.startswith(prefix):
                    yield Completion(
                        subcmd,
                        start_position=-len(prefix),
                        display_meta=self._get_subcommand_description(
                            command, subcmd
                        ),
                    )

    def _complete_flags(self, command: str, prefix: str) -> Iterable[Completion]:
        """Complete flag names.

        Args:
            command: Current command
            prefix: Current input prefix (with -)

        Yields:
            Flag completions
        """
        # Get command-specific flags
        flags = self.FLAGS.get(command, [])

        # Add common flags
        common_flags = ["--help", "-h", "--version"]
        all_flags = flags + common_flags

        for flag in all_flags:
            if flag.startswith(prefix):
                yield Completion(
                    flag,
                    start_position=-len(prefix),
                    display_meta=self._get_flag_description(flag),
                )

    def _complete_file_paths(
        self, partial: str, extensions: set[str] | None = None
    ) -> Iterable[Completion]:
        """Complete file paths.

        Args:
            partial: Partial path input
            extensions: Set of file extensions to filter by

        Yields:
            File path completions
        """
        # Handle empty input - suggest current directory files
        if not partial:
            directory = Path(".")
            prefix = ""
        else:
            path = Path(partial)
            if partial.endswith("/"):
                directory = path
                prefix = ""
            else:
                directory = path.parent if path.parent.name else Path(".")
                prefix = path.name

        # Ensure directory exists
        if not directory.exists():
            return

        try:
            entries = list(directory.iterdir())
        except PermissionError:
            return

        # Sort: directories first, then files
        entries.sort(key=lambda p: (not p.is_dir(), p.name.lower()))

        for entry in entries:
            name = entry.name

            # Skip hidden files unless explicitly requested
            if name.startswith(".") and not prefix.startswith("."):
                continue

            # Check if matches prefix
            if not name.startswith(prefix):
                continue

            # For files, check extension if specified
            if entry.is_file() and extensions:
                if not any(name.endswith(ext) for ext in extensions):
                    continue

            # Calculate relative path
            if directory == Path("."):
                completion_text = name
            else:
                completion_text = str(entry)

            # Add trailing slash for directories
            display = name
            if entry.is_dir():
                completion_text += "/"
                display += "/"

            yield Completion(
                completion_text,
                start_position=-len(prefix) if prefix else 0,
                display=display,
                display_meta="dir" if entry.is_dir() else self._get_file_meta(entry),
            )

    def _get_relevant_extensions(
        self, command: str, words: list[str]
    ) -> set[str] | None:
        """Get relevant file extensions based on command and context.

        Args:
            command: Current command
            words: All words in input

        Returns:
            Set of relevant extensions or None for all files
        """
        # Check for schema/xsd flags
        if len(words) >= 2:
            prev_word = words[-2]
            if prev_word in ("--schema", "--xsd"):
                return {".xsd", ".rng"}
            elif prev_word in ("--template",):
                if command == "render-pptx":
                    return {".pptx"}
                return self.ALL_EXTENSIONS

        # Command-specific extensions
        if command in ("validate", "publish", "diff", "lint"):
            return self.XML_EXTENSIONS
        elif command == "pipeline":
            # Pipeline files are YAML
            return self.YAML_EXTENSIONS
        elif command == "render-pptx":
            return self.XML_EXTENSIONS
        elif command == "stream":
            return self.XML_EXTENSIONS

        # Default: all recognized extensions
        return self.ALL_EXTENSIONS

    def _get_file_meta(self, path: Path) -> str:
        """Get metadata for file completion.

        Args:
            path: File path

        Returns:
            Metadata string
        """
        if not path.is_file():
            return ""

        suffix = path.suffix.lower()
        size = path.stat().st_size

        # Format size
        if size < 1024:
            size_str = f"{size}B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f}KB"
        else:
            size_str = f"{size / (1024 * 1024):.1f}MB"

        return f"{suffix} {size_str}"

    def _get_command_description(self, command: str) -> str:
        """Get short description for command.

        Args:
            command: Command name

        Returns:
            Short description
        """
        descriptions = {
            "validate": "Validate XML documents",
            "publish": "Generate HTML documentation",
            "render-pptx": "Create PowerPoint presentation",
            "diff": "Compare XML documents",
            "roundtrip": "Round-trip XML processing",
            "phpify": "Generate PHP pages",
            "lint": "Check XML formatting",
            "pipeline": "Run automation pipeline",
            "stream": "Stream large files",
            "engine": "Mathematical engine",
            "watch": "Watch files for changes",
            "config": "Manage configuration",
            "help": "Show help",
            "exit": "Exit shell",
            "quit": "Exit shell",
            "clear": "Clear screen",
        }
        return descriptions.get(command, "")

    def _get_subcommand_description(self, command: str, subcommand: str) -> str:
        """Get short description for subcommand.

        Args:
            command: Parent command
            subcommand: Subcommand name

        Returns:
            Short description
        """
        descriptions = {
            "pipeline": {
                "run": "Execute pipeline",
                "list": "List templates",
                "dry-run": "Preview execution",
                "validate": "Check pipeline",
            },
            "stream": {
                "validate": "Validate large file",
                "generate": "Generate test data",
                "benchmark": "Run benchmarks",
            },
            "engine": {
                "export": "Export proofs",
                "visualize": "Visualize proofs",
            },
            "config": {
                "show": "Show configuration",
                "set": "Set config value",
                "get": "Get config value",
                "reset": "Reset to defaults",
            },
        }
        return descriptions.get(command, {}).get(subcommand, "")

    def _get_flag_description(self, flag: str) -> str:
        """Get short description for flag.

        Args:
            flag: Flag name

        Returns:
            Short description
        """
        descriptions = {
            "--help": "Show help",
            "-h": "Show help",
            "--version": "Show version",
            "--output": "Output file/directory",
            "-o": "Output file/directory",
            "--schema": "XSD schema file",
            "--strict": "Strict mode",
            "--format": "Output format",
            "--verbose": "Verbose output",
            "-v": "Variable or verbose",
            "-V": "Verbose output",
            "--streaming": "Enable streaming",
            "--progress": "Show progress",
        }
        return descriptions.get(flag, "")
