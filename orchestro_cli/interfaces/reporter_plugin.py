"""Reporter plugin protocol for custom report formats.

This protocol enables adding new report formats without modifying
the reporting engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol


@dataclass
class ScenarioReport:
    """Report data for a scenario execution."""

    scenario_name: str
    success: bool
    start_time: datetime
    end_time: datetime
    duration: float
    steps_executed: int
    validations_passed: int
    validations_failed: int
    error_message: Optional[str] = None
    output_log: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @property
    def total_validations(self) -> int:
        """Get total validation count."""
        return self.validations_passed + self.validations_failed


class ReporterPlugin(Protocol):
    """Protocol for custom report format implementations.

    Plugins can add new report formats beyond JUnit XML.

    Examples:
        - HTMLReporter (interactive HTML reports)
        - JSONReporter (machine-readable JSON)
        - MarkdownReporter (GitHub-compatible markdown)
        - SlackReporter (post to Slack)
        - PrometheusReporter (export metrics)
        - AllureReporter (Allure test reporting)
        - CustomDashboardReporter (send to custom dashboard)
    """

    @property
    def reporter_name(self) -> str:
        """Unique identifier for this reporter.

        Returns:
            Reporter name (e.g., 'html', 'json', 'slack')
        """
        ...

    @property
    def file_extension(self) -> Optional[str]:
        """File extension for this report format.

        Returns:
            Extension (e.g., '.html', '.json') or None for non-file reporters
        """
        ...

    def start_scenario(self, scenario_name: str) -> None:
        """Called when scenario execution starts.

        Args:
            scenario_name: Name of the scenario being executed
        """
        ...

    def finish_scenario(
        self,
        success: bool,
        error: Optional[Exception] = None
    ) -> None:
        """Called when scenario execution completes.

        Args:
            success: Whether scenario succeeded
            error: Exception if scenario failed
        """
        ...

    def generate_report(
        self,
        report_data: ScenarioReport,
        output_path: Optional[Path] = None
    ) -> None:
        """Generate the report.

        Args:
            report_data: Scenario execution data
            output_path: Optional output path (for file-based reporters)

        Raises:
            ReportGenerationError: If report generation fails
        """
        ...

    def add_metadata(self, key: str, value: Any) -> None:
        """Add custom metadata to the report.

        Args:
            key: Metadata key
            value: Metadata value
        """
        ...


class BaseReporter:
    """Base class for reporter implementations (optional convenience)."""

    def __init__(
        self,
        reporter_name: str,
        file_extension: Optional[str] = None,
        verbose: bool = False
    ):
        """Initialize reporter.

        Args:
            reporter_name: Unique reporter identifier
            file_extension: File extension for reports
            verbose: Enable verbose logging
        """
        self._reporter_name = reporter_name
        self._file_extension = file_extension
        self.verbose = verbose
        self._metadata: Dict[str, Any] = {}
        self._start_time: Optional[datetime] = None
        self._scenario_name: Optional[str] = None

    @property
    def reporter_name(self) -> str:
        """Get reporter name."""
        return self._reporter_name

    @property
    def file_extension(self) -> Optional[str]:
        """Get file extension."""
        return self._file_extension

    def log(self, message: str) -> None:
        """Log message if verbose enabled."""
        if self.verbose:
            print(f"[{self.reporter_name}] {message}")

    def start_scenario(self, scenario_name: str) -> None:
        """Record scenario start."""
        self._scenario_name = scenario_name
        self._start_time = datetime.now()
        self.log(f"Started: {scenario_name}")

    def finish_scenario(
        self,
        success: bool,
        error: Optional[Exception] = None
    ) -> None:
        """Record scenario completion."""
        status = "SUCCESS" if success else "FAILED"
        self.log(f"Finished: {self._scenario_name} [{status}]")

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata."""
        self._metadata[key] = value

    def generate_report(
        self,
        report_data: ScenarioReport,
        output_path: Optional[Path] = None
    ) -> None:
        """Generate report (must be implemented by subclass)."""
        raise NotImplementedError
