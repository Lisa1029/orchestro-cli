"""Example: JSON reporter plugin.

Generates JSON format test reports.

Usage:
  orchestrator = Orchestrator(json_report_path="results.json")
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from orchestro_cli.interfaces.reporter_plugin import (
    BaseReporter,
    ScenarioReport,
)


class JSONReporter(BaseReporter):
    """Reporter that generates JSON format reports."""

    def __init__(self, verbose: bool = False):
        """Initialize JSON reporter.

        Args:
            verbose: Enable verbose logging
        """
        super().__init__(
            reporter_name="json",
            file_extension=".json",
            verbose=verbose
        )
        self._reports: list[Dict[str, Any]] = []

    def generate_report(
        self,
        report_data: ScenarioReport,
        output_path: Optional[Path] = None
    ) -> None:
        """Generate JSON report.

        Args:
            report_data: Scenario execution data
            output_path: Output file path
        """
        # Convert report to dict
        report_dict = {
            "scenario_name": report_data.scenario_name,
            "success": report_data.success,
            "start_time": report_data.start_time.isoformat(),
            "end_time": report_data.end_time.isoformat(),
            "duration_seconds": report_data.duration,
            "steps_executed": report_data.steps_executed,
            "validations": {
                "total": report_data.total_validations,
                "passed": report_data.validations_passed,
                "failed": report_data.validations_failed,
            },
            "error_message": report_data.error_message,
            "metadata": {**self._metadata, **(report_data.metadata or {})},
        }

        self._reports.append(report_dict)

        if output_path:
            # Write to file
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Include all reports
            output_data = {
                "generated_at": datetime.now().isoformat(),
                "total_scenarios": len(self._reports),
                "scenarios": self._reports,
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2)

            self.log(f"JSON report written to {output_path}")


def register(registry):
    """Register JSON reporter plugin.

    Args:
        registry: PluginRegistry instance
    """
    plugin = JSONReporter(verbose=True)
    registry.register_reporter_plugin(plugin)
    print(f"[Plugin] Registered: {plugin.reporter_name} reporter")
