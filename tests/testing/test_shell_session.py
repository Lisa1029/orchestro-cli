"""Tests for ShellSession class."""

import pytest
from pathlib import Path

from orchestro_cli.testing import ShellSession, SessionConfig
from orchestro_cli.testing.assertions import (
    assert_output_contains,
    assert_exit_code,
    assert_success,
    assert_variable_set,
    assert_cwd,
)


class TestShellSessionBasics:
    """Test basic shell session functionality."""

    def test_session_starts_and_closes(self, shell_session):
        """Test session lifecycle."""
        assert shell_session.is_alive()
        assert shell_session._started

    def test_simple_command_execution(self, shell_session):
        """Test executing a simple command."""
        result = shell_session.execute("echo 'Hello World'")

        assert_success(result)
        assert "Hello World" in result.output

    def test_exit_code_tracking(self, shell_session):
        """Test that exit codes are tracked correctly."""
        # Success
        result = shell_session.execute("true")
        assert_exit_code(result, 0)

        # Failure
        result = shell_session.execute("false")
        assert_exit_code(result, 1)

    def test_command_history(self, shell_session):
        """Test command history tracking."""
        shell_session.execute("echo first")
        shell_session.execute("echo second")
        shell_session.execute("echo third")

        assert len(shell_session.state.history) == 3
        assert "echo first" in shell_session.state.history
        assert "echo third" in shell_session.state.history


class TestStatePersistence:
    """Test that session state persists between commands."""

    def test_environment_variable_persistence(self, shell_session):
        """Test that environment variables persist."""
        # Set variable
        shell_session.execute("export TEST_VAR=hello")

        # Use variable
        result = shell_session.execute("echo $TEST_VAR")
        assert_output_contains(result, "hello")
        assert_variable_set(shell_session, "TEST_VAR", "hello")

    def test_directory_change_persistence(self, shell_session):
        """Test that directory changes persist."""
        # Change to /tmp
        shell_session.execute("cd /tmp")

        # Verify we're still in /tmp
        result = shell_session.execute("pwd")
        assert "/tmp" in result.output
        assert_cwd(shell_session, "/tmp")

    def test_multiple_variable_tracking(self, shell_session):
        """Test tracking multiple variables."""
        shell_session.execute("export VAR1=value1")
        shell_session.execute("export VAR2=value2")
        shell_session.execute("export VAR3=value3")

        assert_variable_set(shell_session, "VAR1", "value1")
        assert_variable_set(shell_session, "VAR2", "value2")
        assert_variable_set(shell_session, "VAR3", "value3")

    def test_working_directory_state(self, shell_session):
        """Test working directory state tracking."""
        original_dir = shell_session.state.cwd

        shell_session.execute("cd /tmp")
        assert shell_session.state.cwd == Path("/tmp")

        shell_session.execute(f"cd {original_dir}")
        assert shell_session.state.cwd == original_dir


class TestSessionMethods:
    """Test session helper methods."""

    def test_set_variable_method(self, shell_session):
        """Test set_variable helper method."""
        result = shell_session.set_variable("MY_VAR", "my_value")
        assert_success(result)

        verify = shell_session.execute("echo $MY_VAR")
        assert "my_value" in verify.output

    def test_get_variable_method(self, shell_session):
        """Test get_variable helper method."""
        shell_session.execute("export TEST_GET=fetched")
        value = shell_session.get_variable("TEST_GET")
        assert value == "fetched"

    def test_change_directory_method(self, shell_session):
        """Test change_directory helper method."""
        result = shell_session.change_directory(Path("/tmp"))
        assert_success(result)

        assert_cwd(shell_session, "/tmp")

    def test_send_control(self, shell_session):
        """Test sending control characters."""
        # This is hard to test without a blocking command
        # Just verify it doesn't crash
        shell_session.send_control('l')  # Ctrl+L (clear screen)


