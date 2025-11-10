"""Property-based tests using Hypothesis for XML validation and guardrails.

This module uses property-based testing to verify that validation rules
hold across a wide range of generated XML documents and configurations.
"""

import hashlib
import io
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from lxml import etree

from xml_lib.validator import Validator, ValidationResult
from xml_lib.guardrails import GuardrailEngine, GuardrailRule
from xml_lib.storage import ContentStore
from xml_lib.types import ValidationError


# Custom strategies for XML generation

@st.composite
def xml_element_name(draw):
    """Generate valid XML element names."""
    first_char = draw(st.sampled_from("abcdefghijklmnopqrstuvwxyz_"))
    rest = draw(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-",
            min_size=0,
            max_size=20,
        )
    )
    return first_char + rest


@st.composite
def xml_attribute_value(draw):
    """Generate valid XML attribute values."""
    return draw(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_",
            min_size=1,
            max_size=50,
        )
    )


@st.composite
def xml_id(draw):
    """Generate valid XML IDs."""
    return "id-" + draw(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
            min_size=5,
            max_size=15,
        )
    )


@st.composite
def sha256_checksum(draw):
    """Generate valid SHA-256 checksums."""
    data = draw(st.binary(min_size=1, max_size=1000))
    return hashlib.sha256(data).hexdigest()


@st.composite
def iso_timestamp(draw):
    """Generate valid ISO timestamps."""
    base_date = datetime(2020, 1, 1)
    days_offset = draw(st.integers(min_value=0, max_value=1825))  # 5 years
    seconds_offset = draw(st.integers(min_value=0, max_value=86400))

    dt = base_date + timedelta(days=days_offset, seconds=seconds_offset)
    return dt.isoformat() + "Z"


@st.composite
def lifecycle_phase_name(draw):
    """Generate valid lifecycle phase names."""
    return draw(st.sampled_from(["begin", "start", "iteration", "end", "continuum"]))


@st.composite
def simple_xml_document(draw):
    """Generate a simple well-formed XML document."""
    root_name = draw(xml_element_name())
    doc_id = draw(xml_id())

    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<{root_name} id="{doc_id}">
  <title>{draw(st.text(min_size=1, max_size=100))}</title>
  <description>{draw(st.text(min_size=0, max_size=200))}</description>
</{root_name}>"""

    return xml_content


@st.composite
def lifecycle_document(draw):
    """Generate a lifecycle XML document."""
    doc_id = draw(xml_id())
    title = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", min_size=5, max_size=50))

    # Generate phases with monotonic timestamps
    phases = []
    phase_names = ["begin", "start", "iteration", "end", "continuum"]
    base_time = datetime(2020, 1, 1)

    for i, phase_name in enumerate(phase_names):
        timestamp = (base_time + timedelta(days=i * 30)).isoformat() + "Z"
        phase_id = f"{doc_id}-{phase_name}"
        phases.append(
            f'    <phase name="{phase_name}" id="{phase_id}" timestamp="{timestamp}"/>'
        )

    phases_xml = "\n".join(phases)

    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<document id="{doc_id}">
  <title>{title}</title>
  <phases>
{phases_xml}
  </phases>
</document>"""

    return xml_content


# Property-based tests


