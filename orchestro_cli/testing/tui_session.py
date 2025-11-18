"""TUI session management for interactive application testing."""

import asyncio
import re
import time
from pathlib import Path
from typing import Optional, List

import pexpect

from .shell_session import ShellSession
from .models import SessionConfig, SessionResult


class TUISession(ShellSession):
    """Session for testing TUI (Text User Interface) applications.

    Extends ShellSession to support launching TUI apps and interacting
    with them through key presses and screen captures.

    Example:
        >>> session = TUISession()
        >>> session.start()
        >>> session.launch_tui("vim test.txt")
        >>> session.send_keys("iHello World")
        >>> session.send_control('c')
        >>> session.send_keys(":wq")
        >>> session.close()
    """

    def __init__(self, config: Optional[SessionConfig] = None):
        """Initialize TUI session.

        Args:
            config: Session configuration
        """
        super().__init__(config)
        self.tui_active = False
        self.app_name: Optional[str] = None

    def launch_tui(self, command: str, timeout: Optional[float] = None) -> None:
        """Launch a TUI application.

        Args:
            command: Command to launch TUI app
            timeout: Wait timeout for app to start

        Raises:
            RuntimeError: If session not started or TUI already active
            ValueError: If command is dangerous
        """
        if not self._started:
            raise RuntimeError("Session not started")
        if self.tui_active:
            raise RuntimeError("TUI already active")

        # Validate command
        self.validator.validate_command(command)

        # Extract app name for tracking
        self.app_name = command.split()[0]

        # Launch the TUI app
        self.process.sendline(command)

        # Give app time to initialize
        wait_time = timeout or 2.0
        time.sleep(wait_time)

        self.tui_active = True
        self.state.add_command(f"[TUI] {command}", 0)

    def send_keys(self, keys: str, delay: float = 0.1) -> None:
        """Send keystrokes to TUI application.

        Args:
            keys: Keys to send (can include special sequences)
            delay: Delay between keystrokes (seconds)

        Raises:
            RuntimeError: If TUI not active
        """
        if not self.tui_active:
            raise RuntimeError("No TUI application active")

        # Process special key sequences
        for key in self._parse_keys(keys):
            if key.startswith("<") and key.endswith(">"):
                # Special key (e.g., <Enter>, <Tab>)
                self._send_special_key(key[1:-1])
            else:
                # Regular character
                self.process.send(key)

            if delay > 0:
                time.sleep(delay)

    def _parse_keys(self, keys: str) -> List[str]:
        """Parse key sequence into individual keys.

        Args:
            keys: Key sequence string

        Returns:
            List of individual keys
        """
        result = []
        i = 0
        while i < len(keys):
            if keys[i] == '<':
                # Find matching >
                end = keys.find('>', i)
                if end != -1:
                    result.append(keys[i:end+1])
                    i = end + 1
                else:
                    result.append(keys[i])
                    i += 1
            else:
                result.append(keys[i])
                i += 1
        return result

    def _send_special_key(self, key_name: str) -> None:
        """Send a special key.

        Args:
            key_name: Name of special key (e.g., Enter, Tab, Up)
        """
        key_map = {
            "Enter": "\r",
            "Tab": "\t",
            "Space": " ",
            "Escape": "\x1b",
            "Up": "\x1b[A",
            "Down": "\x1b[B",
            "Right": "\x1b[C",
            "Left": "\x1b[D",
            "Home": "\x1b[H",
            "End": "\x1b[F",
            "PageUp": "\x1b[5~",
            "PageDown": "\x1b[6~",
            "Delete": "\x1b[3~",
            "Backspace": "\x7f",
        }

        key_name_lower = key_name.lower().capitalize()
        if key_name_lower in key_map:
            self.process.send(key_map[key_name_lower])
        else:
            # Try as literal
            self.process.send(key_name)

    def expect_screen(self, pattern: str, timeout: Optional[float] = None) -> str:
        """Wait for pattern to appear on screen.

        Args:
            pattern: Regex pattern to wait for
            timeout: Wait timeout

        Returns:
            Matched output

        Raises:
            pexpect.TIMEOUT: If pattern not found
        """
        if not self.tui_active:
            raise RuntimeError("No TUI application active")

        cmd_timeout = timeout or self.config.timeout
        self.process.expect(pattern, timeout=cmd_timeout)
        return self.process.after or ""

    def get_screen(self) -> str:
        """Get current screen content.

        Returns:
            Current terminal buffer content
        """
        if not self.tui_active:
            raise RuntimeError("No TUI application active")

        return self.process.before or ""

    async def capture_screenshot(
        self,
        name: str,
        trigger_dir: Path,
        artifacts_dir: Path,
        timeout: float = 10.0
    ) -> Path:
        """Capture screenshot of current TUI state.

        Integrates with Orchestro's screenshot trigger mechanism.

        Args:
            name: Screenshot name
            trigger_dir: Directory for trigger files
            artifacts_dir: Directory for screenshot output
            timeout: Wait timeout

        Returns:
            Path to captured screenshot

        Raises:
            TimeoutError: If screenshot not captured
        """
        if not self.tui_active:
            raise RuntimeError("No TUI application active")

        # Sanitize name
        slug = re.sub(r"[^a-zA-Z0-9_-]", "-", name.strip().lower()) or "screenshot"
        filename = slug if slug.endswith(".svg") else f"{slug}.svg"
        screenshot_path = artifacts_dir / filename

        # Create trigger file
        trigger_file = trigger_dir / f"{slug}.trigger"
        trigger_file.touch()

        # Wait for screenshot to appear
        deadline = time.time() + timeout
        while time.time() < deadline:
            if screenshot_path.exists():
                # Clean up trigger
                if trigger_file.exists():
                    trigger_file.unlink()
                return screenshot_path

            await asyncio.sleep(0.2)

        # Timeout - clean up trigger
        if trigger_file.exists():
            trigger_file.unlink()

        raise TimeoutError(f"Screenshot '{filename}' not created within {timeout}s")

    def exit_tui(self, exit_keys: Optional[str] = None) -> SessionResult:
        """Exit the TUI application.

        Args:
            exit_keys: Keys to send to exit (e.g., ":q<Enter>" for vim)
                      If None, sends Ctrl+C

        Returns:
            Result of exit operation
        """
        if not self.tui_active:
            raise RuntimeError("No TUI application active")

        start_time = time.time()

        try:
            if exit_keys:
                self.send_keys(exit_keys)
            else:
                self.send_control('c')

            # Wait for prompt to return
            self.process.expect(re.escape(self.config.prompt), timeout=5.0)

            output = self.process.before or ""
            duration = time.time() - start_time

            self.tui_active = False
            self.app_name = None

            return SessionResult(
                output=output,
                exit_code=0,
                state=self.state,
                success=True,
                duration=duration
            )

        except pexpect.TIMEOUT:
            # Force kill if graceful exit fails
            self.send_control('c')
            time.sleep(0.5)

            self.tui_active = False
            self.app_name = None

            duration = time.time() - start_time
            return SessionResult(
                output=self.process.before or "",
                exit_code=-1,
                state=self.state,
                success=False,
                error="TUI exit timed out",
                duration=duration
            )

    def close(self) -> None:
        """Close session, exiting TUI if active."""
        if self.tui_active:
            try:
                self.exit_tui()
            except Exception:
                pass

        super().close()
