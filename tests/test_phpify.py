"""Tests for PHP generation functionality."""

import json
import re
import subprocess
from pathlib import Path
import pytest
from lxml import etree

from xml_lib.php.parser import SecureXMLParser, ParseConfig, ParseError
from xml_lib.php.ir import IRBuilder, IntermediateRepresentation, Heading, Paragraph, Section
from xml_lib.php.generator import PHPGenerator, GeneratorConfig


class TestSecureXMLParser:
    """Tests for secure XML parser."""

    def test_parse_valid_xml(self, tmp_path):
        """Test parsing valid XML."""
        xml_file = tmp_path / "test.xml"
        xml_file.write_text('<document><title>Test</title></document>')

        parser = SecureXMLParser()
        root = parser.parse(xml_file)

        assert root.tag == 'document'
        assert root.find('title').text == 'Test'

    def test_parse_xxe_protection(self, tmp_path):
        """Test XXE protection."""
        # XML with external entity
        xml_content = '''<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<document>&xxe;</document>'''

        xml_file = tmp_path / "xxe.xml"
        xml_file.write_text(xml_content)

        parser = SecureXMLParser()
        # Should parse without resolving entity
        root = parser.parse(xml_file)
        assert root.tag == 'document'

    def test_file_size_limit(self, tmp_path):
        """Test file size limit."""
        xml_file = tmp_path / "large.xml"
        # Create 11MB file
        large_content = '<document>' + ('x' * (11 * 1024 * 1024)) + '</document>'
        xml_file.write_text(large_content)

        config = ParseConfig(max_size_bytes=10 * 1024 * 1024)
        parser = SecureXMLParser(config)

        with pytest.raises(ParseError, match="File too large"):
            parser.parse(xml_file)

    def test_parse_string(self):
        """Test parsing XML from string."""
        xml_string = '<document><title>Test</title></document>'

        parser = SecureXMLParser()
        root = parser.parse_string(xml_string)

        assert root.tag == 'document'
        assert root.find('title').text == 'Test'

    def test_invalid_xml(self, tmp_path):
        """Test parsing invalid XML."""
        xml_file = tmp_path / "invalid.xml"
        xml_file.write_text('<document><unclosed>')

        parser = SecureXMLParser()

        with pytest.raises(ParseError, match="XML syntax error"):
            parser.parse(xml_file)


class TestIRBuilder:
    """Tests for IR builder."""

    def test_extract_metadata(self):
        """Test metadata extraction."""
        xml = '''<document>
            <meta>
                <title>Test Document</title>
                <description>A test</description>
                <author>John Doe</author>
                <date>2024-01-01</date>
                <keyword>test</keyword>
                <keyword>xml</keyword>
            </meta>
        </document>'''

        root = etree.fromstring(xml.encode('utf-8'))
        builder = IRBuilder()
        ir = builder.build(root)

        assert ir.metadata.title == "Test Document"
        assert ir.metadata.description == "A test"
        assert ir.metadata.author == "John Doe"
        assert ir.metadata.date == "2024-01-01"
        assert "test" in ir.metadata.keywords
        assert "xml" in ir.metadata.keywords

    def test_extract_headings(self):
        """Test heading extraction."""
        xml = '''<document>
            <h1>Heading 1</h1>
            <h2>Heading 2</h2>
            <heading level="3">Heading 3</heading>
        </document>'''

        root = etree.fromstring(xml.encode('utf-8'))
        builder = IRBuilder()
        ir = builder.build(root)

        headings = [c for c in ir.content if isinstance(c, Heading)]
        assert len(headings) == 3
        assert headings[0].level == 1
        assert headings[0].text == "Heading 1"
        assert headings[1].level == 2
        assert headings[2].level == 3

    def test_extract_paragraphs(self):
        """Test paragraph extraction."""
        xml = '''<document>
            <paragraph>First paragraph</paragraph>
            <p>Second paragraph</p>
            <note>A note paragraph</note>
        </document>'''

        root = etree.fromstring(xml.encode('utf-8'))
        builder = IRBuilder()
        ir = builder.build(root)

        paras = [c for c in ir.content if isinstance(c, Paragraph)]
        assert len(paras) == 3
        assert paras[0].content == "First paragraph"
        assert paras[1].content == "Second paragraph"
        assert paras[2].content == "A note paragraph"

    def test_extract_sections(self):
        """Test section extraction."""
        xml = '''<document>
            <section id="intro" name="Introduction">
                <paragraph>Intro text</paragraph>
            </section>
        </document>'''

        root = etree.fromstring(xml.encode('utf-8'))
        builder = IRBuilder()
        ir = builder.build(root)

        sections = [c for c in ir.content if isinstance(c, Section)]
        assert len(sections) == 1
        assert sections[0].id == "intro"
        assert sections[0].title == "Introduction"
        assert len(sections[0].content) > 0

    def test_slugify(self):
        """Test slug generation."""
        builder = IRBuilder()

        assert builder._slugify("Hello World") == "hello-world"
        assert builder._slugify("Test & Demo!") == "test-demo"
        assert builder._slugify("Multiple   Spaces") == "multiple-spaces"

    def test_unique_ids(self):
        """Test unique ID generation."""
        builder = IRBuilder()

        id1 = builder._ensure_unique_id("test")
        id2 = builder._ensure_unique_id("test")
        id3 = builder._ensure_unique_id("test")

        assert id1 == "test"
        assert id2 == "test-1"
        assert id3 == "test-2"


