"""Process management abstraction layer."""

import os
import platform
import shlex
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, List
import pexpect


class ProcessManager:
    """Manages process spawning and lifecycle.

    Single Responsibility: Abstract process interaction.
    Supports: pexpect (POSIX), subprocess (Windows), custom drivers via injection.
    """

    def __init__(
        self,
        workspace: Optional[Path] = None,
        verbose: bool = False,
        driver: Optional[Any] = None
    ):
        """Initialize process manager.

        Args:
            workspace: Optional workspace directory for isolation
            verbose: Enable verbose logging
            driver: Optional custom process driver (auto-selects if None)
        """
        self.workspace = workspace
        self.verbose = verbose
        self._temp_dir = Path(tempfile.gettempdir()) / ".vyb_orchestro"
        self._temp_dir.mkdir(parents=True, exist_ok=True)

        # Auto-select driver based on platform
        if driver is None:
            if platform.system() == "Windows":
                from ..drivers import SubprocessDriver
                self.driver = SubprocessDriver()
            else:
                from ..drivers import PexpectDriver
                self.driver = PexpectDriver()
        else:
            self.driver = driver

        self.process: Optional[Any] = None

    def spawn(
        self,
        command: Any,
        env: Optional[Dict[str, str]] = None,
        timeout: float = 30.0
    ) -> Any:
        """Spawn a new process.

        Args:
            command: Command to execute (string or list)
            env: Environment variables
            timeout: Default timeout for operations

        Returns:
            Spawned process handle
        """
        # Prepare command
        if isinstance(command, str):
            cmd_parts = shlex.split(command)
        else:
            cmd_parts = list(command)

        # Prepare environment
        process_env = self._prepare_env(env or {})

        if self.verbose:
            print(f"[ProcessManager] Spawning: {' '.join(cmd_parts)}")

        # Spawn process using driver
        self.process = self.driver.spawn(
            command=cmd_parts,
            env=process_env,
            timeout=timeout,
            cwd=self.workspace
        )

        return self.process

    def _prepare_env(self, scenario_env: Dict[str, str]) -> Dict[str, str]:
        """Prepare environment variables for process.

        Args:
            scenario_env: Environment variables from scenario

        Returns:
            Complete environment dictionary
        """
        env = os.environ.copy()
        env.update({str(k): str(v) for k, v in scenario_env.items()})

        # Add workspace if configured
        if self.workspace:
            home = self.workspace / "home"
            data = self.workspace / "data"
            home.mkdir(parents=True, exist_ok=True)
            data.mkdir(parents=True, exist_ok=True)
            env["HOME"] = str(home)
            env["VYB_DATA_ROOT"] = str(data)

        # Enable automated screenshot monitoring
        env["VYB_AUTO_SCREENSHOT"] = "1"

        return env

    def is_alive(self) -> bool:
        """Check if process is still running."""
        return self.process is not None and self.driver.is_alive()

    def terminate(self) -> None:
        """Terminate the process gracefully."""
        if self.process:
            self.driver.terminate()

    def kill(self) -> None:
        """Forcefully kill the process."""
        if self.process:
            self.driver.kill()

    @property
    def exit_status(self) -> Optional[int]:
        """Get process exit status."""
        return self.driver.exit_status if self.process else None

    @property
    def trigger_dir(self) -> Path:
        """Get screenshot trigger directory."""
        trigger_path = self._temp_dir / "screenshot_triggers"
        trigger_path.mkdir(parents=True, exist_ok=True)
        return trigger_path

    @property
    def sentinel_file(self) -> Path:
        """Get sentinel file path."""
        return self._temp_dir / "sentinels"
