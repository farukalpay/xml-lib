"""Schema-aware structural diff for XML documents."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional
from lxml import etree

from xml_lib.telemetry import TelemetrySink


class DiffType(Enum):
    """Type of difference."""

    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    MOVED = "moved"


@dataclass
class Difference:
    """A structural difference between documents."""

    type: DiffType
    path: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    explanation: Optional[str] = None

    def format(self, explain: bool = False) -> str:
        """Format difference as string."""
        symbol = {
            DiffType.ADDED: "+",
            DiffType.REMOVED: "-",
            DiffType.MODIFIED: "~",
            DiffType.MOVED: "↔",
        }[self.type]

        parts = [f"{symbol} {self.path}"]

        if self.type == DiffType.ADDED and self.new_value:
            parts.append(f"  Added: {self._truncate(self.new_value)}")
        elif self.type == DiffType.REMOVED and self.old_value:
            parts.append(f"  Removed: {self._truncate(self.old_value)}")
        elif self.type == DiffType.MODIFIED:
            if self.old_value:
                parts.append(f"  Old: {self._truncate(self.old_value)}")
            if self.new_value:
                parts.append(f"  New: {self._truncate(self.new_value)}")

        if explain and self.explanation:
            parts.append(f"  ℹ {self.explanation}")

        return "\n".join(parts)

    def _truncate(self, text: str, max_len: int = 80) -> str:
        """Truncate long text."""
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."


@dataclass
class DiffResult:
    """Result of diff operation."""

    identical: bool
    differences: List[Difference]


class Differ:
    """Schema-aware XML differ."""

    def __init__(
        self,
        schemas_dir: Path,
        telemetry: Optional[TelemetrySink] = None,
    ):
        self.schemas_dir = schemas_dir
        self.telemetry = telemetry

        # Map of element types to their semantic meaning
        self.semantic_map = {
            "begin": "Lifecycle initialization phase",
            "start": "Lifecycle start phase with engineering guidelines",
            "iteration": "Lifecycle iteration phase for cyclic processing",
            "end": "Lifecycle finalization phase",
            "continuum": "Lifecycle governance and continuation phase",
            "guardrails-begin": "Guardrail charter and scope definition",
            "guardrails-middle": "Guardrail engineering and implementation",
            "guardrails-end": "Guardrail finalization and sign-off",
        }

    def diff(
        self,
        file1: Path,
        file2: Path,
        explain: bool = False,
    ) -> DiffResult:
        """Perform schema-aware diff between two XML files.

        Args:
            file1: First XML file
            file2: Second XML file
            explain: Include explanations for differences

        Returns:
            DiffResult
        """
        try:
            # Parse documents
            doc1 = etree.parse(str(file1))
            doc2 = etree.parse(str(file2))

            root1 = doc1.getroot()
            root2 = doc2.getroot()

            # Compare
            differences = []
            self._compare_elements(
                root1,
                root2,
                path=root1.tag,
                differences=differences,
                explain=explain,
            )

            return DiffResult(
                identical=len(differences) == 0,
                differences=differences,
            )

        except Exception as e:
            return DiffResult(
                identical=False,
                differences=[
                    Difference(
                        type=DiffType.MODIFIED,
                        path="/",
                        explanation=f"Error comparing files: {e}",
                    )
                ],
            )

    def _compare_elements(
        self,
        elem1: Optional[etree._Element],
        elem2: Optional[etree._Element],
        path: str,
        differences: List[Difference],
        explain: bool,
    ) -> None:
        """Recursively compare elements."""
        # Handle missing elements
        if elem1 is None and elem2 is None:
            return
        if elem1 is None:
            explanation = None
            if explain:
                explanation = f"Element '{elem2.tag}' was added"
                if elem2.tag in self.semantic_map:
                    explanation += f" ({self.semantic_map[elem2.tag]})"

            differences.append(
                Difference(
                    type=DiffType.ADDED,
                    path=path,
                    new_value=elem2.tag,
                    explanation=explanation,
                )
            )
            return
        if elem2 is None:
            explanation = None
            if explain:
                explanation = f"Element '{elem1.tag}' was removed"
                if elem1.tag in self.semantic_map:
                    explanation += f" ({self.semantic_map[elem1.tag]})"

            differences.append(
                Difference(
                    type=DiffType.REMOVED,
                    path=path,
                    old_value=elem1.tag,
                    explanation=explanation,
                )
            )
            return

        # Compare tags
        if elem1.tag != elem2.tag:
            explanation = None
            if explain:
                explanation = f"Element changed from '{elem1.tag}' to '{elem2.tag}'"

            differences.append(
                Difference(
                    type=DiffType.MODIFIED,
                    path=path,
                    old_value=elem1.tag,
                    new_value=elem2.tag,
                    explanation=explanation,
                )
            )
            return

        # Compare attributes
        attrs1 = set(elem1.attrib.keys())
        attrs2 = set(elem2.attrib.keys())

        for attr in attrs1 - attrs2:
            explanation = None
            if explain:
                explanation = f"Attribute '{attr}' was removed"
                if attr == "timestamp":
                    explanation += " (affects temporal ordering)"
                elif attr == "checksum":
                    explanation += " (affects content verification)"
                elif attr == "id":
                    explanation += " (affects cross-references)"

            differences.append(
                Difference(
                    type=DiffType.REMOVED,
                    path=f"{path}/@{attr}",
                    old_value=elem1.get(attr),
                    explanation=explanation,
                )
            )

        for attr in attrs2 - attrs1:
            explanation = None
            if explain:
                explanation = f"Attribute '{attr}' was added"
                if attr == "timestamp":
                    explanation += " (establishes temporal ordering)"
                elif attr == "checksum":
                    explanation += " (enables content verification)"
                elif attr == "id":
                    explanation += " (enables cross-references)"

            differences.append(
                Difference(
                    type=DiffType.ADDED,
                    path=f"{path}/@{attr}",
                    new_value=elem2.get(attr),
                    explanation=explanation,
                )
            )

        for attr in attrs1 & attrs2:
            val1 = elem1.get(attr)
            val2 = elem2.get(attr)
            if val1 != val2:
                explanation = None
                if explain:
                    explanation = f"Attribute '{attr}' value changed"
                    if attr == "timestamp":
                        explanation += " (may affect temporal monotonicity validation)"
                    elif attr == "checksum":
                        explanation += " (indicates content modification)"

                differences.append(
                    Difference(
                        type=DiffType.MODIFIED,
                        path=f"{path}/@{attr}",
                        old_value=val1,
                        new_value=val2,
                        explanation=explanation,
                    )
                )

        # Compare text content
        text1 = (elem1.text or "").strip()
        text2 = (elem2.text or "").strip()
        if text1 != text2:
            explanation = None
            if explain:
                explanation = f"Text content of '{elem1.tag}' changed"

            differences.append(
                Difference(
                    type=DiffType.MODIFIED,
                    path=f"{path}/text()",
                    old_value=text1,
                    new_value=text2,
                    explanation=explanation,
                )
            )

        # Compare children
        children1 = list(elem1)
        children2 = list(elem2)

        # Build map of children by tag
        children1_map = {}
        for child in children1:
            tag = child.tag
            if tag not in children1_map:
                children1_map[tag] = []
            children1_map[tag].append(child)

        children2_map = {}
        for child in children2:
            tag = child.tag
            if tag not in children2_map:
                children2_map[tag] = []
            children2_map[tag].append(child)

        # Compare children
        all_tags = set(children1_map.keys()) | set(children2_map.keys())
        for tag in all_tags:
            list1 = children1_map.get(tag, [])
            list2 = children2_map.get(tag, [])

            # Compare by index
            for i in range(max(len(list1), len(list2))):
                child1 = list1[i] if i < len(list1) else None
                child2 = list2[i] if i < len(list2) else None

                child_path = f"{path}/{tag}"
                if max(len(list1), len(list2)) > 1:
                    child_path += f"[{i+1}]"

                self._compare_elements(child1, child2, child_path, differences, explain)
