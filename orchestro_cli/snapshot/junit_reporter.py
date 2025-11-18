"""JUnit XML reporter integration for snapshot testing.

Extends JUnit reports with snapshot verification results:
- Adds snapshot mismatches as test failures
- Includes diff output in failure messages
- Tracks snapshot coverage
"""

from typing import Optional

from ..junit_reporter import TestCase
from .models import SnapshotResult


class SnapshotJUnitIntegration:
    """Integrates snapshot results into JUnit XML reports.

    Single Responsibility: Convert snapshot results to JUnit format.
    """

    @staticmethod
    def create_test_case(
        scenario_name: str,
        snapshot_result: SnapshotResult,
        duration: float = 0.0,
    ) -> TestCase:
        """Create JUnit TestCase from snapshot result.

        Args:
            scenario_name: Name of the scenario
            snapshot_result: Snapshot verification result
            duration: Test execution duration

        Returns:
            TestCase for JUnit XML
        """
        test_case = TestCase(
            name=f"{scenario_name}_snapshot",
            classname="orchestro.snapshot",
            time=duration,
        )

        if snapshot_result.passed:
            # Success case
            test_case.system_out = snapshot_result.message
        else:
            # Failure case
            if not snapshot_result.snapshot_exists:
                # Missing snapshot
                test_case.failure_message = (
                    f"Missing snapshot for '{scenario_name}'"
                )
                test_case.failure_type = "MissingSnapshotError"
                test_case.failure_traceback = snapshot_result.message
            elif snapshot_result.has_diff:
                # Snapshot mismatch
                test_case.failure_message = (
                    f"Snapshot mismatch for '{scenario_name}'"
                )
                test_case.failure_type = "SnapshotMismatchError"

                # Include diff in failure traceback
                diff_details = []

                if snapshot_result.diff_result:
                    diff_details.append(
                        f"Similarity: {snapshot_result.diff_result.similarity_score}%"
                    )

                    if not snapshot_result.diff_result.exit_code_match:
                        diff_details.append("\nExit Code Mismatch")

                    if snapshot_result.diff_result.has_stdout_diff:
                        diff_details.append("\nSTDOUT Differences:")
                        diff_details.extend(
                            SnapshotJUnitIntegration._format_diff_lines(
                                snapshot_result.diff_result.stdout_diff
                            )
                        )

                    if snapshot_result.diff_result.has_stderr_diff:
                        diff_details.append("\nSTDERR Differences:")
                        diff_details.extend(
                            SnapshotJUnitIntegration._format_diff_lines(
                                snapshot_result.diff_result.stderr_diff
                            )
                        )

                test_case.failure_traceback = "\n".join(diff_details)
            else:
                # Other failure
                test_case.failure_message = snapshot_result.message
                test_case.failure_type = "SnapshotError"

        return test_case

    @staticmethod
    def _format_diff_lines(diff_lines: list) -> list[str]:
        """Format diff lines for JUnit output (no colors).

        Args:
            diff_lines: List of DiffLine objects

        Returns:
            List of formatted strings
        """
        formatted = []

        for line in diff_lines:
            if line.is_header:
                formatted.append(line.content)
            elif line.is_addition:
                formatted.append(f"+ {line.content}")
            elif line.is_deletion:
                formatted.append(f"- {line.content}")
            elif line.is_context:
                formatted.append(f"  {line.content}")

        return formatted

    @staticmethod
    def add_snapshot_metadata(
        test_case: TestCase, snapshot_result: SnapshotResult
    ) -> None:
        """Add snapshot metadata to existing test case.

        Enriches a scenario test case with snapshot information.

        Args:
            test_case: Existing test case to enrich
            snapshot_result: Snapshot result to add
        """
        # Add snapshot info to system-out
        snapshot_info = []
        snapshot_info.append("\n--- Snapshot Verification ---")
        snapshot_info.append(f"Status: {'PASS' if snapshot_result.passed else 'FAIL'}")

        if snapshot_result.snapshot_path:
            snapshot_info.append(f"Path: {snapshot_result.snapshot_path}")

        if snapshot_result.diff_result:
            snapshot_info.append(
                f"Similarity: {snapshot_result.diff_result.similarity_score}%"
            )

        # Append to existing system-out
        if test_case.system_out:
            test_case.system_out += "\n" + "\n".join(snapshot_info)
        else:
            test_case.system_out = "\n".join(snapshot_info)

        # If snapshot failed, add to failure message
        if not snapshot_result.passed and not test_case.failure_message:
            test_case.failure_message = (
                f"Snapshot verification failed: {snapshot_result.message}"
            )
            test_case.failure_type = "SnapshotMismatchError"
