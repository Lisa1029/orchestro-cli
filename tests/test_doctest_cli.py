"""Tests for documentation testing CLI handler."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile

from orchestro_cli.doctest.cli_handler import DocTestCLIHandler, Colors
from orchestro_cli.doctest.executor import MatchMode
from orchestro_cli.doctest.models import CommandTest, DocTestResult


@pytest.fixture
def temp_markdown():
    """Create temporary Markdown file with test content."""
    content = """# Test Documentation

## Example Commands

```bash
$ echo "hello"
hello

$ echo "world"  #=> world
```
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        f.flush()
        path = Path(f.name)

    yield path

    # Cleanup
    if path.exists():
        path.unlink()


@pytest.fixture
def temp_output_dir():
    """Create temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestColors:
    """Test color code management."""

    def test_disable_colors(self):
        """Test that disable() removes color codes."""
        # Store original values
        original_green = Colors.GREEN

        # Disable colors
        Colors.disable()

        # Check all colors are empty
        assert Colors.GREEN == ''
        assert Colors.RED == ''
        assert Colors.YELLOW == ''
        assert Colors.BLUE == ''
        assert Colors.BOLD == ''
        assert Colors.RESET == ''
        assert Colors.GRAY == ''

        # Restore for other tests
        Colors.GREEN = original_green


class TestDocTestCLIHandler:
    """Test CLI handler functionality."""

    def test_init_with_defaults(self, temp_markdown):
        """Test handler initialization with default values."""
        handler = DocTestCLIHandler(
            markdown_files=[temp_markdown]
        )

        assert handler.markdown_files == [temp_markdown]
        assert handler.prompt_prefix == '$'
        assert handler.verbose is False
        assert handler.fail_fast is False
        assert handler.junit_xml is None
        assert handler.match_mode == MatchMode.CONTAINS
        assert handler.timeout == 30.0

    def test_init_with_custom_values(self, temp_markdown, temp_output_dir):
        """Test handler initialization with custom values."""
        junit_path = temp_output_dir / "results.xml"

        handler = DocTestCLIHandler(
            markdown_files=[temp_markdown],
            prompt_prefix='>',
            verbose=True,
            fail_fast=True,
            junit_xml=junit_path,
            match_mode=MatchMode.EXACT,
            timeout=60.0
        )

        assert handler.prompt_prefix == '>'
        assert handler.verbose is True
        assert handler.fail_fast is True
        assert handler.junit_xml == junit_path
        assert handler.match_mode == MatchMode.EXACT
        assert handler.timeout == 60.0

    def test_nonexistent_file(self, temp_output_dir):
        """Test error handling for nonexistent file."""
        nonexistent = temp_output_dir / "nonexistent.md"

        handler = DocTestCLIHandler(
            markdown_files=[nonexistent]
        )

        exit_code = handler.run()
        assert exit_code == 1

    def test_non_markdown_file(self, temp_output_dir):
        """Test error handling for non-Markdown file."""
        txt_file = temp_output_dir / "test.txt"
        txt_file.write_text("not markdown")

        handler = DocTestCLIHandler(
            markdown_files=[txt_file]
        )

        exit_code = handler.run()
        assert exit_code == 1

    def test_run_successful_tests(self, temp_markdown):
        """Test running successful tests."""
        handler = DocTestCLIHandler(
            markdown_files=[temp_markdown],
            no_color=True  # Disable colors for testing
        )

        exit_code = handler.run()
        assert exit_code == 0

    def test_run_with_verbose(self, temp_markdown, capsys):
        """Test verbose output."""
        handler = DocTestCLIHandler(
            markdown_files=[temp_markdown],
            verbose=True,
            no_color=True
        )

        exit_code = handler.run()
        assert exit_code == 0

        captured = capsys.readouterr()
        assert "Found" in captured.out
        assert "test(s)" in captured.out

    def test_fail_fast_stops_on_failure(self, temp_output_dir):
        """Test that fail_fast stops execution on first failure."""
        # Create file with failing test followed by passing test
        failing_md = temp_output_dir / "failing.md"
        failing_md.write_text("""
```bash
$ false
success

$ echo "should not run"
should not run
```
""")

        handler = DocTestCLIHandler(
            markdown_files=[failing_md],
            fail_fast=True,
            no_color=True
        )

        exit_code = handler.run()
        assert exit_code == 1

    def test_junit_xml_generation(self, temp_markdown, temp_output_dir):
        """Test JUnit XML report generation."""
        junit_path = temp_output_dir / "results.xml"

        handler = DocTestCLIHandler(
            markdown_files=[temp_markdown],
            junit_xml=junit_path,
            no_color=True
        )

        exit_code = handler.run()
        assert exit_code == 0
        assert junit_path.exists()

        # Verify XML content
        xml_content = junit_path.read_text()
        assert '<?xml version' in xml_content
        assert '<testsuites>' in xml_content
        assert '<testsuite' in xml_content
        assert '<testcase' in xml_content

    def test_multiple_files(self, temp_output_dir):
        """Test processing multiple Markdown files."""
        # Create multiple files
        file1 = temp_output_dir / "file1.md"
        file1.write_text("""
