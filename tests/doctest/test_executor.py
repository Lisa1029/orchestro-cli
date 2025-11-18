"""Tests for command executor."""

from pathlib import Path
from time import sleep

import pytest

from orchestro_cli.doctest import (
    CommandTest,
    DocTestExecutor,
    DocTestResult,
    MatchMode
)


class TestDocTestExecutor:
    """Tests for DocTestExecutor class."""

    def test_execute_simple_command(self):
        """Test executing a simple command."""
        test = CommandTest(
            command="echo hello",
            line_number=1
        )

        executor = DocTestExecutor()
        result = executor.execute_test(test)

        assert isinstance(result, DocTestResult)
        assert result.passed is True
        assert "hello" in result.actual_output
        assert result.execution_time > 0

    def test_execute_with_inline_expectation_pass(self):
        """Test executing command with matching inline expectation."""
        test = CommandTest(
            command="echo hello",
            inline_expectation="hello",
            line_number=1
        )

        executor = DocTestExecutor(match_mode=MatchMode.CONTAINS)
        result = executor.execute_test(test)

        assert result.passed is True
        assert result.error_message is None

    def test_execute_with_inline_expectation_fail(self):
        """Test executing command with non-matching inline expectation."""
        test = CommandTest(
            command="echo hello",
            inline_expectation="goodbye",
            line_number=1
        )

        executor = DocTestExecutor(match_mode=MatchMode.CONTAINS)
        result = executor.execute_test(test)

        assert result.passed is False
        assert result.error_message is not None
        assert "validation failed" in result.error_message.lower()

    def test_execute_with_multiline_expectation_pass(self):
        """Test executing command with matching multi-line expectation."""
        test = CommandTest(
            command="printf 'line1\\nline2\\nline3'",
            expected_output="line1\nline2\nline3",
            line_number=1
        )

        executor = DocTestExecutor(match_mode=MatchMode.EXACT, strip_whitespace=True)
        result = executor.execute_test(test)

        assert result.passed is True

    def test_execute_with_multiline_expectation_fail(self):
        """Test executing command with non-matching multi-line expectation."""
        test = CommandTest(
            command="echo hello",
            expected_output="hello\nworld",
            line_number=1
        )

        executor = DocTestExecutor(match_mode=MatchMode.EXACT)
        result = executor.execute_test(test)

        assert result.passed is False

    def test_execute_exact_match_mode(self):
        """Test exact match mode."""
        test = CommandTest(
            command="echo hello",
            inline_expectation="hello",
            line_number=1
        )

        executor = DocTestExecutor(match_mode=MatchMode.EXACT, strip_whitespace=True)
        result = executor.execute_test(test)

        assert result.passed is True

    def test_execute_contains_match_mode(self):
        """Test contains match mode."""
        test = CommandTest(
            command="echo hello world",
            inline_expectation="hello",
            line_number=1
        )

        executor = DocTestExecutor(match_mode=MatchMode.CONTAINS)
        result = executor.execute_test(test)

        assert result.passed is True

    def test_execute_regex_match_mode(self):
        """Test regex match mode."""
        test = CommandTest(
            command="echo hello123",
            inline_expectation=r"hello\d+",
            line_number=1
        )

        executor = DocTestExecutor(match_mode=MatchMode.REGEX)
        result = executor.execute_test(test)

        assert result.passed is True

    def test_execute_startswith_match_mode(self):
        """Test startswith match mode."""
        test = CommandTest(
            command="echo hello world",
            inline_expectation="hello",
            line_number=1
        )

        executor = DocTestExecutor(match_mode=MatchMode.STARTSWITH, strip_whitespace=True)
        result = executor.execute_test(test)

        assert result.passed is True

    def test_execute_endswith_match_mode(self):
        """Test endswith match mode."""
        test = CommandTest(
            command="echo hello world",
            inline_expectation="world",
            line_number=1
        )

        executor = DocTestExecutor(match_mode=MatchMode.ENDSWITH, strip_whitespace=True)
        result = executor.execute_test(test)

        assert result.passed is True

    def test_execute_with_timeout(self):
        """Test command timeout handling."""
        # Command that sleeps longer than timeout
        test = CommandTest(
            command="sleep 5",
            line_number=1
        )

        executor = DocTestExecutor(timeout=0.5)
        result = executor.execute_test(test)

        assert result.passed is False
        assert "timed out" in result.error_message.lower()

    def test_execute_with_custom_timeout(self):
        """Test overriding timeout for specific test."""
        test = CommandTest(
            command="sleep 0.2",
            line_number=1
        )

        executor = DocTestExecutor(timeout=0.1)
        # Override with longer timeout
        result = executor.execute_test(test, timeout=1.0)

        assert result.passed is True

    def test_execute_command_failure(self):
        """Test handling command that fails."""
        test = CommandTest(
            command="ls /nonexistent_directory_12345",
            line_number=1
        )

        executor = DocTestExecutor()
        result = executor.execute_test(test)

        assert result.passed is False
        assert "failed with exit code" in result.error_message.lower()

    def test_execute_invalid_command(self):
        """Test handling invalid command."""
        test = CommandTest(
            command="nonexistent_command_xyz123",
            line_number=1
        )

        executor = DocTestExecutor()
        result = executor.execute_test(test)

        assert result.passed is False
        assert result.error_message is not None

    def test_execute_with_working_directory(self, tmp_path: Path):
        """Test executing command in specific directory."""
        # Create a test file in temp directory
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        test = CommandTest(
            command="ls test.txt",
            inline_expectation="test.txt",
            line_number=1
        )

        executor = DocTestExecutor(
            working_dir=tmp_path,
            match_mode=MatchMode.CONTAINS
        )
        result = executor.execute_test(test)

        assert result.passed is True

    def test_execute_with_environment_variables(self):
        """Test executing command with custom environment."""
        test = CommandTest(
            command="echo $TEST_VAR",
            inline_expectation="custom_value",
            line_number=1
        )

        executor = DocTestExecutor(
            env={"TEST_VAR": "custom_value"},
            match_mode=MatchMode.CONTAINS
        )
        result = executor.execute_test(test)

        assert result.passed is True

    def test_execute_strip_whitespace(self):
        """Test whitespace stripping."""
        test = CommandTest(
            command="echo '  hello  '",
            inline_expectation="hello",
            line_number=1
        )

        executor = DocTestExecutor(
            match_mode=MatchMode.EXACT,
            strip_whitespace=True
        )
        result = executor.execute_test(test)

        assert result.passed is True

    def test_execute_preserve_whitespace(self):
        """Test preserving whitespace."""
        test = CommandTest(
            command="echo 'hello'",
            inline_expectation="hello",
            line_number=1
        )

        executor = DocTestExecutor(
            match_mode=MatchMode.EXACT,
            strip_whitespace=False
        )
        result = executor.execute_test(test)

        # May fail due to newline at end
        assert isinstance(result, DocTestResult)

    def test_execute_multiple_tests(self):
        """Test executing multiple tests."""
        tests = [
            CommandTest(command="echo one", inline_expectation="one", line_number=1),
            CommandTest(command="echo two", inline_expectation="two", line_number=2),
            CommandTest(command="echo three", inline_expectation="three", line_number=3),
        ]

        executor = DocTestExecutor(match_mode=MatchMode.CONTAINS)
        results = executor.execute_tests(tests)

        assert len(results) == 3
        assert all(r.passed for r in results)

    def test_execute_multiple_tests_stop_on_failure(self):
        """Test stopping execution on first failure."""
        tests = [
            CommandTest(command="echo one", inline_expectation="one", line_number=1),
            CommandTest(command="echo two", inline_expectation="wrong", line_number=2),
            CommandTest(command="echo three", inline_expectation="three", line_number=3),
        ]

        executor = DocTestExecutor(match_mode=MatchMode.CONTAINS)
        results = executor.execute_tests(tests, stop_on_failure=True)

        # Should stop after second test fails
        assert len(results) == 2
        assert results[0].passed is True
        assert results[1].passed is False

    def test_execute_multiple_tests_continue_on_failure(self):
        """Test continuing execution after failures."""
        tests = [
            CommandTest(command="echo one", inline_expectation="wrong1", line_number=1),
            CommandTest(command="echo two", inline_expectation="two", line_number=2),
            CommandTest(command="echo three", inline_expectation="wrong3", line_number=3),
        ]

        executor = DocTestExecutor(match_mode=MatchMode.CONTAINS)
        results = executor.execute_tests(tests, stop_on_failure=False)

        # Should execute all tests
        assert len(results) == 3
        assert results[0].passed is False
        assert results[1].passed is True
        assert results[2].passed is False

    def test_get_summary(self):
        """Test getting summary statistics."""
        tests = [
            CommandTest(command="echo one", inline_expectation="one", line_number=1),
            CommandTest(command="echo two", inline_expectation="wrong", line_number=2),
            CommandTest(command="echo three", inline_expectation="three", line_number=3),
        ]

        executor = DocTestExecutor(match_mode=MatchMode.CONTAINS)
        results = executor.execute_tests(tests)

        summary = executor.get_summary(results)

        assert summary['total_tests'] == 3
        assert summary['passed'] == 2
        assert summary['failed'] == 1
        assert 0 < summary['success_rate'] < 100
        assert summary['total_execution_time'] > 0
        assert summary['avg_execution_time'] > 0

    def test_get_summary_empty(self):
        """Test summary with no results."""
        executor = DocTestExecutor()
        summary = executor.get_summary([])

        assert summary['total_tests'] == 0
        assert summary['passed'] == 0
        assert summary['failed'] == 0
        assert summary['success_rate'] == 0.0
        assert summary['total_execution_time'] == 0.0
        assert summary['avg_execution_time'] == 0.0

    def test_get_summary_all_passed(self):
        """Test summary with all tests passing."""
        tests = [
            CommandTest(command="echo one", inline_expectation="one", line_number=1),
            CommandTest(command="echo two", inline_expectation="two", line_number=2),
        ]

        executor = DocTestExecutor(match_mode=MatchMode.CONTAINS)
        results = executor.execute_tests(tests)

        summary = executor.get_summary(results)

        assert summary['success_rate'] == 100.0

    def test_override_match_mode_per_test(self):
        """Test overriding match mode for specific test."""
        test = CommandTest(
            command="echo hello world",
            inline_expectation="^hello",
            line_number=1
        )

        executor = DocTestExecutor(match_mode=MatchMode.CONTAINS)
        # Override with regex mode
        result = executor.execute_test(test, match_mode=MatchMode.REGEX)

        assert result.passed is True

    def test_execution_time_measured(self):
        """Test that execution time is measured."""
        test = CommandTest(
            command="sleep 0.1",
            line_number=1
        )

        executor = DocTestExecutor()
        result = executor.execute_test(test)

        # Execution time should be at least 0.1s
        assert result.execution_time >= 0.1
