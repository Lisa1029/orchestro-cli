"""Reporter management for multiple output formats."""

from pathlib import Path
from typing import Optional

from ..junit_reporter import JUnitReporter, ScenarioTestResult


class ReporterManager:
    """Manages multiple reporters for scenario results.

    Single Responsibility: Coordinate report generation in various formats.
    """

    def __init__(
        self,
        junit_xml_path: Optional[Path] = None,
        verbose: bool = False
    ):
        """Initialize reporter manager.

        Args:
            junit_xml_path: Optional path for JUnit XML report
            verbose: Enable verbose logging
        """
        self.junit_xml_path = junit_xml_path
        self.verbose = verbose
        self.test_result: Optional[ScenarioTestResult] = None

    def _log(self, message: str) -> None:
        """Log message if verbose enabled."""
        if self.verbose:
            print(f"[ReporterManager] {message}")

    def start_scenario(self, scenario_name: str) -> None:
        """Mark start of scenario execution.

        Args:
            scenario_name: Name of the scenario
        """
        if self.junit_xml_path:
            self.test_result = ScenarioTestResult(scenario_name)
            self.test_result.start()
            self._log(f"Started tracking: {scenario_name}")

    def finish_scenario(self, success: bool, error: Optional[Exception] = None) -> None:
        """Mark end of scenario execution.

        Args:
            success: Whether scenario passed
            error: Optional exception if failed
        """
        if self.test_result:
            self.test_result.finish(success=success, error=error)
            self._log(f"Finished tracking: {'PASS' if success else 'FAIL'}")

    def generate_reports(self) -> None:
        """Generate all configured reports."""
        if self.junit_xml_path and self.test_result:
            self._generate_junit_xml()

    def _generate_junit_xml(self) -> None:
        """Generate JUnit XML report."""
        if not self.test_result or not self.junit_xml_path:
            return

        self._log(f"Generating JUnit XML: {self.junit_xml_path}")

        reporter = JUnitReporter()
        reporter.add_test_suite(self.test_result.to_test_suite())
        reporter.generate_xml(self.junit_xml_path)

        self._log(f"JUnit XML report generated: {self.junit_xml_path}")
