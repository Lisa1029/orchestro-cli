"""Data models for testable documentation system."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class CodeBlock:
    """Represents a fenced code block extracted from Markdown.

    Attributes:
        language: Programming language (e.g., 'bash', 'python', 'shell')
        content: Raw content of the code block
        line_number: Starting line number in source file
        file_path: Path to source Markdown file
    """

    language: str
    content: str
    line_number: int
    file_path: Path

    def __post_init__(self) -> None:
        """Validate code block after initialization."""
        if not self.content.strip():
            raise ValueError("Code block content cannot be empty")
        if self.line_number < 1:
            raise ValueError("Line number must be positive")


@dataclass
class CommandTest:
    """Represents a testable command extracted from a code block.

    Supports two validation styles:
    1. Multi-line expected output (lines following the command)
    2. Inline expectation using '#=>' syntax

    Examples:
        # Multi-line style:
        $ orchestro run scenario.yaml
        Running scenario...
        Success!

        # Inline style:
        $ orchestro --version  #=> orchestro 0.2.1

    Attributes:
        command: Command to execute (without prompt prefix)
        expected_output: Expected output for multi-line style
        inline_expectation: Expected output for inline style
        line_number: Line number in source file
        source_file: Path to source Markdown file
    """

    command: str
    expected_output: Optional[str] = None
    inline_expectation: Optional[str] = None
    line_number: int = 1
    source_file: Optional[Path] = None

    def __post_init__(self) -> None:
        """Validate command test after initialization."""
        if not self.command.strip():
            raise ValueError("Command cannot be empty")
        if self.expected_output and self.inline_expectation:
            raise ValueError(
                "Cannot have both expected_output and inline_expectation"
            )

    @property
    def has_expectation(self) -> bool:
        """Check if command has any expected output."""
        return bool(self.expected_output or self.inline_expectation)

    @property
    def expectation_type(self) -> str:
        """Return the type of expectation (multi-line, inline, or none)."""
        if self.inline_expectation:
            return "inline"
        elif self.expected_output:
            return "multi-line"
        return "none"


@dataclass
class DocTestResult:
    """Result of executing a documentation test.

    Attributes:
        test: The command test that was executed
        passed: Whether the test passed
        actual_output: Actual output from command execution
        error_message: Error message if test failed
        execution_time: Time taken to execute in seconds
    """

    test: CommandTest
    passed: bool
    actual_output: str = ""
    error_message: Optional[str] = None
    execution_time: float = 0.0

    def __post_init__(self) -> None:
        """Validate result after initialization."""
        if self.execution_time < 0:
            raise ValueError("Execution time cannot be negative")

    @property
    def location(self) -> str:
        """Return human-readable location of the test."""
        if self.test.source_file:
            return f"{self.test.source_file}:{self.test.line_number}"
        return f"line {self.test.line_number}"

    def get_summary(self) -> str:
        """Return a summary of the test result.

        Returns:
            Single-line summary suitable for reporting
        """
        status = "PASS" if self.passed else "FAIL"
        location = self.location
        command = self.test.command[:50] + "..." if len(self.test.command) > 50 else self.test.command
        return f"[{status}] {location}: {command}"

    def get_detailed_report(self) -> str:
        """Return detailed report of test result.

        Returns:
            Multi-line detailed report including command, output, and errors
        """
        lines = [
            f"Test: {self.location}",
            f"Command: {self.test.command}",
            f"Status: {'PASSED' if self.passed else 'FAILED'}",
            f"Execution Time: {self.execution_time:.3f}s",
        ]

        if self.test.has_expectation:
            lines.append(f"Expectation Type: {self.test.expectation_type}")
            if self.test.inline_expectation:
                lines.append(f"Expected: {self.test.inline_expectation}")
            elif self.test.expected_output:
                lines.append("Expected Output:")
                lines.append(self.test.expected_output)

        if self.actual_output:
            lines.append("Actual Output:")
            lines.append(self.actual_output)

        if self.error_message:
            lines.append("Error:")
            lines.append(self.error_message)

        return "\n".join(lines)
