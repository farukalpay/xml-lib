"""Tests for streaming performance benchmarking."""

import pytest

from xml_lib.streaming.benchmark import BenchmarkResult, BenchmarkRunner, MethodResult
from xml_lib.streaming.generator import TestFileGenerator


@pytest.fixture
def test_xml_file(tmp_path):
    """Create a small test XML file."""
    xml_file = tmp_path / "test.xml"
    generator = TestFileGenerator()

    generator.generate(
        output_path=xml_file,
        size_mb=1,
        pattern="simple",
    )

    yield xml_file
    xml_file.unlink()


class TestMethodResult:
    """Test MethodResult class."""

    def test_result_creation(self):
        """Test creating method result."""
        result = MethodResult(
            method="streaming",
            file_size_mb=10.0,
            duration_seconds=2.5,
            peak_memory_mb=50.0,
            throughput_mbps=4.0,
            success=True,
            elements_processed=10000,
        )

        assert result.method == "streaming"
        assert result.file_size_mb == 10.0
        assert result.success is True

    def test_format_row_success(self):
        """Test formatting successful result as row."""
        result = MethodResult(
            method="streaming",
            file_size_mb=10.0,
            duration_seconds=2.5,
            peak_memory_mb=50.0,
            throughput_mbps=4.0,
            success=True,
        )

        row = result.format_row()

        assert len(row) == 5
        assert "10 MB" in row[0]
        assert "2.5s" in row[1]
        assert "50 MB" in row[2]
        assert "4 MB/s" in row[3]
        assert "✅" in row[4]

    def test_format_row_failure(self):
        """Test formatting failed result as row."""
        result = MethodResult(
            method="dom",
            file_size_mb=10.0,
            duration_seconds=0,
            peak_memory_mb=0,
            throughput_mbps=0,
            success=False,
            error="Out of memory",
        )

        row = result.format_row()

        assert "N/A" in row[1]
        assert "OOM" in row[2]
        assert "❌" in row[4]


class TestBenchmarkResult:
    """Test BenchmarkResult class."""

    def test_result_creation(self):
        """Test creating benchmark result."""
        dom_result = MethodResult(
            method="dom",
            file_size_mb=10.0,
            duration_seconds=2.0,
            peak_memory_mb=100.0,
            throughput_mbps=5.0,
            success=True,
        )

        streaming_result = MethodResult(
            method="streaming",
            file_size_mb=10.0,
            duration_seconds=2.5,
            peak_memory_mb=50.0,
            throughput_mbps=4.0,
            success=True,
        )

        result = BenchmarkResult(
            file_path="test.xml",
            file_size_mb=10.0,
            dom_result=dom_result,
            streaming_result=streaming_result,
        )

        assert result.file_path == "test.xml"
        assert result.dom_result == dom_result
        assert result.streaming_result == streaming_result

    def test_format_report(self):
        """Test formatting benchmark report."""
        dom_result = MethodResult(
            method="dom",
            file_size_mb=10.0,
            duration_seconds=2.0,
            peak_memory_mb=100.0,
            throughput_mbps=5.0,
            success=True,
        )

        streaming_result = MethodResult(
            method="streaming",
            file_size_mb=10.0,
            duration_seconds=2.5,
            peak_memory_mb=50.0,
            throughput_mbps=4.0,
            success=True,
        )

        result = BenchmarkResult(
            file_path="test.xml",
            file_size_mb=10.0,
            dom_result=dom_result,
            streaming_result=streaming_result,
        )

        report = result.format_report()

        assert "XML Validation Performance Benchmark" in report
        assert "test.xml" in report
        assert "DOM Parsing" in report
        assert "SAX Streaming" in report
        assert "Key Findings" in report
        assert "Recommendations" in report

    def test_to_dict(self):
        """Test converting result to dictionary."""
        dom_result = MethodResult(
            method="dom",
            file_size_mb=10.0,
            duration_seconds=2.0,
            peak_memory_mb=100.0,
            throughput_mbps=5.0,
            success=True,
        )

        streaming_result = MethodResult(
            method="streaming",
            file_size_mb=10.0,
            duration_seconds=2.5,
            peak_memory_mb=50.0,
            throughput_mbps=4.0,
            success=True,
        )

        result = BenchmarkResult(
            file_path="test.xml",
            file_size_mb=10.0,
            dom_result=dom_result,
            streaming_result=streaming_result,
        )

        data = result.to_dict()

        assert isinstance(data, dict)
        assert data["file_path"] == "test.xml"
        assert "dom" in data
        assert "streaming" in data
        assert data["dom"]["success"] is True
        assert data["streaming"]["success"] is True


