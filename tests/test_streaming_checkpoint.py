"""Tests for streaming checkpoint management."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from xml_lib.streaming.checkpoint import CheckpointManager, ValidationCheckpoint


class TestValidationCheckpoint:
    """Test ValidationCheckpoint class."""

    def test_checkpoint_creation(self):
        """Test creating a checkpoint."""
        checkpoint = ValidationCheckpoint(
            version="2.0",
            timestamp=datetime.now(),
            file_path="test.xml",
            file_position=1024000,
            element_stack=["root", "item"],
            namespace_context={},
            errors_count=0,
            warnings_count=0,
            elements_validated=1000,
            bytes_processed=1024000,
            checkpoint_count=0,
        )

        assert checkpoint.file_path == "test.xml"
        assert checkpoint.file_position == 1024000
        assert checkpoint.elements_validated == 1000
        assert len(checkpoint.element_stack) == 2

    def test_compute_checksum(self):
        """Test checksum computation."""
        checkpoint = ValidationCheckpoint(
            version="2.0",
            timestamp=datetime.now(),
            file_path="test.xml",
            file_position=1000,
            element_stack=[],
            namespace_context={},
            errors_count=0,
            warnings_count=0,
            elements_validated=100,
            bytes_processed=1000,
            checkpoint_count=0,
        )

        checksum = checkpoint.compute_checksum()
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 hex = 64 chars

    def test_verify_checksum(self):
        """Test checksum verification."""
        checkpoint = ValidationCheckpoint(
            version="2.0",
            timestamp=datetime.now(),
            file_path="test.xml",
            file_position=1000,
            element_stack=[],
            namespace_context={},
            errors_count=0,
            warnings_count=0,
            elements_validated=100,
            bytes_processed=1000,
            checkpoint_count=0,
        )

        # Compute and set checksum
        checkpoint.checksum = checkpoint.compute_checksum()

        # Should verify successfully
        assert checkpoint.verify_checksum() is True

        # Modify checkpoint
        checkpoint.file_position = 2000

        # Should fail verification
        assert checkpoint.verify_checksum() is False

    def test_to_dict(self):
        """Test converting checkpoint to dict."""
        checkpoint = ValidationCheckpoint(
            version="2.0",
            timestamp=datetime.now(),
            file_path="test.xml",
            file_position=1000,
            element_stack=["root"],
            namespace_context={"ns": "http://example.com"},
            errors_count=0,
            warnings_count=0,
            elements_validated=100,
            bytes_processed=1000,
            checkpoint_count=0,
        )

        data = checkpoint.to_dict()

        assert isinstance(data, dict)
        assert data["file_path"] == "test.xml"
        assert data["file_position"] == 1000
        assert "checksum" in data
        assert isinstance(data["timestamp"], str)

    def test_from_dict(self):
        """Test creating checkpoint from dict."""
        data = {
            "version": "2.0",
            "timestamp": "2025-11-12T10:00:00",
            "file_path": "test.xml",
            "file_position": 1000,
            "element_stack": ["root"],
            "namespace_context": {},
            "errors_count": 0,
            "warnings_count": 0,
            "elements_validated": 100,
            "bytes_processed": 1000,
            "checkpoint_count": 0,
            "checksum": "abc123",
        }

        checkpoint = ValidationCheckpoint.from_dict(data)

        assert checkpoint.file_path == "test.xml"
        assert checkpoint.file_position == 1000
        assert checkpoint.elements_validated == 100
        assert checkpoint.checksum == "abc123"


class TestCheckpointManager:
    """Test CheckpointManager class."""

    def test_manager_init(self, tmp_path):
        """Test manager initialization."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager(checkpoint_dir)

        assert manager.checkpoint_dir == checkpoint_dir
        assert checkpoint_dir.exists()  # Should create directory

    def test_save_checkpoint(self, tmp_path):
        """Test saving checkpoint."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager(checkpoint_dir)

        checkpoint = ValidationCheckpoint(
            version="2.0",
            timestamp=datetime.now(),
            file_path="test.xml",
            file_position=1000,
            element_stack=[],
            namespace_context={},
            errors_count=0,
            warnings_count=0,
            elements_validated=100,
            bytes_processed=1000,
            checkpoint_count=0,
        )

        # Save checkpoint
        saved_path = manager.save(checkpoint, Path("test.xml"))

        assert saved_path.exists()
        assert saved_path.suffix == ".json"

        # Verify content
        with open(saved_path) as f:
            data = json.load(f)

        assert data["file_path"] == "test.xml"
        assert data["file_position"] == 1000

    def test_load_checkpoint(self, tmp_path):
        """Test loading checkpoint."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager(checkpoint_dir)

        # Create and save checkpoint
        checkpoint = ValidationCheckpoint(
            version="2.0",
            timestamp=datetime.now(),
            file_path="test.xml",
            file_position=1000,
            element_stack=["root"],
            namespace_context={},
            errors_count=0,
            warnings_count=0,
            elements_validated=100,
            bytes_processed=1000,
            checkpoint_count=0,
        )

        saved_path = manager.save(checkpoint, Path("test.xml"))

        # Load checkpoint
        loaded = manager.load(saved_path)

        assert loaded.file_path == checkpoint.file_path
        assert loaded.file_position == checkpoint.file_position
        assert loaded.elements_validated == checkpoint.elements_validated
        assert loaded.element_stack == checkpoint.element_stack

    def test_list_checkpoints(self, tmp_path):
        """Test listing checkpoints."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager(checkpoint_dir)

        # Create multiple checkpoints
        for i in range(3):
            checkpoint = ValidationCheckpoint(
                version="2.0",
                timestamp=datetime.now(),
                file_path="test.xml",
                file_position=1000 * (i + 1),
                element_stack=[],
                namespace_context={},
                errors_count=0,
                warnings_count=0,
                elements_validated=100 * (i + 1),
                bytes_processed=1000 * (i + 1),
                checkpoint_count=i,
            )
            manager.save(checkpoint, Path("test.xml"))

        # List checkpoints
        checkpoints = manager.list_checkpoints(Path("test.xml"))

        assert len(checkpoints) == 3
        # Should be sorted by checkpoint number
        assert all(isinstance(p, Path) for p in checkpoints)

    def test_latest_checkpoint(self, tmp_path):
        """Test getting latest checkpoint."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager(checkpoint_dir)

        # No checkpoints initially
        latest = manager.latest(Path("test.xml"))
        assert latest is None

        # Create checkpoints
        for i in range(3):
            checkpoint = ValidationCheckpoint(
                version="2.0",
                timestamp=datetime.now(),
                file_path="test.xml",
                file_position=1000 * (i + 1),
                element_stack=[],
                namespace_context={},
                errors_count=0,
                warnings_count=0,
                elements_validated=100,
                bytes_processed=1000,
                checkpoint_count=i,
            )
            manager.save(checkpoint, Path("test.xml"))

        # Get latest
        latest = manager.latest(Path("test.xml"))
        assert latest is not None

        # Load and verify it's the last one
        loaded = manager.load(latest)
        assert loaded.checkpoint_count == 2

    def test_delete_checkpoints(self, tmp_path):
        """Test deleting checkpoints."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager(checkpoint_dir)

        # Create checkpoints
        for i in range(3):
            checkpoint = ValidationCheckpoint(
                version="2.0",
                timestamp=datetime.now(),
                file_path="test.xml",
                file_position=1000,
                element_stack=[],
                namespace_context={},
                errors_count=0,
                warnings_count=0,
                elements_validated=100,
                bytes_processed=1000,
                checkpoint_count=i,
            )
            manager.save(checkpoint, Path("test.xml"))

        # Delete all
        count = manager.delete_checkpoints(Path("test.xml"))
        assert count == 3

        # Should be no checkpoints left
        checkpoints = manager.list_checkpoints(Path("test.xml"))
        assert len(checkpoints) == 0

    def test_checkpoint_rotation(self, tmp_path):
        """Test automatic checkpoint rotation."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager(checkpoint_dir, max_checkpoints=3)

        # Create more than max_checkpoints
        for i in range(5):
            checkpoint = ValidationCheckpoint(
                version="2.0",
                timestamp=datetime.now(),
                file_path="test.xml",
                file_position=1000,
                element_stack=[],
                namespace_context={},
                errors_count=0,
                warnings_count=0,
                elements_validated=100,
                bytes_processed=1000,
                checkpoint_count=i,
            )
            manager.save(checkpoint, Path("test.xml"))

        # Should keep only last 3
        checkpoints = manager.list_checkpoints(Path("test.xml"))
        assert len(checkpoints) <= 3

    def test_get_checkpoint_info(self, tmp_path):
        """Test getting checkpoint metadata."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager(checkpoint_dir)

        checkpoint = ValidationCheckpoint(
            version="2.0",
            timestamp=datetime.now(),
            file_path="test.xml",
            file_position=1000,
            element_stack=[],
            namespace_context={},
            errors_count=5,
            warnings_count=2,
            elements_validated=100,
            bytes_processed=1000,
            checkpoint_count=0,
        )

        saved_path = manager.save(checkpoint, Path("test.xml"))

        # Get info
        info = manager.get_checkpoint_info(saved_path)

        assert info["file_path"] == "test.xml"
        assert info["file_position"] == 1000
        assert info["elements_validated"] == 100
        assert info["errors_count"] == 5
        assert info["warnings_count"] == 2

    def test_format_checkpoint_list(self, tmp_path):
        """Test formatting checkpoint list."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager(checkpoint_dir)

        # Create checkpoint
        checkpoint = ValidationCheckpoint(
            version="2.0",
            timestamp=datetime.now(),
            file_path="test.xml",
            file_position=1024000,
            element_stack=[],
            namespace_context={},
            errors_count=0,
            warnings_count=0,
            elements_validated=1000,
            bytes_processed=1024000,
            checkpoint_count=0,
        )

        manager.save(checkpoint, Path("test.xml"))

        # Format list
        output = manager.format_checkpoint_list(Path("test.xml"))

        assert "test.xml" in output
        assert "1,000 elements" in output

    def test_load_nonexistent_checkpoint(self, tmp_path):
        """Test loading nonexistent checkpoint."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager(checkpoint_dir)

        with pytest.raises(FileNotFoundError):
            manager.load(checkpoint_dir / "nonexistent.json")

    def test_corrupted_checkpoint(self, tmp_path):
        """Test loading corrupted checkpoint."""
        checkpoint_dir = tmp_path / "checkpoints"
        manager = CheckpointManager(checkpoint_dir)

        # Create corrupted file
        corrupted_file = checkpoint_dir / "corrupted.json"
        corrupted_file.write_text("not valid json{[")

        with pytest.raises(ValueError):
            manager.load(corrupted_file)
