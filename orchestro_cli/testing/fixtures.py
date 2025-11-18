"""Pytest fixtures for session-based testing."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from .models import SessionConfig
from .shell_session import ShellSession
from .tui_session import TUISession
from .security import WorkspaceIsolator


@pytest.fixture
def shell_session() -> Generator[ShellSession, None, None]:
    """Create a function-scoped shell session.

    Provides a fresh shell session for each test function.
    Automatically starts and cleans up the session.

    Yields:
        ShellSession instance
    """
    session = ShellSession()
    session.start()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def persistent_shell() -> Generator[ShellSession, None, None]:
    """Create a module-scoped persistent shell session.

    Provides a single shell session shared across all tests in a module.
    State persists between tests - use with caution.

    Yields:
        ShellSession instance
    """
    session = ShellSession()
    session.start()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def isolated_shell_session(temp_workspace: Path) -> Generator[ShellSession, None, None]:
    """Create an isolated shell session with temporary workspace.

    Provides a shell session running in an isolated temporary directory.

    Args:
        temp_workspace: Temporary workspace fixture

    Yields:
        ShellSession instance
    """
    config = SessionConfig(working_dir=temp_workspace)
    session = ShellSession(config)
    session.start()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def tui_session(temp_workspace: Path) -> Generator[TUISession, None, None]:
    """Create a TUI session for interactive application testing.

    Args:
        temp_workspace: Temporary workspace fixture

    Yields:
        TUISession instance
    """
    config = SessionConfig(
        working_dir=temp_workspace,
        dimensions=(40, 120)  # Larger for TUI apps
    )
    session = TUISession(config)
    session.start()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def tui_session_with_screenshots(
    temp_workspace: Path,
    trigger_dir: Path,
    artifacts_dir: Path
) -> Generator[tuple[TUISession, Path, Path], None, None]:
    """Create TUI session with screenshot support.

    Args:
        temp_workspace: Temporary workspace fixture
        trigger_dir: Screenshot trigger directory
        artifacts_dir: Artifacts directory

    Yields:
        Tuple of (TUISession, trigger_dir, artifacts_dir)
    """
    config = SessionConfig(
        working_dir=temp_workspace,
        dimensions=(40, 120)
    )
    session = TUISession(config)
    session.start()

    try:
        yield session, trigger_dir, artifacts_dir
    finally:
        session.close()


@pytest.fixture
def workspace_isolator() -> WorkspaceIsolator:
    """Create workspace isolator for managing test workspaces.

    Returns:
        WorkspaceIsolator instance
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        isolator = WorkspaceIsolator(Path(tmpdir))
        yield isolator


@pytest.fixture
def custom_shell_session() -> Generator[callable, None, None]:
    """Factory fixture for creating custom shell sessions.

    Returns a callable that creates ShellSession instances with custom config.

    Yields:
        Factory function for creating sessions
    """
    sessions = []

    def _create_session(config: SessionConfig) -> ShellSession:
        session = ShellSession(config)
        session.start()
        sessions.append(session)
        return session

    yield _create_session

    # Cleanup all created sessions
    for session in sessions:
        if session.is_alive():
            session.close()
