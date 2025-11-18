"""Snapshot testing system for regression testing via golden output comparison.

This module provides comprehensive snapshot testing capabilities:
- Capture command outputs (stdout, stderr, exit codes)
- Store snapshots in git-friendly format
- Compare outputs with golden snapshots
- Generate diffs for mismatches
- Support for verify/update/record modes

Usage:
    from orchestro_cli.snapshot import SnapshotEngine, SnapshotMode

    # Record snapshots
    engine = SnapshotEngine(mode=SnapshotMode.RECORD)
    engine.capture_output("scenario_name", stdout, stderr, exit_code)

    # Verify snapshots (CI/CD)
    engine = SnapshotEngine(mode=SnapshotMode.VERIFY)
    result = engine.verify_snapshot("scenario_name", stdout, stderr, exit_code)

    # Update snapshots
    engine = SnapshotEngine(mode=SnapshotMode.UPDATE)
    engine.update_snapshot("scenario_name", stdout, stderr, exit_code)
"""

from .models import (
    SnapshotMode,
    CapturedOutput,
    Snapshot,
    SnapshotResult,
)
from .storage import SnapshotStorage
from .diff import SnapshotDiffer
from .engine import SnapshotEngine

__all__ = [
    "SnapshotMode",
    "CapturedOutput",
    "Snapshot",
    "SnapshotResult",
    "SnapshotStorage",
    "SnapshotDiffer",
    "SnapshotEngine",
]
