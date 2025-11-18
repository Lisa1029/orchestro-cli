"""Subprocess-based process driver (Cross-platform including Windows)."""

from __future__ import annotations

import re
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, IO


class SubprocessDriver:
    """Process driver using subprocess (Windows, Linux, macOS).

    This driver provides cross-platform support including Windows where
    pexpect is not available.

    Note: This is a simplified implementation that provides basic
    expect/send functionality. For full terminal emulation features,
    use PexpectDriver on POSIX systems.
    """

    def __init__(self):
        """Initialize subprocess driver."""
        self.process: Optional[subprocess.Popen] = None
        self._stdout_buffer: List[str] = []
        self._stderr_buffer: List[str] = []
        self._reader_thread: Optional[threading.Thread] = None
        self._running = False
        self._last_match = ""
        self._before_match = ""

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
            timeout: Default timeout (stored but not enforced here)
            cwd: Working directory

        Returns:
            subprocess.Popen instance
        """
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=str(cwd) if cwd else None,
            text=True,
            bufsize=1  # Line buffered
        )

        # Start background thread to read output
        self._running = True
        self._reader_thread = threading.Thread(
            target=self._read_output,
            daemon=True
        )
        self._reader_thread.start()

        return self.process

    def _read_output(self) -> None:
        """Background thread to read process output."""
        if not self.process or not self.process.stdout:
            return

        while self._running and self.process.poll() is None:
            try:
                line = self.process.stdout.readline()
                if line:
                    self._stdout_buffer.append(line)
            except Exception:
                break

        # Read any remaining output
        if self.process and self.process.stdout:
            remaining = self.process.stdout.read()
            if remaining:
                self._stdout_buffer.append(remaining)

    def send(self, data: str) -> None:
        """Send data without newline."""
        if not self.process or not self.process.stdin:
            raise RuntimeError("Process not spawned")
        self.process.stdin.write(data)
        self.process.stdin.flush()

    def sendline(self, data: str) -> None:
        """Send data with newline."""
        if not self.process or not self.process.stdin:
            raise RuntimeError("Process not spawned")
        self.process.stdin.write(data + "\n")
        self.process.stdin.flush()

    def sendcontrol(self, char: str) -> None:
        """Send control character.

        Note: Limited support on Windows. Common controls:
        - 'c': Ctrl+C (SIGINT) - terminates process
        - 'd': Ctrl+D (EOF) - closes stdin
        """
        if not self.process:
            raise RuntimeError("Process not spawned")

        if char.lower() == 'c':
            # Ctrl+C - terminate
            self.process.terminate()
        elif char.lower() == 'd':
            # Ctrl+D - close stdin (EOF)
            if self.process.stdin:
                self.process.stdin.close()
        else:
            # Other control characters - limited support
            # Try sending as escape sequence
            if self.process.stdin:
                self.process.stdin.write(chr(ord(char)))
                self.process.stdin.flush()

    def expect(self, pattern: str, timeout: Optional[float] = None) -> str:
        """Wait for pattern in output.

        Args:
            pattern: Regular expression pattern
            timeout: Timeout in seconds

        Returns:
            Matched text

        Raises:
            TimeoutError: If pattern not found within timeout
            RuntimeError: If process exits before match
        """
        if not self.process:
            raise RuntimeError("Process not spawned")

        regex = re.compile(pattern)
        start_time = time.time()
        timeout = timeout or 30.0

        accumulated = ""

        while True:
            # Check timeout
            if time.time() - start_time > timeout:
                raise TimeoutError(
                    f"Pattern '{pattern}' not found within {timeout}s"
                )

            # Check if process terminated
            if self.process.poll() is not None:
                raise RuntimeError(
                    f"Process terminated before pattern match "
                    f"(exit code: {self.process.returncode})"
                )

            # Get new output
            while self._stdout_buffer:
                line = self._stdout_buffer.pop(0)
                accumulated += line

                # Try to match
                match = regex.search(accumulated)
                if match:
                    self._before_match = accumulated[:match.start()]
                    self._last_match = match.group(0)
                    return self._last_match

            # Small sleep to avoid busy waiting
            time.sleep(0.01)

    def is_alive(self) -> bool:
        """Check if process is running."""
        if not self.process:
            return False
        return self.process.poll() is None

    def terminate(self) -> None:
        """Terminate the process."""
        if self.process:
            self._running = False
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

    def kill(self) -> None:
        """Kill the process forcefully."""
        if self.process:
            self._running = False
            self.process.kill()

    @property
    def exit_status(self) -> Optional[int]:
        """Get exit status."""
        if not self.process:
            return None
        return self.process.returncode

    @property
    def before(self) -> str:
        """Get output before last match."""
        return self._before_match

    @property
    def after(self) -> str:
        """Get matched pattern."""
        return self._last_match
