"""Parser for PPTX build plans from XML."""

from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from xml_lib.utils.xml_utils import parse_xml


@dataclass
class SlideSpec:
    """Specification for a single slide."""

    title: str
    content: list[str] = field(default_factory=list)
    layout: str = "title_and_content"
    notes: str = ""


@dataclass
class BuildPlan:
    """PPTX build plan."""

    title: str
    slides: list[SlideSpec] = field(default_factory=list)
    template: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


class PPTXParser:
    """Parser for PPTX build plans."""

    def parse(self, xml_path: Path) -> BuildPlan:
        """Parse PPTX build plan from XML.

        Args:
            xml_path: Path to XML build plan

        Returns:
            BuildPlan
        """
        root = parse_xml(xml_path)

        # Extract title
        title_elem = root.find(".//title")
        title = title_elem.text if title_elem is not None else "Untitled"

        # Extract slides
        slides = []
        for slide_elem in root.findall(".//slide"):
            slide_title = slide_elem.get("title", "")
            content = [item.text for item in slide_elem.findall(".//item") if item.text]
            layout = slide_elem.get("layout", "title_and_content")
            notes_elem = slide_elem.find(".//notes")
            notes = notes_elem.text if notes_elem is not None else ""

            slides.append(
                SlideSpec(
                    title=slide_title,
                    content=content,
                    layout=layout,
                    notes=notes,
                )
            )

        return BuildPlan(title=title, slides=slides)
