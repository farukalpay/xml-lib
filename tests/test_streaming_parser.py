"""Tests for streaming XML parser."""

import tempfile
from pathlib import Path

import pytest

from xml_lib.streaming.parser import (
    EventType,
    ParserEvent,
    ParserState,
    StreamingParser,
    count_elements,
    extract_element_names,
)


@pytest.fixture
def simple_xml():
    """Create a simple XML file for testing."""
    content = """<?xml version="1.0" encoding="UTF-8"?>
<root>
    <item id="1">
        <name>Item 1</name>
        <value>100</value>
    </item>
    <item id="2">
        <name>Item 2</name>
        <value>200</value>
    </item>
</root>"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
        f.write(content)
        path = Path(f.name)

    yield path
    path.unlink()


@pytest.fixture
def nested_xml():
    """Create a deeply nested XML file for testing."""
    content = """<?xml version="1.0" encoding="UTF-8"?>
<root>
    <level1>
        <level2>
            <level3>
                <level4>
                    <level5>Deep content</level5>
                </level4>
            </level3>
        </level2>
    </level1>
</root>"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
        f.write(content)
        path = Path(f.name)

    yield path
    path.unlink()


@pytest.fixture
def malformed_xml():
    """Create a malformed XML file for testing."""
    content = """<?xml version="1.0" encoding="UTF-8"?>
<root>
    <item>
        <name>Unclosed item
    </item>
</root>"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
        f.write(content)
        path = Path(f.name)

    yield path
    path.unlink()


class TestStreamingParser:
    """Test suite for StreamingParser."""

    def test_init(self):
        """Test parser initialization."""
        parser = StreamingParser()
        assert parser.enable_namespaces is True
        assert parser.buffer_size == 8192

        parser_no_ns = StreamingParser(enable_namespaces=False, buffer_size=4096)
        assert parser_no_ns.enable_namespaces is False
        assert parser_no_ns.buffer_size == 4096

    def test_parse_simple_xml(self, simple_xml):
        """Test parsing simple XML file."""
        parser = StreamingParser()
        events = list(parser.parse(simple_xml))

        # Should have start_document, end_document, and element events
        assert len(events) > 0

        # Check event types
        event_types = [e.type for e in events]
        assert EventType.START_DOCUMENT in event_types
        assert EventType.END_DOCUMENT in event_types
        assert EventType.START_ELEMENT in event_types
        assert EventType.END_ELEMENT in event_types

    def test_parse_start_element(self, simple_xml):
        """Test start element events."""
        parser = StreamingParser()
        events = list(parser.parse(simple_xml))

        # Find start element events
        start_events = [e for e in events if e.type == EventType.START_ELEMENT]

        # Should have root, item, name, value elements
        element_names = [e.name for e in start_events]
        assert "root" in element_names
        assert "item" in element_names
        assert "name" in element_names
        assert "value" in element_names

        # Check attributes on item elements
        item_events = [e for e in start_events if e.name == "item"]
        assert len(item_events) == 2
        assert "id" in item_events[0].attributes
        assert item_events[0].attributes["id"] in ["1", "2"]

    def test_parse_end_element(self, simple_xml):
        """Test end element events."""
        parser = StreamingParser()
        events = list(parser.parse(simple_xml))

        # Find end element events
        end_events = [e for e in events if e.type == EventType.END_ELEMENT]

        # Should match start elements
        element_names = [e.name for e in end_events]
        assert "root" in element_names
        assert "item" in element_names

        # Count should match start elements
        start_count = len([e for e in events if e.type == EventType.START_ELEMENT])
        end_count = len(end_events)
        assert start_count == end_count

    def test_parse_characters(self, simple_xml):
        """Test character data events."""
        parser = StreamingParser()
        events = list(parser.parse(simple_xml))

        # Find character events
        char_events = [e for e in events if e.type == EventType.CHARACTERS]

        # Should have content from name and value elements
        content_list = [e.content.strip() for e in char_events if e.content.strip()]
        assert "Item 1" in content_list
        assert "100" in content_list
        assert "Item 2" in content_list
        assert "200" in content_list

    def test_position_tracking(self, simple_xml):
        """Test that positions are tracked."""
        parser = StreamingParser()
        events = list(parser.parse(simple_xml))

        # All events should have position info
        for event in events:
            assert event.line_number >= 0
            assert event.column_number >= 0
            assert event.file_position >= 0

        # Line numbers should increase
        line_numbers = [e.line_number for e in events if e.line_number > 0]
        assert line_numbers == sorted(line_numbers)

    def test_nested_xml(self, nested_xml):
        """Test parsing deeply nested XML."""
        parser = StreamingParser()
        events = list(parser.parse(nested_xml))

        # Should handle deep nesting
        start_events = [e for e in events if e.type == EventType.START_ELEMENT]
        assert len(start_events) >= 6  # root + 5 levels

        # Check that all elements are properly closed
        end_events = [e for e in events if e.type == EventType.END_ELEMENT]
        assert len(start_events) == len(end_events)

    def test_malformed_xml(self, malformed_xml):
        """Test handling of malformed XML."""
        parser = StreamingParser()

        # Should raise SAXException
        with pytest.raises(Exception):  # SAXException or subclass
            list(parser.parse(malformed_xml))

    def test_get_state(self, simple_xml):
        """Test getting parser state."""
        parser = StreamingParser()
        state = parser.get_state(simple_xml)

        assert isinstance(state, ParserState)
        assert state.elements_seen > 0
        assert state.bytes_processed > 0

    def test_validate_structure_valid(self, simple_xml):
        """Test structure validation on valid XML."""
        parser = StreamingParser()
        valid, errors = parser.validate_structure(simple_xml)

        assert valid is True
        assert len(errors) == 0

    def test_validate_structure_invalid(self, malformed_xml):
        """Test structure validation on invalid XML."""
        parser = StreamingParser()
        valid, errors = parser.validate_structure(malformed_xml)

        assert valid is False
        assert len(errors) > 0

    def test_nonexistent_file(self):
        """Test handling of nonexistent file."""
        parser = StreamingParser()

        with pytest.raises(FileNotFoundError):
            list(parser.parse("nonexistent.xml"))


class TestUtilityFunctions:
    """Test utility functions."""

    def test_count_elements(self, simple_xml):
        """Test element counting."""
        count = count_elements(simple_xml)

        # root + 2*item + 2*name + 2*value = 7
        assert count == 7

    def test_extract_element_names(self, simple_xml):
        """Test element name extraction."""
        names = extract_element_names(simple_xml)

        assert isinstance(names, set)
        assert "root" in names
        assert "item" in names
        assert "name" in names
        assert "value" in names
        assert len(names) == 4


class TestParserEvent:
    """Test ParserEvent class."""

    def test_event_creation(self):
        """Test creating parser events."""
        event = ParserEvent(
            type=EventType.START_ELEMENT,
            name="test",
            attributes={"id": "1"},
            line_number=10,
            column_number=5,
        )

        assert event.type == EventType.START_ELEMENT
        assert event.name == "test"
        assert event.attributes["id"] == "1"
        assert event.line_number == 10
        assert event.column_number == 5

    def test_event_repr(self):
        """Test event string representation."""
        event = ParserEvent(
            type=EventType.START_ELEMENT,
            name="test",
            line_number=10,
            column_number=5,
        )

        repr_str = repr(event)
        assert "test" in repr_str
        assert "10" in repr_str
        assert "5" in repr_str


class TestParserState:
    """Test ParserState class."""

    def test_state_creation(self):
        """Test creating parser state."""
        state = ParserState()

        assert state.file_position == 0
        assert state.line_number == 0
        assert state.depth == 0
        assert len(state.element_stack) == 0

    def test_state_clone(self):
        """Test cloning parser state."""
        state = ParserState(
            file_position=100,
            line_number=10,
            element_stack=["root", "item"],
        )

        cloned = state.clone()

        assert cloned.file_position == state.file_position
        assert cloned.line_number == state.line_number
        assert cloned.element_stack == state.element_stack
        assert cloned.element_stack is not state.element_stack  # Deep copy


class TestLargeFile:
    """Test with larger files."""

    def test_parse_10mb_xml(self, tmp_path):
        """Test parsing 10MB XML file."""
        xml_file = tmp_path / "test_10mb.xml"

        # Generate 10MB XML
        with open(xml_file, "w") as f:
            f.write('<?xml version="1.0"?>\n')
            f.write("<root>\n")

            # Write ~10MB of data
            target_size = 10 * 1024 * 1024
            current_size = 0
            index = 0

            while current_size < target_size:
                line = f'  <item id="{index}">Data {index}</item>\n'
                f.write(line)
                current_size += len(line)
                index += 1

            f.write("</root>\n")

        # Parse it
        parser = StreamingParser()
        events = list(parser.parse(xml_file))

        # Should parse successfully
        assert len(events) > 0

        # Verify structure
        event_types = [e.type for e in events]
        assert EventType.START_DOCUMENT in event_types
        assert EventType.END_DOCUMENT in event_types

        # Count elements
        start_count = len([e for e in events if e.type == EventType.START_ELEMENT])
        end_count = len([e for e in events if e.type == EventType.END_ELEMENT])
        assert start_count == end_count

        # Clean up
        xml_file.unlink()
