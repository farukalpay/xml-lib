"""Tests for XML differ."""

import pytest
from pathlib import Path

from xml_lib.differ import Differ, DiffType


@pytest.fixture
def differ():
    """Create differ instance."""
    schemas_dir = Path("schemas")
    return Differ(schemas_dir, telemetry=None)


@pytest.fixture
def xml_files(tmp_path):
    """Create sample XML files for diffing."""
    file1 = tmp_path / "file1.xml"
    file1.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<document id="doc-1" timestamp="2025-01-15T10:00:00Z">
  <meta>
    <title>Original Document</title>
  </meta>
  <phases>
    <phase name="begin">
      <payload>Original content</payload>
    </phase>
  </phases>
</document>
"""
    )

    file2 = tmp_path / "file2.xml"
    file2.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<document id="doc-1" timestamp="2025-01-15T11:00:00Z">
  <meta>
    <title>Modified Document</title>
  </meta>
  <phases>
    <phase name="begin">
      <payload>Modified content</payload>
    </phase>
    <phase name="start">
      <payload>New phase</payload>
    </phase>
  </phases>
</document>
"""
    )

    return file1, file2


def test_diff_identical_files(differ, tmp_path):
    """Test diffing identical files."""
    file1 = tmp_path / "file1.xml"
    file1.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<document>
  <phases>
    <phase name="begin">
      <payload>Test</payload>
    </phase>
  </phases>
</document>
"""
    )

    file2 = tmp_path / "file2.xml"
    file2.write_text(file1.read_text())

    result = differ.diff(file1, file2)

    assert result.identical
    assert len(result.differences) == 0


def test_diff_detects_modifications(differ, xml_files):
    """Test that differ detects modifications."""
    file1, file2 = xml_files

    result = differ.diff(file1, file2, explain=False)

    assert not result.identical
    assert len(result.differences) > 0

    # Should detect timestamp change
    timestamp_diffs = [d for d in result.differences if "timestamp" in d.path.lower()]
    assert len(timestamp_diffs) > 0


def test_diff_detects_additions(differ, xml_files):
    """Test that differ detects added elements."""
    file1, file2 = xml_files

    result = differ.diff(file1, file2)

    # Should detect new phase (will be detected as document/phases/phase[2])
    added_diffs = [
        d for d in result.differences if d.type == DiffType.ADDED and "phase" in str(d.path).lower()
    ]
    assert len(added_diffs) > 0


def test_diff_with_explanations(differ, xml_files):
    """Test that differ provides explanations."""
    file1, file2 = xml_files

    result = differ.diff(file1, file2, explain=True)

    # Explanations should be present
    explained_diffs = [d for d in result.differences if d.explanation is not None]
    assert len(explained_diffs) > 0


def test_diff_format_output(differ, xml_files):
    """Test that differences format correctly."""
    file1, file2 = xml_files

    result = differ.diff(file1, file2, explain=True)

    for diff in result.differences:
        formatted = diff.format(explain=True)
        assert len(formatted) > 0
        # Should include symbol
        assert any(symbol in formatted for symbol in ["+", "-", "~", "↔"])