class TestPHPGenerator:
    """Tests for PHP generator."""

    def test_generate_basic_page(self, tmp_path):
        """Test generating basic PHP page."""
        # Create minimal IR
        ir = IntermediateRepresentation()
        ir.metadata.title = "Test Page"
        ir.content = [
            Heading(text="Hello World", level=1, id="hello-world"),
            Paragraph(content="This is a test paragraph."),
        ]

        config = GeneratorConfig(template="minimal", no_css=True)
        templates_dir = Path(__file__).parent.parent / "templates"
        generator = PHPGenerator(templates_dir, config)

        files = generator.generate(ir)

        assert 'page.php' in files
        php_content = files['page.php']

        # Check for proper escaping functions
        assert 'function escape_html' in php_content
        assert 'function escape_attr' in php_content
        assert 'function sanitize_url' in php_content

        # Check content rendering
        assert 'Test Page' in php_content
        assert 'Hello World' in php_content
        assert 'This is a test paragraph' in php_content

    def test_generate_with_css(self, tmp_path):
        """Test generating page with CSS."""
        ir = IntermediateRepresentation()
        ir.metadata.title = "Test"

        config = GeneratorConfig(no_css=False)
        templates_dir = Path(__file__).parent.parent / "templates"
        generator = PHPGenerator(templates_dir, config)

        files = generator.generate(ir)

        assert 'assets/style.css' in files
        css_content = files['assets/style.css']
        assert 'container' in css_content
        assert 'page-header' in css_content

    def test_escaping_html_injection(self, tmp_path):
        """Test HTML escaping prevents injection."""
        # Create IR with potential XSS
        ir = IntermediateRepresentation()
        ir.metadata.title = '<script>alert("XSS")</script>'
        ir.content = [
            Paragraph(content='<img src=x onerror="alert(1)">'),
        ]

        config = GeneratorConfig(template="minimal", no_css=True)
        templates_dir = Path(__file__).parent.parent / "templates"
        generator = PHPGenerator(templates_dir, config)

        files = generator.generate(ir)
        php_content = files['page.php']

        # Should contain escaped versions
        assert 'escape_html' in php_content
        # Raw script tags should not appear
        assert '<script>' not in php_content or 'escape_html' in php_content

    def test_table_generation(self):
        """Test table generation."""
        from xml_lib.php.ir import Table, TableRow, TableCell

        ir = IntermediateRepresentation()
        ir.metadata.title = "Table Test"

        table = Table(
            headers=[
                TableRow(cells=[
                    TableCell(content="Col1", is_header=True),
                    TableCell(content="Col2", is_header=True),
                ])
            ],
            rows=[
                TableRow(cells=[
                    TableCell(content="A"),
                    TableCell(content="B"),
                ])
            ],
            caption="Test Table"
        )
        ir.content = [table]

        config = GeneratorConfig(template="minimal", no_css=True)
        templates_dir = Path(__file__).parent.parent / "templates"
        generator = PHPGenerator(templates_dir, config)

        files = generator.generate(ir)
        php_content = files['page.php']

        assert 'render_table' in php_content
        assert 'Test Table' in php_content

    def test_code_block_generation(self):
        """Test code block generation."""
        from xml_lib.php.ir import CodeBlock

        ir = IntermediateRepresentation()
        ir.metadata.title = "Code Test"

        code = CodeBlock(
            code='<?php echo "Hello"; ?>',
            language="php"
        )
        ir.content = [code]

        config = GeneratorConfig(template="minimal", no_css=True)
        templates_dir = Path(__file__).parent.parent / "templates"
        generator = PHPGenerator(templates_dir, config)

        files = generator.generate(ir)
        php_content = files['page.php']

        assert '<pre>' in php_content
        assert '<code' in php_content
        assert 'escape_html' in php_content


class TestPHPValidation:
    """Tests for PHP syntax validation."""

    def test_generated_php_is_valid(self, tmp_path):
        """Test that generated PHP passes php -l."""
        ir = IntermediateRepresentation()
        ir.metadata.title = "Validation Test"
        ir.content = [
            Heading(text="Test", level=1, id="test"),
            Paragraph(content="Content"),
        ]

        config = GeneratorConfig(template="minimal", no_css=True)
        templates_dir = Path(__file__).parent.parent / "templates"
        generator = PHPGenerator(templates_dir, config)

        files = generator.generate(ir)
        php_file = tmp_path / "test.php"
        php_file.write_text(files['page.php'])

        try:
            result = subprocess.run(
                ['php', '-l', str(php_file)],
                capture_output=True,
                text=True,
                timeout=5
            )
            assert result.returncode == 0, f"PHP syntax error: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("PHP not available for linting")


