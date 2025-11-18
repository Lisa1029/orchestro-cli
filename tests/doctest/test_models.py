"""Tests for doctest data models."""

from pathlib import Path

import pytest

from orchestro_cli.doctest import CodeBlock, CommandTest, DocTestResult


class TestCodeBlock:
    """Tests for CodeBlock dataclass."""

    def test_code_block_creation(self):
        """Test creating a valid code block."""
        block = CodeBlock(
            language="bash",
            content="echo hello",
            line_number=10,
            file_path=Path("test.md")
        )

        assert block.language == "bash"
        assert block.content == "echo hello"
        assert block.line_number == 10
        assert block.file_path == Path("test.md")

    def test_code_block_empty_content_raises(self):
        """Test that empty content raises ValueError."""
        with pytest.raises(ValueError, match="content cannot be empty"):
            CodeBlock(
                language="bash",
                content="   ",
                line_number=1,
                file_path=Path("test.md")
            )

    def test_code_block_invalid_line_number_raises(self):
        """Test that invalid line number raises ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            CodeBlock(
                language="bash",
                content="echo hello",
                line_number=0,
                file_path=Path("test.md")
            )

        with pytest.raises(ValueError, match="must be positive"):
            CodeBlock(
                language="bash",
                content="echo hello",
                line_number=-5,
                file_path=Path("test.md")
            )


class TestCommandTest:
    """Tests for CommandTest dataclass."""

    def test_command_test_basic(self):
        """Test creating a basic command test."""
        test = CommandTest(
            command="echo hello",
            line_number=5,
            source_file=Path("test.md")
        )

        assert test.command == "echo hello"
        assert test.expected_output is None
        assert test.inline_expectation is None
        assert test.line_number == 5
        assert test.source_file == Path("test.md")

    def test_command_test_inline_expectation(self):
        """Test command with inline expectation."""
        test = CommandTest(
            command="echo hello",
            inline_expectation="hello",
            line_number=1
        )

        assert test.command == "echo hello"
        assert test.inline_expectation == "hello"
        assert test.has_expectation is True
        assert test.expectation_type == "inline"

    def test_command_test_multiline_expectation(self):
        """Test command with multi-line expectation."""
        test = CommandTest(
            command="ls -la",
            expected_output="file1.txt\nfile2.txt",
            line_number=1
        )

        assert test.command == "ls -la"
        assert test.expected_output == "file1.txt\nfile2.txt"
        assert test.has_expectation is True
        assert test.expectation_type == "multi-line"

    def test_command_test_no_expectation(self):
        """Test command without expectation."""
        test = CommandTest(command="echo test", line_number=1)

        assert test.has_expectation is False
        assert test.expectation_type == "none"

    def test_command_test_empty_command_raises(self):
        """Test that empty command raises ValueError."""
        with pytest.raises(ValueError, match="Command cannot be empty"):
            CommandTest(command="   ", line_number=1)

    def test_command_test_both_expectations_raises(self):
        """Test that both expectation types raises ValueError."""
        with pytest.raises(ValueError, match="Cannot have both"):
            CommandTest(
                command="echo test",
                expected_output="output",
                inline_expectation="inline",
                line_number=1
            )


class TestDocTestResult:
    """Tests for DocTestResult dataclass."""

    def test_result_passed(self):
        """Test creating a passed result."""
        test = CommandTest(command="echo hello", line_number=1)
        result = DocTestResult(
            test=test,
            passed=True,
            actual_output="hello",
            execution_time=0.5
        )

        assert result.passed is True
        assert result.actual_output == "hello"
        assert result.error_message is None
        assert result.execution_time == 0.5

    def test_result_failed(self):
        """Test creating a failed result."""
        test = CommandTest(
            command="echo hello",
            inline_expectation="goodbye",
            line_number=1,
            source_file=Path("test.md")
        )
        result = DocTestResult(
            test=test,
            passed=False,
            actual_output="hello",
            error_message="Output mismatch",
            execution_time=0.3
        )

        assert result.passed is False
        assert result.actual_output == "hello"
        assert result.error_message == "Output mismatch"
        assert result.execution_time == 0.3

    def test_result_negative_execution_time_raises(self):
        """Test that negative execution time raises ValueError."""
        test = CommandTest(command="echo test", line_number=1)

        with pytest.raises(ValueError, match="cannot be negative"):
            DocTestResult(
                test=test,
                passed=True,
                execution_time=-1.0
            )

    def test_result_location_with_file(self):
        """Test location property with source file."""
        test = CommandTest(
            command="echo test",
            line_number=42,
            source_file=Path("docs/README.md")
        )
        result = DocTestResult(test=test, passed=True)

        assert result.location == "docs/README.md:42"

    def test_result_location_without_file(self):
        """Test location property without source file."""
        test = CommandTest(command="echo test", line_number=42)
        result = DocTestResult(test=test, passed=True)

        assert result.location == "line 42"

    def test_get_summary_passed(self):
        """Test summary for passed result."""
        test = CommandTest(
            command="echo hello",
            line_number=10,
            source_file=Path("test.md")
        )
        result = DocTestResult(test=test, passed=True)

        summary = result.get_summary()
        assert "[PASS]" in summary
        assert "test.md:10" in summary
        assert "echo hello" in summary

    def test_get_summary_failed(self):
        """Test summary for failed result."""
        test = CommandTest(
            command="echo hello world this is a very long command that should be truncated",
            line_number=5,
            source_file=Path("test.md")
        )
        result = DocTestResult(test=test, passed=False)

        summary = result.get_summary()
        assert "[FAIL]" in summary
        assert "test.md:5" in summary
        assert "..." in summary  # Command was truncated

    def test_get_detailed_report_passed(self):
        """Test detailed report for passed result."""
        test = CommandTest(
            command="echo hello",
            inline_expectation="hello",
            line_number=10,
            source_file=Path("test.md")
        )
        result = DocTestResult(
            test=test,
            passed=True,
            actual_output="hello",
            execution_time=0.123
        )

        report = result.get_detailed_report()
        assert "Test: test.md:10" in report
        assert "Command: echo hello" in report
        assert "Status: PASSED" in report
        assert "Execution Time: 0.123s" in report
        assert "Expected: hello" in report
        assert "Actual Output:" in report

    def test_get_detailed_report_failed(self):
        """Test detailed report for failed result."""
        test = CommandTest(
            command="echo hello",
            expected_output="goodbye",
            line_number=5,
            source_file=Path("test.md")
        )
        result = DocTestResult(
            test=test,
            passed=False,
            actual_output="hello",
            error_message="Output validation failed",
            execution_time=0.456
        )

        report = result.get_detailed_report()
        assert "Status: FAILED" in report
        assert "Error:" in report
        assert "Output validation failed" in report
        assert "Expected Output:" in report
        assert "goodbye" in report
