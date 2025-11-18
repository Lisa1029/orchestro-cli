"""Process driver protocol for custom process backends.

This protocol enables alternative process spawning implementations:
- Windows subprocess support
- Remote execution (SSH, Docker)
- Custom terminal emulators
- Testing mocks
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol


class ProcessDriver(Protocol):
    """Protocol for process spawning and interaction.

    Implementations can provide custom process backends while maintaining
    compatibility with the execution engine.

    Examples:
        - PexpectDriver (default, POSIX systems)
        - SubprocessDriver (Windows support)
        - SSHDriver (remote execution)
        - DockerDriver (containerized execution)
        - MockDriver (testing)
    """

    def spawn(
        self,
        command: List[str],
        env: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        cwd: Optional[Path] = None
    ) -> Any:
        """Spawn a new process.

        Args:
            command: Command and arguments to execute
            env: Environment variables for the process
            timeout: Default timeout for operations
            cwd: Working directory for the process

        Returns:
            Process handle compatible with expect/send operations

        Raises:
            ProcessSpawnError: If process fails to start
        """
        ...

    def send(self, data: str) -> None:
        """Send data to the process stdin.

        Args:
            data: String to send (without newline)
        """
        ...

    def sendline(self, data: str) -> None:
        """Send data to the process stdin with newline.

        Args:
            data: String to send (newline will be appended)
        """
        ...

    def sendcontrol(self, char: str) -> None:
        """Send control character to the process.

        Args:
            char: Control character (e.g., 'c' for Ctrl+C)
        """
        ...

    def expect(self, pattern: str, timeout: Optional[float] = None) -> str:
        """Wait for pattern to appear in process output.

        Args:
            pattern: Regular expression pattern to match
            timeout: Timeout in seconds (None = use default)

        Returns:
            Matched text from the output

        Raises:
            TimeoutError: If pattern not found within timeout
            ProcessTerminated: If process exits before match
        """
        ...

    def is_alive(self) -> bool:
        """Check if the process is still running.

        Returns:
            True if process is alive, False otherwise
        """
        ...

    def terminate(self) -> None:
        """Gracefully terminate the process (SIGTERM)."""
        ...

    def kill(self) -> None:
        """Force kill the process (SIGKILL)."""
        ...

    @property
    def exit_status(self) -> Optional[int]:
        """Get process exit status.

        Returns:
            Exit code if process has exited, None if still running
        """
        ...

    @property
    def before(self) -> str:
        """Get output before the last expect match.

        Returns:
            Text captured before the match
        """
        ...

    @property
    def after(self) -> str:
        """Get output that matched the expect pattern.

        Returns:
            Text that matched the pattern
        """
        ...
