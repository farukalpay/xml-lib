"""Shared types for xml-lib."""

from dataclasses import dataclass


@dataclass
class ValidationError:
    """A validation error or warning."""

    file: str
    line: int | None
    column: int | None
    message: str
    type: str  # 'error' or 'warning'
    rule: str | None = None
