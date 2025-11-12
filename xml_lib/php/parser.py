"""Secure XML parser with XXE protection and size/time limits."""

import time
from dataclasses import dataclass
from pathlib import Path

from lxml import etree


@dataclass
class ParseConfig:
    """Configuration for secure XML parsing."""

    max_size_bytes: int = 10 * 1024 * 1024  # 10MB default
    max_parse_time_seconds: float = 30.0
    validate_schema: bool = True
    schema_path: Path | None = None
    allow_xxe: bool = False  # Allow external entities (SECURITY RISK)


class ParseError(Exception):
    """Exception raised during XML parsing."""

    pass


class SecureXMLParser:
    """Secure XML parser with protections against common vulnerabilities.

    Features:
    - XXE (XML External Entity) protection
    - Size limits
    - Time limits
    - Optional schema validation (Relax NG/Schematron)
    """

    def __init__(self, config: ParseConfig | None = None):
        """Initialize the secure parser.

        Args:
            config: Parse configuration, uses defaults if None
        """
        self.config = config or ParseConfig()

    def parse(self, xml_path: Path) -> etree._Element:
        """Parse an XML file securely.

        Args:
            xml_path: Path to XML file

        Returns:
            Parsed XML element tree

        Raises:
            ParseError: If parsing fails or security checks fail
        """
        # Check file size
        file_size = xml_path.stat().st_size
        if file_size > self.config.max_size_bytes:
            raise ParseError(
                f"File too large: {file_size} bytes " f"(max: {self.config.max_size_bytes})"
            )

        # Create secure parser
        parser = self._create_secure_parser()

        # Parse with timeout
        start_time = time.time()
        try:
            tree = etree.parse(str(xml_path), parser)
        except etree.XMLSyntaxError as e:
            raise ParseError(f"XML syntax error: {e}") from e
        except Exception as e:
            raise ParseError(f"Parse error: {e}") from e

        elapsed = time.time() - start_time
        if elapsed > self.config.max_parse_time_seconds:
            raise ParseError(
                f"Parse timeout: {elapsed:.2f}s " f"(max: {self.config.max_parse_time_seconds}s)"
            )

        root = tree.getroot()

        # Validate against schema if configured
        if self.config.validate_schema and self.config.schema_path:
            self._validate_schema(tree, self.config.schema_path)

        return root

    def parse_string(self, xml_string: str) -> etree._Element:
        """Parse XML from string securely.

        Args:
            xml_string: XML content as string

        Returns:
            Parsed XML element tree

        Raises:
            ParseError: If parsing fails or security checks fail
        """
        # Check size
        size_bytes = len(xml_string.encode("utf-8"))
        if size_bytes > self.config.max_size_bytes:
            raise ParseError(
                f"XML too large: {size_bytes} bytes " f"(max: {self.config.max_size_bytes})"
            )

        # Create secure parser
        parser = self._create_secure_parser()

        # Parse with timeout
        start_time = time.time()
        try:
            root = etree.fromstring(xml_string.encode("utf-8"), parser)
        except etree.XMLSyntaxError as e:
            raise ParseError(f"XML syntax error: {e}") from e
        except Exception as e:
            raise ParseError(f"Parse error: {e}") from e

        elapsed = time.time() - start_time
        if elapsed > self.config.max_parse_time_seconds:
            raise ParseError(
                f"Parse timeout: {elapsed:.2f}s " f"(max: {self.config.max_parse_time_seconds}s)"
            )

        return root

    def _create_secure_parser(self) -> etree.XMLParser:
        """Create a secure XML parser with XXE protection.

        Returns:
            Configured XMLParser instance
        """
        # Configure XXE protection based on allow_xxe setting
        # WARNING: Enabling XXE (allow_xxe=True) is a security risk!
        if self.config.allow_xxe:
            # SECURITY RISK: External entities are enabled
            parser = etree.XMLParser(
                resolve_entities=True,  # WARNING: Enables external entities
                no_network=False,  # WARNING: Enables network access
                dtd_validation=False,  # Still disable DTD validation
                load_dtd=True,  # Allow loading DTD
                huge_tree=False,  # Still prevent billion laughs
                remove_blank_text=False,  # Preserve formatting
                remove_comments=False,  # Keep comments
            )
        else:
            # Secure default: Disable external entity resolution to prevent XXE attacks
            parser = etree.XMLParser(
                resolve_entities=False,  # Disable external entities
                no_network=True,  # Disable network access
                dtd_validation=False,  # Disable DTD validation
                load_dtd=False,  # Don't load DTD
                huge_tree=False,  # Prevent billion laughs attack
                remove_blank_text=False,  # Preserve formatting
                remove_comments=False,  # Keep comments
            )
        return parser

    def _validate_schema(self, tree: etree._ElementTree, schema_path: Path) -> None:
        """Validate XML against Relax NG schema.

        Args:
            tree: Parsed XML tree
            schema_path: Path to Relax NG schema

        Raises:
            ParseError: If validation fails
        """
        if not schema_path.exists():
            raise ParseError(f"Schema not found: {schema_path}")

        try:
            # Determine schema type by extension
            if schema_path.suffix == ".rng":
                schema_doc = etree.parse(str(schema_path))
                schema = etree.RelaxNG(schema_doc)
            elif schema_path.suffix == ".sch":
                schema_doc = etree.parse(str(schema_path))
                schema = etree.Schematron(schema_doc)
            else:
                raise ParseError(f"Unsupported schema type: {schema_path.suffix}")

            if not schema.validate(tree):
                error_log = schema.error_log
                errors = "\n".join(str(e) for e in error_log)
                raise ParseError(f"Schema validation failed:\n{errors}")

        except etree.XMLSyntaxError as e:
            raise ParseError(f"Schema parse error: {e}") from e
        except Exception as e:
            if isinstance(e, ParseError):
                raise
            raise ParseError(f"Schema validation error: {e}") from e
