"""YAML to XSLT transpiler for policy enforcement."""

from pathlib import Path

from lxml import etree

from xml_lib.guardrails.policy import Policy


class PolicyTranspiler:
    """Transpile YAML policies to XSLT."""

    def transpile_to_xslt(self, policy: Policy, output_path: Path) -> None:
        """Transpile policy to XSLT stylesheet.

        Args:
            policy: Policy to transpile
            output_path: Output XSLT file path
        """
        # Create XSLT root
        xslt_root = etree.Element(
            "{http://www.w3.org/1999/XSL/Transform}stylesheet",
            attrib={
                "version": "1.0",
                "xmlns:xsl": "http://www.w3.org/1999/XSL/Transform",
            },
        )

        # Add template for root
        template = etree.SubElement(
            xslt_root,
            "{http://www.w3.org/1999/XSL/Transform}template",
            attrib={"match": "/"},
        )

        # Add policy checks as XSLT
        for rule in policy.rules:
            if rule.constraint_type == "xpath":
                # Create test element
                test = etree.SubElement(
                    template,
                    "{http://www.w3.org/1999/XSL/Transform}if",
                    attrib={"test": f"not({rule.constraint})"},
                )
                message = etree.SubElement(test, "{http://www.w3.org/1999/XSL/Transform}message")
                message.text = rule.message or f"Rule {rule.id} failed: {rule.description}"

        # Write XSLT
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tree = etree.ElementTree(xslt_root)
        tree.write(
            str(output_path),
            pretty_print=True,
            xml_declaration=True,
            encoding="utf-8",
        )