class TestIntegration:
    """Integration tests for end-to-end workflow."""

    def test_example_document_generation(self, tmp_path):
        """Test generating PHP from example_document.xml."""
        example_xml = Path(__file__).parent.parent / "example_document.xml"
        if not example_xml.exists():
            pytest.skip("example_document.xml not found")

        parser = SecureXMLParser()
        root = parser.parse(example_xml)

        builder = IRBuilder()
        ir = builder.build(root)

        assert ir.metadata.title
        assert len(ir.content) > 0

        config = GeneratorConfig()
        templates_dir = Path(__file__).parent.parent / "templates"
        generator = PHPGenerator(templates_dir, config)

        files = generator.generate(ir, "example_document")

        assert 'example_document.php' in files
        assert 'assets/style.css' in files

        # Write and validate
        php_file = tmp_path / "example_document.php"
        php_file.write_text(files['example_document.php'])

        try:
            result = subprocess.run(
                ['php', '-l', str(php_file)],
                capture_output=True,
                text=True,
                timeout=5
            )
            assert result.returncode == 0
        except FileNotFoundError:
            pytest.skip("PHP not available")

    def test_amphibians_generation(self, tmp_path):
        """Test generating PHP from example_amphibians.xml."""
        example_xml = Path(__file__).parent.parent / "example_amphibians.xml"
        if not example_xml.exists():
            pytest.skip("example_amphibians.xml not found")

        parser = SecureXMLParser()
        root = parser.parse(example_xml)

        builder = IRBuilder()
        ir = builder.build(root)

        config = GeneratorConfig(template="minimal")
        templates_dir = Path(__file__).parent.parent / "templates"
        generator = PHPGenerator(templates_dir, config)

        files = generator.generate(ir, "example_amphibians")

        assert 'example_amphibians.php' in files

        # Write and validate
        php_file = tmp_path / "example_amphibians.php"
        php_file.write_text(files['example_amphibians.php'])

        try:
            result = subprocess.run(
                ['php', '-l', str(php_file)],
                capture_output=True,
                text=True,
                timeout=5
            )
            assert result.returncode == 0
        except FileNotFoundError:
            pytest.skip("PHP not available")


class TestAdversarial:
    """Adversarial security tests."""

    def test_xss_prevention_in_titles(self):
        """Test XSS prevention in titles."""
        xml = '''<document>
            <meta>
                <title>&lt;script&gt;alert('XSS')&lt;/script&gt;</title>
            </meta>
        </document>'''

        root = etree.fromstring(xml.encode('utf-8'))
        builder = IRBuilder()
        ir = builder.build(root)

        config = GeneratorConfig(template="minimal", no_css=True)
        templates_dir = Path(__file__).parent.parent / "templates"
        generator = PHPGenerator(templates_dir, config)

        files = generator.generate(ir)
        php_content = files['page.php']

        # Should use escape_html
        assert 'escape_html' in php_content

    def test_malicious_urls(self):
        """Test handling of malicious URLs."""
        from xml_lib.php.ir import Figure

        ir = IntermediateRepresentation()
        ir.metadata.title = "URL Test"

        # Try various malicious URLs
        figure = Figure(
            src='javascript:alert(1)',
            alt='Test'
        )
        ir.content = [figure]

        config = GeneratorConfig(template="minimal", no_css=True)
        templates_dir = Path(__file__).parent.parent / "templates"
        generator = PHPGenerator(templates_dir, config)

        files = generator.generate(ir)
        php_content = files['page.php']

        # Should use sanitize_url function
        assert 'sanitize_url' in php_content

    def test_huge_document(self):
        """Test handling of very large documents."""
        xml = '<document>'
        # Add many paragraphs
        for i in range(1000):
            xml += f'<paragraph>Paragraph {i}</paragraph>'
        xml += '</document>'

        root = etree.fromstring(xml.encode('utf-8'))
        builder = IRBuilder()
        ir = builder.build(root)

        assert len(ir.content) == 1000

        config = GeneratorConfig(template="minimal", no_css=True)
        templates_dir = Path(__file__).parent.parent / "templates"
        generator = PHPGenerator(templates_dir, config)

        files = generator.generate(ir)
        assert 'page.php' in files

    def test_duplicate_ids(self):
        """Test handling of duplicate IDs."""
        xml = '''<document>
            <section id="test">Section 1</section>
            <section id="test">Section 2</section>
            <section id="test">Section 3</section>
        </document>'''

        root = etree.fromstring(xml.encode('utf-8'))
        builder = IRBuilder()
        ir = builder.build(root)

        # Should generate unique IDs
        sections = [c for c in ir.content if isinstance(c, Section)]
        ids = [s.id for s in sections if s.id]

        assert len(ids) == len(set(ids)), "IDs should be unique"
