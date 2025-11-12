"""File watching and auto-execution for xml-lib.

Monitors XML files for changes and automatically executes validation or other
commands when files are modified. Includes debouncing to avoid rapid re-runs.
"""

import fnmatch
import shlex
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from xml_lib.interactive.config import get_config
from xml_lib.interactive.output import get_formatter


@dataclass
class WatchResult:
    """Result of executing command on file change."""

    success: bool
    filepath: str
    duration: float
    output: str | None = None
    error: str | None = None


class XmlFileWatcher(FileSystemEventHandler):
    """Watch XML files and auto-execute command on changes."""

    def __init__(
        self,
        pattern: str,
        command: str,
        debounce_sec: float | None = None,
        clear_on_change: bool | None = None,
        callback: Callable[[WatchResult], None] | None = None,
    ):
        """Initialize file watcher.

        Args:
            pattern: File pattern to watch (e.g., "*.xml", "data/**/*.xml")
            command: Command to execute on file changes
            debounce_sec: Debounce delay in seconds. Uses config if None.
            clear_on_change: Whether to clear terminal on change. Uses config if None.
            callback: Optional callback for custom result handling
        """
        super().__init__()
        self.pattern = pattern
        self.command = command
        self.callback = callback

        config = get_config()
        self.debounce_sec = (
            debounce_sec if debounce_sec is not None else config.watch.debounce_seconds
        )
        self.clear_on_change = (
            clear_on_change if clear_on_change is not None else config.watch.clear_on_change
        )
        self.ignore_patterns = config.watch.ignore_patterns

        self.last_run: dict[str, float] = {}
        self.formatter = get_formatter()

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        filepath = event.src_path

        # Check if file matches pattern
        if not self._matches_pattern(filepath):
            return

        # Check ignore patterns
        if self._should_ignore(filepath):
            return

        # Debounce rapid changes
        now = time.time()
        if filepath in self.last_run:
            elapsed = now - self.last_run[filepath]
            if elapsed < self.debounce_sec:
                return

        self.last_run[filepath] = now

        # Execute command
        self._execute_command(filepath)

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events.

        Args:
            event: File system event
        """
        # Treat creation same as modification
        self.on_modified(event)

    def _matches_pattern(self, filepath: str) -> bool:
        """Check if filepath matches watch pattern.

        Args:
            filepath: Path to file

        Returns:
            True if matches pattern
        """
        path = Path(filepath)

        # Handle glob patterns
        if "**" in self.pattern or "*" in self.pattern:
            return fnmatch.fnmatch(str(path), self.pattern) or fnmatch.fnmatch(
                path.name, self.pattern
            )

        # Handle extensions
        if self.pattern.startswith("*."):
            return path.suffix == self.pattern[1:]

        # Exact match
        return str(path) == self.pattern or path.name == self.pattern

    def _should_ignore(self, filepath: str) -> bool:
        """Check if filepath should be ignored.

        Args:
            filepath: Path to file

        Returns:
            True if should be ignored
        """
        path = Path(filepath)

        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(str(path), pattern) or fnmatch.fnmatch(
                path.name, pattern
            ):
                return True

        return False

    def _execute_command(self, filepath: str) -> None:
        """Execute command on file change.

        Args:
            filepath: Path to changed file
        """
        # Clear terminal if configured
        if self.clear_on_change:
            self.formatter.clear_terminal()

        # Print change notification
        self.formatter.print_file_change(filepath)

        start_time = time.time()
        success = True
        output = None
        error = None

        try:
            # Parse command and substitute {file} placeholder
            command_str = self.command.replace("{file}", filepath)

            # Parse command
            try:
                args = shlex.split(command_str)
            except ValueError as e:
                self.formatter.print_error(f"Command parse error: {e}")
                return

            # Execute through CLI
            from xml_lib.cli import main

            # Preserve original sys.argv
            original_argv = sys.argv

            try:
                # Set sys.argv for Click
                sys.argv = ["xml-lib"] + args

                # Capture output
                import io
                from contextlib import redirect_stderr, redirect_stdout

                stdout_capture = io.StringIO()
                stderr_capture = io.StringIO()

                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    try:
                        main(standalone_mode=False)
                    except SystemExit as e:
                        if e.code != 0:
                            success = False
                    except Exception as e:
                        success = False
                        error = str(e)

                output = stdout_capture.getvalue()
                if stderr_capture.getvalue():
                    error = stderr_capture.getvalue()

            finally:
                # Restore original sys.argv
                sys.argv = original_argv

        except Exception as e:
            success = False
            error = str(e)

        duration = time.time() - start_time

        # Create result
        result = WatchResult(
            success=success,
            filepath=filepath,
            duration=duration,
            output=output,
            error=error,
        )

        # Print result
        if success:
            self.formatter.print_success(f"Command completed ({duration:.2f}s)")
        else:
            self.formatter.print_error(f"Command failed ({duration:.2f}s)")
            if error:
                self.formatter.console.print(f"[red]{error}[/red]")

        # Call callback if provided
        if self.callback:
            self.callback(result)


class FileWatcherService:
    """Service for managing file watchers."""

    def __init__(self):
        """Initialize watcher service."""
        self.observer: Observer | None = None
        self.handler: XmlFileWatcher | None = None
        self.formatter = get_formatter()

    def start(
        self,
        pattern: str,
        command: str,
        path: str = ".",
        recursive: bool = True,
        debounce_sec: float | None = None,
        clear_on_change: bool | None = None,
        callback: Callable[[WatchResult], None] | None = None,
    ) -> None:
        """Start watching files.

        Args:
            pattern: File pattern to watch
            command: Command to execute on changes
            path: Base path to watch (default: current directory)
            recursive: Whether to watch subdirectories
            debounce_sec: Debounce delay in seconds
            clear_on_change: Whether to clear terminal on change
            callback: Optional callback for custom result handling
        """
        if self.observer is not None:
            raise RuntimeError("Watcher is already running")

        # Create handler
        self.handler = XmlFileWatcher(
            pattern=pattern,
            command=command,
            debounce_sec=debounce_sec,
            clear_on_change=clear_on_change,
            callback=callback,
        )

        # Create observer
        self.observer = Observer()
        self.observer.schedule(self.handler, path=path, recursive=recursive)
        self.observer.start()

        # Print start message
        self.formatter.print_watch_start(pattern, command)

    def stop(self) -> None:
        """Stop watching files."""
        if self.observer is None:
            return

        self.observer.stop()
        self.observer.join()
        self.observer = None
        self.handler = None

        self.formatter.print_watch_stop()

    def run_until_interrupted(self) -> int:
        """Run watcher until interrupted by user.

        Returns:
            Exit code (0 for normal exit)
        """
        if self.observer is None:
            raise RuntimeError("Watcher not started")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
            return 0


def watch_files(
    pattern: str,
    command: str,
    path: str = ".",
    recursive: bool = True,
    debounce: float | None = None,
    clear: bool | None = None,
) -> int:
    """Watch files and execute command on changes.

    Args:
        pattern: File pattern to watch (e.g., "*.xml", "data/**/*.xml")
        command: Command to execute on changes (use {file} as placeholder)
        path: Base path to watch (default: current directory)
        recursive: Whether to watch subdirectories
        debounce: Debounce delay in seconds (default: from config)
        clear: Whether to clear terminal on change (default: from config)

    Returns:
        Exit code (0 for success)

    Example:
        >>> watch_files("*.xml", "validate {file} --schema schema.xsd")
        Watching: *.xml
        Command: validate {file} --schema schema.xsd
        Press Ctrl+C to stop

        [12:34:56] Change detected: data.xml
        ✅ Command completed (0.15s)
    """
    service = FileWatcherService()

    try:
        service.start(
            pattern=pattern,
            command=command,
            path=path,
            recursive=recursive,
            debounce_sec=debounce,
            clear_on_change=clear,
        )

        return service.run_until_interrupted()

    except Exception as e:
        formatter = get_formatter()
        formatter.print_error(f"Watch error: {e}")
        return 1


if __name__ == "__main__":
    # Simple CLI for testing
    if len(sys.argv) < 3:
        print("Usage: python -m xml_lib.interactive.watcher <pattern> <command>")
        print("Example: python -m xml_lib.interactive.watcher '*.xml' 'validate {file}'")
        sys.exit(1)

    pattern = sys.argv[1]
    command = " ".join(sys.argv[2:])

    sys.exit(watch_files(pattern, command))
