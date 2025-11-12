"""Interactive features for xml-lib: shell, watch mode, and enhanced output.

This module provides developer-friendly interactive features including:
- Interactive REPL shell with autocomplete and history
- File watching with auto-execution
- Enhanced terminal output with colors and progress bars
- Configuration management
"""

from xml_lib.interactive.config import Config, get_config, reload_config
from xml_lib.interactive.output import (
    OutputFormatter,
    ValidationError,
    ValidationResult,
    get_formatter,
)
from xml_lib.interactive.shell import XmlLibShell, launch_shell
from xml_lib.interactive.watcher import (
    FileWatcherService,
    WatchResult,
    watch_files,
)

__all__ = [
    # Config
    "Config",
    "get_config",
    "reload_config",
    # Output
    "OutputFormatter",
    "ValidationError",
    "ValidationResult",
    "get_formatter",
    # Shell
    "XmlLibShell",
    "launch_shell",
    # Watcher
    "FileWatcherService",
    "WatchResult",
    "watch_files",
]
