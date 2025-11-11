"""Assertion ledger with signing and JSON Lines output."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from lxml import etree

from xml_lib.types import ValidationError

if TYPE_CHECKING:
    from xml_lib.validator import ValidationResult

# Lazy import for cryptography to avoid import-time failures
CRYPTO_AVAILABLE = False
_crypto_modules: dict | None = None


def _get_crypto():
    """Lazy load cryptography modules."""
    global CRYPTO_AVAILABLE, _crypto_modules
    if _crypto_modules is not None:
        return _crypto_modules

    try:
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding, rsa

        _crypto_modules = {
            "hashes": hashes,
            "serialization": serialization,
            "padding": padding,
            "rsa": rsa,
            "default_backend": default_backend,
        }
        CRYPTO_AVAILABLE = True
        return _crypto_modules
    except Exception:
        # Catch ImportError or any other exception (e.g., PanicException, cffi issues)
        _crypto_modules = {}
        CRYPTO_AVAILABLE = False
        return _crypto_modules


class AssertionLedger:
    """Signed assertion ledger for validation results."""

    def __init__(self):
        self.assertions: list[ValidationResult] = []
        self.private_key = self._generate_key()
        self.public_key = self.private_key.public_key() if self.private_key else None

    def _generate_key(self) -> Any | None:
        """Generate RSA key pair for signing."""
        crypto = _get_crypto()
        if not crypto:
            return None
        rsa = crypto["rsa"]
        default_backend = crypto["default_backend"]
        return rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend(),
        )

    def add_validation_result(self, result: "ValidationResult") -> None:
        """Add a validation result to the ledger."""
        self.assertions.append(result)

    def _sign_data(self, data: bytes) -> bytes | None:
        """Sign data with private key."""
        crypto = _get_crypto()
        if not crypto or not self.private_key:
            return None
        padding = crypto["padding"]
        hashes = crypto["hashes"]
        signature = self.private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        return signature

    def write_xml(self, output_path: Path) -> None:
        """Write assertions to XML file with signature."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        root = etree.Element("assertion-ledger")
        root.set("version", "1.0")
        root.set("timestamp", datetime.now().isoformat())

        crypto = _get_crypto()
        if not crypto:
            root.set("signed", "false")

        # Add public key if crypto is available
        if crypto and self.public_key:
            serialization = crypto["serialization"]
            public_pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            key_elem = etree.SubElement(root, "public-key")
            key_elem.text = public_pem.decode("utf-8")

        # Add assertions
        assertions_elem = etree.SubElement(root, "assertions")

        for result in self.assertions:
            assertion = etree.SubElement(assertions_elem, "assertion")
            assertion.set("timestamp", result.timestamp.isoformat())
            assertion.set("valid", str(result.is_valid).lower())

            # Summary
            summary = etree.SubElement(assertion, "summary")
            etree.SubElement(summary, "files-validated").text = str(len(result.validated_files))
            etree.SubElement(summary, "errors").text = str(len(result.errors))
            etree.SubElement(summary, "warnings").text = str(len(result.warnings))

            # Validated files
            if result.validated_files:
                files_elem = etree.SubElement(assertion, "validated-files")
                for file_path in result.validated_files:
                    file_elem = etree.SubElement(files_elem, "file")
                    file_elem.text = file_path
                    if file_path in result.checksums:
                        file_elem.set("checksum", result.checksums[file_path])

            # Errors
            if result.errors:
                errors_elem = etree.SubElement(assertion, "errors")
                for error in result.errors:
                    self._add_validation_error(errors_elem, "error", error)

            # Warnings
            if result.warnings:
                warnings_elem = etree.SubElement(assertion, "warnings")
                for warning in result.warnings:
                    self._add_validation_error(warnings_elem, "warning", warning)

        # Sign the assertions if crypto is available
        xml_bytes = etree.tostring(assertions_elem, encoding="utf-8")
        checksum = hashlib.sha256(xml_bytes).hexdigest()

        if crypto:
            signature = self._sign_data(xml_bytes)
            if signature:
                sig_elem = etree.SubElement(root, "signature")
                sig_elem.set("algorithm", "RSA-PSS-SHA256")
                sig_elem.set("checksum", checksum)
                sig_elem.text = signature.hex()

        # Write to file
        tree = etree.ElementTree(root)
        tree.write(
            str(output_path),
            pretty_print=True,
            xml_declaration=True,
            encoding="utf-8",
        )

    def _add_validation_error(
        self,
        parent: etree._Element,
        tag: str,
        error: ValidationError,
    ) -> None:
        """Add a validation error to XML."""
        elem = etree.SubElement(parent, tag)
        elem.set("file", error.file)
        if error.line is not None:
            elem.set("line", str(error.line))
        if error.column is not None:
            elem.set("column", str(error.column))
        if error.rule:
            elem.set("rule", error.rule)
        elem.text = error.message

    def write_jsonl(self, output_path: Path) -> None:
        """Write assertions to JSON Lines format for CI."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            for result in self.assertions:
                # Write summary line
                summary = {
                    "type": "validation_result",
                    "timestamp": result.timestamp.isoformat(),
                    "valid": result.is_valid,
                    "files_validated": len(result.validated_files),
                    "errors": len(result.errors),
                    "warnings": len(result.warnings),
                }
                f.write(json.dumps(summary) + "\n")

                # Write each error
                for error in result.errors:
                    error_dict = {
                        "type": "error",
                        "file": error.file,
                        "line": error.line,
                        "column": error.column,
                        "message": error.message,
                        "rule": error.rule,
                    }
                    f.write(json.dumps(error_dict) + "\n")

                # Write each warning
                for warning in result.warnings:
                    warning_dict = {
                        "type": "warning",
                        "file": warning.file,
                        "line": warning.line,
                        "column": warning.column,
                        "message": warning.message,
                        "rule": warning.rule,
                    }
                    f.write(json.dumps(warning_dict) + "\n")
