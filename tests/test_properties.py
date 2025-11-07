"""Property-based tests for idempotence and invariants."""

import pytest
from pathlib import Path
from hypothesis import given, strategies as st
from lxml import etree

from xml_lib.validator import Validator
from xml_lib.storage import ContentStore, deterministic_uuid, compute_checksum


# Strategies for generating XML elements
@st.composite
def xml_phase_name(draw):
    """Generate valid phase names."""
    return draw(st.sampled_from(["begin", "start", "iteration", "end", "continuum"]))


@st.composite
def xml_timestamp(draw):
    """Generate valid ISO 8601 timestamps."""
    year = draw(st.integers(min_value=2020, max_value=2030))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))  # Safe for all months
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    second = draw(st.integers(min_value=0, max_value=59))
    return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}Z"


@st.composite
def xml_document(draw):
    """Generate a valid XML document."""
    doc_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Ll", "Nd"))))
    title = draw(st.text(min_size=1, max_size=100))

    phases = []
    phase_names = ["begin", "start", "iteration", "end", "continuum"]

    # Randomly include phases (but always include begin)
    include_begin = True
    include_phases = [include_begin] + [draw(st.booleans()) for _ in range(4)]

    prev_timestamp = None
    for i, (phase_name, include) in enumerate(zip(phase_names, include_phases)):
        if include:
            # Generate monotonically increasing timestamp
            if prev_timestamp:
                # Parse and increment
                parts = prev_timestamp.replace("Z", "").split("T")
                date_parts = parts[0].split("-")
                time_parts = parts[1].split(":")
                minute = int(time_parts[1])
                minute = (minute + draw(st.integers(min_value=1, max_value=10))) % 60
                timestamp = f"{date_parts[0]}-{date_parts[1]}-{date_parts[2]}T{time_parts[0]}:{minute:02d}:{time_parts[2]}Z"
            else:
                timestamp = draw(xml_timestamp())

            phases.append((phase_name, timestamp))
            prev_timestamp = timestamp

    return (doc_id, title, phases)


@given(xml_document())
def test_deterministic_uuid_idempotence(doc_data):
    """Test that deterministic UUIDs are idempotent."""
    doc_id, title, phases = doc_data

    # Generate UUID twice
    uuid1 = deterministic_uuid("xml-lib", doc_id)
    uuid2 = deterministic_uuid("xml-lib", doc_id)

    # Should be identical
    assert uuid1 == uuid2


@given(st.binary(min_size=1, max_size=1000))
def test_content_store_idempotence(tmp_path_factory, content):
    """Test that content storage is idempotent."""
    tmp_path = tmp_path_factory.mktemp("store")
    store = ContentStore(tmp_path)

    # Store content twice
    path1 = store.store(content)
    path2 = store.store(content)

    # Should be the same path
    assert path1 == path2

    # Should be retrievable
    retrieved = store.retrieve(path1.parent.name + path1.name.replace(".xml", ""))
    assert retrieved == content


@given(st.binary(min_size=1, max_size=1000))
def test_checksum_idempotence(tmp_path_factory, content):
    """Test that checksum computation is idempotent."""
    tmp_path = tmp_path_factory.mktemp("checksum")
    file_path = tmp_path / "test.xml"

    # Write and compute checksum twice
    file_path.write_bytes(content)
    checksum1 = compute_checksum(file_path)

    file_path.write_bytes(content)
    checksum2 = compute_checksum(file_path)

    # Should be identical
    assert checksum1 == checksum2


@given(xml_document())
def test_validation_idempotence(tmp_path_factory, doc_data):
    """Test that validation is idempotent."""
    doc_id, title, phases = doc_data

    # Create XML document
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<document id="{doc_id}">
  <meta>
    <title>{title}</title>
  </meta>
  <phases>
"""
    for phase_name, timestamp in phases:
        xml_content += f'    <phase name="{phase_name}" timestamp="{timestamp}">\n'
        xml_content += f'      <payload>Test {phase_name}</payload>\n'
        xml_content += f'    </phase>\n'

    xml_content += """  </phases>
</document>
"""

    tmp_path = tmp_path_factory.mktemp("validation")
    xml_file = tmp_path / "test.xml"
    xml_file.write_text(xml_content)

    # Validate twice
    schemas_dir = Path("schemas")
    guardrails_dir = Path("guardrails")
    validator = Validator(schemas_dir, guardrails_dir, telemetry=None)

    result1 = validator.validate_project(tmp_path)
    result2 = validator.validate_project(tmp_path)

    # Results should be consistent
    assert result1.is_valid == result2.is_valid
    assert len(result1.errors) == len(result2.errors)
    assert len(result1.warnings) == len(result2.warnings)


def test_validation_monotonic_timestamps(tmp_path):
    """Test that validation correctly identifies non-monotonic timestamps."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<document>
  <phases>
    <phase name="begin" timestamp="2025-01-15T10:00:00Z">
      <payload>Begin</payload>
    </phase>
    <phase name="start" timestamp="2025-01-15T09:00:00Z">
      <payload>Start in past</payload>
    </phase>
  </phases>
</document>
"""

    xml_file = tmp_path / "test.xml"
    xml_file.write_text(xml_content)

    schemas_dir = Path("schemas")
    guardrails_dir = Path("guardrails")
    validator = Validator(schemas_dir, guardrails_dir, telemetry=None)

    result = validator.validate_project(tmp_path)

    # Should detect temporal violation
    assert not result.is_valid


def test_cross_file_validation_consistency(tmp_path):
    """Test that cross-file validation is consistent."""
    # Create first file
    file1 = tmp_path / "file1.xml"
    file1.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<document id="doc-1">
  <phases>
    <phase name="begin" id="phase-1">
      <payload>File 1</payload>
    </phase>
  </phases>
</document>
""")

    # Create second file referencing first
    file2 = tmp_path / "file2.xml"
    file2.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<document id="doc-2">
  <phases>
    <phase name="begin" ref-begin="phase-1">
      <payload>File 2 referencing File 1</payload>
    </phase>
  </phases>
</document>
""")

    schemas_dir = Path("schemas")
    guardrails_dir = Path("guardrails")
    validator = Validator(schemas_dir, guardrails_dir, telemetry=None)

    # Validate multiple times
    result1 = validator.validate_project(tmp_path)
    result2 = validator.validate_project(tmp_path)
    result3 = validator.validate_project(tmp_path)

    # All results should be consistent
    assert result1.is_valid == result2.is_valid == result3.is_valid
    assert len(result1.errors) == len(result2.errors) == len(result3.errors)
