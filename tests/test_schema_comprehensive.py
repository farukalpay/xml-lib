"""Comprehensive tests for schema derivation and validation."""

import tempfile
from pathlib import Path

import pytest

from xml_lib.schema import (
    SchemaValidator,
    derive_relaxng_from_examples,
    derive_xsd_from_examples,
    validate_with_schema,
)


class TestSchemaValidator:
    """Tests for SchemaValidator class."""

    def test_create_validator_without_cache(self):
        """Test creating validator without cache directory."""
        validator = SchemaValidator()
        assert validator is not None
        assert validator.xsd_cache is not None
        assert validator.rng_cache is not None

    def test_create_validator_with_cache(self):
        """Test creating validator with cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            validator = SchemaValidator(cache_dir=cache_dir)
            assert validator is not None

    def test_validate_with_xsd_valid_document(self):
        """Test XSD validation with valid document."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create simple XSD schema
            xsd_content = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="root">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="child" type="xs:string" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>'''
            xsd_path = tmpdir / "schema.xsd"
            xsd_path.write_text(xsd_content)

            # Create valid XML
            xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<root>
  <child>test</child>
</root>'''
            xml_path = tmpdir / "valid.xml"
            xml_path.write_text(xml_content)

            # Validate
            validator = SchemaValidator()
            result = validator.validate_with_xsd(xml_path, xsd_path)

            assert result.is_valid is True
            assert len(result.errors) == 0
            assert result.metadata["schema_type"] == "xsd"

    def test_validate_with_xsd_invalid_document(self):
        """Test XSD validation with invalid document."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create simple XSD schema that requires 'name' attribute
            xsd_content = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="root">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="item">
          <xs:complexType>
            <xs:attribute name="id" type="xs:string" use="required"/>
          </xs:complexType>
        </xs:element>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>'''
            xsd_path = tmpdir / "schema.xsd"
            xsd_path.write_text(xsd_content)

            # Create invalid XML (missing required attribute)
            xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<root>
  <item/>
</root>'''
            xml_path = tmpdir / "invalid.xml"
            xml_path.write_text(xml_content)

            # Validate
            validator = SchemaValidator()
            result = validator.validate_with_xsd(xml_path, xsd_path)

            assert result.is_valid is False
            assert len(result.errors) > 0

    def test_validate_with_xsd_malformed_schema(self):
        """Test XSD validation with malformed schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create malformed XSD
            xsd_path = tmpdir / "bad.xsd"
            xsd_path.write_text("not valid xsd")

            xml_path = tmpdir / "test.xml"
            xml_path.write_text("<root/>")

            validator = SchemaValidator()
            result = validator.validate_with_xsd(xml_path, xsd_path)

            assert result.is_valid is False
            assert len(result.errors) > 0

    def test_validate_with_xsd_caching(self):
        """Test that XSD schemas are cached."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create schema
            xsd_content = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="root" type="xs:string"/>
</xs:schema>'''
            xsd_path = tmpdir / "schema.xsd"
            xsd_path.write_text(xsd_content)

            # Create XML
            xml_path = tmpdir / "test.xml"
            xml_path.write_text("<root>test</root>")

            validator = SchemaValidator()

            # First validation - schema not in cache
            result1 = validator.validate_with_xsd(xml_path, xsd_path)
            assert result1.is_valid

            # Second validation - schema should be cached
            result2 = validator.validate_with_xsd(xml_path, xsd_path)
            assert result2.is_valid

    def test_validate_with_relaxng_valid_document(self):
        """Test RELAX NG validation with valid document."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create RELAX NG schema
            rng_content = '''<?xml version="1.0" encoding="UTF-8"?>
<grammar xmlns="http://relaxng.org/ns/structure/1.0">
  <start>
    <element name="root">
      <zeroOrMore>
        <element name="child">
          <text/>
        </element>
      </zeroOrMore>
    </element>
  </start>
</grammar>'''
            rng_path = tmpdir / "schema.rng"
            rng_path.write_text(rng_content)

            # Create valid XML
            xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<root>
  <child>test</child>
</root>'''
            xml_path = tmpdir / "valid.xml"
            xml_path.write_text(xml_content)

            # Validate
            validator = SchemaValidator()
            result = validator.validate_with_relaxng(xml_path, rng_path)

            assert result.is_valid is True
            assert len(result.errors) == 0
            assert result.metadata["schema_type"] == "relaxng"

    def test_validate_with_relaxng_invalid_document(self):
        """Test RELAX NG validation with invalid document."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create RELAX NG schema that requires specific structure
            rng_content = '''<?xml version="1.0" encoding="UTF-8"?>
