"""XML linting for formatting and security checks."""

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from lxml import etree


class LintLevel(Enum):
    """Severity level of a lint issue."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class LintIssue:
    """A lint issue found in an XML document."""

    level: LintLevel
    message: str
    file: str
    line: int | None = None
    column: int | None = None
    rule: str = ""

    def format_text(self) -> str:
        """Format issue as text."""
        location = f"{self.file}"
        if self.line is not None:
            location += f":{self.line}"
            if self.column is not None:
                location += f":{self.column}"

        symbol = {"error": "❌", "warning": "⚠️ ", "info": "ℹ️ "}[self.level.value]
        return f"{symbol} {location}: {self.message} [{self.rule}]"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "level": self.level.value,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "rule": self.rule,
        }


@dataclass
class LintResult:
    """Result of linting operation."""

    issues: list[LintIssue] = field(default_factory=list)
    files_checked: int = 0

    @property
    def error_count(self) -> int:
        """Count of error-level issues."""
        return sum(1 for issue in self.issues if issue.level == LintLevel.ERROR)

    @property
    def warning_count(self) -> int:
        """Count of warning-level issues."""
        return sum(1 for issue in self.issues if issue.level == LintLevel.WARNING)

    @property
    def has_errors(self) -> bool:
        """Whether any errors were found."""
        return self.error_count > 0


class XMLLinter:
    """Linter for XML files checking formatting and security."""

    def __init__(
        self,
        check_indentation: bool = True,
        check_attribute_order: bool = True,
        check_external_entities: bool = True,
        check_formatting: bool = True,
        indent_size: int = 2,
        allow_xxe: bool = False,
    ):
        """Initialize linter with configuration.

        Args:
            check_indentation: Check for consistent indentation
            check_attribute_order: Check for alphabetically sorted attributes
            check_external_entities: Check for XXE vulnerabilities
            check_formatting: Check for general formatting issues
            indent_size: Expected indentation size (spaces)
            allow_xxe: Allow external entities (defaults to False for security)
        """
        self.check_indentation = check_indentation
        self.check_attribute_order = check_attribute_order
        self.check_external_entities = check_external_entities
        self.check_formatting = check_formatting
        self.indent_size = indent_size
        self.allow_xxe = allow_xxe

    def lint_file(self, file_path: Path) -> LintResult:
        """Lint a single XML file.

        Args:
            file_path: Path to XML file

        Returns:
            LintResult with any issues found
        """
        result = LintResult(files_checked=1)

        # Read raw content for line-by-line checks
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            result.issues.append(
                LintIssue(
                    level=LintLevel.ERROR,
                    message=f"Failed to read file: {e}",
                    file=str(file_path),
                    rule="file-access",
                )
            )
            return result

        # Check for external entity declarations (XXE)
        if self.check_external_entities and not self.allow_xxe:
            self._check_external_entities(content, file_path, result)

        # Try to parse the XML
        try:
            parser = etree.XMLParser(
                resolve_entities=False,  # Security: disable entity resolution
                no_network=True,  # Security: disable network access
                remove_blank_text=False,  # Preserve formatting
            )
            doc = etree.parse(str(file_path), parser)
        except etree.XMLSyntaxError as e:
            result.issues.append(
                LintIssue(
                    level=LintLevel.ERROR,
                    message=f"XML syntax error: {e}",
                    file=str(file_path),
                    line=e.lineno,
                    column=getattr(e, "position", [None])[0],
                    rule="xml-syntax",
                )
            )
            return result
        except Exception as e:
            result.issues.append(
                LintIssue(
                    level=LintLevel.ERROR,
                    message=f"Failed to parse XML: {e}",
                    file=str(file_path),
                    rule="xml-parse",
                )
            )
            return result

        # Perform tree-based checks
        if self.check_attribute_order:
            self._check_attribute_order(doc, file_path, result)

        # Perform line-based checks
        lines = content.splitlines()
        if self.check_indentation:
            self._check_indentation(lines, file_path, result)

        if self.check_formatting:
            self._check_formatting(lines, file_path, result)

        return result

    def lint_directory(self, directory: Path, recursive: bool = True) -> LintResult:
        """Lint all XML files in a directory.

        Args:
            directory: Directory to scan
            recursive: Recursively scan subdirectories

        Returns:
            LintResult with all issues found
        """
        result = LintResult()

        pattern = "**/*.xml" if recursive else "*.xml"
        for xml_file in directory.glob(pattern):
            # Skip hidden files and common directories
            if any(part.startswith(".") for part in xml_file.parts):
                continue
            if any(
                part in ("node_modules", "__pycache__", "venv", ".git")
                for part in xml_file.parts
            ):
                continue

            file_result = self.lint_file(xml_file)
            result.issues.extend(file_result.issues)
            result.files_checked += file_result.files_checked

        return result

    def _check_external_entities(
        self, content: str, file_path: Path, result: LintResult
    ) -> None:
        """Check for external entity declarations (XXE vulnerability)."""
        # Pattern for DOCTYPE with ENTITY declarations
        entity_pattern = re.compile(r"<!ENTITY\s+\w+\s+SYSTEM", re.IGNORECASE)

        for i, line in enumerate(content.splitlines(), start=1):
            if entity_pattern.search(line):
                result.issues.append(
                    LintIssue(
                        level=LintLevel.ERROR,
                        message="External entity declaration detected (XXE risk). Use --allow-xxe if intentional.",
                        file=str(file_path),
                        line=i,
                        rule="xxe-entity",
                    )
                )

        # Check for external DTD references
        dtd_pattern = re.compile(r"<!DOCTYPE\s+\w+\s+SYSTEM", re.IGNORECASE)
        for i, line in enumerate(content.splitlines(), start=1):
            if dtd_pattern.search(line):
                result.issues.append(
                    LintIssue(
                        level=LintLevel.WARNING,
                        message="External DTD reference detected. Ensure DTD is trusted.",
                        file=str(file_path),
                        line=i,
                        rule="external-dtd",
                    )
                )

    def _check_attribute_order(
        self, doc: etree._ElementTree, file_path: Path, result: LintResult
    ) -> None:
        """Check that attributes are in alphabetical order."""
        root = doc.getroot()

        for elem in root.iter():
            if not elem.attrib:
                continue

            # Get attributes in order they appear (lxml preserves order)
            attrs = list(elem.attrib.keys())

            # Filter out xml: namespace attributes from sorting requirement
            sortable_attrs = [a for a in attrs if not a.startswith("{")]

            if sortable_attrs:
                sorted_attrs = sorted(sortable_attrs, key=lambda x: x.lower())

                if sortable_attrs != sorted_attrs:
                    result.issues.append(
                        LintIssue(
                            level=LintLevel.WARNING,
                            message=f"Attributes not in alphabetical order. Expected: {', '.join(sorted_attrs)}",
                            file=str(file_path),
                            line=elem.sourceline,
                            rule="attribute-order",
                        )
                    )

    def _check_indentation(
        self, lines: list[str], file_path: Path, result: LintResult
    ) -> None:
        """Check for consistent indentation."""
        for i, line in enumerate(lines, start=1):
            # Skip empty lines
            if not line.strip():
                continue

            # Skip XML declaration and DOCTYPE
            if line.strip().startswith("<?xml") or line.strip().startswith("<!DOCTYPE"):
                continue

            # Count leading spaces
            leading_spaces = len(line) - len(line.lstrip(" "))

            # Check if indentation is a multiple of indent_size
            if leading_spaces > 0 and leading_spaces % self.indent_size != 0:
                result.issues.append(
                    LintIssue(
                        level=LintLevel.WARNING,
                        message=f"Inconsistent indentation: {leading_spaces} spaces (expected multiple of {self.indent_size})",
                        file=str(file_path),
                        line=i,
                        rule="indentation",
                    )
                )

            # Check for tabs
            if "\t" in line[:leading_spaces] if leading_spaces > 0 else "\t" in line:
                result.issues.append(
                    LintIssue(
                        level=LintLevel.WARNING,
                        message="Found tab character, use spaces for indentation",
                        file=str(file_path),
                        line=i,
                        rule="tabs",
                    )
                )

    def _check_formatting(
        self, lines: list[str], file_path: Path, result: LintResult
    ) -> None:
        """Check for general formatting issues."""
        for i, line in enumerate(lines, start=1):
            # Check for trailing whitespace
            if line.rstrip() != line.rstrip("\n").rstrip("\r"):
                result.issues.append(
                    LintIssue(
                        level=LintLevel.INFO,
                        message="Trailing whitespace",
                        file=str(file_path),
                        line=i,
                        rule="trailing-whitespace",
                    )
                )

            # Check for lines that are too long (>120 chars is a common limit)
            if len(line.rstrip()) > 120:
                result.issues.append(
                    LintIssue(
                        level=LintLevel.INFO,
                        message=f"Line too long ({len(line.rstrip())} > 120 characters)",
                        file=str(file_path),
                        line=i,
                        rule="line-length",
                    )
                )

        # Check file ends with newline
        if lines and lines[-1] and not lines[-1].endswith("\n"):
            result.issues.append(
                LintIssue(
                    level=LintLevel.INFO,
                    message="File should end with a newline",
                    file=str(file_path),
                    line=len(lines),
                    rule="final-newline",
                )
            )
