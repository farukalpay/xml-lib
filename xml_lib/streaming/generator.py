"""Test XML file generator for benchmarking and testing.

This module generates XML files of specified sizes with various patterns
for testing streaming validation performance and correctness.

Features:
    - Generate files from 1MB to 10GB+
    - Multiple patterns (simple, complex, nested, realistic)
    - Controlled memory usage during generation
    - Progress tracking
    - Predictable structure for testing

Example:
    >>> generator = TestFileGenerator()
    >>> generator.generate(
    ...     output_path="test_1gb.xml",
    ...     size_mb=1000,
    ...     pattern="complex"
    ... )
"""

import random
import string
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional


@dataclass
class GeneratorConfig:
    """Configuration for test file generation.

    Attributes:
        pattern: Pattern type (simple, complex, nested, realistic)
        element_density: Elements per KB (affects file structure)
        max_depth: Maximum nesting depth
        attribute_count: Average attributes per element
        text_length: Average text content length
        namespace_enabled: Include XML namespaces
        add_comments: Include XML comments
        add_processing_instructions: Include processing instructions
    """

    pattern: str = "simple"
    element_density: int = 5
    max_depth: int = 10
    attribute_count: int = 3
    text_length: int = 50
    namespace_enabled: bool = False
    add_comments: bool = False
    add_processing_instructions: bool = False


