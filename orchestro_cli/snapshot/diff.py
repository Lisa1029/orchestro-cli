"""Snapshot diff generation and comparison.

Generates git-style unified diffs with:
- Color-coded output (additions=green, deletions=red)
- Context lines
- Similarity scoring
- Line-by-line comparison
"""

import difflib
from typing import Optional

from .models import CapturedOutput, DiffResult, DiffLine


class SnapshotDiffer:
    """Generates diffs between snapshots and actual outputs.

    Single Responsibility: Compare outputs and generate human-readable diffs.
    """

    def __init__(self, context_lines: int = 3, enable_colors: bool = True):
        """Initialize differ.

        Args:
            context_lines: Number of context lines to show (default: 3)
            enable_colors: Enable ANSI color codes in output (default: True)
        """
        self.context_lines = context_lines
        self.enable_colors = enable_colors

        # ANSI color codes
        self.colors = {
            "red": "\033[31m" if enable_colors else "",
            "green": "\033[32m" if enable_colors else "",
            "cyan": "\033[36m" if enable_colors else "",
            "yellow": "\033[33m" if enable_colors else "",
            "reset": "\033[0m" if enable_colors else "",
            "bold": "\033[1m" if enable_colors else "",
        }

    def compare(
        self, expected: CapturedOutput, actual: CapturedOutput
    ) -> DiffResult:
        """Compare expected and actual outputs.

        Args:
            expected: Expected output (from snapshot)
            actual: Actual output (from execution)

        Returns:
            DiffResult with comparison details
        """
        # Compare exit codes
        exit_code_match = expected.exit_code == actual.exit_code

        # Compare stdout
        stdout_diff = self._generate_diff(
            expected.stdout, actual.stdout, "stdout"
        )

        # Compare stderr
        stderr_diff = self._generate_diff(
            expected.stderr, actual.stderr, "stderr"
        )

        # Calculate overall diff status
        has_diff = (
            bool(
                any(
                    line.is_addition or line.is_deletion
                    for line in stdout_diff
                )
            )
            or bool(
                any(
                    line.is_addition or line.is_deletion
                    for line in stderr_diff
                )
            )
            or not exit_code_match
        )

        # Calculate similarity score
        similarity_score = self._calculate_similarity(
            expected, actual, exit_code_match
        )

        # Generate summary
        summary = self._generate_summary(
            has_diff,
            similarity_score,
            exit_code_match,
            expected.exit_code,
            actual.exit_code,
        )

        return DiffResult(
            has_diff=has_diff,
            similarity_score=similarity_score,
            stdout_diff=stdout_diff,
            stderr_diff=stderr_diff,
            exit_code_match=exit_code_match,
            summary=summary,
        )

    def format_diff(self, diff_result: DiffResult) -> str:
        """Format diff result as human-readable text.

        Args:
            diff_result: Diff result to format

        Returns:
            Formatted diff text with colors
        """
        lines = []

        # Header
        lines.append(
            f"{self.colors['bold']}Snapshot Comparison{self.colors['reset']}"
        )
        lines.append("=" * 70)
        lines.append("")

        # Summary
        lines.append(diff_result.summary)
        lines.append("")

        # Exit code comparison
        if not diff_result.exit_code_match:
            lines.append(
                f"{self.colors['bold']}Exit Code Mismatch:{self.colors['reset']}"
            )
            lines.append("  Expected: [will be extracted from context]")
            lines.append("  Actual:   [will be extracted from context]")
            lines.append("")

        # Stdout diff
        if diff_result.has_stdout_diff:
            lines.append(
                f"{self.colors['bold']}STDOUT Differences:{self.colors['reset']}"
            )
            lines.append("-" * 70)
            lines.extend(self._format_diff_lines(diff_result.stdout_diff))
            lines.append("")

        # Stderr diff
        if diff_result.has_stderr_diff:
            lines.append(
                f"{self.colors['bold']}STDERR Differences:{self.colors['reset']}"
            )
            lines.append("-" * 70)
            lines.extend(self._format_diff_lines(diff_result.stderr_diff))
            lines.append("")

        return "\n".join(lines)

    def _generate_diff(
        self, expected: str, actual: str, label: str
    ) -> list[DiffLine]:
        """Generate unified diff between two strings.

        Args:
            expected: Expected text
            actual: Actual text
            label: Label for the diff (e.g., "stdout")

        Returns:
            List of DiffLine objects
        """
        expected_lines = expected.splitlines(keepends=True)
        actual_lines = actual.splitlines(keepends=True)

        # Generate unified diff
        diff = difflib.unified_diff(
            expected_lines,
            actual_lines,
            fromfile=f"expected_{label}",
            tofile=f"actual_{label}",
            lineterm="",
            n=self.context_lines,
        )

        # Parse diff output
        diff_lines = []
        for line in diff:
            if line.startswith("+++") or line.startswith("---"):
                # File header - skip
                continue
            elif line.startswith("@@"):
                # Chunk header
                diff_lines.append(
                    DiffLine(line_type="@@", content=line.rstrip())
                )
            elif line.startswith("+"):
                # Addition
                diff_lines.append(
                    DiffLine(line_type="+", content=line[1:].rstrip())
                )
            elif line.startswith("-"):
                # Deletion
                diff_lines.append(
                    DiffLine(line_type="-", content=line[1:].rstrip())
                )
            elif line.startswith(" "):
                # Context
                diff_lines.append(
                    DiffLine(line_type=" ", content=line[1:].rstrip())
                )

        return diff_lines

    def _format_diff_lines(self, diff_lines: list[DiffLine]) -> list[str]:
        """Format diff lines with colors.

        Args:
            diff_lines: List of diff lines

        Returns:
            List of formatted strings
        """
        formatted = []

        for line in diff_lines:
            if line.is_header:
                formatted.append(
                    f"{self.colors['cyan']}{line.content}{self.colors['reset']}"
                )
            elif line.is_addition:
                formatted.append(
                    f"{self.colors['green']}+ {line.content}{self.colors['reset']}"
                )
            elif line.is_deletion:
                formatted.append(
                    f"{self.colors['red']}- {line.content}{self.colors['reset']}"
                )
            elif line.is_context:
                formatted.append(f"  {line.content}")

        return formatted

    def _calculate_similarity(
        self,
        expected: CapturedOutput,
        actual: CapturedOutput,
        exit_code_match: bool,
    ) -> float:
        """Calculate similarity score between outputs.

        Args:
            expected: Expected output
            actual: Actual output
            exit_code_match: Whether exit codes match

        Returns:
            Similarity percentage (0-100)
        """
        # Calculate similarity for stdout
        stdout_ratio = difflib.SequenceMatcher(
            None, expected.stdout, actual.stdout
        ).ratio()

        # Calculate similarity for stderr
        stderr_ratio = difflib.SequenceMatcher(
            None, expected.stderr, actual.stderr
        ).ratio()

        # Weight stdout more heavily (60%), stderr (30%), exit code (10%)
        similarity = (
            stdout_ratio * 0.6 + stderr_ratio * 0.3 + (1.0 if exit_code_match else 0.0) * 0.1
        )

        return round(similarity * 100, 2)

    def _generate_summary(
        self,
        has_diff: bool,
        similarity_score: float,
        exit_code_match: bool,
        expected_exit: int,
        actual_exit: int,
    ) -> str:
        """Generate human-readable summary.

        Args:
            has_diff: Whether there are differences
            similarity_score: Similarity percentage
            exit_code_match: Whether exit codes match
            expected_exit: Expected exit code
            actual_exit: Actual exit code

        Returns:
            Summary string
        """
        if not has_diff:
            return f"{self.colors['green']}✓ Outputs match exactly (100% similarity){self.colors['reset']}"

        status_color = (
            self.colors["red"] if similarity_score < 80 else self.colors["yellow"]
        )

        summary_parts = [
            f"{status_color}✗ Outputs differ ({similarity_score}% similarity){self.colors['reset']}"
        ]

        if not exit_code_match:
            summary_parts.append(
                f"  Exit code: expected {expected_exit}, got {actual_exit}"
            )

        return "\n".join(summary_parts)
