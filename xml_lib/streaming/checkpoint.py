"""Checkpoint management for resumable streaming validation.

This module provides checkpoint save/restore functionality for long-running
validation tasks. Checkpoints allow validation to resume from the last saved
position after interruption.

Features:
    - JSON-based checkpoint format
    - Integrity validation (checksums)
    - Automatic checkpoint rotation
    - Resume from any checkpoint
    - Checkpoint metadata tracking

Example:
    >>> manager = CheckpointManager(".checkpoints")
    >>> checkpoint = ValidationCheckpoint(
    ...     file_path="large.xml",
    ...     file_position=524288000,
    ...     elements_validated=1500000
    ... )
    >>> manager.save(checkpoint, Path("large.xml"))
    >>> # Later, resume:
    >>> checkpoint = manager.load(manager.latest("large.xml"))
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ValidationCheckpoint:
    """Checkpoint data for validation resumption.

    This contains all state needed to resume validation from a specific
    point in the file.

    Attributes:
        version: Checkpoint format version
        timestamp: When checkpoint was created
        file_path: Path to XML file being validated
        file_position: Byte position in file
        element_stack: Stack of currently open elements
        namespace_context: Current namespace mappings
        errors_count: Number of errors found so far
        warnings_count: Number of warnings found so far
        elements_validated: Total elements validated
        bytes_processed: Total bytes processed
        checkpoint_count: Sequential checkpoint number
        checksum: SHA256 checksum of checkpoint data
    """

    version: str
    timestamp: datetime
    file_path: str
    file_position: int
    element_stack: list[str]
    namespace_context: dict[str, str]
    errors_count: int
    warnings_count: int
    elements_validated: int
    bytes_processed: int
    checkpoint_count: int
    checksum: Optional[str] = None

    def compute_checksum(self) -> str:
        """Compute SHA256 checksum of checkpoint data.

        Returns:
            Hex-encoded SHA256 checksum

        Example:
            >>> checkpoint = ValidationCheckpoint(...)
            >>> checksum = checkpoint.compute_checksum()
            >>> print(f"Checksum: {checksum[:16]}...")
        """
        # Create dict without checksum field
        data = asdict(self)
        data.pop("checksum", None)

        # Convert datetime to ISO format for consistent hashing
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()

        # Create stable JSON representation
        json_str = json.dumps(data, sort_keys=True, separators=(",", ":"))

        # Compute SHA256
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()

    def verify_checksum(self) -> bool:
        """Verify checkpoint integrity.

        Returns:
            True if checksum is valid, False otherwise

        Example:
            >>> checkpoint = manager.load("checkpoint.json")
            >>> if not checkpoint.verify_checksum():
            ...     print("Warning: Checkpoint may be corrupted!")
        """
        if not self.checksum:
            return False

        computed = self.compute_checksum()
        return computed == self.checksum

    def to_dict(self) -> dict:
        """Convert checkpoint to dictionary for JSON serialization.

        Returns:
            Dictionary representation

        Example:
            >>> checkpoint = ValidationCheckpoint(...)
            >>> data = checkpoint.to_dict()
            >>> json.dump(data, file, indent=2)
        """
        data = asdict(self)

        # Convert datetime to ISO string
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()

        # Ensure checksum is set
        if not data.get("checksum"):
            data["checksum"] = self.compute_checksum()

        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ValidationCheckpoint":
        """Create checkpoint from dictionary.

        Args:
            data: Dictionary with checkpoint data

        Returns:
            ValidationCheckpoint instance

        Raises:
            ValueError: If required fields are missing

        Example:
            >>> with open("checkpoint.json") as f:
            ...     data = json.load(f)
            >>> checkpoint = ValidationCheckpoint.from_dict(data)
        """
        # Parse timestamp
        timestamp_str = data.get("timestamp")
        if isinstance(timestamp_str, str):
            timestamp = datetime.fromisoformat(timestamp_str)
        else:
            timestamp = timestamp_str or datetime.now()

        return cls(
            version=data.get("version", "2.0"),
            timestamp=timestamp,
            file_path=data["file_path"],
            file_position=data["file_position"],
            element_stack=data.get("element_stack", []),
            namespace_context=data.get("namespace_context", {}),
            errors_count=data.get("errors_count", 0),
            warnings_count=data.get("warnings_count", 0),
            elements_validated=data.get("elements_validated", 0),
            bytes_processed=data.get("bytes_processed", 0),
            checkpoint_count=data.get("checkpoint_count", 0),
            checksum=data.get("checksum"),
        )


class CheckpointManager:
    """Manages checkpoint files for validation resumption.

    This class handles:
    - Saving checkpoints to disk
    - Loading checkpoints
    - Finding latest checkpoint
    - Listing available checkpoints
    - Cleaning up old checkpoints

    Features:
        - Automatic directory creation
        - Checkpoint rotation (keep N latest)
        - Integrity validation
        - Atomic writes

    Example:
        >>> manager = CheckpointManager(".checkpoints")
        >>> checkpoint = ValidationCheckpoint(...)
        >>> manager.save(checkpoint, Path("large.xml"))
        >>> # List all checkpoints for file
        >>> checkpoints = manager.list_checkpoints(Path("large.xml"))
        >>> print(f"Found {len(checkpoints)} checkpoints")
    """

    def __init__(
        self,
        checkpoint_dir: Path,
        max_checkpoints: int = 10,
    ) -> None:
        """Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory to store checkpoints
            max_checkpoints: Maximum checkpoints to keep per file (0 = unlimited)

        Example:
            >>> manager = CheckpointManager(
            ...     checkpoint_dir=Path(".checkpoints"),
            ...     max_checkpoints=10
            ... )
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.max_checkpoints = max_checkpoints

        # Create directory if it doesn't exist
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def _get_checkpoint_path(
        self, file_path: Path, checkpoint_count: int
    ) -> Path:
        """Generate checkpoint file path.

        Args:
            file_path: XML file being validated
            checkpoint_count: Sequential checkpoint number

        Returns:
            Path to checkpoint file

        Example:
            >>> path = manager._get_checkpoint_path(
            ...     Path("data.xml"), checkpoint_count=5
            ... )
            >>> print(path)
            .checkpoints/data_xml_checkpoint_5.json
        """
        # Sanitize filename
        safe_name = file_path.name.replace(".", "_")

        # Create checkpoint filename
        checkpoint_name = f"{safe_name}_checkpoint_{checkpoint_count}.json"

        return self.checkpoint_dir / checkpoint_name

    def save(
        self,
        checkpoint: ValidationCheckpoint,
        file_path: Path,
    ) -> Path:
        """Save checkpoint to disk.

        Args:
            checkpoint: Checkpoint to save
            file_path: XML file being validated

        Returns:
            Path to saved checkpoint file

        Raises:
            IOError: If checkpoint cannot be saved

        Example:
            >>> checkpoint = ValidationCheckpoint(...)
            >>> checkpoint_path = manager.save(checkpoint, Path("data.xml"))
            >>> print(f"Saved checkpoint: {checkpoint_path}")
        """
        # Compute checksum
        checkpoint.checksum = checkpoint.compute_checksum()

        # Get checkpoint path
        checkpoint_path = self._get_checkpoint_path(
            file_path, checkpoint.checkpoint_count
        )

        # Write to temporary file first (atomic write)
        temp_path = checkpoint_path.with_suffix(".json.tmp")

        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(checkpoint.to_dict(), f, indent=2)

            # Rename to final path (atomic on POSIX systems)
            temp_path.replace(checkpoint_path)

            # Clean up old checkpoints
            self._cleanup_old_checkpoints(file_path)

            return checkpoint_path

        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise IOError(f"Failed to save checkpoint: {e}")

    def load(self, checkpoint_path: Path) -> ValidationCheckpoint:
        """Load checkpoint from disk.

        Args:
            checkpoint_path: Path to checkpoint file

        Returns:
            Loaded ValidationCheckpoint

        Raises:
            FileNotFoundError: If checkpoint doesn't exist
            ValueError: If checkpoint is invalid or corrupted

        Example:
            >>> checkpoint = manager.load(Path(".checkpoints/data_checkpoint_5.json"))
            >>> if checkpoint.verify_checksum():
            ...     print(f"Resuming from position {checkpoint.file_position}")
        """
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

        try:
            with open(checkpoint_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            checkpoint = ValidationCheckpoint.from_dict(data)

            # Verify integrity
            if not checkpoint.verify_checksum():
                raise ValueError(f"Checkpoint integrity check failed: {checkpoint_path}")

            return checkpoint

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid checkpoint file: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load checkpoint: {e}")

    def list_checkpoints(self, file_path: Path) -> list[Path]:
        """List all checkpoints for a file.

        Args:
            file_path: XML file

        Returns:
            List of checkpoint paths, sorted by checkpoint number

        Example:
            >>> checkpoints = manager.list_checkpoints(Path("data.xml"))
            >>> for cp in checkpoints:
            ...     print(f"Checkpoint: {cp.name}")
        """
        # Get checkpoint pattern
        safe_name = file_path.name.replace(".", "_")
        pattern = f"{safe_name}_checkpoint_*.json"

        # Find all matching files
        checkpoints = list(self.checkpoint_dir.glob(pattern))

        # Sort by checkpoint number
        def get_checkpoint_number(path: Path) -> int:
            # Extract number from filename
            try:
                parts = path.stem.split("_checkpoint_")
                return int(parts[-1]) if len(parts) > 1 else 0
            except (IndexError, ValueError):
                return 0

        checkpoints.sort(key=get_checkpoint_number)

        return checkpoints

    def latest(self, file_path: Path) -> Optional[Path]:
        """Get latest checkpoint for a file.

        Args:
            file_path: XML file

        Returns:
            Path to latest checkpoint, or None if no checkpoints exist

        Example:
            >>> latest = manager.latest(Path("data.xml"))
            >>> if latest:
            ...     checkpoint = manager.load(latest)
            ...     print(f"Resume from byte {checkpoint.file_position}")
        """
        checkpoints = self.list_checkpoints(file_path)
        return checkpoints[-1] if checkpoints else None

    def _cleanup_old_checkpoints(self, file_path: Path) -> None:
        """Remove old checkpoints, keeping only max_checkpoints.

        Args:
            file_path: XML file

        Example:
            >>> manager._cleanup_old_checkpoints(Path("data.xml"))
        """
        if self.max_checkpoints <= 0:
            return  # Unlimited

        checkpoints = self.list_checkpoints(file_path)

        # Remove oldest checkpoints if we exceed limit
        if len(checkpoints) > self.max_checkpoints:
            for checkpoint in checkpoints[: -self.max_checkpoints]:
                try:
                    checkpoint.unlink()
                except OSError:
                    pass  # Ignore errors during cleanup

    def delete_checkpoints(self, file_path: Path) -> int:
        """Delete all checkpoints for a file.

        Args:
            file_path: XML file

        Returns:
            Number of checkpoints deleted

        Example:
            >>> count = manager.delete_checkpoints(Path("data.xml"))
            >>> print(f"Deleted {count} checkpoints")
        """
        checkpoints = self.list_checkpoints(file_path)
        count = 0

        for checkpoint in checkpoints:
            try:
                checkpoint.unlink()
                count += 1
            except OSError:
                pass  # Ignore errors

        return count

    def get_checkpoint_info(self, checkpoint_path: Path) -> dict:
        """Get metadata about a checkpoint without full loading.

        Args:
            checkpoint_path: Path to checkpoint file

        Returns:
            Dictionary with checkpoint metadata

        Example:
            >>> info = manager.get_checkpoint_info(checkpoint_path)
            >>> print(f"Position: {info['file_position']}")
            >>> print(f"Elements: {info['elements_validated']}")
        """
        try:
            with open(checkpoint_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return {
                "file_path": data.get("file_path"),
                "file_position": data.get("file_position", 0),
                "elements_validated": data.get("elements_validated", 0),
                "bytes_processed": data.get("bytes_processed", 0),
                "errors_count": data.get("errors_count", 0),
                "warnings_count": data.get("warnings_count", 0),
                "timestamp": data.get("timestamp"),
                "checkpoint_count": data.get("checkpoint_count", 0),
            }
        except Exception:
            return {}

    def format_checkpoint_list(self, file_path: Path) -> str:
        """Format checkpoint list as human-readable string.

        Args:
            file_path: XML file

        Returns:
            Formatted string showing all checkpoints

        Example:
            >>> print(manager.format_checkpoint_list(Path("data.xml")))
            Available checkpoints for data.xml:
              1. checkpoint_0 (524.3 MB, 1.5M elements)
              2. checkpoint_1 (1048.6 MB, 3.0M elements)
        """
        checkpoints = self.list_checkpoints(file_path)

        if not checkpoints:
            return f"No checkpoints found for {file_path.name}"

        lines = [f"Available checkpoints for {file_path.name}:"]

        for i, cp in enumerate(checkpoints, 1):
            info = self.get_checkpoint_info(cp)
            mb = info.get("bytes_processed", 0) / 1024 / 1024
            elements = info.get("elements_validated", 0)
            lines.append(f"  {i}. {cp.stem} ({mb:.1f} MB, {elements:,} elements)")

        return "\n".join(lines)
