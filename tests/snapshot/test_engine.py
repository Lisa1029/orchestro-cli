"""Tests for snapshot engine."""

import pytest
from pathlib import Path
import tempfile
import shutil

from orchestro_cli.snapshot.engine import SnapshotEngine
from orchestro_cli.snapshot.models import SnapshotMode


class TestSnapshotEngine:
    """Test SnapshotEngine class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for snapshots."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        # Cleanup
        if temp_path.exists():
            shutil.rmtree(temp_path)

    @pytest.fixture
    def record_engine(self, temp_dir):
        """Create engine in record mode."""
        return SnapshotEngine(
            mode=SnapshotMode.RECORD,
            snapshot_dir=temp_dir,
            verbose=False,
        )

    @pytest.fixture
    def verify_engine(self, temp_dir):
        """Create engine in verify mode."""
        return SnapshotEngine(
            mode=SnapshotMode.VERIFY,
            snapshot_dir=temp_dir,
            verbose=False,
        )

    @pytest.fixture
    def update_engine(self, temp_dir):
        """Create engine in update mode."""
        return SnapshotEngine(
            mode=SnapshotMode.UPDATE,
            snapshot_dir=temp_dir,
            verbose=False,
        )

    def test_record_new_snapshot(self, record_engine, temp_dir):
        """Test recording a new snapshot."""
        result = record_engine.record_snapshot(
            scenario_name="Test Scenario",
            stdout="Hello, World!\n",
            stderr="",
            exit_code=0,
        )

        assert result.passed
        assert not result.snapshot_exists
        assert "recorded" in result.message.lower()

        # Verify snapshot was saved
        snapshot_path = temp_dir / "test-scenario"
        assert snapshot_path.exists()
        assert (snapshot_path / "stdout.txt").exists()

    def test_record_existing_snapshot_fails(self, record_engine):
        """Test that recording fails if snapshot already exists."""
        # Record first time
        record_engine.record_snapshot(
            scenario_name="Test", stdout="test", stderr="", exit_code=0
        )

        # Try to record again
        result = record_engine.record_snapshot(
            scenario_name="Test", stdout="test2", stderr="", exit_code=0
        )

        assert not result.passed
        assert "already exists" in result.message.lower()

    def test_verify_matching_snapshot(self, temp_dir):
        """Test verifying a matching snapshot."""
        # First record
        record_engine = SnapshotEngine(
            mode=SnapshotMode.RECORD, snapshot_dir=temp_dir
        )
        record_engine.record_snapshot(
            scenario_name="Test", stdout="Hello!\n", stderr="", exit_code=0
        )

        # Then verify
        verify_engine = SnapshotEngine(
            mode=SnapshotMode.VERIFY, snapshot_dir=temp_dir
        )
        result = verify_engine.verify_snapshot(
            scenario_name="Test", stdout="Hello!\n", stderr="", exit_code=0
        )

        assert result.passed
        assert "matches" in result.message.lower()
        assert result.snapshot_exists

    def test_verify_mismatched_snapshot(self, temp_dir):
        """Test verifying a mismatched snapshot."""
        # First record
        record_engine = SnapshotEngine(
            mode=SnapshotMode.RECORD, snapshot_dir=temp_dir
        )
        record_engine.record_snapshot(
            scenario_name="Test", stdout="Hello!\n", stderr="", exit_code=0
        )

        # Then verify with different output
        verify_engine = SnapshotEngine(
            mode=SnapshotMode.VERIFY, snapshot_dir=temp_dir
        )
        result = verify_engine.verify_snapshot(
            scenario_name="Test", stdout="Goodbye!\n", stderr="", exit_code=0
        )

        assert not result.passed
        assert result.has_diff
        assert result.diff_result is not None
        assert "differs" in result.message.lower()

    def test_verify_missing_snapshot(self, verify_engine):
        """Test verifying when no snapshot exists."""
        result = verify_engine.verify_snapshot(
            scenario_name="Missing", stdout="test", stderr="", exit_code=0
        )

        assert not result.passed
        assert not result.snapshot_exists
        assert "no snapshot found" in result.message.lower()

    def test_update_existing_snapshot(self, temp_dir):
        """Test updating an existing snapshot."""
        # First record
        record_engine = SnapshotEngine(
            mode=SnapshotMode.RECORD, snapshot_dir=temp_dir
        )
        record_engine.record_snapshot(
            scenario_name="Test", stdout="Old output\n", stderr="", exit_code=0
        )

        # Then update
        update_engine = SnapshotEngine(
            mode=SnapshotMode.UPDATE, snapshot_dir=temp_dir
        )
        result = update_engine.update_snapshot(
            scenario_name="Test", stdout="New output\n", stderr="", exit_code=0
        )

        assert result.passed
        assert "updated" in result.message.lower()

        # Verify the update
        verify_engine = SnapshotEngine(
            mode=SnapshotMode.VERIFY, snapshot_dir=temp_dir
        )
        verify_result = verify_engine.verify_snapshot(
            scenario_name="Test", stdout="New output\n", stderr="", exit_code=0
        )

        assert verify_result.passed

    def test_update_creates_new_snapshot(self, update_engine):
        """Test that update creates new snapshot if none exists."""
        result = update_engine.update_snapshot(
            scenario_name="New", stdout="test", stderr="", exit_code=0
        )

        assert result.passed
        assert "created" in result.message.lower()

    def test_process_output_delegates_correctly(self, record_engine):
        """Test that process_output delegates to correct mode."""
        result = record_engine.process_output(
            scenario_name="Test", stdout="test", stderr="", exit_code=0
        )

        assert result.passed

    def test_list_snapshots(self, temp_dir):
        """Test listing snapshots."""
        engine = SnapshotEngine(
            mode=SnapshotMode.RECORD, snapshot_dir=temp_dir
        )

        # Initially empty
        assert engine.list_snapshots() == []

        # Add snapshots
        engine.record_snapshot(
            scenario_name="Alpha", stdout="test1", stderr="", exit_code=0
        )
        engine.record_snapshot(
            scenario_name="Beta", stdout="test2", stderr="", exit_code=0
        )

        # List
        snapshots = engine.list_snapshots()
        assert len(snapshots) == 2
        assert "Alpha" in snapshots
        assert "Beta" in snapshots

    def test_delete_snapshot(self, temp_dir):
        """Test deleting a snapshot."""
        engine = SnapshotEngine(
            mode=SnapshotMode.RECORD, snapshot_dir=temp_dir
        )

        # Record
        engine.record_snapshot(
            scenario_name="Test", stdout="test", stderr="", exit_code=0
        )

        # Delete
        result = engine.delete_snapshot("Test")
        assert result is True

        # Verify deleted
        assert not engine.storage.exists("Test")

    def test_metadata_preservation(self, temp_dir):
        """Test that metadata is preserved."""
        metadata = {
            "command": "echo test",
            "environment": {"PATH": "/usr/bin"},
        }

        # Record with metadata
        record_engine = SnapshotEngine(
            mode=SnapshotMode.RECORD, snapshot_dir=temp_dir
        )
        record_engine.record_snapshot(
            scenario_name="Test",
            stdout="test",
            stderr="",
            exit_code=0,
            metadata=metadata,
        )

        # Load and verify
        snapshot = record_engine.storage.load("Test")
        assert snapshot is not None
        assert snapshot.output.metadata["command"] == "echo test"

    def test_exit_code_mismatch_detection(self, temp_dir):
        """Test detection of exit code mismatches."""
        # Record with exit code 0
        record_engine = SnapshotEngine(
            mode=SnapshotMode.RECORD, snapshot_dir=temp_dir
        )
        record_engine.record_snapshot(
            scenario_name="Test", stdout="", stderr="", exit_code=0
        )

        # Verify with exit code 1
        verify_engine = SnapshotEngine(
            mode=SnapshotMode.VERIFY, snapshot_dir=temp_dir
        )
        result = verify_engine.verify_snapshot(
            scenario_name="Test", stdout="", stderr="", exit_code=1
        )

        assert not result.passed
        assert result.diff_result is not None
        assert not result.diff_result.exit_code_match

    def test_stderr_difference_detection(self, temp_dir):
        """Test detection of stderr differences."""
        # Record with no stderr
        record_engine = SnapshotEngine(
            mode=SnapshotMode.RECORD, snapshot_dir=temp_dir
        )
        record_engine.record_snapshot(
            scenario_name="Test", stdout="", stderr="", exit_code=0
        )

        # Verify with stderr
        verify_engine = SnapshotEngine(
            mode=SnapshotMode.VERIFY, snapshot_dir=temp_dir
        )
        result = verify_engine.verify_snapshot(
            scenario_name="Test",
            stdout="",
            stderr="Error occurred\n",
            exit_code=0,
        )

        assert not result.passed
        assert result.diff_result.has_stderr_diff

    def test_verbose_logging(self, temp_dir, capsys):
        """Test verbose logging."""
        engine = SnapshotEngine(
            mode=SnapshotMode.RECORD,
            snapshot_dir=temp_dir,
            verbose=True,
        )

        engine.record_snapshot(
            scenario_name="Test", stdout="test", stderr="", exit_code=0
        )

        captured = capsys.readouterr()
        assert "[SnapshotEngine]" in captured.out

    def test_interactive_confirmation_skip(self, temp_dir, monkeypatch):
        """Test interactive confirmation when user declines."""
        # Record first
        record_engine = SnapshotEngine(
            mode=SnapshotMode.RECORD, snapshot_dir=temp_dir
        )
        record_engine.record_snapshot(
            scenario_name="Test", stdout="old", stderr="", exit_code=0
        )

        # Update with confirmation required
        update_engine = SnapshotEngine(
            mode=SnapshotMode.UPDATE,
            snapshot_dir=temp_dir,
            interactive_confirm=True,
        )

        # Simulate user declining
        monkeypatch.setattr("builtins.input", lambda _: "n")

        result = update_engine.update_snapshot(
            scenario_name="Test", stdout="new", stderr="", exit_code=0
        )

        assert not result.passed
        assert "cancelled" in result.message.lower()
