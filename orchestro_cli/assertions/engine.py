"""Assertion engine for validating step results."""

import difflib
import json
import re
from typing import Any, List, Optional

from .models import Assertion, AssertionResult, AssertionType


class AssertionEngine:
    """Executes assertions against command output and results.

    Single Responsibility: Validate different assertion types and generate
    clear failure messages with diffs.
    """

    def __init__(self, fail_fast: bool = True, verbose: bool = False):
        """Initialize assertion engine.

        Args:
            fail_fast: Stop on first assertion failure
            verbose: Enable verbose logging
        """
        self.fail_fast = fail_fast
        self.verbose = verbose
        self._results: List[AssertionResult] = []

    def _log(self, message: str) -> None:
        """Log message if verbose enabled."""
        if self.verbose:
            print(f"[AssertionEngine] {message}")

    def validate(self, assertion: Assertion) -> AssertionResult:
        """Validate a single assertion.

        Args:
            assertion: Assertion to validate

        Returns:
            AssertionResult with pass/fail status and details
        """
        self._log(f"Validating {assertion.type_name}: {assertion.expected}")

        # Dispatch to specific validator
        validators = {
            AssertionType.OUTPUT: self._validate_output,
            AssertionType.CODE: self._validate_code,
            AssertionType.CONTAINS: self._validate_contains,
            AssertionType.REGEX: self._validate_regex,
            AssertionType.LINES: self._validate_lines,
            AssertionType.NOT_CONTAINS: self._validate_not_contains,
            AssertionType.JSON: self._validate_json,
        }

        validator = validators.get(assertion.assertion_type)
        if not validator:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                error_message=f"Unknown assertion type: {assertion.type_name}",
            )

        result = validator(assertion)
        self._results.append(result)

        if not result.passed and self.fail_fast:
            raise AssertionError(result.format_failure())

        return result

    def validate_all(self, assertions: List[Assertion]) -> List[AssertionResult]:
        """Validate multiple assertions.

        Args:
            assertions: List of assertions to validate

        Returns:
            List of assertion results

        Raises:
            AssertionError: If fail_fast is True and any assertion fails
        """
        results = []
        for assertion in assertions:
            result = self.validate(assertion)
            results.append(result)

        return results

    def _validate_output(self, assertion: Assertion) -> AssertionResult:
        """Validate exact output match.

        Args:
            assertion: Assertion with expected output string

        Returns:
            AssertionResult
        """
        expected = str(assertion.expected).strip()
        actual = str(assertion.actual).strip() if assertion.actual else ""

        passed = expected == actual

        if not passed:
            diff = self._generate_diff(expected, actual)
            return AssertionResult(
                assertion=assertion,
                passed=False,
                error_message="Output does not match expected value",
                diff=diff,
                expected_value=expected,
                actual_value=actual,
            )

        return AssertionResult(
            assertion=assertion,
            passed=True,
            expected_value=expected,
            actual_value=actual,
        )

    def _validate_code(self, assertion: Assertion) -> AssertionResult:
        """Validate exit code.

        Args:
            assertion: Assertion with expected exit code

        Returns:
            AssertionResult
        """
        expected = int(assertion.expected)
        actual = int(assertion.actual) if assertion.actual is not None else None

        if actual is None:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                error_message="No exit code captured",
                expected_value=expected,
            )

        passed = expected == actual

        if not passed:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                error_message=f"Exit code mismatch",
                expected_value=expected,
                actual_value=actual,
            )

        return AssertionResult(
            assertion=assertion,
            passed=True,
            expected_value=expected,
            actual_value=actual,
        )

    def _validate_contains(self, assertion: Assertion) -> AssertionResult:
        """Validate that output contains expected text.

        Args:
            assertion: Assertion with expected substring

        Returns:
            AssertionResult
        """
        expected = str(assertion.expected)
        actual = str(assertion.actual) if assertion.actual else ""

        passed = expected in actual

        if not passed:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                error_message=f"Output does not contain expected text",
                expected_value=f"Contains '{expected}'",
                actual_value=actual,
            )

        return AssertionResult(
            assertion=assertion,
            passed=True,
            expected_value=expected,
            actual_value=actual,
        )

    def _validate_not_contains(self, assertion: Assertion) -> AssertionResult:
        """Validate that output does NOT contain expected text.

        Args:
            assertion: Assertion with text that should not be present

        Returns:
            AssertionResult
        """
        expected = str(assertion.expected)
        actual = str(assertion.actual) if assertion.actual else ""

        passed = expected not in actual

        if not passed:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                error_message=f"Output unexpectedly contains text",
                expected_value=f"Not contains '{expected}'",
                actual_value=actual,
            )

        return AssertionResult(
            assertion=assertion,
            passed=True,
            expected_value=expected,
            actual_value=actual,
        )

    def _validate_regex(self, assertion: Assertion) -> AssertionResult:
        """Validate that output matches regex pattern.

        Args:
            assertion: Assertion with regex pattern

        Returns:
            AssertionResult
        """
        pattern = str(assertion.expected)
        actual = str(assertion.actual) if assertion.actual else ""

        try:
            match = re.search(pattern, actual, re.MULTILINE | re.DOTALL)
            passed = match is not None
        except re.error as e:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                error_message=f"Invalid regex pattern: {e}",
                expected_value=pattern,
            )

        if not passed:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                error_message="Output does not match regex pattern",
                expected_value=f"Match regex '{pattern}'",
                actual_value=actual,
            )

        return AssertionResult(
            assertion=assertion,
            passed=True,
            expected_value=pattern,
            actual_value=actual,
        )

    def _validate_lines(self, assertion: Assertion) -> AssertionResult:
        """Validate line count in output.

        Args:
            assertion: Assertion with expected line count

        Returns:
            AssertionResult
        """
        expected = int(assertion.expected)
        actual_text = str(assertion.actual) if assertion.actual else ""
        actual_lines = len(actual_text.splitlines())

        passed = expected == actual_lines

        if not passed:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                error_message="Line count mismatch",
                expected_value=f"{expected} lines",
                actual_value=f"{actual_lines} lines",
            )

        return AssertionResult(
            assertion=assertion,
            passed=True,
            expected_value=expected,
            actual_value=actual_lines,
        )

    def _validate_json(self, assertion: Assertion) -> AssertionResult:
        """Validate JSON structure.

        Args:
            assertion: Assertion with expected JSON structure

        Returns:
            AssertionResult
        """
        actual_text = str(assertion.actual) if assertion.actual else ""

        try:
            actual_json = json.loads(actual_text)
        except json.JSONDecodeError as e:
            return AssertionResult(
                assertion=assertion,
                passed=False,
                error_message=f"Invalid JSON: {e}",
                actual_value=actual_text,
            )

        # If expected is a dict, do structure comparison
        if isinstance(assertion.expected, dict):
            passed = self._compare_json_structure(assertion.expected, actual_json)
            if not passed:
                return AssertionResult(
                    assertion=assertion,
                    passed=False,
                    error_message="JSON structure mismatch",
                    expected_value=json.dumps(assertion.expected, indent=2),
                    actual_value=json.dumps(actual_json, indent=2),
                )
        else:
            # String comparison
            expected_json = json.loads(str(assertion.expected))
            passed = expected_json == actual_json

            if not passed:
                return AssertionResult(
                    assertion=assertion,
                    passed=False,
                    error_message="JSON content mismatch",
                    expected_value=json.dumps(expected_json, indent=2),
                    actual_value=json.dumps(actual_json, indent=2),
                )

        return AssertionResult(
            assertion=assertion,
            passed=True,
            expected_value=assertion.expected,
            actual_value=actual_json,
        )

    def _compare_json_structure(self, expected: Any, actual: Any) -> bool:
        """Compare JSON structures recursively.

        Args:
            expected: Expected JSON structure
            actual: Actual JSON structure

        Returns:
            True if structures match
        """
        if type(expected) != type(actual):
            return False

        if isinstance(expected, dict):
            if set(expected.keys()) != set(actual.keys()):
                return False
            return all(
                self._compare_json_structure(expected[k], actual[k])
                for k in expected.keys()
            )
        elif isinstance(expected, list):
            if len(expected) != len(actual):
                return False
            return all(
                self._compare_json_structure(e, a)
                for e, a in zip(expected, actual)
            )
        else:
            return expected == actual

    def _generate_diff(self, expected: str, actual: str) -> str:
        """Generate unified diff between expected and actual.

        Args:
            expected: Expected string
            actual: Actual string

        Returns:
            Unified diff string
        """
        expected_lines = expected.splitlines(keepends=True)
        actual_lines = actual.splitlines(keepends=True)

        diff = difflib.unified_diff(
            expected_lines,
            actual_lines,
            fromfile="expected",
            tofile="actual",
            lineterm="",
        )

        return "".join(diff)

    def get_results(self) -> List[AssertionResult]:
        """Get all assertion results.

        Returns:
            List of all assertion results
        """
        return self._results.copy()

    def clear_results(self) -> None:
        """Clear all stored results."""
        self._results.clear()

    def has_failures(self) -> bool:
        """Check if any assertions failed.

        Returns:
            True if any assertion failed
        """
        return any(not result.passed for result in self._results)

    def get_summary(self) -> dict:
        """Get summary statistics.

        Returns:
            Dict with pass/fail counts
        """
        total = len(self._results)
        passed = sum(1 for r in self._results if r.passed)
        failed = total - passed

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0.0,
        }
