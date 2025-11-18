"""Tests for snapshot storage."""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from orchestro_cli.snapshot.storage import SnapshotStorage
from orchestro_cli.snapshot.models import Snapshot, CapturedOutput


class TestSnapshotStorage:
    """Test SnapshotStorage class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for snapshots."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        # Cleanup
        if temp_path.exists():
            shutil.rmtree(temp_path)

    @pytest.fixture
    def storage(self, temp_dir):
        """Create storage instance."""
        return SnapshotStorage(snapshot_dir=temp_dir)

    @pytest.fixture
    def sample_snapshot(self):
        """Create sample snapshot."""
        output = CapturedOutput(
            stdout="Hello, World!\n",
            stderr="",
            exit_code=0,
            metadata={"command": "echo Hello"},
        )
        return Snapshot(scenario_name="Test Scenario", output=output)

    def test_save_snapshot(self, storage, sample_snapshot, temp_dir):
        """Test saving snapshot."""
        storage.save(sample_snapshot)

        # Check directory created
        snapshot_path = temp_dir / "test-scenario"
        assert snapshot_path.exists()
        assert snapshot_path.is_dir()

        # Check files created
        assert (snapshot_path / "stdout.txt").exists()
        assert (snapshot_path / "stderr.txt").exists()
        assert (snapshot_path / "metadata.json").exists()

    def test_save_creates_git_friendly_structure(
        self, storage, sample_snapshot, temp_dir
    ):
        """Test that save creates git-friendly structure."""
        storage.save(sample_snapshot)

        snapshot_path = temp_dir / "test-scenario"

        # Check stdout is plain text
        stdout_content = (snapshot_path / "stdout.txt").read_text()
        assert stdout_content == "Hello, World!\n"

        # Check stderr is plain text
        stderr_content = (snapshot_path / "stderr.txt").read_text()
        assert stderr_content == ""

        # Check metadata is formatted JSON
        metadata_content = (snapshot_path / "metadata.json").read_text()
        assert "scenario_name" in metadata_content
        assert "exit_code" in metadata_content
        # Should be pretty-printed
        assert "\n" in metadata_content

    def test_load_snapshot(self, storage, sample_snapshot):
        """Test loading snapshot."""
        # Save first
        storage.save(sample_snapshot)

        # Load
        loaded = storage.load("Test Scenario")

        assert loaded is not None
        assert loaded.scenario_name == "Test Scenario"
        assert loaded.output.stdout == "Hello, World!\n"
        assert loaded.output.stderr == ""
        assert loaded.output.exit_code == 0

    def test_load_nonexistent_snapshot(self, storage):
        """Test loading nonexistent snapshot."""
        result = storage.load("Nonexistent")
        assert result is None

    def test_exists(self, storage, sample_snapshot):
        """Test exists check."""
        assert not storage.exists("Test Scenario")

        storage.save(sample_snapshot)

        assert storage.exists("Test Scenario")

    def test_delete_snapshot(self, storage, sample_snapshot, temp_dir):
        """Test deleting snapshot."""
        # Save first
        storage.save(sample_snapshot)
        snapshot_path = temp_dir / "test-scenario"
        assert snapshot_path.exists()

        # Delete
        result = storage.delete("Test Scenario")

        assert result is True
        assert not snapshot_path.exists()

    def test_delete_nonexistent_snapshot(self, storage):
        """Test deleting nonexistent snapshot."""
        result = storage.delete("Nonexistent")
        assert result is False

    def test_list_scenarios(self, storage):
        """Test listing scenarios."""
        # Initially empty
        assert storage.list_scenarios() == []

        # Add snapshots
        output1 = CapturedOutput(stdout="test1", stderr="", exit_code=0)
        output2 = CapturedOutput(stdout="test2", stderr="", exit_code=0)

        storage.save(Snapshot(scenario_name="Alpha", output=output1))
        storage.save(Snapshot(scenario_name="Beta", output=output2))

        # List
        scenarios = storage.list_scenarios()

        assert len(scenarios) == 2
        assert "Alpha" in scenarios
        assert "Beta" in scenarios
        # Should be sorted
        assert scenarios == sorted(scenarios)

    def test_checksum_verification(self, storage, sample_snapshot, temp_dir):
        """Test checksum verification on load."""
        # Save snapshot
        storage.save(sample_snapshot)

        # Manually corrupt stdout
        snapshot_path = temp_dir / "test-scenario"
        stdout_file = snapshot_path / "stdout.txt"
        stdout_file.write_text("Corrupted content")

        # Loading should raise error
        with pytest.raises(ValueError, match="Checksum mismatch"):
            storage.load("Test Scenario")

    def test_get_snapshot_path(self, storage, temp_dir):
        """Test get_snapshot_path method."""
        path = storage.get_snapshot_path("Test Scenario")

        assert path == temp_dir / "test-scenario"
        assert isinstance(path, Path)

    def test_slug_generation(self, storage, temp_dir):
        """Test slug generation for various scenario names."""
        test_cases = [
            ("Simple Test", "simple-test"),
            ("Test_With_Underscores", "test_with_underscores"),
            ("Test-With-Dashes", "test-with-dashes"),
            ("Test  Multiple   Spaces", "test-multiple-spaces"),
            ("Test@Special#Chars!", "testspecialchars"),
        ]

        for scenario_name, expected_slug in test_cases:
            path = storage.get_snapshot_path(scenario_name)
            assert path.name == expected_slug

    def test_unicode_handling(self, storage):
        """Test handling of unicode characters."""
        output = CapturedOutput(
            stdout="Hello 世界 🌍\n", stderr="", exit_code=0
        )
        snapshot = Snapshot(scenario_name="Unicode Test", output=output)

        # Save and load
        storage.save(snapshot)
        loaded = storage.load("Unicode Test")

        assert loaded is not None
        assert loaded.output.stdout == "Hello 世界 🌍\n"

    def test_large_output(self, storage):
        """Test handling of large outputs."""
        # Create large output (1MB)
        large_content = "x" * (1024 * 1024)
        output = CapturedOutput(
            stdout=large_content, stderr="", exit_code=0
        )
        snapshot = Snapshot(scenario_name="Large Output", output=output)

        # Save and load
        storage.save(snapshot)
        loaded = storage.load("Large Output")

        assert loaded is not None
        assert len(loaded.output.stdout) == 1024 * 1024

    def test_metadata_persistence(self, storage):
        """Test that metadata is persisted correctly."""
        output = CapturedOutput(
            stdout="test",
            stderr="",
            exit_code=0,
            metadata={
                "command": "echo test",
                "environment": {"PATH": "/usr/bin"},
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        snapshot = Snapshot(scenario_name="Metadata Test", output=output)

        # Save and load
        storage.save(snapshot)
        loaded = storage.load("Metadata Test")

        assert loaded is not None
        assert loaded.output.metadata["command"] == "echo test"
        assert "environment" in loaded.output.metadata
        assert loaded.output.metadata["environment"]["PATH"] == "/usr/bin"
