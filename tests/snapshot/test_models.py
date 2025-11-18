"""Tests for snapshot models."""

import pytest
from datetime import datetime

from orchestro_cli.snapshot.models import (
    SnapshotMode,
    CapturedOutput,
    Snapshot,
    DiffLine,
    DiffResult,
    SnapshotResult,
)


class TestSnapshotMode:
    """Test SnapshotMode enum."""

    def test_mode_values(self):
        """Test mode enum values."""
        assert SnapshotMode.VERIFY.value == "verify"
        assert SnapshotMode.UPDATE.value == "update"
        assert SnapshotMode.RECORD.value == "record"

    def test_mode_string_conversion(self):
        """Test string conversion."""
        assert str(SnapshotMode.VERIFY) == "verify"
        assert str(SnapshotMode.UPDATE) == "update"
        assert str(SnapshotMode.RECORD) == "record"


class TestCapturedOutput:
    """Test CapturedOutput model."""

    def test_create_captured_output(self):
        """Test creating captured output."""
        output = CapturedOutput(
            stdout="Hello, World!",
            stderr="",
            exit_code=0,
        )

        assert output.stdout == "Hello, World!"
        assert output.stderr == ""
        assert output.exit_code == 0
        assert isinstance(output.timestamp, datetime)

    def test_captured_output_with_metadata(self):
        """Test captured output with metadata."""
        output = CapturedOutput(
            stdout="Test",
            stderr="",
            exit_code=0,
            metadata={"command": "echo test"},
        )

        assert output.metadata["command"] == "echo test"

    def test_has_output(self):
        """Test has_output property."""
        output1 = CapturedOutput(stdout="test", stderr="", exit_code=0)
        assert output1.has_output

        output2 = CapturedOutput(stdout="", stderr="error", exit_code=1)
        assert output2.has_output

        output3 = CapturedOutput(stdout="", stderr="", exit_code=0)
        assert not output3.has_output

    def test_is_success(self):
        """Test is_success property."""
        output1 = CapturedOutput(stdout="", stderr="", exit_code=0)
        assert output1.is_success

        output2 = CapturedOutput(stdout="", stderr="error", exit_code=1)
        assert not output2.is_success

    def test_to_dict(self):
        """Test serialization to dict."""
        output = CapturedOutput(
            stdout="test", stderr="err", exit_code=1, metadata={"key": "value"}
        )
        data = output.to_dict()

        assert data["stdout"] == "test"
        assert data["stderr"] == "err"
        assert data["exit_code"] == 1
        assert data["metadata"]["key"] == "value"
        assert "timestamp" in data

    def test_from_dict(self):
        """Test deserialization from dict."""
        now = datetime.utcnow()
        data = {
            "stdout": "test",
            "stderr": "err",
            "exit_code": 1,
            "timestamp": now.isoformat(),
            "metadata": {"key": "value"},
        }

        output = CapturedOutput.from_dict(data)

        assert output.stdout == "test"
        assert output.stderr == "err"
        assert output.exit_code == 1
        assert output.metadata["key"] == "value"

    def test_invalid_types(self):
        """Test validation with invalid types."""
        with pytest.raises(TypeError):
            CapturedOutput(stdout=123, stderr="", exit_code=0)

        with pytest.raises(TypeError):
            CapturedOutput(stdout="", stderr=None, exit_code=0)

        with pytest.raises(TypeError):
            CapturedOutput(stdout="", stderr="", exit_code="0")