<grammar xmlns="http://relaxng.org/ns/structure/1.0">
  <start>
    <element name="root">
      <element name="required">
        <text/>
      </element>
    </element>
  </start>
</grammar>'''
            rng_path = tmpdir / "schema.rng"
            rng_path.write_text(rng_content)

            # Create invalid XML (missing required element)
            xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<root>
  <optional>test</optional>
</root>'''
            xml_path = tmpdir / "invalid.xml"
            xml_path.write_text(xml_content)

            # Validate
            validator = SchemaValidator()
            result = validator.validate_with_relaxng(xml_path, rng_path)

            assert result.is_valid is False
            assert len(result.errors) > 0

    def test_validate_with_relaxng_malformed_schema(self):
        """Test RELAX NG validation with malformed schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            rng_path = tmpdir / "bad.rng"
            rng_path.write_text("not valid relaxng")

            xml_path = tmpdir / "test.xml"
            xml_path.write_text("<root/>")

            validator = SchemaValidator()
            result = validator.validate_with_relaxng(xml_path, rng_path)

            assert result.is_valid is False
            assert len(result.errors) > 0

    def test_validate_with_relaxng_caching(self):
        """Test that RELAX NG schemas are cached."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create schema
            rng_content = '''<?xml version="1.0" encoding="UTF-8"?>
<grammar xmlns="http://relaxng.org/ns/structure/1.0">
  <start>
    <element name="root">
      <text/>
    </element>
  </start>
</grammar>'''
            rng_path = tmpdir / "schema.rng"
            rng_path.write_text(rng_content)

            xml_path = tmpdir / "test.xml"
            xml_path.write_text("<root>test</root>")

            validator = SchemaValidator()

            # First validation
            result1 = validator.validate_with_relaxng(xml_path, rng_path)
            assert result1.is_valid

            # Second validation - should use cache
            result2 = validator.validate_with_relaxng(xml_path, rng_path)
            assert result2.is_valid

    def test_validate_with_schema_autodetect_xsd(self):
        """Test auto-detection of XSD schema type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create XSD schema
            xsd_content = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="root" type="xs:string"/>
</xs:schema>'''
            xsd_path = tmpdir / "schema.xsd"
            xsd_path.write_text(xsd_content)

            xml_path = tmpdir / "test.xml"
            xml_path.write_text("<root>test</root>")

            validator = SchemaValidator()
            result = validator.validate_with_schema(xml_path, xsd_path)

            assert result.metadata["schema_type"] == "xsd"

    def test_validate_with_schema_autodetect_rng(self):
        """Test auto-detection of RELAX NG schema type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create RELAX NG schema
            rng_content = '''<?xml version="1.0" encoding="UTF-8"?>
<grammar xmlns="http://relaxng.org/ns/structure/1.0">
  <start>
    <element name="root"><text/></element>
  </start>
</grammar>'''
            rng_path = tmpdir / "schema.rng"
            rng_path.write_text(rng_content)

            xml_path = tmpdir / "test.xml"
            xml_path.write_text("<root>test</root>")

            validator = SchemaValidator()
            result = validator.validate_with_schema(xml_path, rng_path)

            assert result.metadata["schema_type"] == "relaxng"

    def test_validate_with_schema_unknown_extension(self):
        """Test handling of unknown schema extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            schema_path = tmpdir / "schema.unknown"
            schema_path.write_text("something")

            xml_path = tmpdir / "test.xml"
            xml_path.write_text("<root/>")

            validator = SchemaValidator()
            result = validator.validate_with_schema(xml_path, schema_path)

            assert result.is_valid is False
            assert "Unknown schema type" in str(result.errors)

    def test_validate_with_schema_explicit_type(self):
        """Test explicit schema type specification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create XSD schema with .xml extension
            xsd_content = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="root" type="xs:string"/>
</xs:schema>'''
            xsd_path = tmpdir / "schema.xml"  # Using .xml extension
            xsd_path.write_text(xsd_content)

            xml_path = tmpdir / "test.xml"
            xml_path.write_text("<root>test</root>")

            validator = SchemaValidator()
            result = validator.validate_with_schema(xml_path, xsd_path, schema_type="xsd")

            assert result.is_valid is True

    def test_validate_with_schema_unsupported_type(self):
        """Test handling of unsupported schema type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            schema_path = tmpdir / "schema.txt"
            schema_path.write_text("something")

            xml_path = tmpdir / "test.xml"
            xml_path.write_text("<root/>")

            validator = SchemaValidator()
            result = validator.validate_with_schema(xml_path, schema_path, schema_type="dtd")

            assert result.is_valid is False
            assert "Unsupported schema type" in str(result.errors)


class TestDeriveXSDFromExamples:
    """Tests for XSD schema derivation."""

    def test_derive_xsd_single_example(self):
        """Test deriving XSD from single example."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create example XML
            example_content = '''<?xml version="1.0" encoding="UTF-8"?>
