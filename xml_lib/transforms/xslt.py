"""XSLT transformation utilities."""

from pathlib import Path

from lxml import etree

from xml_lib.utils.logging import get_logger

logger = get_logger(__name__)


class XSLTTransformer:
    """XSLT transformation manager."""

    def __init__(self, templates_dir: Path | None = None):
        """Initialize XSLT transformer.

        Args:
            templates_dir: Directory containing XSLT templates
        """
        self.templates_dir = templates_dir or Path("schemas/xslt")
        self._compiled_transforms: dict[str, etree.XSLT] = {}

    def load_transform(self, xslt_path: Path) -> etree.XSLT:
        """Load and compile XSLT transform.

        Args:
            xslt_path: Path to XSLT file

        Returns:
            Compiled XSLT transform
        """
        cache_key = str(xslt_path)
        if cache_key in self._compiled_transforms:
            return self._compiled_transforms[cache_key]

        xslt_doc = etree.parse(str(xslt_path))
        transform = etree.XSLT(xslt_doc)
        self._compiled_transforms[cache_key] = transform

        return transform

    def transform(
        self, xml_path: Path, xslt_path: Path, output_path: Path, **params: str
    ) -> bool:
        """Apply XSLT transform to XML document.

        Args:
            xml_path: Input XML file
            xslt_path: XSLT stylesheet
            output_path: Output file
            **params: XSLT parameters

        Returns:
            True if successful
        """
        try:
            xml_doc = etree.parse(str(xml_path))
            transform = self.load_transform(xslt_path)

            result = transform(xml_doc, **params)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(bytes(result))

            return True
        except Exception as e:
            logger.error(f"XSLT transformation failed: {e}")
            return False