class TestSnapshot:
    """Test Snapshot model."""

    def test_create_snapshot(self):
        """Test creating snapshot."""
        output = CapturedOutput(stdout="test", stderr="", exit_code=0)
        snapshot = Snapshot(scenario_name="Test Scenario", output=output)

        assert snapshot.scenario_name == "Test Scenario"
        assert snapshot.output == output
        assert isinstance(snapshot.created_at, datetime)
        assert isinstance(snapshot.updated_at, datetime)

    def test_slug_generation(self):
        """Test slug generation from scenario name."""
        output = CapturedOutput(stdout="", stderr="", exit_code=0)

        snapshot1 = Snapshot(scenario_name="Test Scenario", output=output)
        assert snapshot1.slug == "test-scenario"

        snapshot2 = Snapshot(scenario_name="Hello World!", output=output)
        assert snapshot2.slug == "hello-world"

        snapshot3 = Snapshot(
            scenario_name="Test_With-Special@Chars#123", output=output
        )
        assert snapshot3.slug == "test_with-specialchars123"

    def test_empty_scenario_name(self):
        """Test validation with empty scenario name."""
        output = CapturedOutput(stdout="", stderr="", exit_code=0)

        with pytest.raises(ValueError):
            Snapshot(scenario_name="", output=output)

    def test_invalid_output_type(self):
        """Test validation with invalid output type."""
        with pytest.raises(TypeError):
            Snapshot(scenario_name="test", output="not a CapturedOutput")

    def test_to_dict(self):
        """Test serialization to dict."""
        output = CapturedOutput(stdout="test", stderr="", exit_code=0)
        snapshot = Snapshot(
            scenario_name="Test", output=output, checksum="abc123"
        )
        data = snapshot.to_dict()

        assert data["scenario_name"] == "Test"
        assert "output" in data
        assert data["checksum"] == "abc123"
        assert "created_at" in data
        assert "updated_at" in data

    def test_from_dict(self):
        """Test deserialization from dict."""
        now = datetime.utcnow()
        data = {
            "scenario_name": "Test",
            "output": {
                "stdout": "test",
                "stderr": "",
                "exit_code": 0,
                "timestamp": now.isoformat(),
                "metadata": {},
            },
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "checksum": "abc123",
        }

        snapshot = Snapshot.from_dict(data)

        assert snapshot.scenario_name == "Test"
        assert snapshot.output.stdout == "test"
        assert snapshot.checksum == "abc123"


class TestDiffLine:
    """Test DiffLine model."""

    def test_addition(self):
        """Test addition line."""
        line = DiffLine(line_type="+", content="added line")
        assert line.is_addition
        assert not line.is_deletion
        assert not line.is_context
        assert not line.is_header

    def test_deletion(self):
        """Test deletion line."""
        line = DiffLine(line_type="-", content="deleted line")
        assert line.is_deletion
        assert not line.is_addition

    def test_context(self):
        """Test context line."""
        line = DiffLine(line_type=" ", content="context line")
        assert line.is_context
        assert not line.is_addition
        assert not line.is_deletion

    def test_header(self):
        """Test header line."""
        line = DiffLine(line_type="@@", content="@@ -1,3 +1,3 @@")
        assert line.is_header


class TestDiffResult:
    """Test DiffResult model."""

    def test_identical_outputs(self):
        """Test identical outputs."""
        result = DiffResult(
            has_diff=False,
            similarity_score=100.0,
            exit_code_match=True,
            summary="Identical",
        )

        assert result.is_identical
        assert not result.has_stdout_diff
        assert not result.has_stderr_diff

    def test_different_outputs(self):
        """Test different outputs."""
        diff_lines = [
            DiffLine(line_type="+", content="new line"),
            DiffLine(line_type="-", content="old line"),
        ]

        result = DiffResult(
            has_diff=True,
            similarity_score=75.5,
            stdout_diff=diff_lines,
            exit_code_match=True,
        )

        assert not result.is_identical
        assert result.has_stdout_diff
        assert result.similarity_score == 75.5

    def test_invalid_similarity_score(self):
        """Test validation with invalid similarity score."""
        with pytest.raises(ValueError):
            DiffResult(has_diff=True, similarity_score=150.0)

        with pytest.raises(ValueError):
            DiffResult(has_diff=True, similarity_score=-10.0)


class TestSnapshotResult:
    """Test SnapshotResult model."""

    def test_passed_result(self):
        """Test passed snapshot result."""
        result = SnapshotResult(
            passed=True, message="Snapshot matches", snapshot_path="/path/to/snapshot"
        )

        assert result.passed
        assert not result.failed
        assert not result.has_diff
        assert result.snapshot_path == "/path/to/snapshot"

    def test_failed_result_with_diff(self):
        """Test failed result with diff."""
        diff_result = DiffResult(has_diff=True, similarity_score=80.0)
        result = SnapshotResult(
            passed=False,
            diff_result=diff_result,
            message="Mismatch",
            snapshot_path="/path",
        )

        assert result.failed
        assert result.has_diff
        assert result.diff_result.similarity_score == 80.0

    def test_to_dict(self):
        """Test serialization to dict."""
        result = SnapshotResult(
            passed=True, message="OK", snapshot_path="/path"
        )
        data = result.to_dict()

        assert data["passed"] is True
        assert data["message"] == "OK"
        assert data["snapshot_path"] == "/path"
        assert "similarity_score" in data
