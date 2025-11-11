"""Schema compilation cache for improved performance."""

import hashlib
import pickle
from pathlib import Path
from typing import Generic, TypeVar

T = TypeVar("T")


class SchemaCache(Generic[T]):
    """Cache for compiled schemas to avoid repeated parsing."""

    def __init__(self, cache_dir: Path | None = None):
        """Initialize schema cache.

        Args:
            cache_dir: Directory for cache files (default: .cache/schemas)
        """
        self.cache_dir = cache_dir or Path(".cache/schemas")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: dict[str, T] = {}

    def _compute_hash(self, schema_path: Path) -> str:
        """Compute hash of schema file.

        Args:
            schema_path: Path to schema file

        Returns:
            SHA-256 hash of file contents
        """
        hasher = hashlib.sha256()
        hasher.update(schema_path.read_bytes())
        return hasher.hexdigest()

    def _cache_file(self, schema_hash: str) -> Path:
        """Get cache file path for schema hash.

        Args:
            schema_hash: Schema hash

        Returns:
            Path to cache file
        """
        return self.cache_dir / f"{schema_hash}.pkl"

    def get(self, schema_path: Path) -> T | None:
        """Get compiled schema from cache.

        Args:
            schema_path: Path to schema file

        Returns:
            Cached compiled schema or None if not in cache
        """
        schema_hash = self._compute_hash(schema_path)

        # Check memory cache first
        if schema_hash in self._memory_cache:
            return self._memory_cache[schema_hash]

        # Check disk cache
        cache_file = self._cache_file(schema_hash)
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    schema = pickle.load(f)
                    self._memory_cache[schema_hash] = schema
                    return schema
            except (pickle.PickleError, EOFError):
                # Cache corrupted, remove it
                cache_file.unlink(missing_ok=True)

        return None

    def put(self, schema_path: Path, schema: T) -> None:
        """Store compiled schema in cache.

        Args:
            schema_path: Path to schema file
            schema: Compiled schema object
        """
        schema_hash = self._compute_hash(schema_path)

        # Store in memory cache
        self._memory_cache[schema_hash] = schema

        # Store in disk cache
        cache_file = self._cache_file(schema_hash)
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(schema, f)
        except pickle.PickleError:
            # If pickling fails, just keep in memory
            pass

    def clear(self) -> None:
        """Clear all caches (memory and disk)."""
        self._memory_cache.clear()
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink(missing_ok=True)