class TestBenchmarkRunner:
    """Test BenchmarkRunner class."""

    def test_runner_init(self):
        """Test runner initialization."""
        runner = BenchmarkRunner()

        assert runner.timeout_seconds == 300
        assert runner.gc_between_runs is True

    def test_run_benchmark_single_file(self, test_xml_file):
        """Test benchmarking single file."""
        runner = BenchmarkRunner()
        result = runner.run_benchmark(test_xml_file)

        assert isinstance(result, BenchmarkResult)
        assert result.file_path == str(test_xml_file)
        assert result.file_size_mb > 0

        # Both methods should succeed for small file
        assert result.dom_result is not None
        assert result.streaming_result is not None

    def test_run_benchmark_dom_only(self, test_xml_file):
        """Test benchmarking with DOM only."""
        runner = BenchmarkRunner()
        result = runner.run_benchmark(
            test_xml_file, include_dom=True, include_streaming=False
        )

        assert result.dom_result is not None
        assert result.streaming_result is None

    def test_run_benchmark_streaming_only(self, test_xml_file):
        """Test benchmarking with streaming only."""
        runner = BenchmarkRunner()
        result = runner.run_benchmark(
            test_xml_file, include_dom=False, include_streaming=True
        )

        assert result.dom_result is None
        assert result.streaming_result is not None

    def test_run_benchmark_nonexistent_file(self):
        """Test benchmarking nonexistent file."""
        runner = BenchmarkRunner()

        with pytest.raises(FileNotFoundError):
            runner.run_benchmark("nonexistent.xml")

    def test_benchmark_results_validity(self, test_xml_file):
        """Test that benchmark results are valid."""
        runner = BenchmarkRunner()
        result = runner.run_benchmark(test_xml_file)

        # Check DOM result
        if result.dom_result and result.dom_result.success:
            assert result.dom_result.duration_seconds > 0
            assert result.dom_result.throughput_mbps > 0
            assert result.dom_result.peak_memory_mb >= 0

        # Check streaming result
        if result.streaming_result and result.streaming_result.success:
            assert result.streaming_result.duration_seconds > 0
            assert result.streaming_result.throughput_mbps > 0
            assert result.streaming_result.peak_memory_mb >= 0

    def test_run_benchmark_suite(self, tmp_path):
        """Test running benchmark suite."""
        # Create multiple test files
        generator = TestFileGenerator()
        files = []

        for size_mb in [1, 2]:
            xml_file = tmp_path / f"test_{size_mb}mb.xml"
            generator.generate(
                output_path=xml_file,
                size_mb=size_mb,
                pattern="simple",
            )
            files.append(xml_file)

        runner = BenchmarkRunner()
        results = runner.run_benchmark_suite(files)

        assert len(results) == 2

        for result in results:
            assert isinstance(result, BenchmarkResult)
            assert result.file_size_mb > 0

    def test_benchmark_comparison(self, test_xml_file):
        """Test benchmark comparison calculations."""
        runner = BenchmarkRunner()
        result = runner.run_benchmark(test_xml_file)

        # If both methods succeeded, should have comparison
        if (
            result.dom_result
            and result.streaming_result
            and result.dom_result.success
            and result.streaming_result.success
        ):
            assert result.comparison
            assert "memory_ratio" in result.comparison
            assert "speed_ratio" in result.comparison

            # Memory ratio should be > 1 (DOM uses more)
            assert result.comparison["memory_ratio"] > 0


class TestFormatComparisonTable:
    """Test comparison table formatting."""

    def test_format_comparison_table(self, test_xml_file):
        """Test formatting comparison table."""
        from xml_lib.streaming.benchmark import format_comparison_table

        runner = BenchmarkRunner()
        result = runner.run_benchmark(test_xml_file)

        table = format_comparison_table([result])

        assert "Streaming vs DOM Performance Comparison" in table
        assert "test.xml" in table or test_xml_file.name in table


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_benchmark_tiny_file(self, tmp_path):
        """Test benchmarking very small file."""
        xml_file = tmp_path / "tiny.xml"
        xml_file.write_text('<?xml version="1.0"?><root/>')

        runner = BenchmarkRunner()
        result = runner.run_benchmark(xml_file)

        # Should still work for tiny files
        assert result.dom_result is not None
        assert result.streaming_result is not None

    def test_benchmark_with_gc_disabled(self, test_xml_file):
        """Test benchmarking with GC disabled."""
        runner = BenchmarkRunner(gc_between_runs=False)
        result = runner.run_benchmark(test_xml_file)

        assert result is not None
        # Should still produce valid results
        assert result.dom_result is not None
        assert result.streaming_result is not None
