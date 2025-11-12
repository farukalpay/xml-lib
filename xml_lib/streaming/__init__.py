"""Streaming XML validation for enterprise-scale files.

This module provides SAX-based streaming validation for large XML files
(1GB-10GB+) with constant memory usage (~50MB), validation checkpoints,
and resume capability.

Main Components:
    - StreamingParser: SAX-based parser with position tracking
    - StreamingValidator: Incremental validation during parsing
    - CheckpointManager: Save/restore validation state
    - BenchmarkRunner: Performance comparison suite
    - TestFileGenerator: Generate test XML files

Example:
    >>> from xml_lib.streaming import StreamingValidator
    >>> validator = StreamingValidator(schema_path="schema.xsd")
    >>> result = validator.validate_stream("large_file.xml")
    >>> print(f"Valid: {result.is_valid}, Memory: {result.peak_memory_mb}MB")
"""

from xml_lib.streaming.benchmark import BenchmarkRunner, BenchmarkResult
from xml_lib.streaming.checkpoint import CheckpointManager, ValidationCheckpoint
from xml_lib.streaming.generator import TestFileGenerator
from xml_lib.streaming.parser import StreamingParser, ParserEvent, ParserState
from xml_lib.streaming.validator import (
    StreamingValidator,
    StreamingValidationResult,
    ValidationState,
)

__all__ = [
    # Parser
    "StreamingParser",
    "ParserEvent",
    "ParserState",
    # Validator
    "StreamingValidator",
    "StreamingValidationResult",
    "ValidationState",
    # Checkpoint
    "CheckpointManager",
    "ValidationCheckpoint",
    # Benchmark
    "BenchmarkRunner",
    "BenchmarkResult",
    # Generator
    "TestFileGenerator",
]
