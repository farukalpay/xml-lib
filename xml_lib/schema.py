"""Schema derivation and validation using XSD and RELAX NG.

This module provides functionality to:
- Derive schemas from example XML documents
- Validate XML against XSD and RELAX NG schemas
- Cache compiled schemas for performance
"""

from pathlib import Path

import xmlschema
from lxml import etree

from xml_lib.types import ValidationResult
from xml_lib.utils.cache import SchemaCache
from xml_lib.utils.logging import get_logger, structured_log
from xml_lib.utils.xml_utils import parse_xml

logger = get_logger(__name__)


class SchemaValidator:
    """Validator for XSD and RELAX NG schemas."""

    def __init__(self, cache_dir: Path | None = None):
        """Initialize schema validator.

        Args:
            cache_dir: Directory for schema cache
        """
        self.xsd_cache: SchemaCache[xmlschema.XMLSchema] = SchemaCache(
            cache_dir / "xsd" if cache_dir else None
        )
        self.rng_cache: SchemaCache[etree.RelaxNG] = SchemaCache(
            cache_dir / "rng" if cache_dir else None
        )

    def validate_with_xsd(self, xml_path: Path, xsd_path: Path) -> ValidationResult:
        """Validate XML document against XSD schema.

        Args:
            xml_path: Path to XML document
            xsd_path: Path to XSD schema

        Returns:
            ValidationResult with errors and warnings
        """
        structured_log(
            logger,
            "info",
            "Validating with XSD",
            xml_file=str(xml_path),
            schema_file=str(xsd_path),
        )

        errors = []
        warnings = []

        try:
            # Try to get from cache
            schema = self.xsd_cache.get(xsd_path)
            if schema is None:
                schema = xmlschema.XMLSchema(str(xsd_path))
                self.xsd_cache.put(xsd_path, schema)

            # Validate
            schema.validate(str(xml_path))
            is_valid = True

        except xmlschema.XMLSchemaException as e:
            errors.append(f"XSD validation error: {e}")
            is_valid = False
        except Exception as e:
            errors.append(f"Validation error: {e}")
            is_valid = False

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metadata={"schema_type": "xsd", "schema": str(xsd_path)},
        )

    def validate_with_relaxng(self, xml_path: Path, rng_path: Path) -> ValidationResult:
        """Validate XML document against RELAX NG schema.

        Args:
            xml_path: Path to XML document
            rng_path: Path to RELAX NG schema

        Returns:
            ValidationResult with errors and warnings
        """
        structured_log(
            logger,
            "info",
            "Validating with RELAX NG",
            xml_file=str(xml_path),
            schema_file=str(rng_path),
        )

        errors = []
        warnings = []

        try:
            # Try to get from cache
            schema = self.rng_cache.get(rng_path)
            if schema is None:
                relaxng_doc = etree.parse(str(rng_path))
                schema = etree.RelaxNG(relaxng_doc)
                self.rng_cache.put(rng_path, schema)

            # Parse and validate XML
            xml_doc = etree.parse(str(xml_path))
            is_valid = schema.validate(xml_doc)

            if not is_valid:
                error_log = schema.error_log
                for error in error_log:
                    errors.append(f"Line {error.line}: {error.message}")

        except etree.DocumentInvalid as e:
            errors.append(f"RELAX NG validation error: {e}")
            is_valid = False
        except Exception as e:
            errors.append(f"Validation error: {e}")
            is_valid = False

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metadata={"schema_type": "relaxng", "schema": str(rng_path)},
        )

    def validate_with_schema(
        self, xml_path: Path, schema_path: Path, schema_type: str | None = None
    ) -> ValidationResult:
        """Validate XML with appropriate schema type.

        Args:
            xml_path: Path to XML document
            schema_path: Path to schema
            schema_type: Schema type ('xsd', 'relaxng', or auto-detect)

        Returns:
            ValidationResult
        """
        if schema_type is None:
            # Auto-detect from extension
            if schema_path.suffix in [".xsd", ".xml"]:
                schema_type = "xsd"
            elif schema_path.suffix in [".rng", ".rnc"]:
                schema_type = "relaxng"
            else:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Unknown schema type: {schema_path.suffix}"],
                    warnings=[],
                )

        if schema_type == "xsd":
            return self.validate_with_xsd(xml_path, schema_path)
        elif schema_type == "relaxng":
            return self.validate_with_relaxng(xml_path, schema_path)
        else:
            return ValidationResult(
                is_valid=False,
                errors=[f"Unsupported schema type: {schema_type}"],
                warnings=[],
            )


