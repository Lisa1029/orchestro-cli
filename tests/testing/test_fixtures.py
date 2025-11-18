"""Tests for pytest fixtures."""

import pytest

from orchestro_cli.testing import ShellSession, TUISession, SessionConfig


def test_shell_session_fixture(shell_session):
    """Test that shell_session fixture works."""
    assert isinstance(shell_session, ShellSession)
    assert shell_session.is_alive()

    result = shell_session.execute("echo test")
    assert result.success


def test_shell_session_isolated_per_test():
    """Test that sessions are isolated between tests."""
    # This test should run in a fresh session, separate from the previous test
    # We can't directly test isolation, but we can verify the fixture pattern works
    pass


def test_isolated_shell_session_fixture(isolated_shell_session, temp_workspace):
    """Test isolated shell session fixture."""
    assert isinstance(isolated_shell_session, ShellSession)
    assert isolated_shell_session.state.cwd == temp_workspace


def test_tui_session_fixture(tui_session):
    """Test that tui_session fixture works."""
    assert isinstance(tui_session, TUISession)
    assert tui_session.is_alive()

    # Should have shell capabilities
    result = tui_session.execute("echo test")
    assert result.success


def test_tui_session_with_screenshots_fixture(tui_session_with_screenshots, trigger_dir, artifacts_dir):
    """Test TUI session with screenshot support."""
    session, trigger_dir_from_fixture, artifacts_dir_from_fixture = tui_session_with_screenshots

    assert isinstance(session, TUISession)
    assert trigger_dir_from_fixture == trigger_dir
    assert artifacts_dir_from_fixture == artifacts_dir


def test_custom_shell_session_fixture(custom_shell_session):
    """Test custom session factory fixture."""
    config = SessionConfig(timeout=5.0)
    session = custom_shell_session(config)

    assert isinstance(session, ShellSession)
    assert session.config.timeout == 5.0
    assert session.is_alive()


def test_custom_shell_session_creates_multiple(custom_shell_session):
    """Test that custom fixture can create multiple sessions."""
    config1 = SessionConfig(timeout=5.0)
    config2 = SessionConfig(timeout=10.0)

    session1 = custom_shell_session(config1)
    session2 = custom_shell_session(config2)

    assert session1.config.timeout == 5.0
    assert session2.config.timeout == 10.0

    # Both should be alive
    assert session1.is_alive()
    assert session2.is_alive()


def test_workspace_isolator_fixture(workspace_isolator):
    """Test workspace isolator fixture."""
    workspace = workspace_isolator.create_workspace("test-workspace")

    assert workspace.exists()
    assert (workspace / "home").exists()
    assert (workspace / "data").exists()
