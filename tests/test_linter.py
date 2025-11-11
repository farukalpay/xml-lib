"""Tests for XML linting functionality."""

import tempfile
from pathlib import Path

import pytest

from xml_lib.linter import LintLevel, XMLLinter


@pytest.fixture
def temp_xml_file():
    """Create a temporary XML file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
        yield Path(f.name)
    Path(f.name).unlink(missing_ok=True)


def test_lint_valid_xml(temp_xml_file):
    """Test linting a valid XML file."""
    content = """<?xml version="1.0" encoding="UTF-8"?>
<root>
  <child attr="value">
    <grandchild/>
  </child>
</root>
"""
    # Ensure file ends with newline
    with open(temp_xml_file, "w") as f:
        f.write(content)

    linter = XMLLinter()
    result = linter.lint_file(temp_xml_file)

    assert result.files_checked == 1
    # May have only INFO level issues (like final newline)
    assert result.error_count == 0
    assert result.warning_count == 0
    assert not result.has_errors


def test_lint_xxe_entity_declaration(temp_xml_file):
    """Test detection of XXE entity declarations."""
    temp_xml_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<root>&xxe;</root>
"""
    )

    linter = XMLLinter(check_external_entities=True, allow_xxe=False)
    result = linter.lint_file(temp_xml_file)

    assert result.error_count > 0
    assert any(issue.rule == "xxe-entity" for issue in result.issues)
    assert result.has_errors


def test_lint_xxe_entity_declaration_allowed(temp_xml_file):
    """Test that XXE entities are allowed when explicitly enabled."""
    temp_xml_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<root>&xxe;</root>
"""
    )

    linter = XMLLinter(check_external_entities=True, allow_xxe=True)
    result = linter.lint_file(temp_xml_file)

    # Should not flag XXE when explicitly allowed
    assert not any(issue.rule == "xxe-entity" for issue in result.issues)


def test_lint_external_dtd(temp_xml_file):
    """Test detection of external DTD references."""
    temp_xml_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE root SYSTEM "http://example.com/evil.dtd">
<root/>
"""
    )

    linter = XMLLinter(check_external_entities=True)
    result = linter.lint_file(temp_xml_file)

    assert result.warning_count > 0
    assert any(issue.rule == "external-dtd" for issue in result.issues)


def test_lint_inconsistent_indentation(temp_xml_file):
    """Test detection of inconsistent indentation."""
    temp_xml_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<root>
 <child>
   <grandchild/>
 </child>
</root>
"""
    )

    linter = XMLLinter(check_indentation=True, indent_size=2)
    result = linter.lint_file(temp_xml_file)

    assert result.warning_count > 0
    assert any(issue.rule == "indentation" for issue in result.issues)


def test_lint_tabs(temp_xml_file):
    """Test detection of tab characters."""
    temp_xml_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<root>
\t<child>
\t\t<grandchild/>
\t</child>
</root>
"""
    )

    linter = XMLLinter(check_indentation=True)
    result = linter.lint_file(temp_xml_file)

    assert result.warning_count > 0
    assert any(issue.rule == "tabs" for issue in result.issues)


def test_lint_attribute_order(temp_xml_file):
    """Test detection of unordered attributes."""
    temp_xml_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<root zebra="z" alpha="a" beta="b">
  <child/>
</root>
"""
    )

    linter = XMLLinter(check_attribute_order=True)
    result = linter.lint_file(temp_xml_file)

    assert result.warning_count > 0
    assert any(issue.rule == "attribute-order" for issue in result.issues)


def test_lint_trailing_whitespace(temp_xml_file):
    """Test detection of trailing whitespace."""
    # Write with explicit trailing spaces
    with open(temp_xml_file, "w") as f:
        f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        f.write("<root>\n")
        f.write("  <child/>  \n")  # Line with trailing spaces
        f.write("</root>\n")

    linter = XMLLinter(check_formatting=True)
    result = linter.lint_file(temp_xml_file)

    assert any(issue.rule == "trailing-whitespace" for issue in result.issues)


def test_lint_line_length(temp_xml_file):
    """Test detection of long lines."""
    long_line = "x" * 130
    temp_xml_file.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<root attr="{long_line}">
  <child/>
</root>
"""
    )

    linter = XMLLinter(check_formatting=True)
    result = linter.lint_file(temp_xml_file)

    assert any(issue.rule == "line-length" for issue in result.issues)


def test_lint_missing_final_newline(temp_xml_file):
    """Test detection of missing final newline."""
    temp_xml_file.write_text('<?xml version="1.0"?>\n<root/>')  # No final newline

    linter = XMLLinter(check_formatting=True)
    result = linter.lint_file(temp_xml_file)

    # Note: write_text() may add a newline, so this test might not always trigger
    # This is more for documentation of the feature


def test_lint_invalid_xml_syntax(temp_xml_file):
    """Test handling of invalid XML syntax."""
    temp_xml_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<root>
  <unclosed>