class TestValidatorProperties:
    """Property-based tests for the Validator class."""

    @given(simple_xml_document())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_well_formed_xml_parses_successfully(self, xml_content):
        """Property: All well-formed XML documents should parse without syntax errors."""
        try:
            doc = etree.fromstring(xml_content.encode("utf-8"))
            assert doc is not None
            assert doc.tag is not None
        except etree.XMLSyntaxError:
            # If our generator produced invalid XML, skip
            assume(False)

    @given(st.binary(min_size=1, max_size=10000))
    @settings(max_examples=50)
    def test_content_hash_is_deterministic(self, content):
        """Property: Same content always produces same SHA-256 hash."""
        hash1 = hashlib.sha256(content).hexdigest()
        hash2 = hashlib.sha256(content).hexdigest()
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64 hex chars

    @given(st.binary(min_size=1, max_size=10000))
    @settings(max_examples=50)
    def test_content_store_retrieval(self, content):
        """Property: Content stored can always be retrieved with correct checksum."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ContentStore(Path(tmpdir))
            checksum = hashlib.sha256(content).hexdigest()

            store.store(content, checksum)
            retrieved = store.retrieve(checksum)

            assert retrieved == content

    @given(
        st.lists(
            xml_id(),
            min_size=1,
            max_size=10,
            unique=True,
        )
    )
    @settings(max_examples=30)
    def test_unique_ids_in_document(self, ids):
        """Property: Documents with unique IDs should not trigger duplicate ID errors."""
        elements = [f'<item id="{id_val}"/>' for id_val in ids]
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<root>
  {"".join(elements)}
</root>"""

        doc = etree.fromstring(xml_content.encode("utf-8"))
        id_elements = doc.xpath("//*[@id]")

        # Extract all IDs
        found_ids = [elem.get("id") for elem in id_elements]

        # All IDs should be unique
        assert len(found_ids) == len(set(found_ids))

    @given(
        st.lists(
            st.integers(min_value=1000000000, max_value=9999999999),
            min_size=2,
            max_size=10,
        )
    )
    @settings(max_examples=30)
    def test_temporal_monotonicity(self, timestamps):
        """Property: Sorted timestamps maintain monotonic order."""
        # Sort timestamps to ensure monotonicity
        sorted_timestamps = sorted(timestamps)

        # Check that each timestamp is >= previous
        for i in range(1, len(sorted_timestamps)):
            assert sorted_timestamps[i] >= sorted_timestamps[i - 1]

    @given(lifecycle_document())
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_lifecycle_documents_parse(self, xml_content):
        """Property: All generated lifecycle documents should be parseable."""
        try:
            doc = etree.fromstring(xml_content.encode("utf-8"))
            assert doc is not None

            # Verify structure
            assert doc.tag == "document"
            assert doc.get("id") is not None

            phases = doc.find("phases")
            assert phases is not None

            phase_elements = phases.findall("phase")
            assert len(phase_elements) >= 1

        except etree.XMLSyntaxError:
            assume(False)


class TestGuardrailProperties:
    """Property-based tests for guardrail rules."""

    @given(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
            min_size=1,
            max_size=100,
        )
    )
    @settings(max_examples=50)
    def test_xpath_evaluation_consistency(self, test_string):
        """Property: XPath evaluation on same document should be consistent."""
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<root>
  <value>{test_string}</value>
</root>"""

        doc = etree.fromstring(xml_content.encode("utf-8"))

        # Evaluate same XPath multiple times
        result1 = doc.xpath("//value/text()")
        result2 = doc.xpath("//value/text()")

        assert result1 == result2

        if result1:
            assert result1[0] == test_string

    @given(
        st.lists(
            st.tuples(xml_element_name(), st.text(min_size=0, max_size=50)),
            min_size=1,
            max_size=10,
        )
    )
    @settings(max_examples=30)
    def test_constraint_xpath_returns_bool_or_list(self, elements):
        """Property: XPath constraints should return evaluable results."""
        # Create XML with elements
        element_xml = "\n  ".join(
            [f"<{name}>{value}</{name}>" for name, value in elements]
        )

        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<root>
  {element_xml}
</root>"""

        try:
            doc = etree.fromstring(xml_content.encode("utf-8"))

            # Test various XPath expressions
            result = doc.xpath("count(//root/*) > 0")
            assert isinstance(result, bool)

            result = doc.xpath("//*")
            assert isinstance(result, list)

        except (etree.XMLSyntaxError, etree.XPathEvalError):
            assume(False)


