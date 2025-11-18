"""Snapshot testing engine - orchestrates capture, verify, update operations.

This is the main entry point for snapshot testing functionality.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import (
    SnapshotMode,
    CapturedOutput,
    Snapshot,
    SnapshotResult,
)
from .storage import SnapshotStorage
from .diff import SnapshotDiffer


class SnapshotEngine:
    """Orchestrates snapshot testing operations.

    Single Responsibility: Coordinate snapshot capture, verification, and updates.

    Usage:
        # Record mode
        engine = SnapshotEngine(mode=SnapshotMode.RECORD)
        engine.record_snapshot("test_scenario", stdout, stderr, exit_code)

        # Verify mode (CI/CD)
        engine = SnapshotEngine(mode=SnapshotMode.VERIFY)
        result = engine.verify_snapshot("test_scenario", stdout, stderr, exit_code)
        if result.failed:
            print(result.message)

        # Update mode
        engine = SnapshotEngine(mode=SnapshotMode.UPDATE)
        engine.update_snapshot("test_scenario", stdout, stderr, exit_code)
    """

    def __init__(
        self,
        mode: SnapshotMode = SnapshotMode.VERIFY,
        snapshot_dir: Path = Path(".snapshots"),
        context_lines: int = 3,
        enable_colors: bool = True,
        interactive_confirm: bool = False,
        verbose: bool = False,
    ):
        """Initialize snapshot engine.

        Args:
            mode: Snapshot testing mode
            snapshot_dir: Directory for snapshot storage
            context_lines: Number of context lines in diffs
            enable_colors: Enable colored output
            interactive_confirm: Require confirmation for updates
            verbose: Enable verbose logging
        """
        self.mode = mode
        self.snapshot_dir = snapshot_dir
        self.interactive_confirm = interactive_confirm
        self.verbose = verbose

        # Initialize components
        self.storage = SnapshotStorage(snapshot_dir=snapshot_dir)
        self.differ = SnapshotDiffer(
            context_lines=context_lines, enable_colors=enable_colors
        )

    def _log(self, message: str) -> None:
        """Log message if verbose enabled."""
        if self.verbose:
            print(f"[SnapshotEngine] {message}")

    def process_output(
        self,
        scenario_name: str,
        stdout: str,
        stderr: str,
        exit_code: int,
        metadata: Optional[dict] = None,
    ) -> SnapshotResult:
        """Process output based on current mode.

        This is the main entry point that delegates to the appropriate handler.

        Args:
            scenario_name: Name of the scenario
            stdout: Standard output
            stderr: Standard error
            exit_code: Exit code
            metadata: Optional metadata

        Returns:
            SnapshotResult indicating success/failure
        """
        if self.mode == SnapshotMode.RECORD:
            return self.record_snapshot(
                scenario_name, stdout, stderr, exit_code, metadata
            )
        elif self.mode == SnapshotMode.VERIFY:
            return self.verify_snapshot(
                scenario_name, stdout, stderr, exit_code, metadata
            )
        elif self.mode == SnapshotMode.UPDATE:
            return self.update_snapshot(
                scenario_name, stdout, stderr, exit_code, metadata
            )
        else:
            raise ValueError(f"Unknown snapshot mode: {self.mode}")

    def record_snapshot(
        self,
        scenario_name: str,
        stdout: str,
        stderr: str,
        exit_code: int,
        metadata: Optional[dict] = None,
    ) -> SnapshotResult:
        """Record new snapshot.

        Args:
            scenario_name: Name of the scenario
            stdout: Standard output
            stderr: Standard error
            exit_code: Exit code
            metadata: Optional metadata

        Returns:
            SnapshotResult indicating success
        """
        self._log(f"Recording snapshot: {scenario_name}")

        # Check if snapshot already exists
        if self.storage.exists(scenario_name):
            return SnapshotResult(
                passed=False,
                message=f"Snapshot already exists for '{scenario_name}'. Use UPDATE mode to overwrite.",
                snapshot_exists=True,
                snapshot_path=str(
                    self.storage.get_snapshot_path(scenario_name)
                ),
            )

        # Create snapshot
        output = CapturedOutput(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
        )

        snapshot = Snapshot(
            scenario_name=scenario_name,
            output=output,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Save snapshot
        self.storage.save(snapshot)
        snapshot_path = self.storage.get_snapshot_path(scenario_name)

        self._log(f"Snapshot recorded: {snapshot_path}")

        return SnapshotResult(
            passed=True,
            message=f"Snapshot recorded for '{scenario_name}' at {snapshot_path}",
            snapshot_exists=False,
            snapshot_path=str(snapshot_path),
        )

    def verify_snapshot(
        self,
        scenario_name: str,
        stdout: str,
        stderr: str,
        exit_code: int,
        metadata: Optional[dict] = None,
    ) -> SnapshotResult:
        """Verify output against stored snapshot.

        Args:
            scenario_name: Name of the scenario
            stdout: Standard output
            stderr: Standard error
            exit_code: Exit code
            metadata: Optional metadata

        Returns:
            SnapshotResult with verification details
        """
        self._log(f"Verifying snapshot: {scenario_name}")

        # Load snapshot
        snapshot = self.storage.load(scenario_name)

        if snapshot is None:
            snapshot_path = self.storage.get_snapshot_path(scenario_name)
            return SnapshotResult(
                passed=False,
                message=f"No snapshot found for '{scenario_name}'. Run with --snapshot=record to create it.",
                snapshot_exists=False,
                snapshot_path=str(snapshot_path),
            )

        # Create actual output
        actual = CapturedOutput(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
        )

        # Compare
        diff_result = self.differ.compare(snapshot.output, actual)

        if diff_result.is_identical:
            self._log(f"Snapshot verified: {scenario_name}")
            return SnapshotResult(
                passed=True,
                message=f"Output matches snapshot for '{scenario_name}'",
                snapshot_exists=True,
                snapshot_path=str(
                    self.storage.get_snapshot_path(scenario_name)
                ),
            )
        else:
            # Format diff for display
            diff_text = self.differ.format_diff(diff_result)

            self._log(f"Snapshot mismatch: {scenario_name}")

            return SnapshotResult(
                passed=False,
                diff_result=diff_result,
                message=f"Output differs from snapshot for '{scenario_name}':\n\n{diff_text}",
                snapshot_exists=True,
                snapshot_path=str(
                    self.storage.get_snapshot_path(scenario_name)
                ),
            )

    def update_snapshot(
        self,
        scenario_name: str,
        stdout: str,
        stderr: str,
        exit_code: int,
        metadata: Optional[dict] = None,
    ) -> SnapshotResult:
        """Update existing snapshot or create new one.

        Args:
            scenario_name: Name of the scenario
            stdout: Standard output
            stderr: Standard error
            exit_code: Exit code
            metadata: Optional metadata

        Returns:
            SnapshotResult indicating success
        """
        self._log(f"Updating snapshot: {scenario_name}")

        # Check if snapshot exists
        snapshot_exists = self.storage.exists(scenario_name)
        existing_snapshot = (
            self.storage.load(scenario_name) if snapshot_exists else None
        )

        # Interactive confirmation if enabled
        if self.interactive_confirm and snapshot_exists:
            if not self._confirm_update(scenario_name, existing_snapshot):
                return SnapshotResult(
                    passed=False,
                    message=f"Update cancelled for '{scenario_name}'",
                    snapshot_exists=True,
                    snapshot_path=str(
                        self.storage.get_snapshot_path(scenario_name)
                    ),
                )

        # Create updated output
        output = CapturedOutput(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
        )

        # Create snapshot
        snapshot = Snapshot(
            scenario_name=scenario_name,
            output=output,
            created_at=(
                existing_snapshot.created_at
                if existing_snapshot
                else datetime.utcnow()
            ),
            updated_at=datetime.utcnow(),
        )

        # Save snapshot
        self.storage.save(snapshot)
        snapshot_path = self.storage.get_snapshot_path(scenario_name)

        action = "updated" if snapshot_exists else "created"
        self._log(f"Snapshot {action}: {snapshot_path}")

        return SnapshotResult(
            passed=True,
            message=f"Snapshot {action} for '{scenario_name}' at {snapshot_path}",
            snapshot_exists=snapshot_exists,
            snapshot_path=str(snapshot_path),
        )

    def _confirm_update(
        self, scenario_name: str, existing_snapshot: Optional[Snapshot]
    ) -> bool:
        """Prompt user to confirm snapshot update.

        Args:
            scenario_name: Name of the scenario
            existing_snapshot: Existing snapshot

        Returns:
            True if confirmed, False otherwise
        """
        print(f"\nUpdate snapshot for '{scenario_name}'?")

        if existing_snapshot:
            print(
                f"  Created: {existing_snapshot.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            print(
                f"  Updated: {existing_snapshot.updated_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        response = input("Confirm [y/N]: ").strip().lower()
        return response in ("y", "yes")

    def list_snapshots(self) -> list[str]:
        """List all stored snapshots.

        Returns:
            List of scenario names with snapshots
        """
        return self.storage.list_scenarios()

    def delete_snapshot(self, scenario_name: str) -> bool:
        """Delete a snapshot.

        Args:
            scenario_name: Name of scenario

        Returns:
            True if deleted, False if didn't exist
        """
        return self.storage.delete(scenario_name)