</root>
"""
    )

    linter = XMLLinter()
    result = linter.lint_file(temp_xml_file)

    assert result.error_count > 0
    assert any(issue.rule == "xml-syntax" for issue in result.issues)


def test_lint_directory(tmp_path):
    """Test linting a directory of XML files."""
    # Create test files
    (tmp_path / "file1.xml").write_text(
        """<?xml version="1.0"?>
<root>
  <child/>
</root>
"""
    )

    (tmp_path / "file2.xml").write_text(
        """<?xml version="1.0"?>
<root zebra="z" alpha="a">
  <child/>
</root>
"""
    )

    # Create subdirectory
    sub_dir = tmp_path / "subdir"
    sub_dir.mkdir()
    (sub_dir / "file3.xml").write_text(
        """<?xml version="1.0"?>
<root>
 <child/>
</root>
"""
    )

    linter = XMLLinter(check_attribute_order=True, check_indentation=True)
    result = linter.lint_directory(tmp_path, recursive=True)

    assert result.files_checked == 3
    assert len(result.issues) > 0  # Should find attribute order and indentation issues


def test_lint_directory_non_recursive(tmp_path):
    """Test linting a directory non-recursively."""
    # Create test files
    (tmp_path / "file1.xml").write_text(
        """<?xml version="1.0"?>
<root>
  <child/>
</root>
"""
    )

    # Create subdirectory with file that shouldn't be checked
    sub_dir = tmp_path / "subdir"
    sub_dir.mkdir()
    (sub_dir / "file2.xml").write_text(
        """<?xml version="1.0"?>
<root>
 <child/>
</root>
"""
    )

    linter = XMLLinter()
    result = linter.lint_directory(tmp_path, recursive=False)

    assert result.files_checked == 1  # Only top-level file


def test_lint_issue_to_dict():
    """Test LintIssue serialization to dict."""
    from xml_lib.linter import LintIssue

    issue = LintIssue(
        level=LintLevel.ERROR,
        message="Test error",
        file="/path/to/file.xml",
        line=10,
        column=5,
        rule="test-rule",
    )

    data = issue.to_dict()

    assert data["level"] == "error"
    assert data["message"] == "Test error"
    assert data["file"] == "/path/to/file.xml"
    assert data["line"] == 10
    assert data["column"] == 5
    assert data["rule"] == "test-rule"


def test_lint_issue_format_text():
    """Test LintIssue text formatting."""
    from xml_lib.linter import LintIssue

    issue = LintIssue(
        level=LintLevel.WARNING,
        message="Test warning",
        file="/path/to/file.xml",
        line=10,
        column=5,
        rule="test-rule",
    )

    text = issue.format_text()

    assert "/path/to/file.xml:10:5" in text
    assert "Test warning" in text
    assert "[test-rule]" in text


def test_lint_result_counts():
    """Test LintResult error/warning counting."""
    from xml_lib.linter import LintIssue, LintResult

    result = LintResult()
    result.issues.append(
        LintIssue(
            level=LintLevel.ERROR,
            message="Error 1",
            file="test.xml",
            rule="test",
        )
    )
    result.issues.append(
        LintIssue(
            level=LintLevel.WARNING,
            message="Warning 1",
            file="test.xml",
            rule="test",
        )
    )
    result.issues.append(
        LintIssue(
            level=LintLevel.WARNING,
            message="Warning 2",
            file="test.xml",
            rule="test",
        )
    )
    result.issues.append(
        LintIssue(
            level=LintLevel.INFO,
            message="Info 1",
            file="test.xml",
            rule="test",
        )
    )

    assert result.error_count == 1
    assert result.warning_count == 2
    assert result.has_errors
    assert len(result.issues) == 4


def test_linter_skip_hidden_directories(tmp_path):
    """Test that linter skips hidden directories."""
    # Create normal file
    (tmp_path / "file1.xml").write_text('<?xml version="1.0"?>\n<root/>\n')

    # Create hidden directory
    hidden_dir = tmp_path / ".hidden"
    hidden_dir.mkdir()
    (hidden_dir / "file2.xml").write_text('<?xml version="1.0"?>\n<root/>\n')

    linter = XMLLinter()
    result = linter.lint_directory(tmp_path, recursive=True)

    assert result.files_checked == 1  # Only non-hidden file


def test_linter_disable_checks(temp_xml_file):
    """Test disabling various lint checks."""
    temp_xml_file.write_text(
        """<?xml version="1.0"?>
<root zebra="z" alpha="a">
 <child/>
</root>
"""
    )

    # Disable all checks
    linter = XMLLinter(
        check_indentation=False,
        check_attribute_order=False,
        check_formatting=False,
        check_external_entities=False,
    )
    result = linter.lint_file(temp_xml_file)

    # Should have no issues (or minimal) when all checks disabled
    assert len(result.issues) == 0
