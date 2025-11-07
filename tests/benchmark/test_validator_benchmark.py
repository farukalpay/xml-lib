"""Performance benchmarks for xml-lib components."""

import pytest
from pathlib import Path
from xml_lib.validator import Validator
from xml_lib.publisher import Publisher
from xml_lib.differ import Differ


@pytest.fixture
def validator():
    """Create validator for benchmarks."""
    return Validator(
        schemas_dir=Path("schemas"),
        guardrails_dir=Path("guardrails"),
        telemetry=None,
    )


@pytest.fixture
def publisher():
    """Create publisher for benchmarks."""
    return Publisher(xslt_dir=Path("schemas/xslt"), telemetry=None)


@pytest.fixture
def differ():
    """Create differ for benchmarks."""
    return Differ(schemas_dir=Path("schemas"), telemetry=None)


@pytest.fixture
def valid_xml(tmp_path):
    """Create a valid XML file for benchmarks."""
    xml_file = tmp_path / "benchmark.xml"
    xml_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<document timestamp="2025-01-01T00:00:00Z" checksum="sha256:abc123">
  <meta>
    <title>Benchmark Document</title>
  </meta>
  <phases>
    <phase name="begin" timestamp="2025-01-01T00:00:00Z">
      <payload>Initial phase</payload>
    </phase>
  </phases>
</document>
"""
    )
    return xml_file


def test_validator_parse_xml(benchmark, validator, valid_xml):
    """Benchmark XML parsing performance."""

    def parse():
        from lxml import etree

        etree.parse(str(valid_xml))

    benchmark(parse)


def test_validator_validate_single_file(benchmark, validator, valid_xml):
    """Benchmark validation of a single XML file."""

    def validate():
        validator._validate_file(valid_xml)

    benchmark(validate)


def test_validator_validate_project(benchmark, validator, tmp_path, valid_xml):
    """Benchmark full project validation."""
    # Create a small project
    project = tmp_path / "project"
    project.mkdir()
    for i in range(5):
        (project / f"doc_{i}.xml").write_text(valid_xml.read_text())

    def validate():
        validator.validate_project(project)

    benchmark(validate)


def test_publisher_transform_single(benchmark, publisher, tmp_path, valid_xml):
    """Benchmark XSLT transformation of a single file."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    def transform():
        publisher.publish(valid_xml.parent, output_dir)

    benchmark(transform)


def test_differ_compare_identical(benchmark, differ, valid_xml, tmp_path):
    """Benchmark diff of identical files."""
    xml_file2 = tmp_path / "benchmark2.xml"
    xml_file2.write_text(valid_xml.read_text())

    def diff():
        differ.diff(valid_xml, xml_file2)

    benchmark(diff)


def test_storage_content_addressing(benchmark, tmp_path):
    """Benchmark content-addressed storage operations."""
    from xml_lib.storage import ContentStore

    store = ContentStore(tmp_path / "store")
    data = b"benchmark data" * 1000

    def store_data():
        store.store(data, "benchmark.bin")

    benchmark(store_data)


def test_guardrails_rule_compilation(benchmark):
    """Benchmark guardrail rule compilation."""
    from xml_lib.guardrails import GuardrailEngine

    engine = GuardrailEngine(Path("guardrails"))

    def compile_rules():
        engine._load_guardrails()

    benchmark(compile_rules)
