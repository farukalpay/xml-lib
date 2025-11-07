"""Shared types for xml-lib."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ValidationError:
    """A validation error or warning."""
    file: str
    line: Optional[int]
    column: Optional[int]
    message: str
    type: str  # 'error' or 'warning'
    rule: Optional[str] = None
