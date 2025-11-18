"""Main orchestrator - coordinates all components."""

import asyncio
from pathlib import Path
from typing import Optional
import io

import pexpect

from ..parsing import ScenarioParser
from ..execution import ProcessManager, StepExecutor
from ..validation import ValidationEngine
from ..reporting import ReporterManager
from ..sentinel_monitor import SentinelMonitor
from ..plugins import PluginManager, PluginRegistry
from ..snapshot import SnapshotEngine, SnapshotMode


class Orchestrator:
    """Coordinates scenario execution through specialized components.

    Single Responsibility: Orchestrate the execution flow.
    Complexity: LOW (delegates to specialized components)

    Supports plugin injection for extensibility:
    - Custom process drivers
    - Step plugins
    - Validator plugins
    - Reporter plugins
    """

    def __init__(
        self,
        workspace: Optional[Path] = None,
        verbose: bool = False,
        junit_xml_path: Optional[Path] = None,
        plugin_manager: Optional[PluginManager] = None,
        auto_discover_plugins: bool = False,
        snapshot_mode: Optional[SnapshotMode] = None,
        snapshot_dir: Path = Path(".snapshots"),
        snapshot_interactive: bool = False
    ):
        """Initialize orchestrator with configuration.

        Args:
            workspace: Optional workspace for isolation
            verbose: Enable verbose logging
            junit_xml_path: Optional path for JUnit XML report
            plugin_manager: Optional plugin manager (creates new if None)
            auto_discover_plugins: Auto-discover plugins from standard paths
            snapshot_mode: Optional snapshot testing mode
            snapshot_dir: Directory for snapshot storage
            snapshot_interactive: Require confirmation for snapshot updates
        """
        self.workspace = workspace
        self.verbose = verbose
        self.junit_xml_path = junit_xml_path
        self.snapshot_mode = snapshot_mode

        # Initialize plugin system
        self.plugin_manager = plugin_manager or PluginManager()
        if auto_discover_plugins:
            count = self.plugin_manager.discover_plugins()
            self._log(f"Auto-discovered {count} plugins")

        # Initialize components (can be overridden via dependency injection)
        self.parser = ScenarioParser()
        self.process_manager = ProcessManager(workspace=workspace, verbose=verbose)
        self.validation_engine = ValidationEngine(
            base_dir=workspace if workspace else Path.cwd(),
            verbose=verbose
        )
        self.reporter_manager = ReporterManager(
            junit_xml_path=junit_xml_path,
            verbose=verbose
        )

        # Initialize snapshot engine if enabled
        self.snapshot_engine: Optional[SnapshotEngine] = None
        if snapshot_mode:
            self.snapshot_engine = SnapshotEngine(
                mode=snapshot_mode,
                snapshot_dir=snapshot_dir,
                interactive_confirm=snapshot_interactive,
                verbose=verbose
            )

    def _log(self, message: str) -> None:
        """Log message if verbose enabled."""
        if self.verbose:
            print(f"[Orchestrator] {message}")

    def run(self, scenario_path: Path) -> None:
        """Execute scenario from file (synchronous wrapper).

        Args:
            scenario_path: Path to YAML scenario file

        Raises:
            Various exceptions from components
        """
        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, raise error
            raise RuntimeError(
                "Orchestrator.run() cannot be called from async context. "
                "Use 'await orchestrator.run_async(scenario_path)' instead."
            )
        except RuntimeError:
            # No event loop running, safe to use asyncio.run()
            asyncio.run(self._run_async(scenario_path))

    async def run_async(self, scenario_path: Path) -> None:
        """Execute scenario from file (async version).

        Use this method when calling from async context (e.g., worker pools).

        Args:
            scenario_path: Path to YAML scenario file

        Raises:
            Various exceptions from components
        """
        await self._run_async(scenario_path)

    async def _run_async(self, scenario_path: Path) -> None:
        """Async scenario execution.

        Args:
            scenario_path: Path to YAML scenario file
        """
        # Parse scenario
        self._log("Parsing scenario...")
        scenario = self.parser.parse_file(scenario_path)
        self._log(f"Loaded: {scenario.name} ({scenario.step_count} steps)")

        # Start tracking
        self.reporter_manager.start_scenario(scenario.name)

        # Capture output buffers for snapshot testing
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        try:
            # Spawn process
            self._log(f"Spawning process: {scenario.command}")
            process = self.process_manager.spawn(
                command=scenario.command,
                env=scenario.env,
                timeout=scenario.timeout
            )

            # Initialize sentinel monitor
            sentinel_file = self.process_manager.sentinel_file
            sentinel_monitor = SentinelMonitor(sentinel_file)
            sentinel_monitor.clear()

            # Give process time to initialize
            await asyncio.sleep(2)

            # Check if process is alive
            if not self.process_manager.is_alive():
                raise RuntimeError(
                    f"Process failed to start. "
                    f"Exit status: {self.process_manager.exit_status}"
                )

            self._log("Process alive and ready")

            # Create step executor
            step_executor = StepExecutor(
                process=process,
                sentinel_monitor=sentinel_monitor,
                trigger_dir=self.process_manager.trigger_dir,
                verbose=self.verbose
            )

            # Execute all steps
            self._log(f"Executing {scenario.step_count} steps...")
            for i, step in enumerate(scenario.steps, 1):
                self._log(f"Step {i}/{scenario.step_count}: {step.step_type}")
                await step_executor.execute_step(step, scenario.timeout)

            # Wait for process completion
            try:
                process.expect(pexpect.EOF, timeout=5)
            except Exception:
                self._log("Process did not terminate cleanly")

            # Capture output for snapshot testing
            if self.snapshot_engine and hasattr(process, 'before'):
                # Capture stdout from pexpect
                stdout_output = process.before if process.before else ""
                if isinstance(stdout_output, bytes):
                    stdout_output = stdout_output.decode('utf-8', errors='replace')
                stdout_buffer.write(str(stdout_output))

            # Get exit code
            exit_code = self.process_manager.exit_status or 0

            # Run validations
            if scenario.validations:
                self._log(f"Running {scenario.validation_count} validations...")
                self.validation_engine.validate_all(scenario.validations)
                self._log("All validations passed")

            # Cleanup
            sentinel_monitor.cleanup()

            # Process snapshot if enabled
            if self.snapshot_engine:
                snapshot_result = self.snapshot_engine.process_output(
                    scenario_name=scenario.name,
                    stdout=stdout_buffer.getvalue(),
                    stderr=stderr_buffer.getvalue(),
                    exit_code=exit_code
                )

                # Log snapshot result
                if snapshot_result.passed:
                    self._log(f"Snapshot: {snapshot_result.message}")
                else:
                    self._log(f"Snapshot FAILED: {snapshot_result.message}")
                    # In verify mode, fail the scenario if snapshot doesn't match
                    if self.snapshot_mode == SnapshotMode.VERIFY:
                        raise AssertionError(f"Snapshot verification failed:\n{snapshot_result.message}")

            # Mark success
            self.reporter_manager.finish_scenario(success=True)

        except Exception as e:
            # Mark failure
            self.reporter_manager.finish_scenario(success=False, error=e)
            raise

        finally:
            # Generate reports
            self.reporter_manager.generate_reports()

            # Ensure process cleanup
            if self.process_manager.is_alive():
                self.process_manager.terminate()
