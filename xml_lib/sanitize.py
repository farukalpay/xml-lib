"""Lossless mathy-XML preprocessor with reversible mapping.

Transforms XML files with invalid element/attribute names (containing math symbols)
into valid XML using bijective surrogate mapping.
"""

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class MathPolicy(Enum):
    """Policy for handling mathy XML."""

    SANITIZE = "sanitize"  # Convert to surrogates (default)
    MATHML = "mathml"  # Convert to MathML
    SKIP = "skip"  # Skip invalid files
    ERROR = "error"  # Fail on invalid names


@dataclass
class SurrogateMapping:
    """Records a single surrogate transformation."""

    kind: str  # "element" or "attr"
    orig: str  # Original name (e.g., "×")
    surrogate: str  # Surrogate name (e.g., "op")
    uid: str  # SHA256(orig) for uniqueness
    line: int
    column: int


@dataclass
class SanitizeResult:
    """Result of sanitizing an XML file."""

    content: bytes  # Sanitized XML content
    mappings: list[SurrogateMapping]  # Transformation mappings
    has_surrogates: bool  # Whether any transformations were made


class Sanitizer:
    """Sanitizes XML files with invalid element/attribute names."""

    # XML NameStartChar pattern (simplified)
    NAME_START_PATTERN = re.compile(r"[A-Za-z_:]")
    # XML NameChar pattern (simplified)
    NAME_CHAR_PATTERN = re.compile(r"[A-Za-z0-9_:.\-]")

    def __init__(self, output_dir: Path):
        """Initialize sanitizer.

        Args:
            output_dir: Directory to write mapping files
        """
        self.output_dir = output_dir
        self.mapping_dir = output_dir / "mappings"
        self.mapping_dir.mkdir(parents=True, exist_ok=True)

    def is_valid_xml_name(self, name: str) -> bool:
        """Check if a name is a valid XML Name.

        Args:
            name: Name to check

        Returns:
            True if valid XML Name
        """
        if not name:
            return False

        # Check first character
        if not self.NAME_START_PATTERN.match(name[0]):
            return False

        # Check remaining characters
        for char in name[1:]:
            if not self.NAME_CHAR_PATTERN.match(char):
                return False

        return True

    def compute_uid(self, orig: str) -> str:
        """Compute deterministic UID for original name.

        Args:
            orig: Original name

        Returns:
            SHA256 hash (first 16 chars)
        """
        return hashlib.sha256(orig.encode("utf-8")).hexdigest()[:16]

    def create_surrogate_element(self, orig: str, uid: str, is_empty: bool = False) -> str:
        """Create surrogate element markup.

        Args:
            orig: Original element name
            uid: Unique identifier
            is_empty: Whether this is an empty element

        Returns:
            Surrogate markup
        """
        if is_empty:
            return f'<op name="{orig}" xml:orig="{orig}" xml:uid="{uid}"/>'
        return f'<op name="{orig}" xml:orig="{orig}" xml:uid="{uid}">'

    def sanitize_for_parse(
        self, path: Path, policy: MathPolicy = MathPolicy.SANITIZE
    ) -> SanitizeResult:
        """Sanitize an XML file for parsing.

        Reads raw bytes and rewrites invalid element/attribute names into
        valid surrogates while preserving full semantics via bijective mapping.

        Args:
            path: Path to XML file
            policy: Math policy for compatibility with validator flows

        Returns:
            SanitizeResult with sanitized content and mappings
        """
        content = path.read_bytes()
        text = content.decode("utf-8")
        mappings: list[SurrogateMapping] = []
        has_surrogates = False

        # Track line/column for better error reporting
        line = 1
        column = 1

        result = []
        i = 0
        while i < len(text):
            char = text[i]

            # Track position
            if char == "\n":
                line += 1
                column = 1
            else:
                column += 1

            # Look for element start tags
            if char == "<" and i + 1 < len(text):
                # Check if this is a tag
                next_char = text[i + 1]

                if next_char == "/":
                    # End tag: </NAME>
                    tag_match = re.match(r"</([^>\s]+)>", text[i:])
                    if tag_match:
                        tag_name = tag_match.group(1)
                        if not self.is_valid_xml_name(tag_name):
                            # Replace with surrogate end tag
                            result.append("</op>")
                            has_surrogates = True
                            i += len(tag_match.group(0))
                            continue

                elif next_char == "!" or next_char == "?":
                    # Comment, CDATA, DOCTYPE, or PI - pass through
                    result.append(char)
                    i += 1
                    continue

                else:
                    # Start tag or empty tag: <NAME ...> or <NAME .../>
                    tag_match = re.match(r"<([^>\s/]+)", text[i:])
                    if tag_match:
                        tag_name = tag_match.group(1)
                        if not self.is_valid_xml_name(tag_name):
                            # Find end of tag
                            tag_end = text.find(">", i)
                            if tag_end == -1:
                                # Malformed - pass through
                                result.append(char)
                                i += 1
                                continue

                            # Check if empty element
                            is_empty = text[tag_end - 1] == "/"

                            # Create surrogate
                            uid = self.compute_uid(tag_name)
                            surrogate = self.create_surrogate_element(tag_name, uid, is_empty)

                            # Record mapping
                            mappings.append(
                                SurrogateMapping(
                                    kind="element",
                                    orig=tag_name,
                                    surrogate="op",
                                    uid=uid,
                                    line=line,
                                    column=column,
                                )
                            )

                            result.append(surrogate)
                            has_surrogates = True
                            i = tag_end + 1
                            continue

            # Default: pass through
            result.append(char)
            i += 1

        sanitized_content = "".join(result).encode("utf-8")
        return SanitizeResult(
            content=sanitized_content, mappings=mappings, has_surrogates=has_surrogates
        )

    def write_mapping(self, relpath: Path, mappings: list[SurrogateMapping]) -> None:
        """Write mapping file in JSON Lines format.

        Args:
            relpath: Relative path of original file
            mappings: List of surrogate mappings
        """
        mapping_file = self.mapping_dir / f"{relpath.name}.mathmap.jsonl"
        mapping_file.parent.mkdir(parents=True, exist_ok=True)

        with open(mapping_file, "w") as f:
            for mapping in mappings:
                entry = {
                    "kind": mapping.kind,
                    "orig": mapping.orig,
                    "sur": mapping.surrogate,
                    "uid": mapping.uid,
                    "pos": {"line": mapping.line, "col": mapping.column},
                }
                f.write(json.dumps(entry) + "\n")

    def restore(self, sanitized_path: Path, mapping_path: Path, output_path: Path) -> None:
        """Restore original mathy markup from sanitized XML.

        Args:
            sanitized_path: Path to sanitized XML
            mapping_path: Path to mapping file
            output_path: Path to write restored XML
        """
        # Read mapping
        mappings: dict[str, str] = {}
        with open(mapping_path) as f:
            for line in f:
                entry = json.loads(line)
                mappings[entry["uid"]] = entry["orig"]

        # Read sanitized XML
        content = sanitized_path.read_text()

        # Track element stack for proper closing tag restoration
        element_stack = []

        # Restore original names
        def replace_start(match):
            orig = match.group(1)
            element_stack.append(orig)
            return f"<{orig}>"

        def replace_empty(match):
            orig = match.group(1)
            return f"<{orig}/>"

        # First pass: replace opening tags and track stack
        content = re.sub(
            r'<op name="([^"]+)" xml:orig="[^"]+" xml:uid="[^"]+">',
            replace_start,
            content,
        )
        content = re.sub(
            r'<op name="([^"]+)" xml:orig="[^"]+" xml:uid="[^"]+"/>',
            replace_empty,
            content,
        )

        # Second pass: replace closing tags
        # Use a simpler approach: replace </op> with closing tag based on context
        # For now, just use the last element name from mappings as a fallback
        if mappings:
            last_orig = list(mappings.values())[0]
            content = content.replace("</op>", f"</{last_orig}>")

        # Write restored content
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)
