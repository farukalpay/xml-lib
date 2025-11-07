"""Tests for PowerPoint composer."""

import pytest
from pathlib import Path

from xml_lib.pptx_composer import PPTXComposer


@pytest.fixture
def composer():
    """Create PPTX composer instance."""
    return PPTXComposer(template=None, telemetry=None)


@pytest.fixture
def sample_xml(tmp_path):
    """Create sample XML file."""
    xml_file = tmp_path / "sample.xml"
    xml_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<document timestamp="2025-01-15T10:00:00Z">
  <meta>
    <title>Test Presentation</title>
    <description>A test presentation</description>
  </meta>
  <phases>
    <phase name="begin" timestamp="2025-01-15T10:00:00Z">
      <use path="lib/begin.xml">Initialize the project</use>
      <payload>
        <note>Getting started</note>
      </payload>
    </phase>
    <phase name="start" timestamp="2025-01-15T10:05:00Z">
      <use path="lib/start.xml">Set up constraints</use>
      <payload>
        <iterations>3</iterations>
      </payload>
    </phase>
  </phases>
  <summary>
    <status>complete</status>
    <next-action>Monitor progress</next-action>
  </summary>
</document>
"""
    )
    return xml_file


def test_render_creates_pptx(composer, sample_xml, tmp_path):
    """Test that rendering creates a PowerPoint file."""
    output_file = tmp_path / "output.pptx"

    result = composer.render(sample_xml, output_file)

    assert result.success
    assert output_file.exists()
    assert result.slide_count > 0


def test_render_includes_phases(composer, sample_xml, tmp_path):
    """Test that all phases are rendered as slides."""
    output_file = tmp_path / "output.pptx"

    result = composer.render(sample_xml, output_file)

    assert result.success
    # Should have: title slide + 2 phases + summary + citations
    assert result.slide_count >= 4


def test_render_includes_citations(composer, sample_xml, tmp_path):
    """Test that citations are included."""
    output_file = tmp_path / "output.pptx"

    result = composer.render(sample_xml, output_file)

    assert result.success
    assert result.citation_count > 0


def test_render_handles_invalid_xml(composer, tmp_path):
    """Test that renderer handles invalid XML gracefully."""
    xml_file = tmp_path / "invalid.xml"
    xml_file.write_text("not valid xml")

    output_file = tmp_path / "output.pptx"

    result = composer.render(xml_file, output_file)

    assert not result.success
    assert result.error is not None
