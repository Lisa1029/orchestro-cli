"""Assertion models for inline testing."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class AssertionType(Enum):
    """Types of assertions supported."""

    OUTPUT = "output"  # Exact output match
    CODE = "code"  # Exit code match
    CONTAINS = "contains"  # Output contains text
    REGEX = "regex"  # Regex pattern match
    LINES = "lines"  # Line count match
    NOT_CONTAINS = "not_contains"  # Output does not contain text
    JSON = "json"  # JSON structure validation
    CUSTOM = "custom"  # Custom validation function


@dataclass
class Assertion:
    """Represents a single assertion to be validated.

    Attributes:
        assertion_type: Type of assertion to perform
        expected: Expected value for the assertion
        actual: Actual value captured during execution
        passed: Whether the assertion passed
        description: Optional description of the assertion
        line_number: YAML line number for error reporting
    """

    assertion_type: AssertionType
    expected: Any
    actual: Optional[Any] = None
    passed: bool = False
    description: Optional[str] = None
    line_number: Optional[int] = None

    @property
    def type_name(self) -> str:
        """Get human-readable assertion type name."""
        return self.assertion_type.value


@dataclass
class AssertionResult:
    """Result of an assertion validation with detailed failure info.

    Attributes:
        assertion: The assertion that was validated
        passed: Whether the assertion passed
        error_message: Detailed error message if failed
        diff: Human-readable diff between expected and actual
        actual_value: The actual value that was checked
        expected_value: The expected value
    """

    assertion: Assertion
    passed: bool
    error_message: Optional[str] = None
    diff: Optional[str] = None
    actual_value: Optional[Any] = None
    expected_value: Optional[Any] = None

    @property
    def status_icon(self) -> str:
        """Get status icon for display."""
        return "✓" if self.passed else "❌"

    def format_failure(self) -> str:
        """Format failure message with details.

        Returns:
            Formatted multi-line error message
        """
        if self.passed:
            return f"{self.status_icon} Assertion passed"

        msg_parts = [
            f"{self.status_icon} Assertion failed: {self.assertion.type_name}",
        ]

        if self.error_message:
            msg_parts.append(f"  Error: {self.error_message}")

        if self.expected_value is not None:
            msg_parts.append(f"  Expected: {self._format_value(self.expected_value)}")

        if self.actual_value is not None:
            msg_parts.append(f"  Actual:   {self._format_value(self.actual_value)}")

        if self.diff:
            msg_parts.append(f"  Diff:\n{self.diff}")

        if self.assertion.line_number:
            msg_parts.append(f"  Location: line {self.assertion.line_number}")

        return "\n".join(msg_parts)

    @staticmethod
    def _format_value(value: Any, max_length: int = 100) -> str:
        """Format value for display, truncating if necessary."""
        str_value = str(value)
        if len(str_value) > max_length:
            return str_value[:max_length] + "..."
        return str_value
