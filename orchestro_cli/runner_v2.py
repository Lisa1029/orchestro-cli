"""ScenarioRunner - Backward compatible facade over new architecture.

This is a compatibility layer that delegates to the new component-based architecture
while maintaining the same public API.
"""

from __future__ import annotations

import asyncio
import os
import platform
import re
import shutil
import sys
import tempfile
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import time

import pexpect
import yaml

# Import legacy models for backward compatibility
from .runner import ScenarioStep, Validation

# Import new architecture components
from .core.orchestrator import Orchestrator


class ScenarioRunner:
    """Facade over new architecture for backward compatibility.

    This class maintains the same public API as v0.1.0 but delegates to
    the new component-based architecture internally.

    WARNING: This class is deprecated and will be removed in v0.3.0.
    Use Orchestrator directly for new code.
    """

    def __init__(
        self,
        scenario_path: Path,
        workspace: Optional[Path] = None,
        verbose: bool = False,
        junit_xml_path: Optional[Path] = None,
        snapshot_mode: Optional[Any] = None,
        snapshot_dir: Path = Path(".snapshots"),
        snapshot_interactive: bool = False
    ) -> None:
        """Initialize scenario runner (DEPRECATED - use Orchestrator).

        Args:
            scenario_path: Path to YAML scenario file
            workspace: Optional workspace for isolation
            verbose: Enable verbose logging
            junit_xml_path: Optional JUnit XML report path
            snapshot_mode: Optional snapshot testing mode
            snapshot_dir: Directory for snapshot storage
            snapshot_interactive: Require confirmation for snapshot updates
        """
        warnings.warn(
            "ScenarioRunner is deprecated and will be removed in v0.3.0. "
            "Use Orchestrator from orchestro_cli.core instead.",
            DeprecationWarning,
            stacklevel=2
        )

        self.scenario_path = scenario_path.resolve()
        self.verbose = verbose
        self.workspace = workspace.resolve() if workspace else None
        self.junit_xml_path = junit_xml_path

        # Load spec for dry-run compatibility
        self.spec = self._load_spec()

        # Create orchestrator
        self._orchestrator = Orchestrator(
            workspace=self.workspace,
            verbose=self.verbose,
            junit_xml_path=self.junit_xml_path,
            snapshot_mode=snapshot_mode,
            snapshot_dir=snapshot_dir,
            snapshot_interactive=snapshot_interactive
        )

        # Backward compatibility attributes
        self.process: Optional[pexpect.spawn] = None
        temp_dir = Path(tempfile.gettempdir()) / ".vyb_orchestro"
        temp_dir.mkdir(parents=True, exist_ok=True)
        self.trigger_dir = temp_dir / "screenshot_triggers"
        self.trigger_dir.mkdir(parents=True, exist_ok=True)

        # Import sentinel monitor for backward compat
        from .sentinel_monitor import SentinelMonitor
        sentinel_file = temp_dir / "sentinels"
        self.sentinel_monitor = SentinelMonitor(sentinel_file)

    def _log(self, message: str) -> None:
        """Log message if verbose enabled."""
        if self.verbose:
            print(f"[CLI Orchestro] {message}")

    def _load_spec(self) -> Dict[str, Any]:
        """Load YAML spec (for backward compatibility)."""
        with open(self.scenario_path, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)

    def validate(self) -> Dict[str, Any]:
        """Validate scenario structure without executing.

        This method is preserved for dry-run functionality.

        Returns:
            Dictionary with validation results
        """
        # Import original validation logic
        from .runner import ScenarioRunner as LegacyRunner

        # Create legacy runner just for validation
        legacy = LegacyRunner(
            scenario_path=self.scenario_path,
            workspace=self.workspace,
            verbose=self.verbose,
            junit_xml_path=self.junit_xml_path
        )

        return legacy.validate()

    def run(self) -> None:
        """Execute scenario (delegates to orchestrator)."""
        try:
            self._orchestrator.run(self.scenario_path)
        except Exception as e:
            # Preserve backward compatible error handling
            raise

    def _parse_steps(self) -> List[ScenarioStep]:
        """Parse steps from spec (backward compatibility)."""
        steps: List[ScenarioStep] = []
        for raw in self.spec.get("steps", []):
            expect_pattern = raw.get("expect") or raw.get("pattern")
            steps.append(
                ScenarioStep(
                    expect=expect_pattern,
                    send=raw.get("send"),
                    control=raw.get("control"),
                    note=raw.get("note"),
                    timeout=raw.get("timeout"),
                    raw=bool(raw.get("raw", False)),
                    screenshot=raw.get("screenshot"),
                )
            )
        return steps

    def _parse_validations(self) -> List[Validation]:
        """Parse validations from spec (backward compatibility)."""
        validations: List[Validation] = []
        for raw in self.spec.get("validations", []):
            validations.append(
                Validation(
                    type=raw.get("type"),
                    path=raw.get("path"),
                    text=raw.get("text"),
                )
            )
        return validations
