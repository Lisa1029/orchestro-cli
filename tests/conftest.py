"""Pytest configuration and fixtures for Orchestro CLI tests."""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest

# Import session testing fixtures
from orchestro_cli.testing.fixtures import (
    shell_session,
    persistent_shell,
    isolated_shell_session,
    tui_session,
    tui_session_with_screenshots,
    workspace_isolator,
    custom_shell_session,
)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add CLI options for selective test execution."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests that spawn real processes and worker pools",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip integration tests unless explicitly requested."""
    if config.getoption("--integration"):
        return

    skip_marker = pytest.mark.skip(reason="integration test skipped (use --integration)")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_marker)


@pytest.fixture
def temp_workspace() -> Generator[Path, None, None]:
    """Create a temporary workspace for testing.

    Yields:
        Path to temporary workspace directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        yield workspace


@pytest.fixture
def scenario_file(temp_workspace: Path) -> Path:
    """Create a temporary scenario file path.

    Args:
        temp_workspace: Temporary workspace fixture

    Returns:
        Path to scenario file location
    """
    return temp_workspace / "test_scenario.yaml"


@pytest.fixture
def artifacts_dir(temp_workspace: Path) -> Path:
    """Create artifacts directory.

    Args:
        temp_workspace: Temporary workspace fixture

    Returns:
        Path to artifacts directory
    """
    artifacts = temp_workspace / "artifacts" / "screenshots"
    artifacts.mkdir(parents=True, exist_ok=True)
    return artifacts


@pytest.fixture
def trigger_dir() -> Generator[Path, None, None]:
    """Create temporary trigger directory.

    Yields:
        Path to trigger directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        trigger_path = Path(tmpdir) / ".vyb_screenshot_triggers"
        trigger_path.mkdir(parents=True, exist_ok=True)
        yield trigger_path


@pytest.fixture
def sentinel_file() -> Generator[Path, None, None]:
    """Create temporary sentinel file.

    Yields:
        Path to sentinel file
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        sentinel_path = Path(tmpdir) / ".vyb_orchestro_sentinels"
        sentinel_path.touch()
        yield sentinel_path
