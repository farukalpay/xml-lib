"""PHP code generator with template rendering and proper escaping."""

import json
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .ir import (
    Citation,
    CodeBlock,
    ContentElement,
    Figure,
    Heading,
    IntermediateRepresentation,
    IRList,
    ListItem,
    Paragraph,
    Section,
    Table,
)


@dataclass
class GeneratorConfig:
    """Configuration for PHP generator."""

    template: str = "default"  # 'default' or 'minimal'
    title: str | None = None
    favicon: str | None = None
    assets_dir: str = "assets"
    no_toc: bool = False
    no_css: bool = False
    css_path: str | None = None


class PHPGenerator:
    """Generates production-ready PHP from intermediate representation.

    Features:
    - Context-aware escaping (HTML, attributes, URLs)
    - Clean separation of layout and content
    - PSR-12 compliant PHP
    - Semantic HTML5
    - Accessibility landmarks
    - Responsive layout
    """

    def __init__(self, templates_dir: Path, config: GeneratorConfig | None = None):
        """Initialize PHP generator.

        Args:
            templates_dir: Directory containing Jinja2 templates
            config: Generator configuration
        """
        self.templates_dir = templates_dir
        self.config = config or GeneratorConfig()

        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self.env.filters["tojson"] = self._json_encode

    def generate(
        self, ir: IntermediateRepresentation, output_basename: str = "page"
    ) -> dict[str, str]:
        """Generate PHP files from IR.

        Args:
            ir: Intermediate representation
            output_basename: Base name for output file (without extension)

        Returns:
            Dictionary mapping file paths to content
        """
        files = {}

        # Generate main PHP page
        php_content = self._generate_page(ir)
        files[f"{output_basename}.php"] = php_content

        # Generate CSS if not disabled
        if not self.config.no_css:
            css_content = self._generate_css()
            css_path = f"{self.config.assets_dir}/style.css"
            files[css_path] = css_content

        return files

    def _generate_page(self, ir: IntermediateRepresentation) -> str:
        """Generate main PHP page.

        Args:
            ir: Intermediate representation

        Returns:
            PHP page content
        """
        # Use title from config or metadata
        title = self.config.title or ir.metadata.title

        # Build table of contents
        toc_items = []
        if not self.config.no_toc:
            toc_items = self._build_toc(ir.content)

        # Render content
        content_html = self._render_content(ir.content)

        # Prepare template variables
        template_vars = {
            "title": title,
            "description": ir.metadata.description,
            "author": ir.metadata.author,
            "date": ir.metadata.date,
            "keywords": ir.metadata.keywords,
            "favicon": self.config.favicon,
            "no_css": self.config.no_css,
            "css_path": self.config.css_path or f"{self.config.assets_dir}/style.css",
            "no_toc": self.config.no_toc,
            "toc_items": toc_items,
            "content": content_html,
            "citations": {k: v.content for k, v in ir.citations.items()},
        }

        # Select template
        template_name = (
            "php/minimal_page.php.j2" if self.config.template == "minimal" else "php/page.php.j2"
        )

        # Render template
        template = self.env.get_template(template_name)

        # First, render the functions.php template
        functions_template = self.env.get_template("php/functions.php.j2")
        functions_php = functions_template.render()

        # Render the page
        page_html = template.render(**template_vars)

        # Combine functions and page
        return f"{functions_php}\n?>\n{page_html}"

    def _generate_css(self) -> str:
        """Generate CSS file.

        Returns:
            CSS content
        """
        template = self.env.get_template("php/style.css.j2")
        return template.render()

    def _build_toc(self, content: list[ContentElement]) -> list[dict[str, str]]:
        """Build table of contents from content.

        Args:
            content: List of content elements

        Returns:
            List of TOC items with id and text
        """
        toc = []

        for element in content:
            if isinstance(element, Heading):
                if element.level <= 3:  # Only include h1-h3 in TOC
                    toc.append(
                        {
                            "id": element.id,
                            "text": element.text,
                            "level": element.level,
                        }
                    )
            elif isinstance(element, Section):
                if element.title and element.id:
                    toc.append(
                        {
                            "id": element.id,
                            "text": element.title,
                            "level": 2,
                        }
                    )
                # Recurse into section content
                section_toc = self._build_toc(element.content)
                toc.extend(section_toc)

        return toc

    def _render_content(self, content: list[ContentElement]) -> str:
        """Render content elements to PHP/HTML.

        Args:
            content: List of content elements

        Returns:
            Rendered PHP/HTML
        """
        html_parts = []

        for element in content:
            if isinstance(element, Heading):
                html_parts.append(self._render_heading(element))
            elif isinstance(element, Paragraph):
                html_parts.append(self._render_paragraph(element))
            elif isinstance(element, IRList):
                html_parts.append(self._render_list(element))
            elif isinstance(element, Table):
                html_parts.append(self._render_table(element))
            elif isinstance(element, CodeBlock):
                html_parts.append(self._render_code(element))
            elif isinstance(element, Figure):
                html_parts.append(self._render_figure(element))
            elif isinstance(element, Section):
                html_parts.append(self._render_section(element))
            elif isinstance(element, Citation):
                html_parts.append(self._render_citation(element))

        return "\n".join(html_parts)

    def _render_heading(self, heading: Heading) -> str:
        """Render heading to HTML.

        Args:
            heading: Heading element

        Returns:
            HTML string
        """
        level = heading.level
        id_attr = (
            f' id="<?php echo escape_attr({self._json_encode(heading.id)}); ?>"'
            if heading.id
            else ""
        )
        text = f"<?php echo escape_html({self._json_encode(heading.text)}); ?>"

        return f"                <h{level}{id_attr}>{text}</h{level}>"

    def _render_paragraph(self, para: Paragraph) -> str:
        """Render paragraph to HTML.

        Args:
            para: Paragraph element

        Returns:
            HTML string
        """
        style_attr = f' class="{para.style}"' if para.style else ""
        text = f"<?php echo escape_html({self._json_encode(para.content)}); ?>"

        return f"                <p{style_attr}>{text}</p>"

    def _render_list(self, lst: IRList) -> str:
        """Render list to HTML.

        Args:
            lst: List element

        Returns:
            HTML string
        """
        tag = "ol" if lst.ordered else "ul"
        items_html = []

        for item in lst.items:
            items_html.append(self._render_list_item(item, lst.ordered))

        items = "\n".join(items_html)
        return f"                <{tag}>\n{items}\n                </{tag}>"

    def _render_list_item(self, item: ListItem, ordered: bool = False) -> str:
        """Render list item to HTML.

        Args:
            item: List item
            ordered: Whether parent list is ordered

        Returns:
            HTML string
        """
        text = f"<?php echo escape_html({self._json_encode(item.content)}); ?>"
        html = f"                    <li>{text}"

        # Render nested items
        if item.children:
            tag = "ol" if ordered else "ul"
            nested_html = []
            for child in item.children:
                nested_html.append(self._render_list_item(child, ordered))
            nested = "\n".join(nested_html)
            html += f"\n                        <{tag}>\n{nested}\n                        </{tag}>"

        html += "</li>"
        return html

    def _render_table(self, table: Table) -> str:
        """Render table to HTML.

        Args:
            table: Table element

        Returns:
            HTML string
        """
        # Build arrays for PHP function
        headers = []
        for row in table.headers:
            header_row = [cell.content for cell in row.cells]
            headers.append(header_row)

        rows = []
        for row in table.rows:
            data_row = [cell.content for cell in row.cells]
            rows.append(data_row)

        caption = self._json_encode(table.caption) if table.caption else "null"
        headers_json = self._json_encode(headers)
        rows_json = self._json_encode(rows)

        return (
            f"                <?php echo render_table({headers_json}, {rows_json}, {caption}); ?>"
        )

    def _render_code(self, code: CodeBlock) -> str:
        """Render code block to HTML.

        Args:
            code: Code block element

        Returns:
            HTML string
        """
        lang_class = f' class="language-{code.language}"' if code.language else ""
        code_text = f"<?php echo escape_html({self._json_encode(code.code)}); ?>"

        return f"                <pre><code{lang_class}>{code_text}</code></pre>"

    def _render_figure(self, figure: Figure) -> str:
        """Render figure to HTML.

        Args:
            figure: Figure element

        Returns:
            HTML string
        """
        src = self._json_encode(figure.src)
        alt = self._json_encode(figure.alt)
        caption = self._json_encode(figure.caption) if figure.caption else "null"
        width = self._json_encode(figure.width) if figure.width else "null"
        height = self._json_encode(figure.height) if figure.height else "null"

        return f"                <?php echo render_figure({src}, {alt}, {caption}, {width}, {height}); ?>"

    def _render_section(self, section: Section) -> str:
        """Render section to HTML.

        Args:
            section: Section element

        Returns:
            HTML string
        """
        id_attr = (
            f' id="<?php echo escape_attr({self._json_encode(section.id)}); ?>"'
            if section.id
            else ""
        )
        html = f"                <section{id_attr}>"

        if section.title:
            title = f"<?php echo escape_html({self._json_encode(section.title)}); ?>"
            html += f"\n                    <h2>{title}</h2>"

        # Render section content
        content_html = self._render_content(section.content)
        if content_html:
            html += f"\n{content_html}"

        html += "\n                </section>"
        return html

    def _render_citation(self, citation: Citation) -> str:
        """Render citation reference to HTML.

        Args:
            citation: Citation element

        Returns:
            HTML string
        """
        id_val = self._json_encode(citation.id)
        return f'                <sup><a href="#<?php echo escape_attr({id_val}); ?>" id="ref-<?php echo escape_attr({id_val}); ?>">[{citation.ref_count}]</a></sup>'

    def _json_encode(self, value) -> str:
        """Encode value as JSON for safe embedding in PHP.

        Args:
            value: Value to encode

        Returns:
            JSON string
        """
        return json.dumps(value, ensure_ascii=False)