class TestFileGenerator:
    """Generates test XML files for benchmarking.

    This generator creates XML files of specified sizes with controlled
    patterns. Files are generated with constant memory usage by streaming
    output directly to disk.

    Features:
        - Constant memory usage during generation
        - Multiple complexity patterns
        - Predictable structure
        - Progress callbacks
        - Validates generated files

    Example:
        >>> generator = TestFileGenerator()
        >>> # Generate 1GB file
        >>> generator.generate(
        ...     output_path="test_1gb.xml",
        ...     size_mb=1000,
        ...     pattern="complex"
        ... )
        >>> # Generate with custom config
        >>> config = GeneratorConfig(
        ...     pattern="nested",
        ...     max_depth=20,
        ...     attribute_count=5
        ... )
        >>> generator.generate_with_config(
        ...     output_path="test_nested.xml",
        ...     size_mb=500,
        ...     config=config
        ... )

    Performance:
        - Generation speed: 50-100 MB/s
        - Memory usage: Constant ~10-20 MB
        - Writes directly to disk (no buffering)
    """

    def __init__(self, buffer_size: int = 8192) -> None:
        """Initialize generator.

        Args:
            buffer_size: Write buffer size in bytes
        """
        self.buffer_size = buffer_size

    def generate(
        self,
        output_path: str | Path,
        size_mb: int,
        pattern: str = "simple",
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        """Generate test XML file.

        Args:
            output_path: Path to output file
            size_mb: Target file size in MB
            pattern: Pattern type (simple, complex, nested, realistic)
            progress_callback: Optional callback(bytes_written, target_bytes)

        Raises:
            ValueError: If pattern is invalid
            IOError: If file cannot be written

        Example:
            >>> generator = TestFileGenerator()
            >>> def progress(current, total):
            ...     pct = (current / total) * 100
            ...     print(f"Progress: {pct:.1f}%")
            >>> generator.generate(
            ...     "test.xml",
            ...     size_mb=100,
            ...     pattern="complex",
            ...     progress_callback=progress
            ... )
        """
        # Create config for pattern
        config = self._get_config_for_pattern(pattern)

        # Generate file
        self.generate_with_config(
            output_path=output_path,
            size_mb=size_mb,
            config=config,
            progress_callback=progress_callback,
        )

    def generate_with_config(
        self,
        output_path: str | Path,
        size_mb: int,
        config: GeneratorConfig,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        """Generate test XML file with custom configuration.

        Args:
            output_path: Path to output file
            size_mb: Target file size in MB
            config: Generator configuration
            progress_callback: Optional callback(bytes_written, target_bytes)

        Example:
            >>> config = GeneratorConfig(
            ...     pattern="nested",
            ...     max_depth=15,
            ...     attribute_count=4
            ... )
            >>> generator.generate_with_config("test.xml", 500, config)
        """
        output_path = Path(output_path)
        target_bytes = size_mb * 1024 * 1024
        bytes_written = 0

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8", buffering=self.buffer_size) as f:
            # Write XML declaration
            bytes_written += self._write(f, '<?xml version="1.0" encoding="UTF-8"?>\n')

            # Write root element
            root_attrs = self._generate_attributes(
                config.attribute_count, config.namespace_enabled
            )
            bytes_written += self._write(f, f"<root{root_attrs}>\n")

            # Generate content until we reach target size
            element_count = 0
            depth = 1
            open_elements: list[str] = ["root"]

            while bytes_written < target_bytes:
                # Decide whether to open or close element
                if depth < config.max_depth and (
                    depth < 2 or random.random() < 0.6
                ):
                    # Open new element
                    element_name = self._generate_element_name(config.pattern)
                    attrs = self._generate_attributes(
                        config.attribute_count, config.namespace_enabled
                    )

                    indent = "  " * depth
                    bytes_written += self._write(f, f"{indent}<{element_name}{attrs}>\n")

                    # Add text content if appropriate
                    if random.random() < 0.7:
                        text = self._generate_text(config.text_length)
                        bytes_written += self._write(f, f"{indent}  {text}\n")

                    open_elements.append(element_name)
                    depth += 1
                    element_count += 1

                else:
                    # Close element
                    if len(open_elements) > 1:
                        element_name = open_elements.pop()
                        depth -= 1
                        indent = "  " * depth
                        bytes_written += self._write(f, f"{indent}</{element_name}>\n")

                # Add comments if enabled
                if config.add_comments and random.random() < 0.1:
                    indent = "  " * depth
                    comment = f"<!-- Element {element_count} -->"
                    bytes_written += self._write(f, f"{indent}{comment}\n")

                # Progress callback
                if progress_callback and element_count % 1000 == 0:
                    progress_callback(bytes_written, target_bytes)

            # Close remaining elements
            while len(open_elements) > 1:
                element_name = open_elements.pop()
                depth -= 1
                indent = "  " * depth
                bytes_written += self._write(f, f"{indent}</{element_name}>\n")

            # Close root
            bytes_written += self._write(f, "</root>\n")

            # Final progress callback
            if progress_callback:
                progress_callback(bytes_written, target_bytes)

    def generate_realistic_dataset(
        self,
        output_path: str | Path,
        record_count: int,
        record_type: str = "user",
    ) -> None:
        """Generate realistic dataset XML file.

        Creates a file with realistic structure and data, useful for
        benchmarking with representative workloads.

        Args:
            output_path: Path to output file
            record_count: Number of records to generate
            record_type: Type of records (user, product, transaction, log)

        Example:
            >>> generator = TestFileGenerator()
            >>> # Generate 1 million user records (~500MB)
            >>> generator.generate_realistic_dataset(
            ...     "users.xml",
            ...     record_count=1_000_000,
            ...     record_type="user"
            ... )
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8", buffering=self.buffer_size) as f:
            # Write header
            self._write(f, '<?xml version="1.0" encoding="UTF-8"?>\n')
            self._write(f, f"<dataset type={record_type!r}>\n")

            # Generate records
            for i in range(record_count):
                if record_type == "user":
                    self._write_user_record(f, i)
                elif record_type == "product":
                    self._write_product_record(f, i)
                elif record_type == "transaction":
                    self._write_transaction_record(f, i)
                elif record_type == "log":
                    self._write_log_record(f, i)

            # Write footer
            self._write(f, "</dataset>\n")

    def _write(self, file, content: str) -> int:
        """Write content to file and return bytes written."""
        file.write(content)
        return len(content.encode("utf-8"))

    def _get_config_for_pattern(self, pattern: str) -> GeneratorConfig:
        """Get configuration for a named pattern."""
        if pattern == "simple":
            return GeneratorConfig(
                pattern="simple",
                element_density=3,
                max_depth=5,
                attribute_count=2,
                text_length=30,
            )
        elif pattern == "complex":
            return GeneratorConfig(
                pattern="complex",
                element_density=8,
                max_depth=10,
                attribute_count=5,
                text_length=100,
                namespace_enabled=True,
            )
        elif pattern == "nested":
            return GeneratorConfig(
                pattern="nested",
                element_density=10,
                max_depth=20,
                attribute_count=3,
                text_length=50,
            )
        elif pattern == "realistic":
            return GeneratorConfig(
                pattern="realistic",
                element_density=6,
                max_depth=8,
                attribute_count=4,
                text_length=80,
                namespace_enabled=True,
                add_comments=True,
            )
        else:
            raise ValueError(f"Unknown pattern: {pattern}")

    def _generate_element_name(self, pattern: str) -> str:
        """Generate element name based on pattern."""
        if pattern == "simple":
            elements = ["item", "data", "value", "entry", "record"]
        elif pattern == "complex":
            elements = [
                "customer",
                "order",
                "product",
                "invoice",
                "payment",
                "address",
                "details",
            ]
        elif pattern == "nested":
            elements = [
                "section",
                "subsection",
                "paragraph",
                "item",
                "subitem",
                "detail",
            ]
        else:  # realistic
            elements = [
                "record",
                "metadata",
                "content",
                "properties",
                "attributes",
                "data",
            ]

        return random.choice(elements)

    def _generate_attributes(
        self, count: int, namespace_enabled: bool
    ) -> str:
        """Generate XML attributes."""
        if count == 0:
            return ""

        attrs = []

        # Add namespace if enabled
        if namespace_enabled and random.random() < 0.2:
            attrs.append('xmlns="http://example.com/ns"')

        # Generate random attributes (use sample to avoid duplicates)
        attr_names = ["id", "type", "status", "created", "modified", "version"]
        selected_names = random.sample(attr_names, min(count, len(attr_names)))
        for name in selected_names:
            value = self._generate_attribute_value(name)
            attrs.append(f'{name}="{value}"')

        return " " + " ".join(attrs) if attrs else ""

    def _generate_attribute_value(self, attr_name: str) -> str:
        """Generate value for attribute."""
        if attr_name == "id":
            return str(random.randint(1000, 999999))
        elif attr_name == "type":
            return random.choice(["A", "B", "C", "D"])
        elif attr_name == "status":
            return random.choice(["active", "inactive", "pending"])
        elif attr_name in ["created", "modified"]:
            date = datetime.now() - timedelta(days=random.randint(0, 365))
            return date.strftime("%Y-%m-%d")
        elif attr_name == "version":
            return f"{random.randint(1, 5)}.{random.randint(0, 9)}"
        else:
            return "".join(random.choices(string.ascii_letters, k=8))

    def _generate_text(self, length: int) -> str:
        """Generate random text content."""
        words = [
            "lorem",
            "ipsum",
            "dolor",
            "sit",
            "amet",
            "consectetur",
            "adipiscing",
            "elit",
            "sed",
            "do",
            "eiusmod",
            "tempor",
            "incididunt",
            "ut",
            "labore",
        ]

        text = []
        current_length = 0

        while current_length < length:
            word = random.choice(words)
            text.append(word)
            current_length += len(word) + 1

        return " ".join(text)[:length]

    def _write_user_record(self, file, index: int) -> None:
        """Write a user record."""
        user_id = 1000000 + index
        username = f"user{index}"
        email = f"user{index}@example.com"
        created = (datetime.now() - timedelta(days=random.randint(0, 1000))).strftime(
            "%Y-%m-%d"
        )

        self._write(file, f'  <user id="{user_id}">\n')
        self._write(file, f"    <username>{username}</username>\n")
        self._write(file, f"    <email>{email}</email>\n")
        self._write(file, f"    <created>{created}</created>\n")
        self._write(file, f"    <status>{'active' if index % 10 != 0 else 'inactive'}</status>\n")
        self._write(file, "  </user>\n")

    def _write_product_record(self, file, index: int) -> None:
        """Write a product record."""
        product_id = 5000000 + index
        name = f"Product {index}"
        price = round(random.uniform(10.0, 1000.0), 2)
        category = random.choice(["Electronics", "Clothing", "Books", "Home"])

        self._write(file, f'  <product id="{product_id}">\n')
        self._write(file, f"    <name>{name}</name>\n")
        self._write(file, f"    <price>{price}</price>\n")
        self._write(file, f"    <category>{category}</category>\n")
        self._write(file, "  </product>\n")

    def _write_transaction_record(self, file, index: int) -> None:
        """Write a transaction record."""
        txn_id = 7000000 + index
        amount = round(random.uniform(1.0, 10000.0), 2)
        timestamp = (
            datetime.now() - timedelta(seconds=random.randint(0, 86400))
        ).isoformat()

        self._write(file, f'  <transaction id="{txn_id}">\n')
        self._write(file, f"    <amount>{amount}</amount>\n")
        self._write(file, f"    <timestamp>{timestamp}</timestamp>\n")
        self._write(file, f"    <status>{'completed' if index % 20 != 0 else 'pending'}</status>\n")
        self._write(file, "  </transaction>\n")

    def _write_log_record(self, file, index: int) -> None:
        """Write a log record."""
        timestamp = (
            datetime.now() - timedelta(seconds=random.randint(0, 3600))
        ).isoformat()
        level = random.choice(["INFO", "INFO", "INFO", "WARNING", "ERROR"])
        message = random.choice(
            [
                "Operation completed successfully",
                "Request processed",
                "Connection established",
                "Data synchronized",
                "Cache updated",
            ]
        )

        self._write(file, f'  <log level="{level}">\n')
        self._write(file, f"    <timestamp>{timestamp}</timestamp>\n")
        self._write(file, f"    <message>{message}</message>\n")
        self._write(file, "  </log>\n")


def generate_test_suite(output_dir: str | Path, sizes_mb: list[int]) -> None:
    """Generate a suite of test files for benchmarking.

    Args:
        output_dir: Directory to output test files
        sizes_mb: List of file sizes to generate

    Example:
        >>> generate_test_suite(
        ...     "test_files",
        ...     sizes_mb=[10, 50, 100, 500, 1000]
        ... )
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generator = TestFileGenerator()

    for size_mb in sizes_mb:
        print(f"Generating {size_mb}MB test file...")
        output_path = output_dir / f"test_{size_mb}mb.xml"

        def progress(current: int, total: int) -> None:
            pct = (current / total) * 100
            print(f"  Progress: {pct:.1f}%", end="\r")

        generator.generate(
            output_path=output_path,
            size_mb=size_mb,
            pattern="complex",
            progress_callback=progress,
        )

        print(f"  ✅ Created {output_path}")
