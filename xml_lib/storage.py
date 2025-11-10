"""Content-addressed storage with deterministic UUIDs."""

import hashlib
import uuid
from pathlib import Path


class ContentStore:
    """Content-addressed storage using SHA-256."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.sha256_dir = base_path / "sha256"
        self.sha256_dir.mkdir(parents=True, exist_ok=True)

    def store(self, content: bytes, checksum: str | None = None) -> Path:
        """Store content and return its path.

        Args:
            content: Content to store
            checksum: Pre-computed checksum (optional)

        Returns:
            Path to stored content
        """
        if checksum is None:
            checksum = hashlib.sha256(content).hexdigest()

        # Create subdirectories from first 4 chars of checksum
        prefix = checksum[:2]
        subdir = self.sha256_dir / prefix
        subdir.mkdir(exist_ok=True)

        # Store file
        file_path = subdir / f"{checksum[2:]}.xml"
        if not file_path.exists():
            file_path.write_bytes(content)

        return file_path

    def retrieve(self, checksum: str) -> bytes | None:
        """Retrieve content by checksum.

        Args:
            checksum: SHA-256 checksum

        Returns:
            Content if found, None otherwise
        """
        prefix = checksum[:2]
        file_path = self.sha256_dir / prefix / f"{checksum[2:]}.xml"

        if file_path.exists():
            return file_path.read_bytes()

        return None

    def exists(self, checksum: str) -> bool:
        """Check if content exists.

        Args:
            checksum: SHA-256 checksum

        Returns:
            True if content exists
        """
        prefix = checksum[:2]
        file_path = self.sha256_dir / prefix / f"{checksum[2:]}.xml"
        return file_path.exists()


def deterministic_uuid(namespace: str, name: str) -> str:
    """Generate a deterministic UUID v5.

    Args:
        namespace: Namespace identifier
        name: Name within namespace

    Returns:
        UUID as string
    """
    # Use DNS namespace as default
    namespace_uuid = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

    # Create namespace-specific UUID
    if namespace:
        namespace_uuid = uuid.uuid5(namespace_uuid, namespace)

    # Generate deterministic UUID
    return str(uuid.uuid5(namespace_uuid, name))


def compute_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file.

    Args:
        file_path: Path to file

    Returns:
        Hex-encoded SHA-256 checksum
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
