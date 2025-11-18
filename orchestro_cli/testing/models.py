"""Domain models for session state testing."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Any


@dataclass
class SessionState:
    """Tracks state of a persistent shell session.

    Attributes:
        variables: Environment variables set in session
        cwd: Current working directory
        exit_codes: History of exit codes from executed commands
        history: Command history
    """

    variables: Dict[str, str] = field(default_factory=dict)
    cwd: Optional[Path] = None
    exit_codes: list[int] = field(default_factory=list)
    history: list[str] = field(default_factory=list)

    def add_command(self, command: str, exit_code: int) -> None:
        """Record a command execution.

        Args:
            command: Command that was executed
            exit_code: Exit code from command
        """
        self.history.append(command)
        self.exit_codes.append(exit_code)

    def update_variable(self, name: str, value: str) -> None:
        """Update an environment variable.

        Args:
            name: Variable name
            value: Variable value
        """
        self.variables[name] = value

    def get_last_exit_code(self) -> Optional[int]:
        """Get the most recent exit code.

        Returns:
            Last exit code or None if no commands executed
        """
        return self.exit_codes[-1] if self.exit_codes else None


@dataclass
class SessionConfig:
    """Configuration for shell session creation.

    Attributes:
        timeout: Default timeout for operations (seconds)
        env: Environment variables to set
        working_dir: Initial working directory
        shell: Shell executable to use
        prompt: Custom prompt pattern for reliable parsing
        echo: Enable command echo
        dimensions: Terminal dimensions (rows, cols)
    """

    timeout: float = 30.0
    env: Optional[Dict[str, str]] = None
    working_dir: Optional[Path] = None
    shell: str = "/bin/bash"
    prompt: str = "ORCHESTRO_PROMPT>"
    echo: bool = False
    dimensions: tuple[int, int] = (24, 80)

    def __post_init__(self):
        """Validate configuration."""
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        if self.dimensions[0] <= 0 or self.dimensions[1] <= 0:
            raise ValueError("Dimensions must be positive")


@dataclass
class SessionResult:
    """Result from a session command execution.

    Attributes:
        output: Captured output from command
        exit_code: Command exit code
        state: Updated session state
        success: Whether command succeeded
        error: Error message if command failed
        duration: Execution time in seconds
    """

    output: str
    exit_code: int
    state: SessionState
    success: bool
    error: Optional[str] = None
    duration: float = 0.0

    @property
    def stdout(self) -> str:
        """Alias for output for consistency with subprocess."""
        return self.output

    def assert_success(self) -> None:
        """Assert that command succeeded.

        Raises:
            AssertionError: If command failed
        """
        if not self.success:
            error_msg = self.error or f"Command failed with exit code {self.exit_code}"
            raise AssertionError(error_msg)

    def assert_exit_code(self, expected: int) -> None:
        """Assert exit code matches expected value.

        Args:
            expected: Expected exit code

        Raises:
            AssertionError: If exit code doesn't match
        """
        if self.exit_code != expected:
            raise AssertionError(
                f"Expected exit code {expected}, got {self.exit_code}\n"
                f"Output: {self.output}"
            )

    def assert_output_contains(self, text: str) -> None:
        """Assert output contains text.

        Args:
            text: Text to search for

        Raises:
            AssertionError: If text not found in output
        """
        if text not in self.output:
            raise AssertionError(
                f"Expected output to contain '{text}'\n"
                f"Actual output: {self.output}"
            )