```bash
$ echo "test1"
test1
```
""")

        file2 = temp_output_dir / "file2.md"
        file2.write_text("""
```bash
$ echo "test2"
test2
```
""")

        handler = DocTestCLIHandler(
            markdown_files=[file1, file2],
            no_color=True
        )

        exit_code = handler.run()
        assert exit_code == 0

    def test_empty_file(self, temp_output_dir):
        """Test handling of file with no tests."""
        empty_md = temp_output_dir / "empty.md"
        empty_md.write_text("# No Tests Here\n\nJust text.")

        handler = DocTestCLIHandler(
            markdown_files=[empty_md],
            no_color=True
        )

        exit_code = handler.run()
        assert exit_code == 0

    def test_print_result_passed(self, temp_markdown, capsys):
        """Test printing passed test result."""
        # Create a passing result
        test = CommandTest(
            command="echo test",
            inline_expectation="test",
            line_number=10,
            source_file=temp_markdown
        )
        result = DocTestResult(
            test=test,
            passed=True,
            actual_output="test",
            execution_time=0.1
        )

        handler = DocTestCLIHandler(
            markdown_files=[temp_markdown],
            no_color=True
        )

        handler._print_result(result)

        captured = capsys.readouterr()
        assert "✓" in captured.out
        assert "echo test" in captured.out

    def test_print_result_failed(self, temp_markdown, capsys):
        """Test printing failed test result."""
        # Create a failing result
        test = CommandTest(
            command="echo wrong",
            inline_expectation="expected",
            line_number=10,
            source_file=temp_markdown
        )
        result = DocTestResult(
            test=test,
            passed=False,
            actual_output="wrong",
            error_message="Output mismatch",
            execution_time=0.1
        )

        handler = DocTestCLIHandler(
            markdown_files=[temp_markdown],
            no_color=True
        )

        handler._print_result(result)

        captured = capsys.readouterr()
        assert "✗" in captured.out
        assert "echo wrong" in captured.out
        assert "Output mismatch" in captured.out

    def test_print_summary_all_passed(self, capsys):
        """Test summary with all tests passing."""
        test = CommandTest(command="true", line_number=1)
        results = [
            DocTestResult(test=test, passed=True, execution_time=0.1),
            DocTestResult(test=test, passed=True, execution_time=0.2),
        ]

        handler = DocTestCLIHandler(
            markdown_files=[Path("test.md")],
            no_color=True
        )

        success = handler._print_summary(results, 2)

        assert success is True
        captured = capsys.readouterr()
        assert "2 passed" in captured.out
        assert "0 failed" in captured.out

    def test_print_summary_with_failures(self, capsys):
        """Test summary with failures."""
        test = CommandTest(command="test", line_number=1)
        results = [
            DocTestResult(test=test, passed=True, execution_time=0.1),
            DocTestResult(test=test, passed=False, execution_time=0.2),
        ]

        handler = DocTestCLIHandler(
            markdown_files=[Path("test.md")],
            no_color=True
        )

        success = handler._print_summary(results, 2)

        assert success is False
        captured = capsys.readouterr()
        assert "1 passed" in captured.out
        assert "1 failed" in captured.out

    def test_custom_prompt_prefix(self, temp_output_dir):
        """Test using custom prompt prefix."""
        custom_md = temp_output_dir / "custom.md"
        custom_md.write_text("""
```bash
> echo "test"
test
```
""")

        handler = DocTestCLIHandler(
            markdown_files=[custom_md],
            prompt_prefix='>',
            no_color=True
        )

        exit_code = handler.run()
        assert exit_code == 0

    def test_match_mode_exact(self, temp_output_dir):
        """Test exact match mode."""
        exact_md = temp_output_dir / "exact.md"
        exact_md.write_text("""
```bash
$ echo "test"
test
```
""")

        handler = DocTestCLIHandler(
            markdown_files=[exact_md],
            match_mode=MatchMode.EXACT,
            no_color=True
        )

        exit_code = handler.run()
        assert exit_code == 0

    def test_working_directory(self, temp_markdown, temp_output_dir):
        """Test custom working directory."""
        handler = DocTestCLIHandler(
            markdown_files=[temp_markdown],
            working_dir=temp_output_dir,
            no_color=True
        )

        exit_code = handler.run()
        assert exit_code == 0

    def test_timeout_configuration(self, temp_markdown):
        """Test timeout configuration."""
        handler = DocTestCLIHandler(
            markdown_files=[temp_markdown],
            timeout=1.0,
            no_color=True
        )

        exit_code = handler.run()
        assert exit_code == 0
