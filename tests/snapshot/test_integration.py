"""Integration tests for snapshot testing system."""

import pytest
from pathlib import Path
import tempfile
import shutil

from orchestro_cli.snapshot import (
    SnapshotEngine,
    SnapshotMode,
    SnapshotStorage,
)


class TestSnapshotIntegration:
    """Integration tests for full snapshot workflows."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for integration tests."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        # Cleanup
        if temp_path.exists():
            shutil.rmtree(temp_path)

    def test_full_record_verify_update_workflow(self, temp_dir):
        """Test complete workflow: record → verify → update."""
        scenario_name = "Integration Test"
        initial_output = "Hello, World!\n"
        modified_output = "Hello, Universe!\n"

        # Step 1: Record initial snapshot
        record_engine = SnapshotEngine(
            mode=SnapshotMode.RECORD, snapshot_dir=temp_dir
        )
        record_result = record_engine.record_snapshot(
            scenario_name=scenario_name,
            stdout=initial_output,
            stderr="",
            exit_code=0,
        )

        assert record_result.passed
        assert not record_result.snapshot_exists
        snapshot_path = Path(record_result.snapshot_path)
        assert snapshot_path.exists()
        assert (snapshot_path / "stdout.txt").read_text() == initial_output

        # Step 2: Verify with matching output
        verify_engine = SnapshotEngine(
            mode=SnapshotMode.VERIFY, snapshot_dir=temp_dir
        )
        verify_result_pass = verify_engine.verify_snapshot(
            scenario_name=scenario_name,
            stdout=initial_output,
            stderr="",
            exit_code=0,
        )

        assert verify_result_pass.passed
        assert verify_result_pass.snapshot_exists

        # Step 3: Verify with different output (should fail)
        verify_result_fail = verify_engine.verify_snapshot(
            scenario_name=scenario_name,
            stdout=modified_output,
            stderr="",
            exit_code=0,
        )

        assert not verify_result_fail.passed
        assert verify_result_fail.has_diff
        assert verify_result_fail.diff_result is not None

        # Step 4: Update with new output
        update_engine = SnapshotEngine(
            mode=SnapshotMode.UPDATE, snapshot_dir=temp_dir
        )
        update_result = update_engine.update_snapshot(
            scenario_name=scenario_name,
            stdout=modified_output,
            stderr="",
            exit_code=0,
        )

        assert update_result.passed
        assert (snapshot_path / "stdout.txt").read_text() == modified_output

        # Step 5: Verify updated snapshot
        verify_result_updated = verify_engine.verify_snapshot(
            scenario_name=scenario_name,
            stdout=modified_output,
            stderr="",
            exit_code=0,
        )

        assert verify_result_updated.passed

    def test_multiple_scenarios_in_same_directory(self, temp_dir):
        """Test managing multiple scenarios in same snapshot directory."""
        engine = SnapshotEngine(
            mode=SnapshotMode.RECORD, snapshot_dir=temp_dir
        )

        scenarios = [
            ("Scenario A", "Output A", ""),
            ("Scenario B", "Output B", "Error B"),
            ("Scenario C", "Output C", ""),
        ]

        # Record all scenarios
        for name, stdout, stderr in scenarios:
            result = engine.record_snapshot(
                scenario_name=name,
                stdout=stdout,
                stderr=stderr,
                exit_code=0,
            )
            assert result.passed

        # Verify all exist
        stored_scenarios = engine.list_snapshots()
        assert len(stored_scenarios) == 3
        assert all(name in stored_scenarios for name, _, _ in scenarios)

        # Verify each can be loaded independently
        storage = SnapshotStorage(snapshot_dir=temp_dir)
        for name, expected_stdout, expected_stderr in scenarios:
            snapshot = storage.load(name)
            assert snapshot is not None
            assert snapshot.output.stdout == expected_stdout
            assert snapshot.output.stderr == expected_stderr

    def test_snapshot_with_metadata(self, temp_dir):
        """Test metadata preservation through record/verify cycle."""
        metadata = {
            "command": "python -c 'print(123)'",
            "environment": {"PYTHONPATH": "/usr/lib"},
            "tags": ["python", "integration"],
        }

        # Record with metadata
        record_engine = SnapshotEngine(
            mode=SnapshotMode.RECORD, snapshot_dir=temp_dir
        )
        record_engine.record_snapshot(
            scenario_name="Metadata Test",
            stdout="123\n",
            stderr="",
            exit_code=0,
            metadata=metadata,
        )

        # Load and verify metadata
        storage = SnapshotStorage(snapshot_dir=temp_dir)
        snapshot = storage.load("Metadata Test")

        assert snapshot is not None
        assert snapshot.output.metadata["command"] == metadata["command"]
        assert snapshot.output.metadata["environment"] == metadata["environment"]
        assert snapshot.output.metadata["tags"] == metadata["tags"]

    def test_error_handling_for_corrupted_snapshot(self, temp_dir):
        """Test handling of corrupted snapshot files."""
        # Create valid snapshot
        engine = SnapshotEngine(
            mode=SnapshotMode.RECORD, snapshot_dir=temp_dir
        )
        engine.record_snapshot(
            scenario_name="Corrupted Test",
            stdout="Original",
            stderr="",
            exit_code=0,
        )

        # Corrupt the stdout file
        snapshot_path = temp_dir / "corrupted-test"
        stdout_file = snapshot_path / "stdout.txt"
        stdout_file.write_text("Corrupted content")

        # Verify should fail with checksum error
        storage = SnapshotStorage(snapshot_dir=temp_dir)
        with pytest.raises(ValueError, match="Checksum mismatch"):
            storage.load("Corrupted Test")

    def test_snapshot_deletion_workflow(self, temp_dir):
        """Test snapshot deletion."""
        engine = SnapshotEngine(
            mode=SnapshotMode.RECORD, snapshot_dir=temp_dir
        )

        # Create snapshot
        engine.record_snapshot(
            scenario_name="To Delete",
            stdout="temp",
            stderr="",
            exit_code=0,
        )

        assert "To Delete" in engine.list_snapshots()

        # Delete snapshot
        deleted = engine.delete_snapshot("To Delete")
        assert deleted is True
        assert "To Delete" not in engine.list_snapshots()

        # Try to delete again
        deleted_again = engine.delete_snapshot("To Delete")
        assert deleted_again is False

    def test_exit_code_change_detection(self, temp_dir):
        """Test detection of exit code changes."""
        scenario_name = "Exit Code Test"

        # Record with exit code 0
        record_engine = SnapshotEngine(
            mode=SnapshotMode.RECORD, snapshot_dir=temp_dir
        )
        record_engine.record_snapshot(
            scenario_name=scenario_name,
            stdout="Success",
            stderr="",
            exit_code=0,
        )

        # Verify with exit code 1
        verify_engine = SnapshotEngine(
            mode=SnapshotMode.VERIFY, snapshot_dir=temp_dir
        )
        result = verify_engine.verify_snapshot(
            scenario_name=scenario_name,
            stdout="Success",
            stderr="",
            exit_code=1,
        )

        assert not result.passed
        assert result.diff_result is not None
        assert not result.diff_result.exit_code_match

    def test_empty_outputs_handling(self, temp_dir):
        """Test handling of empty stdout/stderr."""
        engine = SnapshotEngine(
            mode=SnapshotMode.RECORD, snapshot_dir=temp_dir
        )

        # Record with empty outputs
        engine.record_snapshot(
            scenario_name="Empty Test",
            stdout="",
            stderr="",
            exit_code=0,
        )

        # Verify with empty outputs
        verify_engine = SnapshotEngine(
            mode=SnapshotMode.VERIFY, snapshot_dir=temp_dir
        )
        result = verify_engine.verify_snapshot(
            scenario_name="Empty Test",
            stdout="",
            stderr="",
            exit_code=0,
        )

        assert result.passed

        # Verify with non-empty output
        result_diff = verify_engine.verify_snapshot(
            scenario_name="Empty Test",
            stdout="Not empty",
            stderr="",
            exit_code=0,
        )

        assert not result_diff.passed
        assert result_diff.has_diff