<document>
  <title>Test</title>
  <content>Body</content>
</document>'''
            example_path = tmpdir / "example.xml"
            example_path.write_text(example_content)

            output_path = tmpdir / "derived.xsd"

            derive_xsd_from_examples([example_path], output_path)

            assert output_path.exists()
            content = output_path.read_text()
            assert "xs:schema" in content
            assert 'name="document"' in content
            assert 'name="title"' in content
            assert 'name="content"' in content

    def test_derive_xsd_multiple_examples(self):
        """Test deriving XSD from multiple examples."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create first example
            ex1_content = '''<?xml version="1.0" encoding="UTF-8"?>
<document>
  <title>Test 1</title>
</document>'''
            ex1_path = tmpdir / "example1.xml"
            ex1_path.write_text(ex1_content)

            # Create second example with additional element
            ex2_content = '''<?xml version="1.0" encoding="UTF-8"?>
<document>
  <author>John</author>
</document>'''
            ex2_path = tmpdir / "example2.xml"
            ex2_path.write_text(ex2_content)

            output_path = tmpdir / "derived.xsd"

            derive_xsd_from_examples([ex1_path, ex2_path], output_path)

            content = output_path.read_text()
            # Should include elements from both examples
            assert 'name="title"' in content
            assert 'name="author"' in content

    def test_derive_xsd_with_root_element_override(self):
        """Test deriving XSD with custom root element name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            example_content = '''<?xml version="1.0" encoding="UTF-8"?>
<doc>
  <field>value</field>
</doc>'''
            example_path = tmpdir / "example.xml"
            example_path.write_text(example_content)

            output_path = tmpdir / "derived.xsd"

            derive_xsd_from_examples([example_path], output_path, root_element="document")

            content = output_path.read_text()
            assert 'name="document"' in content

    def test_derive_xsd_creates_parent_directories(self):
        """Test that derive creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            example_path = tmpdir / "example.xml"
            example_path.write_text("<root><child>test</child></root>")

            output_path = tmpdir / "nested" / "dir" / "schema.xsd"

            derive_xsd_from_examples([example_path], output_path)

            assert output_path.exists()

    def test_derive_xsd_no_examples_raises_error(self):
        """Test that empty examples list raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "schema.xsd"

            with pytest.raises(ValueError, match="No example files provided"):
                derive_xsd_from_examples([], output_path)


class TestDeriveRelaxNGFromExamples:
    """Tests for RELAX NG schema derivation."""

    def test_derive_relaxng_single_example(self):
        """Test deriving RELAX NG from single example."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            example_content = '''<?xml version="1.0" encoding="UTF-8"?>
<document>
  <title>Test</title>
  <content>Body</content>
</document>'''
            example_path = tmpdir / "example.xml"
            example_path.write_text(example_content)

            output_path = tmpdir / "derived.rng"

            derive_relaxng_from_examples([example_path], output_path)

            assert output_path.exists()
            content = output_path.read_text()
            assert "relaxng.org/ns/structure" in content
            assert 'name="document"' in content
            assert 'name="title"' in content
            assert 'name="content"' in content

    def test_derive_relaxng_multiple_examples(self):
        """Test deriving RELAX NG from multiple examples."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            ex1_path = tmpdir / "ex1.xml"
            ex1_path.write_text("<root><field1>val1</field1></root>")

            ex2_path = tmpdir / "ex2.xml"
            ex2_path.write_text("<root><field2>val2</field2></root>")

            output_path = tmpdir / "derived.rng"

            derive_relaxng_from_examples([ex1_path, ex2_path], output_path)

            content = output_path.read_text()
            assert 'name="field1"' in content
            assert 'name="field2"' in content

    def test_derive_relaxng_with_root_element_override(self):
        """Test deriving RELAX NG with custom root element."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            example_path = tmpdir / "example.xml"
            example_path.write_text("<doc><item>test</item></doc>")

            output_path = tmpdir / "derived.rng"

            derive_relaxng_from_examples([example_path], output_path, root_element="document")

            content = output_path.read_text()
            assert 'name="document"' in content

    def test_derive_relaxng_creates_parent_directories(self):
        """Test that derive creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            example_path = tmpdir / "example.xml"
            example_path.write_text("<root><child>test</child></root>")

            output_path = tmpdir / "nested" / "dir" / "schema.rng"

            derive_relaxng_from_examples([example_path], output_path)

            assert output_path.exists()

    def test_derive_relaxng_no_examples_raises_error(self):
        """Test that empty examples list raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "schema.rng"

            with pytest.raises(ValueError, match="No example files provided"):
                derive_relaxng_from_examples([], output_path)


class TestValidateWithSchemaFunction:
    """Tests for the convenience function validate_with_schema."""

    def test_validate_with_schema_xsd(self):
        """Test convenience function with XSD schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            xsd_content = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="root" type="xs:string"/>
</xs:schema>'''
            xsd_path = tmpdir / "schema.xsd"
            xsd_path.write_text(xsd_content)

            xml_path = tmpdir / "test.xml"
            xml_path.write_text("<root>test</root>")

            result = validate_with_schema(xml_path, xsd_path)

            assert result.is_valid is True

    def test_validate_with_schema_relaxng(self):
        """Test convenience function with RELAX NG schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            rng_content = '''<?xml version="1.0" encoding="UTF-8"?>
<grammar xmlns="http://relaxng.org/ns/structure/1.0">
  <start>
    <element name="root"><text/></element>
  </start>
</grammar>'''
            rng_path = tmpdir / "schema.rng"
            rng_path.write_text(rng_content)

            xml_path = tmpdir / "test.xml"
            xml_path.write_text("<root>test</root>")

            result = validate_with_schema(xml_path, rng_path)

            assert result.is_valid is True

    def test_validate_with_schema_with_cache(self):
        """Test convenience function with cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            xsd_content = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="root" type="xs:string"/>
