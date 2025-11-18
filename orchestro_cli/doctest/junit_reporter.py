"""JUnit XML reporter for documentation tests.

Converts documentation test results to JUnit XML format for CI/CD integration.
Compatible with Jenkins, GitHub Actions, GitLab CI, Azure DevOps, and CircleCI.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List
import socket

from orchestro_cli.junit_reporter import JUnitReporter, TestSuite, TestCase
from .models import DocTestResult


class DocTestJUnitReporter:
    """Converts documentation test results to JUnit XML format.

    Uses the existing Orchestro JUnit infrastructure to ensure consistent
    reporting across all Orchestro testing features.
    """

    def generate_report(
        self,
        results: List[DocTestResult],
        output_path: Path
    ) -> None:
        """Generate JUnit XML report from test results.

        Args:
            output_path: Path where XML report should be written
            results: List of documentation test results
        """
        # Group results by source file
        results_by_file = self._group_by_file(results)

        # Create JUnit reporter
        reporter = JUnitReporter()

        # Create test suite for each source file
        for file_path, file_results in results_by_file.items():
            suite = self._create_test_suite(file_path, file_results)
            reporter.add_test_suite(suite)

        # Generate XML file
        reporter.generate_xml(output_path)

    def _group_by_file(
        self,
        results: List[DocTestResult]
    ) -> dict[Path, List[DocTestResult]]:
        """Group results by source file.

        Args:
            results: List of test results

        Returns:
            Dictionary mapping file paths to their results
        """
        grouped: dict[Path, List[DocTestResult]] = {}

        for result in results:
            file_path = result.test.source_file or Path('<unknown>')
            if file_path not in grouped:
                grouped[file_path] = []
            grouped[file_path].append(result)

        return grouped

    def _create_test_suite(
        self,
        file_path: Path,
        results: List[DocTestResult]
    ) -> TestSuite:
        """Create JUnit test suite from file results.

        Args:
            file_path: Source file path
            results: Test results from this file

        Returns:
            JUnit TestSuite
        """
        # Create test suite
        suite = TestSuite(
            name=f"doctest.{file_path.stem}",
            test_cases=[],
            timestamp=datetime.utcnow().isoformat(),
            hostname=socket.gethostname()
        )

        # Convert each result to test case
        for result in results:
            test_case = self._create_test_case(result)
            suite.test_cases.append(test_case)

        return suite

    def _create_test_case(self, result: DocTestResult) -> TestCase:
        """Convert test result to JUnit test case.

        Args:
            result: Documentation test result

        Returns:
            JUnit TestCase
        """
        # Generate test case name
        command = result.test.command
        line_num = result.test.line_number
        name = f"line_{line_num}_{self._sanitize_name(command)}"

        # Create base test case
        test_case = TestCase(
            name=name,
            classname=f"doctest.{result.test.source_file.stem if result.test.source_file else 'unknown'}",
            time=result.execution_time
        )

        # Add system output
        if result.actual_output:
            test_case.system_out = result.actual_output

        # Add failure information if test failed
        if not result.passed:
            # Determine failure type
            if result.error_message and "timed out" in result.error_message.lower():
                failure_type = "TimeoutError"
            elif result.error_message and "exit code" in result.error_message.lower():
                failure_type = "CommandError"
            else:
                failure_type = "OutputMismatch"

            # Create failure message
            test_case.failure_type = failure_type
            test_case.failure_message = result.error_message or "Test failed"

            # Create detailed traceback
            traceback_lines = [
                f"Command: {result.test.command}",
                f"Location: {result.location}",
                "",
            ]

            if result.test.has_expectation:
                traceback_lines.append(f"Expectation type: {result.test.expectation_type}")
                if result.test.inline_expectation:
                    traceback_lines.append(f"Expected: {result.test.inline_expectation}")
                elif result.test.expected_output:
                    traceback_lines.append("Expected output:")
                    traceback_lines.append(result.test.expected_output)
                    traceback_lines.append("")

            if result.actual_output:
                traceback_lines.append("Actual output:")
                traceback_lines.append(result.actual_output)
                traceback_lines.append("")

            if result.error_message:
                traceback_lines.append("Error:")
                traceback_lines.append(result.error_message)

            test_case.failure_traceback = "\n".join(traceback_lines)

        return test_case

    def _sanitize_name(self, text: str) -> str:
        """Sanitize text for use in test case name.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text safe for XML
        """
        # Truncate long commands
        if len(text) > 50:
            text = text[:47] + "..."

        # Replace special characters
        safe_chars = []
        for char in text:
            if char.isalnum() or char in '-_.':
                safe_chars.append(char)
            elif char == ' ':
                safe_chars.append('_')
            else:
                # Skip other characters
                pass

        return ''.join(safe_chars) or 'test'
