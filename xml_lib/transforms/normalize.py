"""XML normalization for diff-able output."""

from pathlib import Path

from lxml import etree

from xml_lib.utils.xml_utils import parse_xml


class Normalizer:
    """XML normalizer for canonical formatting."""

    def normalize(
        self, xml_path: Path, output_path: Path | None = None, sort_attributes: bool = True
    ) -> bytes:
        """Normalize XML to canonical form.

        Args:
            xml_path: Input XML file
            output_path: Optional output file
            sort_attributes: Sort attributes alphabetically

        Returns:
            Normalized XML bytes
        """
        root = parse_xml(xml_path)

        # Sort attributes if requested
        if sort_attributes:
            self._sort_attributes(root)

        # Sort child elements by tag name
        self._sort_children(root)

        # Serialize canonically
        result = etree.tostring(
            root,
            pretty_print=True,
            xml_declaration=True,
            encoding="utf-8",
            exclusive=False,
        )

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(result)

        return result

    def _sort_attributes(self, element: etree._Element) -> None:
        """Sort attributes of element and descendants."""
        # Sort this element's attributes
        if element.attrib:
            sorted_attribs = dict(sorted(element.attrib.items()))
            element.attrib.clear()
            element.attrib.update(sorted_attribs)

        # Recurse
        for child in element:
            self._sort_attributes(child)

    def _sort_children(self, element: etree._Element) -> None:
        """Sort child elements by tag name."""
        # Sort children
        children = list(element)
        if children:
            children.sort(key=lambda e: (e.tag, e.get("id", "")))
            element[:] = children

        # Recurse
        for child in element:
            self._sort_children(child)