def derive_xsd_from_examples(
    examples: list[Path], output_path: Path, root_element: str | None = None
) -> None:
    """Derive XSD schema from example XML documents.

    Args:
        examples: List of example XML files
        output_path: Path to write XSD schema
        root_element: Optional root element name

    Raises:
        ValueError: If no valid examples provided
    """
    if not examples:
        raise ValueError("No example files provided")

    structured_log(
        logger,
        "info",
        "Deriving XSD schema",
        example_count=len(examples),
        output=str(output_path),
    )

    # This is a simplified version - in production, you'd use xmlschema.create_schema
    # or a more sophisticated schema inference algorithm

    # Parse first example to get structure
    root = parse_xml(examples[0])

    # Build basic XSD structure
    xsd_root = etree.Element(
        "{http://www.w3.org/2001/XMLSchema}schema",
        attrib={
            "xmlns:xs": "http://www.w3.org/2001/XMLSchema",
            "elementFormDefault": "qualified",
        },
    )

    # Add root element
    element_name = root_element or root.tag
    element_decl = etree.SubElement(
        xsd_root, "{http://www.w3.org/2001/XMLSchema}element", attrib={"name": element_name}
    )

    complex_type = etree.SubElement(element_decl, "{http://www.w3.org/2001/XMLSchema}complexType")
    sequence = etree.SubElement(complex_type, "{http://www.w3.org/2001/XMLSchema}sequence")

    # Infer child elements from examples
    seen_elements: set[str] = set()
    for example in examples:
        root = parse_xml(example)
        for child in root:
            if child.tag not in seen_elements:
                etree.SubElement(
                    sequence,
                    "{http://www.w3.org/2001/XMLSchema}element",
                    attrib={"name": child.tag, "minOccurs": "0", "maxOccurs": "unbounded"},
                )
                seen_elements.add(child.tag)

    # Write XSD
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree = etree.ElementTree(xsd_root)
    tree.write(
        str(output_path),
        pretty_print=True,
        xml_declaration=True,
        encoding="utf-8",
    )

    logger.info(f"Derived XSD schema written to: {output_path}")


def derive_relaxng_from_examples(
    examples: list[Path], output_path: Path, root_element: str | None = None
) -> None:
    """Derive RELAX NG schema from example XML documents.

    Args:
        examples: List of example XML files
        output_path: Path to write RELAX NG schema
        root_element: Optional root element name

    Raises:
        ValueError: If no valid examples provided
    """
    if not examples:
        raise ValueError("No example files provided")

    structured_log(
        logger,
        "info",
        "Deriving RELAX NG schema",
        example_count=len(examples),
        output=str(output_path),
    )

    # Parse first example
    root = parse_xml(examples[0])

    # Build RELAX NG structure
    rng_root = etree.Element(
        "{http://relaxng.org/ns/structure/1.0}grammar",
        attrib={
            "xmlns": "http://relaxng.org/ns/structure/1.0",
            "datatypeLibrary": "http://www.w3.org/2001/XMLSchema-datatypes",
        },
    )

    start = etree.SubElement(rng_root, "{http://relaxng.org/ns/structure/1.0}start")
    element_name = root_element or root.tag
    element_ref = etree.SubElement(
        start, "{http://relaxng.org/ns/structure/1.0}ref", attrib={"name": element_name}
    )

    # Define element
    define = etree.SubElement(
        rng_root, "{http://relaxng.org/ns/structure/1.0}define", attrib={"name": element_name}
    )
    element = etree.SubElement(
        define, "{http://relaxng.org/ns/structure/1.0}element", attrib={"name": element_name}
    )

    # Infer child elements
    seen_elements: set[str] = set()
    for example in examples:
        root = parse_xml(example)
        for child in root:
            if child.tag not in seen_elements:
                child_element = etree.SubElement(
                    element,
                    "{http://relaxng.org/ns/structure/1.0}element",
                    attrib={"name": child.tag},
                )
                text_node = etree.SubElement(
                    child_element, "{http://relaxng.org/ns/structure/1.0}text"
                )
                seen_elements.add(child.tag)

    # Write RELAX NG
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree = etree.ElementTree(rng_root)
    tree.write(
        str(output_path),
        pretty_print=True,
        xml_declaration=True,
        encoding="utf-8",
    )

    logger.info(f"Derived RELAX NG schema written to: {output_path}")


def validate_with_schema(
    xml_path: Path,
    schema_path: Path,
    schema_type: str | None = None,
    cache_dir: Path | None = None,
) -> ValidationResult:
    """Validate XML document against a schema.

    Args:
        xml_path: Path to XML document
        schema_path: Path to schema file
        schema_type: Schema type ('xsd' or 'relaxng'), auto-detected if None
        cache_dir: Optional cache directory

    Returns:
        ValidationResult
    """
    validator = SchemaValidator(cache_dir=cache_dir)
    return validator.validate_with_schema(xml_path, schema_path, schema_type)