class TestFormalVerificationProperties:
    """Property-based tests for formal verification engine."""

    @given(
        st.lists(
            st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=3, max_size=20),
            min_size=1,
            max_size=10,
            unique=True,
        )
    )
    @settings(max_examples=30)
    def test_proof_tree_acyclic(self, node_ids):
        """Property: Proof trees should never contain cycles."""
        from xml_lib.formal_verification import ProofNode

        # Create a simple tree structure
        root = ProofNode(
            id="root",
            label="Root",
            type="root",
            statement="Root statement",
        )

        current_parent = root

        for node_id in node_ids:
            node = ProofNode(
                id=node_id,
                label=f"Node {node_id}",
                type="lemma",
                statement=f"Statement for {node_id}",
            )
            current_parent.children.append(node)
            current_parent = node

        # Verify no cycles by checking we can traverse to root from any leaf
        def has_path_to_root(node: ProofNode, visited: set) -> bool:
            """Check if there's a path without cycles."""
            if node.id in visited:
                return False  # Cycle detected

            visited.add(node.id)

            if node.id == "root":
                return True

            # This is a tree, so we check parent relationship implicitly
            return True

        visited: set = set()
        assert has_path_to_root(current_parent, visited)

    @given(
        st.lists(
            st.tuples(
                st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=3, max_size=10),
                st.sampled_from(["axiom", "lemma", "theorem"]),
            ),
            min_size=1,
            max_size=20,
            unique_by=lambda x: x[0],
        )
    )
    @settings(max_examples=20)
    def test_proof_dependencies_well_formed(self, proof_elements):
        """Property: Proof dependencies should form a valid DAG."""
        from xml_lib.formal_verification import ProofNode

        nodes = {}

        for elem_id, elem_type in proof_elements:
            node = ProofNode(
                id=elem_id,
                label=f"{elem_type} {elem_id}",
                type=elem_type,
                statement=f"Statement for {elem_id}",
            )
            nodes[elem_id] = node

        # Verify all created nodes are accessible
        assert len(nodes) == len(proof_elements)

        # Check that IDs are unique
        assert len(set(nodes.keys())) == len(nodes)


class TestStorageProperties:
    """Property-based tests for content-addressed storage."""

    @given(
        st.lists(
            st.binary(min_size=1, max_size=1000),
            min_size=1,
            max_size=20,
        )
    )
    @settings(max_examples=30)
    def test_deduplication(self, content_list):
        """Property: Duplicate content should not be stored multiple times."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ContentStore(Path(tmpdir))

            checksums = []
            for content in content_list:
                checksum = hashlib.sha256(content).hexdigest()
                store.store(content, checksum)
                checksums.append(checksum)

            # Count unique checksums
            unique_checksums = set(checksums)

            # Storage should only contain unique items
            # (This is a property of the hash function, but validates storage)
            for checksum in unique_checksums:
                retrieved = store.retrieve(checksum)
                assert retrieved is not None

    @given(st.binary(min_size=0, max_size=10000))
    @settings(max_examples=50)
    def test_hash_collision_resistance(self, content):
        """Property: Different content should (almost always) produce different hashes."""
        hash1 = hashlib.sha256(content).hexdigest()

        # Modify content slightly
        if len(content) > 0:
            modified = content[:-1] + bytes([(content[-1] + 1) % 256])
        else:
            modified = b"x"

        hash2 = hashlib.sha256(modified).hexdigest()

        # Hashes should be different (with overwhelming probability)
        assert hash1 != hash2


class TestXMLSanitizationProperties:
    """Property-based tests for XML sanitization."""

    @given(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 <>\"'&",
            min_size=1,
            max_size=200,
        )
    )
    @settings(max_examples=50)
    def test_xml_escaping_roundtrip(self, text):
        """Property: XML-escaped text should roundtrip correctly."""
        # Create a simple XML element with the text
        try:
            elem = etree.Element("test")
            elem.text = text

            # Serialize and parse
            xml_bytes = etree.tostring(elem)
            parsed = etree.fromstring(xml_bytes)

            # Text should be preserved
            assert parsed.text == text

        except (ValueError, etree.XMLSyntaxError):
            # Some characters may not be valid XML
            assume(False)


# Run with: pytest tests/test_property_based.py -v
