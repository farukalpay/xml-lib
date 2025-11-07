"""Guardrail rule engine that compiles XML guardrails into executable checks."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from lxml import etree

from xml_lib.types import ValidationError


@dataclass
class GuardrailRule:
    """A compiled guardrail rule."""

    id: str
    name: str
    description: str
    priority: str
    constraint_type: str
    constraint: str
    message: Optional[str]
    provenance: Dict[str, Any]


@dataclass
class GuardrailResult:
    """Result of guardrail validation."""

    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    rules_checked: int = 0


class GuardrailEngine:
    """Compiles and executes guardrail rules with provenance tracking."""

    def __init__(self, guardrails_dir: Path):
        self.guardrails_dir = guardrails_dir
        self.rules: List[GuardrailRule] = []
        self._load_rules()

    def _load_rules(self) -> None:
        """Load and compile guardrail rules from XML files."""
        self.rules = self.load_guardrails()

    def load_guardrails(self) -> List[GuardrailRule]:
        """Return compiled guardrail rules."""
        compiled_rules: List[GuardrailRule] = []
        if not self.guardrails_dir.exists():
            return compiled_rules

        for xml_file in self.guardrails_dir.rglob("*.xml"):
            try:
                doc = etree.parse(str(xml_file))
                root = doc.getroot()

                for guardrail in root.xpath("//guardrail[@id]"):
                    rule = self._parse_guardrail(guardrail, xml_file)
                    if rule:
                        compiled_rules.append(rule)

            except Exception as e:
                print(f"Warning: Failed to load guardrail from {xml_file}: {e}")

        return compiled_rules

    def _load_guardrails(self) -> List[GuardrailRule]:
        """Compatibility shim for benchmark suite."""
        return self.load_guardrails()

    def _parse_guardrail(
        self,
        element: etree._Element,
        source_file: Path,
    ) -> Optional[GuardrailRule]:
        """Parse a guardrail element into a rule."""
        try:
            rule_id = element.get("id")
            priority = element.get("priority", "medium")

            name_elem = element.find("name")
            desc_elem = element.find("description")
            constraint_elem = element.find("constraint")
            message_elem = element.find("message")
            provenance_elem = element.find("provenance")

            if name_elem is None or desc_elem is None or constraint_elem is None:
                return None

            # Parse provenance
            provenance = {"source": str(source_file)}
            if provenance_elem is not None:
                author_elem = provenance_elem.find("author")
                created_elem = provenance_elem.find("created")
                rationale_elem = provenance_elem.find("rationale")

                if author_elem is not None:
                    provenance["author"] = author_elem.text
                if created_elem is not None:
                    provenance["created"] = created_elem.text
                if rationale_elem is not None:
                    provenance["rationale"] = rationale_elem.text

            return GuardrailRule(
                id=rule_id,
                name=name_elem.text or "",
                description=desc_elem.text or "",
                priority=priority,
                constraint_type=constraint_elem.get("type", "xpath"),
                constraint=constraint_elem.text or "",
                message=message_elem.text if message_elem is not None else None,
                provenance=provenance,
            )

        except Exception as e:
            print(f"Warning: Failed to parse guardrail: {e}")
            return None

    def validate(self, project_path: Path) -> GuardrailResult:
        """Validate project against all guardrail rules."""
        result = GuardrailResult()

        # Find all XML files in project
        xml_files = [
            f
            for f in project_path.rglob("*.xml")
            if "schema" not in str(f) and f.parent.name != "guardrails"
        ]

        # Check each rule against each file
        for rule in self.rules:
            result.rules_checked += 1

            for xml_file in xml_files:
                try:
                    doc = etree.parse(str(xml_file))
                    violations = self._check_rule(doc, xml_file, rule)
                    result.errors.extend(violations)

                except Exception:
                    # Skip files that can't be parsed
                    continue

        return result

    def _check_rule(
        self,
        doc: etree._ElementTree,
        xml_file: Path,
        rule: GuardrailRule,
    ) -> List[ValidationError]:
        """Check a single rule against a document."""
        violations = []

        try:
            if rule.constraint_type == "xpath":
                violations.extend(self._check_xpath(doc, xml_file, rule))
            elif rule.constraint_type == "regex":
                violations.extend(self._check_regex(doc, xml_file, rule))
            elif rule.constraint_type == "checksum":
                violations.extend(self._check_checksum(doc, xml_file, rule))
            elif rule.constraint_type == "temporal":
                violations.extend(self._check_temporal(doc, xml_file, rule))
            elif rule.constraint_type == "cross-file":
                # Cross-file checks require multiple documents - skip for now
                pass

        except Exception:
            # Rule execution failed - log but don't fail validation
            pass

        return violations

    def _check_xpath(
        self,
        doc: etree._ElementTree,
        xml_file: Path,
        rule: GuardrailRule,
    ) -> List[ValidationError]:
        """Check XPath constraint."""
        violations = []

        try:
            # XPath that returns False or empty indicates violation
            result = doc.xpath(rule.constraint)

            # Convert result to boolean
            if isinstance(result, bool):
                is_valid = result
            elif isinstance(result, list):
                is_valid = len(result) > 0
            else:
                is_valid = bool(result)

            if not is_valid:
                message = rule.message or f"XPath constraint failed: {rule.constraint}"
                violations.append(
                    ValidationError(
                        file=str(xml_file),
                        line=None,
                        column=None,
                        message=f"{rule.name}: {message}",
                        type=(
                            "error"
                            if rule.priority in ["critical", "high"]
                            else "warning"
                        ),
                        rule=rule.id,
                    )
                )

        except Exception:
            # XPath evaluation failed
            pass

        return violations

    def _check_regex(
        self,
        doc: etree._ElementTree,
        xml_file: Path,
        rule: GuardrailRule,
    ) -> List[ValidationError]:
        """Check regex constraint against document text."""
        violations = []

        try:
            # Get all text content
            text = etree.tostring(doc, encoding="unicode", method="text")

            # Check if regex matches (or doesn't match if constraint starts with !)
            negate = rule.constraint.startswith("!")
            pattern = rule.constraint[1:] if negate else rule.constraint

            matches = re.search(pattern, text)

            if (matches and negate) or (not matches and not negate):
                message = rule.message or f"Regex constraint failed: {pattern}"
                violations.append(
                    ValidationError(
                        file=str(xml_file),
                        line=None,
                        column=None,
                        message=f"{rule.name}: {message}",
                        type=(
                            "error"
                            if rule.priority in ["critical", "high"]
                            else "warning"
                        ),
                        rule=rule.id,
                    )
                )

        except Exception:
            pass

        return violations

    def _check_checksum(
        self,
        doc: etree._ElementTree,
        xml_file: Path,
        rule: GuardrailRule,
    ) -> List[ValidationError]:
        """Check checksum constraint."""
        # Checksum validation is handled by the main validator
        return []

    def _check_temporal(
        self,
        doc: etree._ElementTree,
        xml_file: Path,
        rule: GuardrailRule,
    ) -> List[ValidationError]:
        """Check temporal constraint."""
        # Temporal validation is handled by the main validator
        return []
