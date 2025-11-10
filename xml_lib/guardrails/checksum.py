"""Checksum validation and signoff logic."""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from xml_lib.types import Priority, ValidationResult


@dataclass
class Signoff:
    """Multi-party signoff record."""

    role: str
    name: str
    timestamp: datetime
    checksum: str
    verified: bool = False


class ChecksumValidator:
    """Validator for checksums and signoffs."""

    def __init__(self) -> None:
        """Initialize checksum validator."""
        self.signoffs: list[Signoff] = []

    def compute_checksum(self, file_path: Path, algorithm: str = "sha256") -> str:
        """Compute checksum of file.

        Args:
            file_path: Path to file
            algorithm: Hash algorithm (sha256, sha512)

        Returns:
            Hex-encoded checksum
        """
        if algorithm == "sha256":
            hasher = hashlib.sha256()
        elif algorithm == "sha512":
            hasher = hashlib.sha512()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        hasher.update(file_path.read_bytes())
        return hasher.hexdigest()

    def validate_checksum(
        self, file_path: Path, expected_checksum: str, algorithm: str = "sha256"
    ) -> ValidationResult:
        """Validate file checksum.

        Args:
            file_path: Path to file
            expected_checksum: Expected checksum value
            algorithm: Hash algorithm

        Returns:
            ValidationResult
        """
        computed = self.compute_checksum(file_path, algorithm)
        is_valid = computed == expected_checksum

        errors = (
            [] if is_valid else [f"Checksum mismatch: expected {expected_checksum}, got {computed}"]
        )

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            metadata={"algorithm": algorithm, "computed": computed, "expected": expected_checksum},
        )

    def add_signoff(self, signoff: Signoff) -> None:
        """Add signoff record.

        Args:
            signoff: Signoff record
        """
        self.signoffs.append(signoff)

    def verify_signoffs(self, required_roles: list[str]) -> ValidationResult:
        """Verify all required signoffs present.

        Args:
            required_roles: List of required roles

        Returns:
            ValidationResult
        """
        signed_roles = {s.role for s in self.signoffs if s.verified}
        missing_roles = set(required_roles) - signed_roles

        is_valid = len(missing_roles) == 0
        errors = [f"Missing signoff from: {role}" for role in missing_roles]

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            metadata={
                "required_roles": required_roles,
                "signed_roles": list(signed_roles),
                "signoff_count": len(self.signoffs),
            },
        )
