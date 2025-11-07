"""Pluggable telemetry sink for capturing validation metrics."""

import json
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


@dataclass
class TelemetryEvent:
    """A telemetry event."""
    timestamp: datetime
    event_type: str
    data: Dict[str, Any]


class TelemetrySink(ABC):
    """Abstract telemetry sink."""

    @abstractmethod
    def log_event(self, event_type: str, **kwargs: Any) -> None:
        """Log a telemetry event."""
        pass

    def log_validation(
        self,
        project: str,
        success: bool,
        duration: float,
        file_count: int,
        error_count: int,
        warning_count: int,
    ) -> None:
        """Log a validation event."""
        self.log_event(
            "validation",
            project=project,
            success=success,
            duration=duration,
            file_count=file_count,
            error_count=error_count,
            warning_count=warning_count,
        )

    def log_publish(
        self,
        project: str,
        success: bool,
        duration: float,
        output_files: int,
    ) -> None:
        """Log a publish event."""
        self.log_event(
            "publish",
            project=project,
            success=success,
            duration=duration,
            output_files=output_files,
        )

    @staticmethod
    def create(backend: str, target: str) -> "TelemetrySink":
        """Create a telemetry sink.

        Args:
            backend: Backend type ('file', 'sqlite', 'postgres')
            target: Target location (file path or connection string)

        Returns:
            TelemetrySink instance
        """
        if backend == "file":
            return FileTelemetrySink(Path(target))
        elif backend == "sqlite":
            return SQLiteTelemetrySink(target)
        elif backend == "postgres":
            if not POSTGRES_AVAILABLE:
                raise RuntimeError("psycopg2 not available")
            return PostgresTelemetrySink(target)
        else:
            raise ValueError(f"Unknown telemetry backend: {backend}")


class FileTelemetrySink(TelemetrySink):
    """File-based telemetry sink (JSON Lines)."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(self, event_type: str, **kwargs: Any) -> None:
        """Log event to file."""
        event = TelemetryEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            data=kwargs,
        )

        with open(self.file_path, "a") as f:
            json.dump(
                {
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type,
                    **event.data,
                },
                f,
            )
            f.write("\n")


class SQLiteTelemetrySink(TelemetrySink):
    """SQLite-based telemetry sink."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                data TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def log_event(self, event_type: str, **kwargs: Any) -> None:
        """Log event to SQLite."""
        timestamp = datetime.now().isoformat()
        data = json.dumps(kwargs)

        self.conn.execute(
            "INSERT INTO telemetry_events (timestamp, event_type, data) VALUES (?, ?, ?)",
            (timestamp, event_type, data),
        )
        self.conn.commit()

    def __del__(self) -> None:
        """Close connection."""
        if hasattr(self, "conn"):
            self.conn.close()


class PostgresTelemetrySink(TelemetrySink):
    """PostgreSQL-based telemetry sink."""

    def __init__(self, connection_string: str):
        if not POSTGRES_AVAILABLE:
            raise RuntimeError("psycopg2 not available")

        self.conn = psycopg2.connect(connection_string)
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_events (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL,
                    event_type TEXT NOT NULL,
                    data JSONB NOT NULL
                )
            """)
            self.conn.commit()

    def log_event(self, event_type: str, **kwargs: Any) -> None:
        """Log event to PostgreSQL."""
        timestamp = datetime.now()
        data = json.dumps(kwargs)

        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO telemetry_events (timestamp, event_type, data) VALUES (%s, %s, %s)",
                (timestamp, event_type, data),
            )
            self.conn.commit()

    def __del__(self) -> None:
        """Close connection."""
        if hasattr(self, "conn"):
            self.conn.close()
