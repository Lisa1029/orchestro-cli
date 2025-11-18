"""Step execution results."""

from dataclasses import dataclass, field
from typing import List, Optional

from ..assertions.models import AssertionResult


@dataclass
class StepResult:
    """Result of executing a single step.

    Attributes:
        step_index: Index of the step in the scenario
        success: Whether the step executed successfully
        output: Captured output from the step
        exit_code: Exit code if applicable
        error_message: Error message if step failed
        assertion_results: Results of inline assertions
        duration: Step execution duration in seconds
    """

    step_index: int
    success: bool = True
    output: Optional[str] = None
    exit_code: Optional[int] = None
    error_message: Optional[str] = None
    assertion_results: List[AssertionResult] = field(default_factory=list)
    duration: float = 0.0

    @property
    def has_assertion_failures(self) -> bool:
        """Check if any assertions failed."""
        return any(not result.passed for result in self.assertion_results)

    @property
    def assertion_count(self) -> int:
        """Get number of assertions."""
        return len(self.assertion_results)

    @property
    def passed_assertions(self) -> int:
        """Get number of passed assertions."""
        return sum(1 for result in self.assertion_results if result.passed)

    @property
    def failed_assertions(self) -> int:
        """Get number of failed assertions."""
        return sum(1 for result in self.assertion_results if not result.passed)

    def get_failure_summary(self) -> str:
        """Get a summary of all failures.

        Returns:
            Formatted string with failure details
        """
        if not self.has_assertion_failures and self.success:
            return ""

        parts = []

        if not self.success and self.error_message:
            parts.append(f"Step execution failed: {self.error_message}")

        if self.has_assertion_failures:
            parts.append(f"\nAssertion failures ({self.failed_assertions}/{self.assertion_count}):")
            for result in self.assertion_results:
                if not result.passed:
                    parts.append(f"\n{result.format_failure()}")

        return "\n".join(parts)