class TestSessionReset:
    """Test session reset functionality."""

    def test_reset_clears_variables(self, shell_session):
        """Test that reset clears custom variables."""
        shell_session.execute("export TEMP_VAR=temporary")
        assert_variable_set(shell_session, "TEMP_VAR")

        shell_session.reset()

        # Variable should be cleared
        result = shell_session.execute("echo $TEMP_VAR")
        assert result.output.strip() == ""

    def test_reset_returns_to_initial_directory(self, shell_session, temp_workspace):
        """Test that reset returns to initial directory."""
        config = SessionConfig(working_dir=temp_workspace)
        session = ShellSession(config)
        session.start()

        try:
            session.execute("cd /tmp")
            session.reset()

            assert_cwd(session, temp_workspace)
        finally:
            session.close()


class TestContextManager:
    """Test context manager protocol."""

    def test_context_manager_starts_and_closes(self):
        """Test session as context manager."""
        with ShellSession() as session:
            assert session.is_alive()
            result = session.execute("echo test")
            assert_success(result)

        # Session should be closed after context
        assert not session.is_alive()


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_command_timeout(self):
        """Test command timeout handling."""
        config = SessionConfig(timeout=1.0)
        with ShellSession(config) as session:
            result = session.execute("sleep 10")

            # Should timeout and return error result
            assert not result.success
            assert result.error is not None
            assert "timed out" in result.error.lower()

    def test_execute_before_start_raises(self):
        """Test that executing before start raises error."""
        session = ShellSession()

        with pytest.raises(RuntimeError, match="not started"):
            session.execute("echo test")

    def test_double_start_raises(self):
        """Test that starting twice raises error."""
        session = ShellSession()
        session.start()

        try:
            with pytest.raises(RuntimeError, match="already started"):
                session.start()
        finally:
            session.close()

    def test_dangerous_command_blocked(self, shell_session):
        """Test that dangerous commands are blocked."""
        with pytest.raises(ValueError, match="blocked for security"):
            shell_session.execute("rm -rf /")


class TestCustomConfiguration:
    """Test custom session configuration."""

    def test_custom_timeout(self):
        """Test custom timeout configuration."""
        config = SessionConfig(timeout=5.0)
        assert config.timeout == 5.0

    def test_custom_environment(self):
        """Test custom environment variables."""
        config = SessionConfig(env={"CUSTOM_VAR": "custom_value"})

        with ShellSession(config) as session:
            result = session.execute("echo $CUSTOM_VAR")
            assert "custom_value" in result.output

    def test_custom_working_directory(self, temp_workspace):
        """Test custom working directory."""
        config = SessionConfig(working_dir=temp_workspace)

        with ShellSession(config) as session:
            result = session.execute("pwd")
            assert str(temp_workspace) in result.output


class TestMultiStepWorkflow:
    """Test realistic multi-step workflows."""

    def test_git_workflow(self, shell_session, temp_workspace):
        """Test a git workflow with state persistence."""
        # Initialize git repo
        shell_session.change_directory(temp_workspace)

        result = shell_session.execute("git init")
        assert_success(result)

        # Create a file
        result = shell_session.execute("echo 'test content' > test.txt")
        assert_success(result)

        # Add and commit
        result = shell_session.execute("git add test.txt")
        assert_success(result)

        result = shell_session.execute("git commit -m 'Initial commit'")
        assert_success(result)

        # Verify commit exists
        result = shell_session.execute("git log --oneline")
        assert "Initial commit" in result.output

    def test_build_workflow(self, shell_session, temp_workspace):
        """Test a build workflow."""
        shell_session.change_directory(temp_workspace)

        # Set build variables
        shell_session.set_variable("BUILD_DIR", "build")
        shell_session.set_variable("SRC_DIR", "src")

        # Create directories
        shell_session.execute("mkdir -p $BUILD_DIR $SRC_DIR")

        # Verify directories exist
        result = shell_session.execute("ls -d $BUILD_DIR $SRC_DIR")
        assert "build" in result.output
        assert "src" in result.output

    def test_environment_setup_workflow(self, shell_session):
        """Test environment setup workflow."""
        # Set multiple variables
        shell_session.execute("export API_URL=https://api.example.com")
        shell_session.execute("export API_KEY=test_key_123")
        shell_session.execute("export DEBUG=true")

        # Use variables in compound command
        result = shell_session.execute(
            "echo API_URL=$API_URL KEY=$API_KEY DEBUG=$DEBUG"
        )

        assert "API_URL=https://api.example.com" in result.output
        assert "KEY=test_key_123" in result.output
        assert "DEBUG=true" in result.output
