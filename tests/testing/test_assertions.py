"""Tests for assertion helpers."""

import pytest
from pathlib import Path

from orchestro_cli.testing import ShellSession, SessionResult, SessionState
from orchestro_cli.testing.assertions import (
    assert_output_contains,
    assert_exit_code,
    assert_success,
    assert_failure,
    assert_variable_set,
    assert_cwd,
    assert_file_exists,
    assert_command_in_history,
    assert_execution_time,
)


class TestOutputAssertions:
    """Test output assertion helpers."""

    def test_assert_output_contains_success(self):
        """Test output contains assertion passes."""
        result = SessionResult(
            output="Hello World",
            exit_code=0,
            state=SessionState(),
            success=True
        )

        assert_output_contains(result, "Hello")
        assert_output_contains(result, "World")

    def test_assert_output_contains_failure(self):
        """Test output contains assertion fails."""
        result = SessionResult(
            output="Hello World",
            exit_code=0,
            state=SessionState(),
            success=True
        )

        with pytest.raises(AssertionError, match="not found"):
            assert_output_contains(result, "Goodbye")

    def test_assert_output_contains_regex(self):
        """Test output contains with regex."""
        result = SessionResult(
            output="Version 1.2.3",
            exit_code=0,
            state=SessionState(),
            success=True
        )

        assert_output_contains(result, r"Version \d+\.\d+\.\d+")

    def test_assert_output_contains_custom_message(self):
        """Test custom assertion message."""
        result = SessionResult(
            output="test",
            exit_code=0,
            state=SessionState(),
            success=True
        )

        with pytest.raises(AssertionError, match="Custom message"):
            assert_output_contains(result, "missing", message="Custom message")


class TestExitCodeAssertions:
    """Test exit code assertion helpers."""

    def test_assert_exit_code_success(self):
        """Test exit code assertion passes."""
        result = SessionResult(
            output="",
            exit_code=0,
            state=SessionState(),
            success=True
        )

        assert_exit_code(result, 0)

    def test_assert_exit_code_failure(self):
        """Test exit code assertion fails."""
        result = SessionResult(
            output="",
            exit_code=1,
            state=SessionState(),
            success=False
        )

        with pytest.raises(AssertionError, match="Expected exit code 0"):
            assert_exit_code(result, 0)

    def test_assert_success(self):
        """Test success assertion."""
        result = SessionResult(
            output="",
            exit_code=0,
            state=SessionState(),
            success=True
        )

        assert_success(result)

    def test_assert_success_failure(self):
        """Test success assertion fails."""
        result = SessionResult(
            output="error",
            exit_code=1,
            state=SessionState(),
            success=False,
            error="Command failed"
        )

        with pytest.raises(AssertionError, match="Command failed"):
            assert_success(result)

    def test_assert_failure(self):
        """Test failure assertion."""
        result = SessionResult(
            output="error",
            exit_code=1,
            state=SessionState(),
            success=False
        )

        assert_failure(result)

    def test_assert_failure_on_success(self):
        """Test failure assertion when command succeeded."""
        result = SessionResult(
            output="",
            exit_code=0,
            state=SessionState(),
            success=True
        )

        with pytest.raises(AssertionError, match="Expected command to fail"):
            assert_failure(result)


class TestVariableAssertions:
    """Test variable assertion helpers."""

    def test_assert_variable_set(self, shell_session):
        """Test variable set assertion."""
        shell_session.execute("export TEST_VAR=test_value")

        assert_variable_set(shell_session, "TEST_VAR")
        assert_variable_set(shell_session, "TEST_VAR", "test_value")

    def test_assert_variable_set_failure(self, shell_session):
        """Test variable set assertion fails."""
        with pytest.raises(AssertionError, match="not set"):
            assert_variable_set(shell_session, "NONEXISTENT_VAR")

    def test_assert_variable_wrong_value(self, shell_session):
        """Test variable with wrong value fails."""
        shell_session.execute("export TEST_VAR=actual")

        with pytest.raises(AssertionError, match="wrong value"):
            assert_variable_set(shell_session, "TEST_VAR", "expected")


class TestDirectoryAssertions:
    """Test directory assertion helpers."""

    def test_assert_cwd(self, shell_session):
        """Test current directory assertion."""
        shell_session.execute("cd /tmp")
        assert_cwd(shell_session, "/tmp")

    def test_assert_cwd_failure(self, shell_session):
        """Test current directory assertion fails."""
        shell_session.execute("cd /tmp")

        with pytest.raises(AssertionError, match="doesn't match"):
            assert_cwd(shell_session, "/var")


class TestFileAssertions:
    """Test file assertion helpers."""

    def test_assert_file_exists(self, shell_session, temp_workspace):
        """Test file exists assertion."""
        shell_session.change_directory(temp_workspace)
        shell_session.execute("touch test_file.txt")

        assert_file_exists(shell_session, "test_file.txt")

    def test_assert_file_exists_failure(self, shell_session):
        """Test file exists assertion fails."""
        with pytest.raises(AssertionError, match="does not exist"):
            assert_file_exists(shell_session, "nonexistent_file.txt")


class TestHistoryAssertions:
    """Test history assertion helpers."""

    def test_assert_command_in_history(self, shell_session):
        """Test command in history assertion."""
        shell_session.execute("echo test")

        assert_command_in_history(shell_session, "echo test")

    def test_assert_command_not_in_history(self, shell_session):
        """Test command not in history fails."""
        with pytest.raises(AssertionError, match="not found in history"):
            assert_command_in_history(shell_session, "never_executed")


class TestTimingAssertions:
    """Test timing assertion helpers."""

    def test_assert_execution_time(self):
        """Test execution time assertion."""
        result = SessionResult(
            output="",
            exit_code=0,
            state=SessionState(),
            success=True,
            duration=0.5
        )

        assert_execution_time(result, 1.0)

    def test_assert_execution_time_failure(self):
        """Test execution time assertion fails."""
        result = SessionResult(
            output="",
            exit_code=0,
            state=SessionState(),
            success=True,
            duration=2.0
        )

        with pytest.raises(AssertionError, match="took too long"):
            assert_execution_time(result, 1.0)


class TestAssertionUsageExamples:
    """Test realistic assertion usage patterns."""

    def test_workflow_with_multiple_assertions(self, shell_session, temp_workspace):
        """Test complex workflow with multiple assertions."""
        shell_session.change_directory(temp_workspace)

        # Set up environment
        result = shell_session.execute("export PROJECT_NAME=test-project")
        assert_success(result)
        assert_variable_set(shell_session, "PROJECT_NAME", "test-project")

        # Create directory
        result = shell_session.execute("mkdir -p $PROJECT_NAME")
        assert_success(result)

        # Change into directory
        result = shell_session.execute("cd $PROJECT_NAME")
        assert_success(result)

        # Create file
        result = shell_session.execute("echo 'content' > README.md")
        assert_success(result)
        assert_file_exists(shell_session, "README.md")

        # Verify history
        assert_command_in_history(shell_session, "export PROJECT_NAME=test-project")
        assert_command_in_history(shell_session, "mkdir -p $PROJECT_NAME")
