"""Tests for mathy-XML sanitizer."""

from pathlib import Path

from xml_lib.sanitize import MathPolicy, Sanitizer


def test_sanitizer_detects_invalid_names():
    """Test that sanitizer detects invalid element names."""
    sanitizer = Sanitizer(Path("out"))

    assert not sanitizer.is_valid_xml_name("×")
    assert not sanitizer.is_valid_xml_name("∘")
    assert not sanitizer.is_valid_xml_name("⊗")
    assert not sanitizer.is_valid_xml_name("123invalid")

    assert sanitizer.is_valid_xml_name("valid")
    assert sanitizer.is_valid_xml_name("_valid")
    assert sanitizer.is_valid_xml_name("valid-name")
    assert sanitizer.is_valid_xml_name("valid123")


def test_sanitizer_sanitizes_simple_element(tmp_path):
    """Test sanitization of simple mathy element."""
    # Create a file with an invalid element
    xml_file = tmp_path / "test.xml"
    xml_file.write_text('<?xml version="1.0"?>\n<×/>')

    sanitizer = Sanitizer(tmp_path)
    result = sanitizer.sanitize_for_parse(xml_file)

    assert result.has_surrogates
    assert len(result.mappings) > 0
    assert result.mappings[0].orig == "×"
    assert result.mappings[0].kind == "element"

    # Check that surrogate is valid XML
    assert '<op name="×"'.encode() in result.content
    assert 'xml:orig="×"'.encode() in result.content


def test_sanitizer_sanitizes_nested_elements(tmp_path):
    """Test sanitization of nested mathy elements."""
    xml_file = tmp_path / "test.xml"
    xml_file.write_text('<?xml version="1.0"?>\n<×><∘/></×>')

    sanitizer = Sanitizer(tmp_path)
    result = sanitizer.sanitize_for_parse(xml_file)

    assert result.has_surrogates
    assert len(result.mappings) == 2  # Two invalid elements

    # Verify both elements were sanitized
    orig_names = {m.orig for m in result.mappings}
    assert "×" in orig_names
    assert "∘" in orig_names


def test_sanitizer_roundtrip(tmp_path):
    """Test that sanitization is reversible."""
    # Create a file with invalid elements
    xml_file = tmp_path / "test.xml"
    original_content = '<?xml version="1.0"?>\n<×><∘/></×>'
    xml_file.write_text(original_content)

    sanitizer = Sanitizer(tmp_path)

    # Sanitize
    result = sanitizer.sanitize_for_parse(xml_file)
    sanitized_file = tmp_path / "sanitized.xml"
    sanitized_file.write_bytes(result.content)

    # Write mapping
    sanitizer.write_mapping(Path("test.xml"), result.mappings)

    # Restore
    restored_file = tmp_path / "restored.xml"
    mapping_file = tmp_path / "mappings/test.xml.mathmap.jsonl"

    sanitizer.restore(sanitized_file, mapping_file, restored_file)

    # Note: exact restoration may differ in whitespace, but structure should match
    restored_content = restored_file.read_text()
    assert "<×>" in restored_content or "<×/>" in restored_content
    assert "<∘/>" in restored_content


def test_sanitizer_preserves_valid_xml(tmp_path):
    """Test that valid XML passes through unchanged."""
    xml_file = tmp_path / "test.xml"
    xml_file.write_text('<?xml version="1.0"?>\n<valid><element/></valid>')

    sanitizer = Sanitizer(tmp_path)
    result = sanitizer.sanitize_for_parse(xml_file)

    assert not result.has_surrogates
    assert len(result.mappings) == 0

    # Content should be essentially unchanged
    assert b"<valid>" in result.content
    assert b"<element/>" in result.content


def test_sanitizer_compute_uid():
    """Test that UIDs are deterministic."""
    sanitizer = Sanitizer(Path("out"))

    uid1 = sanitizer.compute_uid("×")
    uid2 = sanitizer.compute_uid("×")
    uid3 = sanitizer.compute_uid("∘")

    assert uid1 == uid2  # Same input -> same UID
    assert uid1 != uid3  # Different input -> different UID
    assert len(uid1) == 16  # Should be truncated hash


def test_math_policy_enum():
    """Test MathPolicy enum values."""
    assert MathPolicy.SANITIZE.value == "sanitize"
    assert MathPolicy.MATHML.value == "mathml"
    assert MathPolicy.SKIP.value == "skip"
    assert MathPolicy.ERROR.value == "error"

    # Test that we can construct from string
    policy = MathPolicy("sanitize")
    assert policy == MathPolicy.SANITIZE
