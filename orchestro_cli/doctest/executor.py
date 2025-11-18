"""Command executor for running documentation tests."""

from __future__ import annotations

import re
import subprocess
import time
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List

from .models import CommandTest, DocTestResult


class MatchMode(str, Enum):
    """Output matching mode for validation."""

    EXACT = "exact"          # Exact string match
    CONTAINS = "contains"    # Expected is substring of actual
    REGEX = "regex"          # Expected is regex pattern
    STARTSWITH = "startswith"  # Actual starts with expected
    ENDSWITH = "endswith"    # Actual ends with expected


class DocTestExecutor:
    """Executes documentation tests and validates output.

    Runs commands via subprocess and compares actual output against
    expected output using configurable matching strategies.
    """

    def __init__(
        self,
        working_dir: Optional[Path] = None,
        timeout: float = 30.0,
        match_mode: MatchMode = MatchMode.CONTAINS,
        strip_whitespace: bool = True,
        env: Optional[Dict[str, str]] = None
    ):
        """Initialize executor.

        Args:
            working_dir: Working directory for command execution
            timeout: Command timeout in seconds (default: 30)
            match_mode: Output matching strategy
            strip_whitespace: Strip leading/trailing whitespace before comparison
            env: Environment variables for command execution
        """
        self.working_dir = working_dir or Path.cwd()
        self.timeout = timeout
        self.match_mode = match_mode
        self.strip_whitespace = strip_whitespace
        self.env = env or {}

    def execute_test(
        self,
        test: CommandTest,
        timeout: Optional[float] = None,
        match_mode: Optional[MatchMode] = None
    ) -> DocTestResult:
        """Execute a single command test.

        Args:
            test: Command test to execute
            timeout: Override default timeout
            match_mode: Override default match mode

        Returns:
            Test result with pass/fail status
        """
        start_time = time.time()
        timeout_value = timeout if timeout is not None else self.timeout
        match_mode_value = match_mode if match_mode is not None else self.match_mode

        try:
            # Execute command
            actual_output = self._run_command(test.command, timeout_value)

            # Validate output if expectation exists
            if test.has_expectation:
                expected = test.inline_expectation or test.expected_output or ""
                passed = self._validate_output(
                    actual_output,
                    expected,
                    match_mode_value
                )

                error_message = None
                if not passed:
                    error_message = self._generate_error_message(
                        expected,
                        actual_output,
                        match_mode_value
                    )
            else:
                # No expectation - just check command succeeded
                passed = True
                error_message = None

            execution_time = time.time() - start_time

            return DocTestResult(
                test=test,
                passed=passed,
                actual_output=actual_output,
                error_message=error_message,
                execution_time=execution_time
            )

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return DocTestResult(
                test=test,
                passed=False,
                actual_output="",
                error_message=f"Command timed out after {timeout_value}s",
                execution_time=execution_time
            )

        except subprocess.CalledProcessError as e:
            execution_time = time.time() - start_time
            error_output = e.stderr or e.stdout or ""
            return DocTestResult(
                test=test,
                passed=False,
                actual_output=error_output,
                error_message=f"Command failed with exit code {e.returncode}",
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return DocTestResult(
                test=test,
                passed=False,
                actual_output="",
                error_message=f"Execution error: {str(e)}",
                execution_time=execution_time
            )

    def execute_tests(
        self,
        tests: List[CommandTest],
        stop_on_failure: bool = False
    ) -> List[DocTestResult]:
        """Execute multiple command tests.

        Args:
            tests: List of command tests
            stop_on_failure: Stop execution on first failure

        Returns:
            List of test results
        """
        results: List[DocTestResult] = []

        for test in tests:
            result = self.execute_test(test)
            results.append(result)

            if stop_on_failure and not result.passed:
                break

        return results

    def _run_command(self, command: str, timeout: float) -> str:
        """Run command and capture output.

        Args:
            command: Command to execute
            timeout: Command timeout in seconds

        Returns:
            Command output (stdout + stderr)

        Raises:
            subprocess.TimeoutExpired: If command times out
            subprocess.CalledProcessError: If command fails
        """
        # Merge environment variables
        env = {**subprocess.os.environ, **self.env}

        # Execute command
        result = subprocess.run(
            command,
            shell=True,
            cwd=self.working_dir,
            timeout=timeout,
            capture_output=True,
            text=True,
            env=env,
            check=True  # Raise CalledProcessError on non-zero exit
        )

        # Combine stdout and stderr
        output = result.stdout
        if result.stderr:
            output += "\n" + result.stderr

        return output.strip() if self.strip_whitespace else output

    def _validate_output(
        self,
        actual: str,
        expected: str,
        match_mode: MatchMode
    ) -> bool:
        """Validate actual output against expected.

        Args:
            actual: Actual command output
            expected: Expected output
            match_mode: Matching strategy

        Returns:
            True if validation passed
        """
        # Normalize whitespace if configured
        if self.strip_whitespace:
            actual = actual.strip()
            expected = expected.strip()

        # Apply matching strategy
        if match_mode == MatchMode.EXACT:
            return actual == expected

        elif match_mode == MatchMode.CONTAINS:
            return expected in actual

        elif match_mode == MatchMode.REGEX:
            try:
                return bool(re.search(expected, actual))
            except re.error:
                # Invalid regex - treat as literal string
                return expected in actual

        elif match_mode == MatchMode.STARTSWITH:
            return actual.startswith(expected)

        elif match_mode == MatchMode.ENDSWITH:
            return actual.endswith(expected)

        return False

    def _generate_error_message(
        self,
        expected: str,
        actual: str,
        match_mode: MatchMode
    ) -> str:
        """Generate detailed error message for failed validation.

        Args:
            expected: Expected output
            actual: Actual output
            match_mode: Matching mode used

        Returns:
            Error message describing the mismatch
        """
        lines = [f"Output validation failed (mode: {match_mode.value})"]

        # Truncate long outputs for readability
        max_len = 200
        expected_display = (
            expected[:max_len] + "..." if len(expected) > max_len else expected
        )
        actual_display = (
            actual[:max_len] + "..." if len(actual) > max_len else actual
        )

        lines.append(f"Expected: {expected_display}")
        lines.append(f"Actual: {actual_display}")

        return "\n".join(lines)

    def get_summary(self, results: List[DocTestResult]) -> Dict[str, Any]:
        """Generate summary statistics for test results.

        Args:
            results: List of test results

        Returns:
            Dictionary with summary statistics
        """
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        total_time = sum(r.execution_time for r in results)

        return {
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'success_rate': (passed / total * 100) if total > 0 else 0.0,
            'total_execution_time': total_time,
            'avg_execution_time': total_time / total if total > 0 else 0.0
        }
