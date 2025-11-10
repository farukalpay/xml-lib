"""Tests for HTML publisher."""


import pytest

from xml_lib.publisher import Publisher


@pytest.fixture
def publisher(tmp_path):
    """Create publisher instance."""
    xslt_dir = tmp_path / "xslt"
    xslt_dir.mkdir()
    return Publisher(xslt_dir, telemetry=None)


@pytest.fixture
def sample_project(tmp_path):
    """Create sample project."""
    project = tmp_path / "project"
    project.mkdir()

    # Create a sample XML document
    doc = project / "sample.xml"
    doc.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<document>
  <meta>
    <title>Sample Document</title>
    <description>A sample for testing</description>
  </meta>
  <phases>
    <phase name="begin">
      <use path="lib/begin.xml">Initialize</use>
      <payload>
        <note>Starting</note>
      </payload>
    </phase>
  </phases>
  <summary>
    <status>complete</status>
  </summary>
</document>
"""
    )

    return project


def test_publish_creates_html(publisher, sample_project, tmp_path):
    """Test that publishing creates HTML files."""
    output_dir = tmp_path / "output"

    result = publisher.publish(sample_project, output_dir)

    assert result.success
    assert len(result.files) > 0
    assert output_dir.exists()

    # Check that HTML was created
    html_files = list(output_dir.rglob("*.html"))
    assert len(html_files) > 0


def test_publish_creates_index(publisher, sample_project, tmp_path):
    """Test that publishing creates an index page."""
    output_dir = tmp_path / "output"

    result = publisher.publish(sample_project, output_dir)

    assert result.success

    # Check for index.html
    index_file = output_dir / "index.html"
    assert index_file.exists()

    # Check content
    content = index_file.read_text()
    assert "XML-Lib Documentation" in content


def test_publish_transforms_xml(publisher, sample_project, tmp_path):
    """Test that XML is properly transformed."""
    output_dir = tmp_path / "output"

    result = publisher.publish(sample_project, output_dir)

    assert result.success

    # Find generated HTML
    html_file = next(output_dir.rglob("sample.html"))
    content = html_file.read_text()

    # Should contain transformed content
    assert "Sample Document" in content
    assert "Phase" in content or "begin" in content


def test_publish_handles_errors(publisher, tmp_path):
    """Test that publisher handles errors gracefully."""
    # Try to publish non-existent project
    result = publisher.publish(tmp_path / "nonexistent", tmp_path / "output")

    # Should handle gracefully
    assert not result.success
    assert result.error is not None