</xs:schema>'''
            xsd_path = tmpdir / "schema.xsd"
            xsd_path.write_text(xsd_content)

            xml_path = tmpdir / "test.xml"
            xml_path.write_text("<root>test</root>")

            cache_dir = tmpdir / "cache"
            result = validate_with_schema(xml_path, xsd_path, cache_dir=cache_dir)

            assert result.is_valid is True

    def test_validate_with_schema_explicit_type(self):
        """Test convenience function with explicit schema type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            xsd_content = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="root" type="xs:string"/>
</xs:schema>'''
            xsd_path = tmpdir / "schema.xml"  # Non-standard extension
            xsd_path.write_text(xsd_content)

            xml_path = tmpdir / "test.xml"
            xml_path.write_text("<root>test</root>")

            result = validate_with_schema(xml_path, xsd_path, schema_type="xsd")

            assert result.is_valid is True


class TestSchemaErrorHandling:
    """Tests for error handling in schema operations."""

    def test_validate_nonexistent_xml_file(self):
        """Test validation with nonexistent XML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            xsd_content = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="root" type="xs:string"/>
</xs:schema>'''
            xsd_path = tmpdir / "schema.xsd"
            xsd_path.write_text(xsd_content)

            xml_path = tmpdir / "nonexistent.xml"

            validator = SchemaValidator()
            result = validator.validate_with_xsd(xml_path, xsd_path)

            assert result.is_valid is False
            assert len(result.errors) > 0

    def test_validate_nonexistent_schema_file(self):
        """Test validation with nonexistent schema file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            xml_path = tmpdir / "test.xml"
            xml_path.write_text("<root/>")

            xsd_path = tmpdir / "nonexistent.xsd"

            validator = SchemaValidator()
            result = validator.validate_with_xsd(xml_path, xsd_path)

            assert result.is_valid is False

    def test_validate_malformed_xml_document(self):
        """Test validation with malformed XML document."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            xsd_content = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="root" type="xs:string"/>
</xs:schema>'''
            xsd_path = tmpdir / "schema.xsd"
            xsd_path.write_text(xsd_content)

            xml_path = tmpdir / "malformed.xml"
            xml_path.write_text("<root>not closed")

            validator = SchemaValidator()
            result = validator.validate_with_xsd(xml_path, xsd_path)

            assert result.is_valid is False
            assert len(result.errors) > 0

    def test_relaxng_validation_error_includes_line_numbers(self):
        """Test that RELAX NG errors include line numbers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            rng_content = '''<?xml version="1.0" encoding="UTF-8"?>
<grammar xmlns="http://relaxng.org/ns/structure/1.0">
  <start>
    <element name="root">
      <element name="required"><text/></element>
    </element>
  </start>
</grammar>'''
            rng_path = tmpdir / "schema.rng"
            rng_path.write_text(rng_content)

            xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<root>
  <wrong>test</wrong>
</root>'''
            xml_path = tmpdir / "invalid.xml"
            xml_path.write_text(xml_content)

            validator = SchemaValidator()
            result = validator.validate_with_relaxng(xml_path, rng_path)

            assert result.is_valid is False
            # Check that errors mention line numbers
            assert any("Line" in str(err) for err in result.errors)
