"""Custom assertion helpers for session testing."""

import re
from pathlib import Path
from typing import Optional, Union

from .shell_session import ShellSession
from .models import SessionResult


def assert_output_contains(
    result: Union[SessionResult, ShellSession],
    pattern: str,
    message: Optional[str] = None
) -> None:
    """Assert that output contains a pattern.

    Args:
        result: SessionResult or ShellSession (uses last result)
        pattern: String or regex pattern to search for
        message: Custom assertion message

    Raises:
        AssertionError: If pattern not found in output
    """
    if isinstance(result, ShellSession):
        # Get last command output from state
        if not result.state.history:
            raise AssertionError("No commands executed in session")
        # For ShellSession, we need to re-execute to get output
        # This is a limitation - better to use SessionResult
        raise ValueError("Use SessionResult for output assertions, not ShellSession")

    output = result.output

    # Try as regex first, fall back to literal
    try:
        if not re.search(pattern, output):
            msg = message or f"Pattern '{pattern}' not found in output"
            raise AssertionError(f"{msg}\nActual output:\n{output}")
    except re.error:
        # Not a valid regex, try literal
        if pattern not in output:
            msg = message or f"Text '{pattern}' not found in output"
            raise AssertionError(f"{msg}\nActual output:\n{output}")


def assert_output_matches(
    result: SessionResult,
    regex: str,
    message: Optional[str] = None
) -> None:
    """Assert that output matches a regex pattern.

    Args:
        result: SessionResult to check
        regex: Regex pattern to match
        message: Custom assertion message

    Raises:
        AssertionError: If pattern doesn't match
    """
    if not re.search(regex, result.output):
        msg = message or f"Output does not match regex: {regex}"
        raise AssertionError(f"{msg}\nActual output:\n{result.output}")


def assert_exit_code(
    result: SessionResult,
    expected: int,
    message: Optional[str] = None
) -> None:
    """Assert command exit code.

    Args:
        result: SessionResult to check
        expected: Expected exit code
        message: Custom assertion message

    Raises:
        AssertionError: If exit code doesn't match
    """
    if result.exit_code != expected:
        msg = message or f"Expected exit code {expected}, got {result.exit_code}"
        raise AssertionError(f"{msg}\nOutput:\n{result.output}")


def assert_success(
    result: SessionResult,
    message: Optional[str] = None
) -> None:
    """Assert command succeeded (exit code 0).

    Args:
        result: SessionResult to check
        message: Custom assertion message

    Raises:
        AssertionError: If command failed
    """
    if not result.success:
        msg = message or f"Command failed with exit code {result.exit_code}"
        error_info = f"\nError: {result.error}" if result.error else ""
        raise AssertionError(f"{msg}{error_info}\nOutput:\n{result.output}")


def assert_failure(
    result: SessionResult,
    message: Optional[str] = None
) -> None:
    """Assert command failed (non-zero exit code).

    Args:
        result: SessionResult to check
        message: Custom assertion message

    Raises:
        AssertionError: If command succeeded
    """
    if result.success:
        msg = message or "Expected command to fail, but it succeeded"
        raise AssertionError(f"{msg}\nOutput:\n{result.output}")


def assert_variable_set(
    session: ShellSession,
    var_name: str,
    expected_value: Optional[str] = None,
    message: Optional[str] = None
) -> None:
    """Assert environment variable is set.

    Args:
        session: ShellSession to check
        var_name: Variable name
        expected_value: Expected value (if None, just checks if set)
        message: Custom assertion message

    Raises:
        AssertionError: If variable not set or value doesn't match
    """
    actual_value = session.get_variable(var_name)

    if actual_value is None:
        msg = message or f"Variable '{var_name}' is not set"
        raise AssertionError(msg)

    if expected_value is not None and actual_value != expected_value:
        msg = message or f"Variable '{var_name}' has wrong value"
        raise AssertionError(
            f"{msg}\nExpected: {expected_value}\nActual: {actual_value}"
        )


def assert_variable_unset(
    session: ShellSession,
    var_name: str,
    message: Optional[str] = None
) -> None:
    """Assert environment variable is not set.

    Args:
        session: ShellSession to check
        var_name: Variable name
        message: Custom assertion message

    Raises:
        AssertionError: If variable is set
    """
    actual_value = session.get_variable(var_name)

    if actual_value is not None:
        msg = message or f"Variable '{var_name}' should not be set"
        raise AssertionError(f"{msg}\nActual value: {actual_value}")


def assert_cwd(
    session: ShellSession,
    expected_path: Union[str, Path],
    message: Optional[str] = None
) -> None:
    """Assert current working directory.

    Args:
        session: ShellSession to check
        expected_path: Expected working directory
        message: Custom assertion message

    Raises:
        AssertionError: If working directory doesn't match
    """
    expected = Path(expected_path).resolve()
    actual = session.state.cwd

    if actual is None:
        raise AssertionError("Current working directory not tracked")

    if actual.resolve() != expected:
        msg = message or "Working directory doesn't match"
        raise AssertionError(
            f"{msg}\nExpected: {expected}\nActual: {actual}"
        )


def assert_file_exists(
    session: ShellSession,
    file_path: Union[str, Path],
    message: Optional[str] = None
) -> None:
    """Assert file exists in session context.

    Args:
        session: ShellSession to check
        file_path: Path to file
        message: Custom assertion message

    Raises:
        AssertionError: If file doesn't exist
    """
    result = session.execute(f'test -f "{file_path}" && echo EXISTS || echo MISSING')

    if "MISSING" in result.output:
        msg = message or f"File does not exist: {file_path}"
        raise AssertionError(msg)


def assert_file_contains(
    session: ShellSession,
    file_path: Union[str, Path],
    pattern: str,
    message: Optional[str] = None
) -> None:
    """Assert file contains pattern.

    Args:
        session: ShellSession to check
        file_path: Path to file
        pattern: Pattern to search for
        message: Custom assertion message

    Raises:
        AssertionError: If file doesn't contain pattern
    """
    result = session.execute(f'grep -q "{pattern}" "{file_path}" && echo FOUND || echo MISSING')

    if "MISSING" in result.output:
        msg = message or f"Pattern '{pattern}' not found in {file_path}"
        raise AssertionError(msg)


def assert_command_in_history(
    session: ShellSession,
    command: str,
    message: Optional[str] = None
) -> None:
    """Assert command was executed in session history.

    Args:
        session: ShellSession to check
        command: Command to search for
        message: Custom assertion message

    Raises:
        AssertionError: If command not found in history
    """
    if command not in session.state.history:
        msg = message or f"Command not found in history: {command}"
        commands = "\n".join(session.state.history)
        raise AssertionError(f"{msg}\nHistory:\n{commands}")


def assert_execution_time(
    result: SessionResult,
    max_seconds: float,
    message: Optional[str] = None
) -> None:
    """Assert command execution time is within limit.

    Args:
        result: SessionResult to check
        max_seconds: Maximum allowed execution time
        message: Custom assertion message

    Raises:
        AssertionError: If execution took too long
    """
    if result.duration > max_seconds:
        msg = message or f"Command took too long: {result.duration:.2f}s (max: {max_seconds}s)"
        raise AssertionError(msg)
