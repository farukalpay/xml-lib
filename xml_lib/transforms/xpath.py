"""XPath query utilities."""

from pathlib import Path
from typing import Any

from lxml import etree

from xml_lib.utils.xml_utils import parse_xml


class XPathEvaluator:
    """XPath query evaluator."""

    def __init__(self, namespaces: dict[str, str] | None = None):
        """Initialize XPath evaluator.

        Args:
            namespaces: XML namespace mappings
        """
        self.namespaces = namespaces or {}

    def query(self, xml_path: Path, xpath: str) -> list[Any]:
        """Execute XPath query on XML document.

        Args:
            xml_path: Path to XML file
            xpath: XPath query string

        Returns:
            List of matching elements/values
        """
        root = parse_xml(xml_path)
        return root.xpath(xpath, namespaces=self.namespaces)

    def query_element(self, element: etree._Element, xpath: str) -> list[Any]:
        """Execute XPath query on element.

        Args:
            element: XML element
            xpath: XPath query string

        Returns:
            List of matching elements/values
        """
        return element.xpath(xpath, namespaces=self.namespaces)
