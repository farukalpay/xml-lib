"""Intermediate Representation for XML-to-PHP conversion."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from lxml import etree


class ContentType(Enum):
    """Types of content elements."""
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    CODE_BLOCK = "code_block"
    FIGURE = "figure"
    LINK = "link"
    CITATION = "citation"
    SECTION = "section"
    METADATA = "metadata"


@dataclass
class Link:
    """Represents a link (internal or external)."""
    href: str
    text: str
    is_external: bool
    title: Optional[str] = None


@dataclass
class Figure:
    """Represents an image or figure."""
    src: str
    alt: str
    caption: Optional[str] = None
    width: Optional[str] = None
    height: Optional[str] = None


@dataclass
class TableCell:
    """Represents a table cell."""
    content: str
    is_header: bool = False
    colspan: int = 1
    rowspan: int = 1


@dataclass
class TableRow:
    """Represents a table row."""
    cells: List[TableCell] = field(default_factory=list)


@dataclass
class Table:
    """Represents a table."""
    headers: List[TableRow] = field(default_factory=list)
    rows: List[TableRow] = field(default_factory=list)
    caption: Optional[str] = None


@dataclass
class CodeBlock:
    """Represents a code block."""
    code: str
    language: Optional[str] = None
    line_numbers: bool = False


@dataclass
class ListItem:
    """Represents a list item."""
    content: str
    children: List['ListItem'] = field(default_factory=list)


@dataclass
class List:
    """Represents a list (ordered or unordered)."""
    items: List[ListItem] = field(default_factory=list)
    ordered: bool = False


@dataclass
class Heading:
    """Represents a heading."""
    text: str
    level: int  # 1-6
    id: Optional[str] = None


@dataclass
class Paragraph:
    """Represents a paragraph."""
    content: str
    style: Optional[str] = None


@dataclass
class Citation:
    """Represents a citation or footnote."""
    id: str
    content: str
    ref_count: int = 0


@dataclass
class Section:
    """Represents a document section."""
    title: Optional[str] = None
    id: Optional[str] = None
    content: List['ContentElement'] = field(default_factory=list)


@dataclass
class Metadata:
    """Document metadata."""
    title: str = "Untitled Document"
    description: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    custom: Dict[str, str] = field(default_factory=dict)


ContentElement = Union[Heading, Paragraph, List, Table, CodeBlock, Figure, Link, Citation, Section]


@dataclass
class IntermediateRepresentation:
    """Typed intermediate representation of XML document."""

    metadata: Metadata = field(default_factory=Metadata)
    content: List[ContentElement] = field(default_factory=list)
    citations: Dict[str, Citation] = field(default_factory=dict)
    internal_links: Dict[str, str] = field(default_factory=dict)  # id -> href


class IRBuilder:
    """Builds intermediate representation from XML."""

    def __init__(self, strict: bool = False):
        """Initialize IR builder.

        Args:
            strict: If True, raise errors on malformed content
        """
        self.strict = strict
        self.id_counter = 0
        self.seen_ids: set = set()

    def build(self, root: etree._Element) -> IntermediateRepresentation:
        """Build IR from XML element tree.

        Args:
            root: Root XML element

        Returns:
            IntermediateRepresentation instance
        """
        ir = IntermediateRepresentation()

        # Extract metadata
        ir.metadata = self._extract_metadata(root)

        # Process content
        ir.content = self._process_element(root, ir)

        return ir

    def _extract_metadata(self, root: etree._Element) -> Metadata:
        """Extract metadata from XML.

        Args:
            root: Root XML element

        Returns:
            Metadata instance
        """
        meta = Metadata()

        # Look for <meta> element
        meta_elem = root.find('.//meta')
        if meta_elem is not None:
            title_elem = meta_elem.find('title')
            if title_elem is not None and title_elem.text:
                meta.title = title_elem.text.strip()

            desc_elem = meta_elem.find('description')
            if desc_elem is not None and desc_elem.text:
                meta.description = desc_elem.text.strip()

            author_elem = meta_elem.find('author')
            if author_elem is not None and author_elem.text:
                meta.author = author_elem.text.strip()

            date_elem = meta_elem.find('date')
            if date_elem is not None and date_elem.text:
                meta.date = date_elem.text.strip()

            # Extract keywords
            for kw_elem in meta_elem.findall('keyword'):
                if kw_elem.text:
                    meta.keywords.append(kw_elem.text.strip())

            # Extract custom metadata
            for child in meta_elem:
                if child.tag not in ['title', 'description', 'author', 'date', 'keyword']:
                    if child.text:
                        meta.custom[child.tag] = child.text.strip()

        # Fallback to document title or root element attributes
        if meta.title == "Untitled Document":
            # Try to find first heading or title
            for elem in root.iter():
                if elem.tag in ['title', 'h1', 'heading'] and elem.text:
                    meta.title = elem.text.strip()
                    break

        return meta

    def _process_element(
        self,
        elem: etree._Element,
        ir: IntermediateRepresentation,
        parent_context: Optional[str] = None
    ) -> List[ContentElement]:
        """Process XML element and convert to content elements.

        Args:
            elem: XML element
            ir: IR being built (for citations, links)
            parent_context: Parent element context

        Returns:
            List of content elements
        """
        content: List[ContentElement] = []

        for child in elem:
            tag = child.tag.lower()

            # Skip metadata elements
            if tag == 'meta':
                continue

            # Headings
            if tag in ['heading', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                heading = self._extract_heading(child)
                if heading:
                    content.append(heading)

            # Paragraphs and notes
            elif tag in ['paragraph', 'p', 'note', 'description', 'summary', 'payload']:
                para = self._extract_paragraph(child)
                if para:
                    content.append(para)

            # Lists
            elif tag in ['list', 'ul', 'ol', 'items']:
                lst = self._extract_list(child)
                if lst:
                    content.append(lst)

            # Tables
            elif tag in ['table', 'matrix', 'iteration-matrix']:
                table = self._extract_table(child)
                if table:
                    content.append(table)

            # Code blocks
            elif tag in ['code', 'pre', 'script']:
                code = self._extract_code(child)
                if code:
                    content.append(code)

            # Figures/Images
            elif tag in ['figure', 'img', 'image']:
                figure = self._extract_figure(child)
                if figure:
                    content.append(figure)

            # Sections
            elif tag in ['section', 'phase', 'phases', 'lifecycle', 'layer', 'appendix', 'appendices']:
                section = self._extract_section(child, ir)
                if section:
                    content.append(section)

            # Citations and references
            elif tag in ['citation', 'ref', 'footnote']:
                citation = self._extract_citation(child, ir)
                if citation:
                    content.append(citation)

            # Nested content - recurse
            elif len(child) > 0:
                nested = self._process_element(child, ir, tag)
                content.extend(nested)

            # Text content in generic elements
            elif child.text and child.text.strip():
                para = Paragraph(content=child.text.strip())
                content.append(para)

        return content

    def _extract_heading(self, elem: etree._Element) -> Optional[Heading]:
        """Extract heading from element."""
        text = self._get_text_content(elem)
        if not text:
            return None

        # Determine level
        level = 2  # Default
        if elem.tag == 'h1':
            level = 1
        elif elem.tag == 'h2':
            level = 2
        elif elem.tag == 'h3':
            level = 3
        elif elem.tag == 'h4':
            level = 4
        elif elem.tag == 'h5':
            level = 5
        elif elem.tag == 'h6':
            level = 6
        elif 'level' in elem.attrib:
            try:
                level = int(elem.attrib['level'])
                level = max(1, min(6, level))
            except ValueError:
                pass

        # Get or generate ID
        elem_id = elem.get('id') or self._slugify(text)
        elem_id = self._ensure_unique_id(elem_id)

        return Heading(text=text, level=level, id=elem_id)

    def _extract_paragraph(self, elem: etree._Element) -> Optional[Paragraph]:
        """Extract paragraph from element."""
        text = self._get_text_content(elem)
        if not text:
            return None

        style = elem.get('style')
        return Paragraph(content=text, style=style)

    def _extract_list(self, elem: etree._Element) -> Optional[List]:
        """Extract list from element."""
        items = []
        ordered = elem.tag.lower() in ['ol'] or elem.get('type') == 'ordered'

        for item in elem:
            if item.tag.lower() in ['item', 'li', 'iteration', 'step', 'value', 'rule', 'control', 'layer', 'module', 'artifact']:
                text = self._get_text_content(item)
                if text:
                    list_item = ListItem(content=text)
                    # Check for nested lists
                    for nested in item:
                        if nested.tag.lower() in ['list', 'ul', 'ol', 'items', 'steps']:
                            nested_list = self._extract_list(nested)
                            if nested_list:
                                # Convert nested list items
                                for nested_item in nested_list.items:
                                    list_item.children.append(nested_item)
                    items.append(list_item)

        if not items:
            return None

        return List(items=items, ordered=ordered)

    def _extract_table(self, elem: etree._Element) -> Optional[Table]:
        """Extract table from element."""
        headers = []
        rows = []
        caption = None

        # Look for caption
        caption_elem = elem.find('.//caption')
        if caption_elem is not None and caption_elem.text:
            caption = caption_elem.text.strip()

        # Look for thead
        thead = elem.find('.//thead')
        if thead is not None:
            for tr in thead.findall('.//tr'):
                row = TableRow()
                for cell in tr:
                    if cell.tag.lower() in ['th', 'td']:
                        text = self._get_text_content(cell)
                        row.cells.append(TableCell(content=text, is_header=True))
                if row.cells:
                    headers.append(row)

        # Look for tbody or direct rows
        tbody = elem.find('.//tbody')
        row_container = tbody if tbody is not None else elem

        for tr in row_container.findall('.//tr'):
            row = TableRow()
            for cell in tr:
                if cell.tag.lower() in ['td', 'th']:
                    text = self._get_text_content(cell)
                    is_header = cell.tag.lower() == 'th'
                    row.cells.append(TableCell(content=text, is_header=is_header))
            if row.cells:
                rows.append(row)

        # If no explicit table structure, try to extract from other elements
        if not headers and not rows:
            # Try to extract from iteration-matrix or similar structures
            for child in elem:
                if child.tag.lower() in ['axis', 'row']:
                    row = TableRow()
                    name = child.get('name', '')
                    if name:
                        row.cells.append(TableCell(content=name, is_header=True))
                    for value in child:
                        text = self._get_text_content(value)
                        if text:
                            row.cells.append(TableCell(content=text))
                    if row.cells:
                        rows.append(row)

        if not headers and not rows:
            return None

        return Table(headers=headers, rows=rows, caption=caption)

    def _extract_code(self, elem: etree._Element) -> Optional[CodeBlock]:
        """Extract code block from element."""
        code = self._get_text_content(elem, preserve_whitespace=True)
        if not code:
            return None

        language = elem.get('language') or elem.get('lang')
        line_numbers = elem.get('line-numbers') == 'true'

        return CodeBlock(code=code, language=language, line_numbers=line_numbers)

    def _extract_figure(self, elem: etree._Element) -> Optional[Figure]:
        """Extract figure/image from element."""
        src = elem.get('src') or elem.get('path', '')
        if not src:
            return None

        alt = elem.get('alt', '')
        caption = None

        caption_elem = elem.find('.//caption')
        if caption_elem is not None and caption_elem.text:
            caption = caption_elem.text.strip()

        width = elem.get('width')
        height = elem.get('height')

        return Figure(src=src, alt=alt, caption=caption, width=width, height=height)

    def _extract_section(
        self,
        elem: etree._Element,
        ir: IntermediateRepresentation
    ) -> Optional[Section]:
        """Extract section from element."""
        title = elem.get('name') or elem.get('title')
        section_id = elem.get('id')

        # Try to find title in child elements
        if not title:
            title_elem = elem.find('.//title')
            if title_elem is not None and title_elem.text:
                title = title_elem.text.strip()

        # Process content
        content = self._process_element(elem, ir, elem.tag)

        # Ensure ID is unique (even if provided in XML)
        if section_id:
            section_id = self._ensure_unique_id(section_id)
        elif title:
            section_id = self._slugify(title)
            section_id = self._ensure_unique_id(section_id)

        return Section(title=title, id=section_id, content=content)

    def _extract_citation(
        self,
        elem: etree._Element,
        ir: IntermediateRepresentation
    ) -> Optional[Citation]:
        """Extract citation from element."""
        citation_id = elem.get('id') or f"cite-{len(ir.citations) + 1}"
        content = self._get_text_content(elem)

        if not content:
            return None

        citation = Citation(id=citation_id, content=content)
        ir.citations[citation_id] = citation

        return citation

    def _get_text_content(
        self,
        elem: etree._Element,
        preserve_whitespace: bool = False
    ) -> str:
        """Get text content from element and its children.

        Args:
            elem: XML element
            preserve_whitespace: If True, preserve whitespace

        Returns:
            Text content
        """
        parts = []

        if elem.text:
            parts.append(elem.text)

        for child in elem:
            child_text = self._get_text_content(child, preserve_whitespace)
            if child_text:
                parts.append(child_text)
            if child.tail:
                parts.append(child.tail)

        text = ''.join(parts)

        if preserve_whitespace:
            return text
        else:
            # Normalize whitespace
            return ' '.join(text.split())

    def _slugify(self, text: str) -> str:
        """Convert text to URL-safe slug.

        Args:
            text: Input text

        Returns:
            Slugified text
        """
        # Convert to lowercase
        slug = text.lower()
        # Replace spaces and special chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        # Trim hyphens
        slug = slug.strip('-')
        # Limit length
        slug = slug[:50]
        return slug or f"section-{self.id_counter}"

    def _ensure_unique_id(self, base_id: str) -> str:
        """Ensure ID is unique.

        Args:
            base_id: Base ID string

        Returns:
            Unique ID
        """
        if base_id not in self.seen_ids:
            self.seen_ids.add(base_id)
            return base_id

        # Append counter
        counter = 1
        while f"{base_id}-{counter}" in self.seen_ids:
            counter += 1

        unique_id = f"{base_id}-{counter}"
        self.seen_ids.add(unique_id)
        return unique_id
