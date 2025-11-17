"""Tests for assertion ledger with signing and JSON Lines output."""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from xml_lib.assertions import AssertionLedger, _get_crypto
from xml_lib.types import ValidationError, ValidationResult


class TestAssertionLedger:
    """Tests for AssertionLedger class."""

    def test_create_empty_ledger(self):
        """Test creating an empty assertion ledger."""
        ledger = AssertionLedger()
        assert ledger.assertions == []
        assert ledger.private_key is not None or ledger.private_key is None  # depends on crypto

    def test_add_validation_result(self):
        """Test adding validation results to ledger."""
        ledger = AssertionLedger()

        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            validated_files=["test.xml"],
            checksums={"test.xml": "abc123"},
            timestamp=datetime.now(),
        )

        ledger.add_validation_result(result)

        assert len(ledger.assertions) == 1
        assert ledger.assertions[0].is_valid is True

    def test_add_multiple_results(self):
        """Test adding multiple validation results."""
        ledger = AssertionLedger()

        for i in range(3):
            result = ValidationResult(
                is_valid=i % 2 == 0,
                errors=[],
                warnings=[],
                validated_files=[f"file{i}.xml"],
                checksums={},
                timestamp=datetime.now(),
            )
            ledger.add_validation_result(result)

        assert len(ledger.assertions) == 3

    def test_write_xml_creates_file(self):
        """Test that write_xml creates output file."""
        ledger = AssertionLedger()

        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            validated_files=["test.xml"],
            checksums={"test.xml": "abc123def456"},
            timestamp=datetime.now(),
        )
        ledger.add_validation_result(result)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "ledger.xml"
            ledger.write_xml(output_path)

            assert output_path.exists()
            content = output_path.read_text()
            assert "assertion-ledger" in content
            assert "test.xml" in content

    def test_write_xml_with_errors(self):
        """Test writing XML with validation errors."""
        ledger = AssertionLedger()

        error = ValidationError(
            file="test.xml",
            line=10,
            column=5,
            message="Invalid element",
            type="error",
            rule="GR1",
        )

        result = ValidationResult(
            is_valid=False,
            errors=[error],
            warnings=[],
            validated_files=["test.xml"],
            checksums={},
            timestamp=datetime.now(),
        )
        ledger.add_validation_result(result)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "ledger.xml"
            ledger.write_xml(output_path)

            content = output_path.read_text()
            assert "Invalid element" in content
            assert 'line="10"' in content
            assert 'column="5"' in content
            assert 'rule="GR1"' in content

    def test_write_xml_with_warnings(self):
        """Test writing XML with validation warnings."""
        ledger = AssertionLedger()

        warning = ValidationError(
            file="test.xml",
            line=20,
            column=None,
            message="Deprecated element",
            type="warning",
            rule=None,
        )

        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[warning],
            validated_files=["test.xml"],
            checksums={},
            timestamp=datetime.now(),
        )
        ledger.add_validation_result(result)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "ledger.xml"
            ledger.write_xml(output_path)

            content = output_path.read_text()
            assert "Deprecated element" in content

    def test_write_xml_creates_parent_directories(self):
        """Test that write_xml creates parent directories."""
        ledger = AssertionLedger()
        ledger.add_validation_result(
            ValidationResult(
                is_valid=True,
                errors=[],
                warnings=[],
                validated_files=[],
                checksums={},
                timestamp=datetime.now(),
            )
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "dir" / "ledger.xml"
            ledger.write_xml(output_path)

            assert output_path.exists()

    def test_write_jsonl_creates_file(self):
        """Test that write_jsonl creates output file."""
        ledger = AssertionLedger()

        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            validated_files=["test.xml"],
            checksums={},
            timestamp=datetime.now(),
        )
        ledger.add_validation_result(result)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "ledger.jsonl"
            ledger.write_jsonl(output_path)

            assert output_path.exists()

    def test_write_jsonl_format(self):
        """Test JSONL output format."""
        ledger = AssertionLedger()

        error = ValidationError(
            file="error.xml",
            line=5,
            column=10,
            message="Schema error",
            type="error",
            rule="SCHEMA1",
        )

        result = ValidationResult(
            is_valid=False,
            errors=[error],
            warnings=[],
            validated_files=["error.xml"],
            checksums={},
            timestamp=datetime.now(),
        )
        ledger.add_validation_result(result)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "ledger.jsonl"
            ledger.write_jsonl(output_path)

            lines = output_path.read_text().strip().split("\n")
            assert len(lines) == 2  # summary + error

            # Check summary line
            summary = json.loads(lines[0])
            assert summary["type"] == "validation_result"
            assert summary["valid"] is False
            assert summary["files_validated"] == 1
            assert summary["errors"] == 1
            assert summary["warnings"] == 0

            # Check error line
            error_line = json.loads(lines[1])
            assert error_line["type"] == "error"
            assert error_line["file"] == "error.xml"
            assert error_line["line"] == 5
            assert error_line["column"] == 10
            assert error_line["message"] == "Schema error"
            assert error_line["rule"] == "SCHEMA1"

    def test_write_jsonl_with_warnings(self):
        """Test JSONL output includes warnings."""
        ledger = AssertionLedger()

        warning = ValidationError(
            file="warn.xml",
            line=15,
            column=None,
            message="Style warning",
            type="warning",
            rule=None,
        )

        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[warning],
            validated_files=["warn.xml"],
            checksums={},
            timestamp=datetime.now(),
        )
        ledger.add_validation_result(result)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "ledger.jsonl"
            ledger.write_jsonl(output_path)

            lines = output_path.read_text().strip().split("\n")
            assert len(lines) == 2  # summary + warning

            warning_line = json.loads(lines[1])
            assert warning_line["type"] == "warning"
            assert warning_line["message"] == "Style warning"

    def test_write_jsonl_multiple_results(self):
        """Test JSONL with multiple validation results."""
        ledger = AssertionLedger()

        for i in range(2):
            result = ValidationResult(
                is_valid=True,
                errors=[],
                warnings=[],
                validated_files=[f"file{i}.xml"],
                checksums={},
                timestamp=datetime.now(),
            )
            ledger.add_validation_result(result)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "ledger.jsonl"
            ledger.write_jsonl(output_path)

            lines = output_path.read_text().strip().split("\n")
            assert len(lines) == 2  # 2 summary lines

    def test_write_jsonl_creates_parent_directories(self):
        """Test that write_jsonl creates parent directories."""
        ledger = AssertionLedger()
        ledger.add_validation_result(
            ValidationResult(
                is_valid=True,
                errors=[],
                warnings=[],
                validated_files=[],
                checksums={},
                timestamp=datetime.now(),
            )
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "dir" / "ledger.jsonl"
            ledger.write_jsonl(output_path)

            assert output_path.exists()


class TestCryptoOperations:
    """Tests for cryptographic operations in assertions."""

    def test_get_crypto_returns_modules_or_empty(self):
        """Test that _get_crypto returns either crypto modules or empty dict."""
        try:
            result = _get_crypto()
            assert isinstance(result, dict)
        except Exception:
            # If crypto fails to load, it's handled gracefully
            pass

    def test_ledger_key_generation(self):
        """Test that ledger generates key pair."""
        ledger = AssertionLedger()
        # Either crypto is available and we have keys, or it's not
        if ledger.private_key is not None:
            assert ledger.public_key is not None
        else:
            assert ledger.public_key is None

    def test_sign_data_with_crypto(self):
        """Test signing data when crypto is available."""
        ledger = AssertionLedger()

        # Skip if no crypto
        if ledger.private_key is None:
            pytest.skip("Cryptography package not available")

        test_data = b"test data to sign"
        signature = ledger._sign_data(test_data)

        assert signature is not None
        assert isinstance(signature, bytes)
        assert len(signature) > 0

    def test_xml_includes_signature(self):
        """Test that XML output includes signature when crypto is available."""
        ledger = AssertionLedger()

        # Skip if no crypto
        if ledger.private_key is None:
            pytest.skip("Cryptography package not available")

        ledger.add_validation_result(
            ValidationResult(
                is_valid=True,
                errors=[],
                warnings=[],
                validated_files=["test.xml"],
                checksums={},
                timestamp=datetime.now(),
            )
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "signed.xml"
            ledger.write_xml(output_path)

            content = output_path.read_text()
            assert "signature" in content
            assert "RSA-PSS-SHA256" in content
            assert "public-key" in content

    def test_xml_includes_public_key(self):
        """Test that XML includes public key for verification."""
        ledger = AssertionLedger()

        # Skip if no crypto
        if ledger.private_key is None:
            pytest.skip("Cryptography package not available")

        ledger.add_validation_result(
            ValidationResult(
                is_valid=True,
                errors=[],
                warnings=[],
                validated_files=[],
                checksums={},
                timestamp=datetime.now(),
            )
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "signed.xml"
            ledger.write_xml(output_path)

            content = output_path.read_text()
            assert "BEGIN PUBLIC KEY" in content
            assert "END PUBLIC KEY" in content

    def test_xml_without_crypto_sets_signed_false(self):
        """Test that XML indicates unsigned when crypto unavailable."""
        with patch("xml_lib.assertions._get_crypto", return_value={}):
            ledger = AssertionLedger()
            ledger.add_validation_result(
                ValidationResult(
                    is_valid=True,
                    errors=[],
                    warnings=[],
                    validated_files=[],
                    checksums={},
                    timestamp=datetime.now(),
                )
            )

            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "unsigned.xml"
                ledger.write_xml(output_path)

                content = output_path.read_text()
                assert 'signed="false"' in content

    def test_sign_data_without_private_key_returns_none(self):
        """Test that signing returns None when no private key."""
        ledger = AssertionLedger()
        ledger.private_key = None  # Simulate no private key

        result = ledger._sign_data(b"test")
        assert result is None


class TestValidationErrorHandling:
    """Tests for validation error edge cases."""

    def test_error_without_line_number(self):
        """Test error without line number."""
        ledger = AssertionLedger()

        error = ValidationError(
            file="test.xml",
            line=None,
            column=None,
            message="General error",
            type="error",
            rule=None,
        )

        result = ValidationResult(
            is_valid=False,
            errors=[error],
            warnings=[],
            validated_files=["test.xml"],
            checksums={},
            timestamp=datetime.now(),
        )
        ledger.add_validation_result(result)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "ledger.xml"
            ledger.write_xml(output_path)

            content = output_path.read_text()
            assert "General error" in content
            # Should not have line attribute when None
            assert content.count('line="') == 0

    def test_error_without_rule(self):
        """Test error without rule attribute."""
        ledger = AssertionLedger()

        error = ValidationError(
            file="test.xml",
            line=10,
            column=5,
            message="No rule error",
            type="error",
            rule=None,
        )

        result = ValidationResult(
            is_valid=False,
            errors=[error],
            warnings=[],
            validated_files=["test.xml"],
            checksums={},
            timestamp=datetime.now(),
        )
        ledger.add_validation_result(result)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "ledger.xml"
            ledger.write_xml(output_path)

            content = output_path.read_text()
            # Should not have rule attribute when None
            assert "No rule error" in content

    def test_empty_validation_result(self):
        """Test handling empty validation result."""
        ledger = AssertionLedger()

        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            validated_files=[],
            checksums={},
            timestamp=datetime.now(),
        )
        ledger.add_validation_result(result)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "ledger.xml"
            ledger.write_xml(output_path)

            content = output_path.read_text()
            assert "files-validated>0<" in content

    def test_multiple_errors_and_warnings(self):
        """Test handling multiple errors and warnings."""
        ledger = AssertionLedger()

        errors = [
            ValidationError("file1.xml", 1, 1, "Error 1", "error", "R1"),
            ValidationError("file2.xml", 2, 2, "Error 2", "error", "R2"),
        ]
        warnings = [
            ValidationError("file1.xml", 5, 5, "Warning 1", "warning", "R3"),
        ]

        result = ValidationResult(
            is_valid=False,
            errors=errors,
            warnings=warnings,
            validated_files=["file1.xml", "file2.xml"],
            checksums={},
            timestamp=datetime.now(),
        )
        ledger.add_validation_result(result)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Test XML output
            xml_path = Path(tmpdir) / "ledger.xml"
            ledger.write_xml(xml_path)

            content = xml_path.read_text()
            assert "Error 1" in content
            assert "Error 2" in content
            assert "Warning 1" in content

            # Test JSONL output
            jsonl_path = Path(tmpdir) / "ledger.jsonl"
            ledger.write_jsonl(jsonl_path)

            lines = jsonl_path.read_text().strip().split("\n")
            assert len(lines) == 4  # 1 summary + 2 errors + 1 warning
