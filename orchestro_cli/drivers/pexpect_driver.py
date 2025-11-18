"""Pexpect-based process driver (POSIX only)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pexpect


class PexpectDriver:
    """Process driver using pexpect (POSIX systems: Linux, macOS, BSD).

    This is the default driver used by Orchestro CLI.
    """

    def __init__(self):
        """Initialize pexpect driver."""
        self.process: Optional[pexpect.spawn] = None

    def spawn(
        self,
        command: List[str],
        env: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        cwd: Optional[Path] = None
    ) -> Any:
        """Spawn a new process.

        Args:
            command: Command and arguments
            env: Environment variables
            timeout: Default timeout
            cwd: Working directory

        Returns:
            pexpect.spawn instance
        """
        self.process = pexpect.spawn(
            command[0],
            command[1:] if len(command) > 1 else [],
            env=env,
            encoding="utf-8",
            timeout=timeout,
            dimensions=(80, 120),
            echo=False,
            cwd=str(cwd) if cwd else None
        )
        return self.process

    def send(self, data: str) -> None:
        """Send data without newline."""
        if not self.process:
            raise RuntimeError("Process not spawned")
        self.process.send(data)

    def sendline(self, data: str) -> None:
        """Send data with newline."""
        if not self.process:
            raise RuntimeError("Process not spawned")
        self.process.sendline(data)

    def sendcontrol(self, char: str) -> None:
        """Send control character."""
        if not self.process:
            raise RuntimeError("Process not spawned")
        self.process.sendcontrol(char)

    def expect(self, pattern: str, timeout: Optional[float] = None) -> str:
        """Wait for pattern in output."""
        if not self.process:
            raise RuntimeError("Process not spawned")
        self.process.expect(pattern, timeout=timeout)
        return self.process.after

    def is_alive(self) -> bool:
        """Check if process is running."""
        if not self.process:
            return False
        return self.process.isalive()

    def terminate(self) -> None:
        """Terminate the process (SIGTERM)."""
        if self.process:
            self.process.terminate()

    def kill(self) -> None:
        """Kill the process (SIGKILL)."""
        if self.process:
            self.process.kill(9)

    @property
    def exit_status(self) -> Optional[int]:
        """Get exit status."""
        if not self.process:
            return None
        return self.process.exitstatus

    @property
    def before(self) -> str:
        """Get output before last match."""
        if not self.process:
            return ""
        return self.process.before or ""

    @property
    def after(self) -> str:
        """Get matched pattern."""
        if not self.process:
            return ""
        return self.process.after or ""
