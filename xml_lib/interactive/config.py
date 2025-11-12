"""Configuration management for xml-lib interactive features.

Handles loading, saving, and managing configuration settings for the interactive
shell, watch mode, and output formatting. Supports user-level configuration with
sensible defaults.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class AliasConfig:
    """Command aliases configuration."""

    aliases: dict[str, str] = field(default_factory=dict)

    def get(self, alias: str) -> str | None:
        """Get alias expansion for a given alias name."""
        return self.aliases.get(alias)

    def set(self, alias: str, command: str) -> None:
        """Set an alias."""
        self.aliases[alias] = command

    def remove(self, alias: str) -> bool:
        """Remove an alias. Returns True if alias existed."""
        if alias in self.aliases:
            del self.aliases[alias]
            return True
        return False


@dataclass
class WatchConfig:
    """Watch mode configuration."""

    debounce_seconds: float = 0.5
    notify: bool = False
    clear_on_change: bool = True
    ignore_patterns: list[str] = field(
        default_factory=lambda: [
            "*.swp",
            "*.tmp",
            "*~",
            ".git/*",
            "__pycache__/*",
            "*.pyc",
        ]
    )


@dataclass
class OutputConfig:
    """Output formatting configuration."""

    colors: bool = True
    emoji: bool = True
    verbose: bool = False
    show_timing: bool = True
    progress_bars: bool = True
    max_error_lines: int = 50


@dataclass
class ShellConfig:
    """Interactive shell configuration."""

    prompt: str = "xml-lib> "
    history_size: int = 1000
    multiline: bool = True
    vi_mode: bool = False
    auto_suggest: bool = True
    complete_while_typing: bool = True


@dataclass
class Config:
    """Main configuration container."""

    aliases: AliasConfig = field(default_factory=AliasConfig)
    watch: WatchConfig = field(default_factory=WatchConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    shell: ShellConfig = field(default_factory=ShellConfig)

    @classmethod
    def get_config_dir(cls) -> Path:
        """Get the configuration directory path."""
        config_home = os.environ.get("XDG_CONFIG_HOME")
        if config_home:
            config_dir = Path(config_home) / "xml-lib"
        else:
            config_dir = Path.home() / ".xml-lib"

        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    @classmethod
    def get_config_file(cls) -> Path:
        """Get the configuration file path."""
        return cls.get_config_dir() / "config.yaml"

    @classmethod
    def load(cls, config_file: Path | None = None) -> "Config":
        """Load configuration from file.

        Args:
            config_file: Optional path to config file. Uses default if None.

        Returns:
            Config object with loaded settings or defaults.
        """
        if config_file is None:
            config_file = cls.get_config_file()

        if not config_file.exists():
            return cls()

        try:
            with open(config_file) as f:
                data = yaml.safe_load(f)

            if not data:
                return cls()

            # Load aliases
            alias_config = AliasConfig()
            if "aliases" in data and isinstance(data["aliases"], dict):
                alias_config.aliases = data["aliases"]

            # Load watch config
            watch_config = WatchConfig()
            if "watch" in data and isinstance(data["watch"], dict):
                watch_data = data["watch"]
                if "debounce_seconds" in watch_data:
                    watch_config.debounce_seconds = float(watch_data["debounce_seconds"])
                if "notify" in watch_data:
                    watch_config.notify = bool(watch_data["notify"])
                if "clear_on_change" in watch_data:
                    watch_config.clear_on_change = bool(watch_data["clear_on_change"])
                if "ignore_patterns" in watch_data:
                    watch_config.ignore_patterns = list(watch_data["ignore_patterns"])

            # Load output config
            output_config = OutputConfig()
            if "output" in data and isinstance(data["output"], dict):
                output_data = data["output"]
                if "colors" in output_data:
                    output_config.colors = bool(output_data["colors"])
                if "emoji" in output_data:
                    output_config.emoji = bool(output_data["emoji"])
                if "verbose" in output_data:
                    output_config.verbose = bool(output_data["verbose"])
                if "show_timing" in output_data:
                    output_config.show_timing = bool(output_data["show_timing"])
                if "progress_bars" in output_data:
                    output_config.progress_bars = bool(output_data["progress_bars"])
                if "max_error_lines" in output_data:
                    output_config.max_error_lines = int(output_data["max_error_lines"])

            # Load shell config
            shell_config = ShellConfig()
            if "shell" in data and isinstance(data["shell"], dict):
                shell_data = data["shell"]
                if "prompt" in shell_data:
                    shell_config.prompt = str(shell_data["prompt"])
                if "history_size" in shell_data:
                    shell_config.history_size = int(shell_data["history_size"])
                if "multiline" in shell_data:
                    shell_config.multiline = bool(shell_data["multiline"])
                if "vi_mode" in shell_data:
                    shell_config.vi_mode = bool(shell_data["vi_mode"])
                if "auto_suggest" in shell_data:
                    shell_config.auto_suggest = bool(shell_data["auto_suggest"])
                if "complete_while_typing" in shell_data:
                    shell_config.complete_while_typing = bool(
                        shell_data["complete_while_typing"]
                    )

            return cls(
                aliases=alias_config,
                watch=watch_config,
                output=output_config,
                shell=shell_config,
            )

        except Exception as e:
            # If config is corrupted, return defaults
            import sys

            print(f"Warning: Failed to load config from {config_file}: {e}", file=sys.stderr)
            return cls()

    def save(self, config_file: Path | None = None) -> None:
        """Save configuration to file.

        Args:
            config_file: Optional path to config file. Uses default if None.
        """
        if config_file is None:
            config_file = self.get_config_file()

        config_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "aliases": self.aliases.aliases,
            "watch": {
                "debounce_seconds": self.watch.debounce_seconds,
                "notify": self.watch.notify,
                "clear_on_change": self.watch.clear_on_change,
                "ignore_patterns": self.watch.ignore_patterns,
            },
            "output": {
                "colors": self.output.colors,
                "emoji": self.output.emoji,
                "verbose": self.output.verbose,
                "show_timing": self.output.show_timing,
                "progress_bars": self.output.progress_bars,
                "max_error_lines": self.output.max_error_lines,
            },
            "shell": {
                "prompt": self.shell.prompt,
                "history_size": self.shell.history_size,
                "multiline": self.shell.multiline,
                "vi_mode": self.shell.vi_mode,
                "auto_suggest": self.shell.auto_suggest,
                "complete_while_typing": self.shell.complete_while_typing,
            },
        }

        with open(config_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def get(self, key: str) -> Any:
        """Get a configuration value by dot-separated key.

        Args:
            key: Dot-separated key (e.g., 'output.colors', 'shell.prompt')

        Returns:
            The configuration value or None if not found.
        """
        parts = key.split(".")
        current: Any = self

        for part in parts:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                return None

        return current

    def set(self, key: str, value: Any) -> bool:
        """Set a configuration value by dot-separated key.

        Args:
            key: Dot-separated key (e.g., 'output.colors', 'shell.prompt')
            value: Value to set

        Returns:
            True if successful, False if key not found.
        """
        parts = key.split(".")
        if len(parts) < 2:
            return False

        current: Any = self
        for part in parts[:-1]:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                return False

        final_key = parts[-1]
        if hasattr(current, final_key):
            # Type conversion based on current type
            current_value = getattr(current, final_key)
            if isinstance(current_value, bool):
                value = str(value).lower() in ("true", "1", "yes", "on")
            elif isinstance(current_value, int):
                value = int(value)
            elif isinstance(current_value, float):
                value = float(value)
            elif isinstance(current_value, list):
                if isinstance(value, str):
                    value = [v.strip() for v in value.split(",")]

            setattr(current, final_key, value)
            return True

        return False

    def reset(self) -> None:
        """Reset configuration to defaults."""
        self.aliases = AliasConfig()
        self.watch = WatchConfig()
        self.output = OutputConfig()
        self.shell = ShellConfig()


# Global config instance (lazy-loaded)
_global_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance.

    Returns:
        Global Config object, loading from file if not already loaded.
    """
    global _global_config
    if _global_config is None:
        _global_config = Config.load()
    return _global_config


def reload_config() -> Config:
    """Reload configuration from file.

    Returns:
        Freshly loaded Config object.
    """
    global _global_config
    _global_config = Config.load()
    return _global_config
