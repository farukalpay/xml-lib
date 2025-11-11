"""Comprehensive tests for guardrail engine."""

import tempfile
from pathlib import Path

import pytest
from lxml import etree

from xml_lib.guardrails import GuardrailEngine, GuardrailResult, GuardrailRule
from xml_lib.types import ValidationError


class TestGuardrailEngine:
    """Comprehensive tests for GuardrailEngine."""

    @pytest.fixture
    def temp_guardrails_dir(self):
        """Create temporary directory with test guardrails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            guardrails_dir = Path(tmpdir) / "guardrails"
            guardrails_dir.mkdir()

            # Create comprehensive test guardrail file
            guardrail_xml = """<?xml version="1.0" encoding="UTF-8"?>
<guardrails>
  <guardrail id="GR1" priority="critical">
    <name>ID Uniqueness</name>
    <description>All IDs must be unique across documents</description>
    <constraint type="xpath">count(//*[@id]) = count(//*[@id][not(@id = preceding::*/@id)])</constraint>
    <message>Duplicate IDs detected</message>
    <provenance>
      <author>System</author>
      <created>2024-01-01</created>
      <rationale>Ensures referential integrity</rationale>
    </provenance>
  </guardrail>

  <guardrail id="GR2" priority="high">
    <name>Checksum Format</name>
    <description>Checksums must be valid SHA-256</description>
    <constraint type="regex">[a-f0-9]{64}</constraint>
    <message>Invalid checksum format</message>
    <provenance>
      <author>System</author>
      <created>2024-01-01</created>
    </provenance>
  </guardrail>

  <guardrail id="GR3" priority="medium">
    <name>Required Title</name>
    <description>Documents must have a title</description>
    <constraint type="xpath">//title</constraint>
    <message>Missing required title element</message>
  </guardrail>

  <guardrail id="GR4" priority="low">
    <name>Temporal Ordering</name>
    <description>Timestamps must be in order</description>
    <constraint type="temporal">monotonic</constraint>
  </guardrail>
</guardrails>"""
            (guardrails_dir / "test.xml").write_text(guardrail_xml)

            yield guardrails_dir

    def test_engine_initialization(self, temp_guardrails_dir):
        """Test guardrail engine initialization."""
        engine = GuardrailEngine(temp_guardrails_dir)

        assert engine.guardrails_dir == temp_guardrails_dir
        assert len(engine.rules) >= 4

    def test_load_guardrails(self, temp_guardrails_dir):
        """Test loading guardrails from XML files."""
        engine = GuardrailEngine(temp_guardrails_dir)
        rules = engine.load_guardrails()

        assert len(rules) >= 4

        # Check rule properties
        id_uniqueness_rule = next((r for r in rules if r.id == "GR1"), None)
        assert id_uniqueness_rule is not None
        assert id_uniqueness_rule.name == "ID Uniqueness"
        assert id_uniqueness_rule.priority == "critical"
        assert id_uniqueness_rule.constraint_type == "xpath"

    def test_parse_guardrail_with_provenance(self, temp_guardrails_dir):
        """Test parsing guardrail with full provenance."""
        engine = GuardrailEngine(temp_guardrails_dir)

        gr1 = next((r for r in engine.rules if r.id == "GR1"), None)
        assert gr1 is not None

        # Check provenance
        assert "author" in gr1.provenance
        assert gr1.provenance["author"] == "System"
        assert "created" in gr1.provenance
        assert "rationale" in gr1.provenance

    def test_validate_project(self, temp_guardrails_dir):
        """Test validating a project against guardrails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "project"
            project_dir.mkdir()

            # Create test XML file
            test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<document id="test1">
  <title>Test Document</title>
  <checksum>a1b2c3d4e5f6</checksum>
</document>"""
            (project_dir / "test.xml").write_text(test_xml)

            engine = GuardrailEngine(temp_guardrails_dir)
            result = engine.validate(project_dir)

            assert isinstance(result, GuardrailResult)
            assert result.rules_checked > 0

    def test_xpath_constraint_checking(self, temp_guardrails_dir):
        """Test XPath constraint checking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "project"
            project_dir.mkdir()

            # Create XML without title (violates GR3)
            test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<document id="test1">
  <content>No title here</content>
</document>"""
            (project_dir / "test.xml").write_text(test_xml)

            engine = GuardrailEngine(temp_guardrails_dir)
            result = engine.validate(project_dir)

            # Should have warnings/errors about missing title
            assert len(result.errors) + len(result.warnings) > 0

    def test_regex_constraint_checking(self):
        """Test regex constraint checking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            guardrails_dir = Path(tmpdir) / "guardrails"
            guardrails_dir.mkdir()

            # Create guardrail with regex
            guardrail_xml = """<?xml version="1.0" encoding="UTF-8"?>
<guardrails>
  <guardrail id="REGEX1" priority="medium">
    <name>Email Format</name>
    <description>Check email format</description>
    <constraint type="regex">\\w+@\\w+\\.\\w+</constraint>
  </guardrail>
</guardrails>"""
            (guardrails_dir / "regex.xml").write_text(guardrail_xml)

            project_dir = Path(tmpdir) / "project"
            project_dir.mkdir()

            # Create XML with email
            test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<document>
  <contact>test@example.com</contact>
</document>"""
            (project_dir / "test.xml").write_text(test_xml)

            engine = GuardrailEngine(guardrails_dir)
            result = engine.validate(project_dir)

            # Should pass validation
            assert isinstance(result, GuardrailResult)

    def test_multiple_constraint_types(self, temp_guardrails_dir):
        """Test handling multiple constraint types."""
        engine = GuardrailEngine(temp_guardrails_dir)

        # Verify we have different constraint types
        constraint_types = {r.constraint_type for r in engine.rules}

        assert "xpath" in constraint_types
        assert "regex" in constraint_types
        assert "temporal" in constraint_types

    def test_priority_levels(self, temp_guardrails_dir):
        """Test different priority levels."""
        engine = GuardrailEngine(temp_guardrails_dir)

        priorities = {r.priority for r in engine.rules}

        assert "critical" in priorities
        assert "high" in priorities
        assert "medium" in priorities
        assert "low" in priorities

    def test_guardrail_without_message(self):
        """Test guardrail without custom message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            guardrails_dir = Path(tmpdir) / "guardrails"
            guardrails_dir.mkdir()

            guardrail_xml = """<?xml version="1.0" encoding="UTF-8"?>
<guardrails>
  <guardrail id="NO_MSG" priority="medium">
    <name>No Message Rule</name>
    <description>Test rule without message</description>
    <constraint type="xpath">//test</constraint>
  </guardrail>
</guardrails>"""
            (guardrails_dir / "test.xml").write_text(guardrail_xml)

            engine = GuardrailEngine(guardrails_dir)
            rule = next((r for r in engine.rules if r.id == "NO_MSG"), None)

            assert rule is not None
            assert rule.message is None

    def test_invalid_guardrail_xml(self):
        """Test handling invalid guardrail XML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            guardrails_dir = Path(tmpdir) / "guardrails"
            guardrails_dir.mkdir()

            # Create invalid XML (malformed)
            (guardrails_dir / "invalid.xml").write_text("not valid xml")

            # Should not crash, just skip the file
            engine = GuardrailEngine(guardrails_dir)

            # Engine should still initialize
            assert engine.rules is not None

    def test_guardrail_result_structure(self, temp_guardrails_dir):
        """Test GuardrailResult structure."""
        result = GuardrailResult()

        assert result.errors == []
        assert result.warnings == []
        assert result.rules_checked == 0

        # Add some data
        result.errors.append(
            ValidationError(
                file="test.xml",
                line=10,
                column=5,
                message="Test error",
                type="error",
                rule="GR1",
            )
        )
        result.rules_checked = 5

        assert len(result.errors) == 1
        assert result.rules_checked == 5

    def test_empty_guardrails_directory(self):
        """Test with empty guardrails directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            guardrails_dir = Path(tmpdir) / "empty"
            guardrails_dir.mkdir()

            engine = GuardrailEngine(guardrails_dir)

            assert engine.rules == []

    def test_nonexistent_guardrails_directory(self):
        """Test with nonexistent guardrails directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            guardrails_dir = Path(tmpdir) / "nonexistent"

            engine = GuardrailEngine(guardrails_dir)

            # Should not crash
            assert engine.rules == []

    def test_nested_guardrail_directories(self):
        """Test loading guardrails from nested directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            guardrails_dir = Path(tmpdir) / "guardrails"
            guardrails_dir.mkdir()

            # Create nested structure
            nested_dir = guardrails_dir / "category1" / "subcategory"
            nested_dir.mkdir(parents=True)

            # Add guardrail in nested directory
            guardrail_xml = """<?xml version="1.0" encoding="UTF-8"?>
<guardrails>
  <guardrail id="NESTED1" priority="medium">
    <name>Nested Rule</name>
    <description>Rule in nested directory</description>
    <constraint type="xpath">//test</constraint>
  </guardrail>
</guardrails>"""
            (nested_dir / "nested.xml").write_text(guardrail_xml)

            engine = GuardrailEngine(guardrails_dir)

            # Should find nested guardrails
            nested_rule = next((r for r in engine.rules if r.id == "NESTED1"), None)
            assert nested_rule is not None

    def test_check_rule_error_handling(self, temp_guardrails_dir):
        """Test error handling in _check_rule method."""
        engine = GuardrailEngine(temp_guardrails_dir)

        # Create a document
        doc = etree.fromstring(b"<test/>")

        # Create a rule with invalid XPath
        invalid_rule = GuardrailRule(
            id="INVALID",
            name="Invalid Rule",
            description="Test",
            priority="medium",
            constraint_type="xpath",
            constraint="//[invalid xpath syntax",
            message=None,
            provenance={},
        )

        # Should not crash
        violations = engine._check_rule(doc, Path("test.xml"), invalid_rule)

        # Should return empty list on error
        assert isinstance(violations, list)


class TestGuardrailRule:
    """Tests for GuardrailRule dataclass."""

    def test_create_guardrail_rule(self):
        """Test creating a GuardrailRule."""
        rule = GuardrailRule(
            id="TEST1",
            name="Test Rule",
            description="Test description",
            priority="high",
            constraint_type="xpath",
            constraint="//test",
            message="Test message",
            provenance={"author": "Test Author"},
        )

        assert rule.id == "TEST1"
        assert rule.name == "Test Rule"
        assert rule.priority == "high"
        assert rule.constraint_type == "xpath"
        assert rule.message == "Test message"
        assert rule.provenance["author"] == "Test Author"

    def test_rule_without_optional_fields(self):
        """Test creating rule without optional fields."""
        rule = GuardrailRule(
            id="TEST2",
            name="Minimal Rule",
            description="Minimal",
            priority="low",
            constraint_type="xpath",
            constraint="//test",
            message=None,
            provenance={},
        )

        assert rule.message is None
        assert rule.provenance == {}
