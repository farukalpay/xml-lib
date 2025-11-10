"""XML parsing utilities with streaming support."""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from lxml import etree


def parse_xml(xml_path: Path, remove_blank_text: bool = True) -> etree._Element:
    """Parse XML file with security settings.

    Args:
        xml_path: Path to XML file
        remove_blank_text: Remove blank text nodes

    Returns:
        Parsed XML element tree

    Raises:
        etree.XMLSyntaxError: If XML is malformed
    """
    parser = etree.XMLParser(
        remove_blank_text=remove_blank_text,
        resolve_entities=False,  # Security: disable entity resolution
        no_network=True,  # Security: disable network access
        remove_comments=False,
        dtd_validation=False,
        load_dtd=False,
    )

    tree = etree.parse(str(xml_path), parser)
    return tree.getroot()


def stream_parse(
    xml_path: Path,
    tag: str | None = None,
    events: tuple[str, ...] = ("end",),
) -> Iterator[tuple[str, Any]]:
    """Stream parse large XML files using iterparse.

    Args:
        xml_path: Path to XML file
        tag: Optional tag to filter events
        events: Events to capture (start, end, start-ns, end-ns)

    Yields:
        Tuples of (event, element)

    Example:
        >>> for event, elem in stream_parse(path, tag="document"):
        ...     process(elem)
        ...     elem.clear()  # Free memory
    """
    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        remove_comments=False,
        dtd_validation=False,
        load_dtd=False,
    )

    context = etree.iterparse(
        str(xml_path),
        events=events,
        tag=tag,
        parser=parser,
    )

    for event, elem in context:
        yield event, elem


def serialize_xml(
    element: etree._Element,
    output_path: Path | None = None,
    pretty_print: bool = True,
    xml_declaration: bool = True,
    encoding: str = "utf-8",
) -> bytes | None:
    """Serialize XML element to file or bytes.

    Args:
        element: XML element to serialize
        output_path: Optional output file path
        pretty_print: Format with indentation
        xml_declaration: Include XML declaration
        encoding: Character encoding

    Returns:
        Serialized bytes if output_path is None, otherwise None
    """
    result = etree.tostring(
        element,
        pretty_print=pretty_print,
        xml_declaration=xml_declaration,
        encoding=encoding,
    )

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(result)
        return None

    return result


def xpath_query(element: etree._Element, query: str) -> list[Any]:
    """Execute XPath query on element.

    Args:
        element: XML element
        query: XPath query string

    Returns:
        List of matching elements/values
    """
    return element.xpath(query)


def get_element_id(element: etree._Element) -> str | None:
    """Get ID attribute from element.

    Args:
        element: XML element

    Returns:
        ID value or None if not present
    """
    return element.get("id")


def get_element_timestamp(element: etree._Element) -> str | None:
    """Get timestamp attribute from element.

    Args:
        element: XML element

    Returns:
        Timestamp value or None if not present
    """
    return element.get("timestamp")


def get_element_checksum(element: etree._Element) -> str | None:
    """Get checksum attribute from element.

    Args:
        element: XML element

    Returns:
        Checksum value or None if not present
    """
    return element.get("checksum")
