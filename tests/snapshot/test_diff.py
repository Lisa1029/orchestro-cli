"""Tests for snapshot diff generation."""

import pytest

from orchestro_cli.snapshot.diff import SnapshotDiffer
from orchestro_cli.snapshot.models import CapturedOutput


class TestSnapshotDiffer:
    """Test SnapshotDiffer class."""

    @pytest.fixture
    def differ(self):
        """Create differ instance without colors for testing."""
        return SnapshotDiffer(context_lines=3, enable_colors=False)

    @pytest.fixture
    def colored_differ(self):
        """Create differ with colors enabled."""
        return SnapshotDiffer(context_lines=3, enable_colors=True)

    def test_identical_outputs(self, differ):
        """Test comparing identical outputs."""
        expected = CapturedOutput(
            stdout="Hello, World!\n", stderr="", exit_code=0
        )
        actual = CapturedOutput(
            stdout="Hello, World!\n", stderr="", exit_code=0
        )

        result = differ.compare(expected, actual)

        assert result.is_identical
        assert not result.has_diff
        assert result.similarity_score == 100.0
        assert result.exit_code_match

    def test_different_stdout(self, differ):
        """Test comparing different stdout."""
        expected = CapturedOutput(
            stdout="Hello, World!\n", stderr="", exit_code=0
        )
        actual = CapturedOutput(
            stdout="Goodbye, World!\n", stderr="", exit_code=0
        )

        result = differ.compare(expected, actual)

        assert not result.is_identical
        assert result.has_diff
        assert result.has_stdout_diff
        assert not result.has_stderr_diff
        assert result.similarity_score < 100.0
        assert result.exit_code_match

        # Check diff lines
        assert len(result.stdout_diff) > 0
        additions = [line for line in result.stdout_diff if line.is_addition]
        deletions = [line for line in result.stdout_diff if line.is_deletion]
        assert len(additions) > 0
        assert len(deletions) > 0

    def test_different_stderr(self, differ):
        """Test comparing different stderr."""
        expected = CapturedOutput(
            stdout="", stderr="", exit_code=0
        )
        actual = CapturedOutput(
            stdout="", stderr="Error occurred\n", exit_code=0
        )

        result = differ.compare(expected, actual)

        assert not result.is_identical
        assert result.has_diff
        assert result.has_stderr_diff
        assert not result.has_stdout_diff

    def test_different_exit_code(self, differ):
        """Test comparing different exit codes."""
        expected = CapturedOutput(
            stdout="", stderr="", exit_code=0
        )
        actual = CapturedOutput(
            stdout="", stderr="", exit_code=1
        )

        result = differ.compare(expected, actual)

        assert not result.is_identical
        assert not result.exit_code_match
        assert result.similarity_score < 100.0

    def test_multiline_diff(self, differ):
        """Test diff with multiple lines."""
        expected_text = "Line 1\nLine 2\nLine 3\nLine 4\n"
        actual_text = "Line 1\nModified Line 2\nLine 3\nLine 5\n"

        expected = CapturedOutput(
            stdout=expected_text, stderr="", exit_code=0
        )
        actual = CapturedOutput(
            stdout=actual_text, stderr="", exit_code=0
        )

        result = differ.compare(expected, actual)

        assert result.has_diff
        assert result.has_stdout_diff

        # Check for context lines
        context_lines = [
            line for line in result.stdout_diff if line.is_context
        ]
        assert len(context_lines) > 0

    def test_format_diff(self, differ):
        """Test formatting diff output."""
        expected = CapturedOutput(
            stdout="Hello\n", stderr="", exit_code=0
        )
        actual = CapturedOutput(
            stdout="Goodbye\n", stderr="", exit_code=0
        )

        result = differ.compare(expected, actual)
        formatted = differ.format_diff(result)

        assert isinstance(formatted, str)
        assert "Snapshot Comparison" in formatted
        assert "STDOUT Differences" in formatted

    def test_colored_output(self, colored_differ):
        """Test that colored output contains ANSI codes."""
        expected = CapturedOutput(
            stdout="Hello\n", stderr="", exit_code=0
        )
        actual = CapturedOutput(
            stdout="Goodbye\n", stderr="", exit_code=0
        )

        result = colored_differ.compare(expected, actual)
        formatted = colored_differ.format_diff(result)

        # Should contain ANSI escape codes
        assert "\033[" in formatted

    def test_similarity_scoring(self, differ):
        """Test similarity score calculation."""
        # Completely different
        expected1 = CapturedOutput(
            stdout="AAAA", stderr="", exit_code=0
        )
        actual1 = CapturedOutput(
            stdout="BBBB", stderr="", exit_code=0
        )
        result1 = differ.compare(expected1, actual1)
        assert result1.similarity_score < 50.0

        # Mostly similar
        expected2 = CapturedOutput(
            stdout="Hello World" * 10, stderr="", exit_code=0
        )
        actual2 = CapturedOutput(
            stdout="Hello World" * 9 + "Goodbye", stderr="", exit_code=0
        )
        result2 = differ.compare(expected2, actual2)
        assert result2.similarity_score > 80.0

    def test_context_lines_configuration(self):
        """Test configuring context lines."""
        differ_small = SnapshotDiffer(context_lines=1, enable_colors=False)
        differ_large = SnapshotDiffer(context_lines=5, enable_colors=False)

        expected_text = "\n".join([f"Line {i}" for i in range(1, 11)])
        actual_text = "\n".join([f"Line {i}" if i != 5 else "Modified" for i in range(1, 11)])

        expected = CapturedOutput(stdout=expected_text, stderr="", exit_code=0)
        actual = CapturedOutput(stdout=actual_text, stderr="", exit_code=0)

        result_small = differ_small.compare(expected, actual)
        result_large = differ_large.compare(expected, actual)

        # Both should detect the difference
        assert result_small.has_diff
        assert result_large.has_diff

    def test_empty_outputs(self, differ):
        """Test comparing empty outputs."""
        expected = CapturedOutput(stdout="", stderr="", exit_code=0)
        actual = CapturedOutput(stdout="", stderr="", exit_code=0)

        result = differ.compare(expected, actual)

        assert result.is_identical
        assert result.similarity_score == 100.0

    def test_whitespace_differences(self, differ):
        """Test detecting whitespace differences."""
        expected = CapturedOutput(
            stdout="Line 1\nLine 2\n", stderr="", exit_code=0
        )
        actual = CapturedOutput(
            stdout="Line 1 \nLine 2\n", stderr="", exit_code=0  # Extra space
        )

        result = differ.compare(expected, actual)

        # Should detect the difference
        assert result.has_diff
        assert result.similarity_score < 100.0

    def test_summary_generation(self, differ):
        """Test summary message generation."""
        # Identical
        expected1 = CapturedOutput(stdout="test", stderr="", exit_code=0)
        actual1 = CapturedOutput(stdout="test", stderr="", exit_code=0)
        result1 = differ.compare(expected1, actual1)
        assert "match exactly" in result1.summary.lower()
        assert "100%" in result1.summary

        # Different
        expected2 = CapturedOutput(stdout="test", stderr="", exit_code=0)
        actual2 = CapturedOutput(stdout="test2", stderr="", exit_code=1)
        result2 = differ.compare(expected2, actual2)
        assert "differ" in result2.summary.lower()
        assert "exit code" in result2.summary.lower()

    def test_large_diff(self, differ):
        """Test handling large diffs."""
        # Create large outputs with a difference in the middle
        lines = 1000
        expected_lines = [f"Line {i}" for i in range(lines)]
        actual_lines = expected_lines.copy()
        actual_lines[500] = "Modified Line"

        expected = CapturedOutput(
            stdout="\n".join(expected_lines), stderr="", exit_code=0
        )
        actual = CapturedOutput(
            stdout="\n".join(actual_lines), stderr="", exit_code=0
        )

        result = differ.compare(expected, actual)

        assert result.has_diff
        # Should have decent similarity despite one line difference
        # Note: Similarity calculation is weighted (stdout 60%, stderr 30%, exit code 10%)
        assert result.similarity_score > 60.0
        assert result.exit_code_match
