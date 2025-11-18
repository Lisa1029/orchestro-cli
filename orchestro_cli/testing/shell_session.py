"""Persistent shell session for multi-step testing."""

import re
import time
from pathlib import Path
from typing import Optional, Dict

import pexpect

from .models import SessionState, SessionConfig, SessionResult
from .security import InputValidator


class ShellSession:
    """Persistent shell session with state tracking.

    Provides a long-lived shell environment where state persists between
    commands, enabling realistic workflow testing.

    Example:
        >>> session = ShellSession()
        >>> session.start()
        >>> session.execute("export FOO=bar")
        >>> result = session.execute("echo $FOO")
        >>> assert "bar" in result.output
        >>> session.close()
    """

    def __init__(self, config: Optional[SessionConfig] = None):
        """Initialize shell session.

        Args:
            config: Session configuration (uses defaults if None)
        """
        self.config = config or SessionConfig()
        self.state = SessionState(cwd=self.config.working_dir)
        self.process: Optional[pexpect.spawn] = None
        self.validator = InputValidator()
        self._started = False

    def start(self) -> None:
        """Start the shell session.

        Sets up a bash session with custom prompt for reliable parsing.

        Raises:
            RuntimeError: If session already started
            ValueError: If shell configuration is invalid
        """
        if self._started:
            raise RuntimeError("Session already started")

        # Prepare environment
        import os
        env = os.environ.copy()
        if self.config.env:
            env.update(self.config.env)
        env["PS1"] = self.config.prompt
        env["PS2"] = ""

        # Spawn shell process
        self.process = pexpect.spawn(
            self.config.shell,
            args=[],  # Empty args list
            env=env,
            encoding="utf-8",
            timeout=self.config.timeout,
            dimensions=self.config.dimensions,
            echo=False,  # Disable echo at pexpect level
            cwd=str(self.config.working_dir) if self.config.working_dir else None
        )

        # Wait for any initial prompt and consume it
        import time
        time.sleep(0.3)  # Give shell time to start

        # Read and discard any initial output
        try:
            self.process.expect('[\$#>] ', timeout=1.0)
        except pexpect.TIMEOUT:
            pass  # No initial prompt found

        # Send a newline to trigger a prompt
        self.process.sendline('')
        time.sleep(0.1)

        # Disable bracketed paste mode immediately
        self.process.sendline('bind "set enable-bracketed-paste off" 2>/dev/null')
        time.sleep(0.1)

        # Set custom prompt
        self.process.sendline('PS1="{}"'.format(self.config.prompt))
        self.process.sendline('PS2=""')

        # Wait for our custom prompt to appear
        try:
            self.process.expect(re.escape(self.config.prompt), timeout=5.0)
        except pexpect.TIMEOUT:
            raise RuntimeError("Failed to initialize shell session: prompt not detected")

        # Additional setup commands
        self.process.sendline('unset PROMPT_COMMAND')
        self.process.expect(re.escape(self.config.prompt), timeout=2.0)

        # Track initial working directory
        if self.config.working_dir:
            self.state.cwd = self.config.working_dir
        else:
            # Get PWD but consume the output properly
            self.process.sendline("pwd")
            time.sleep(0.05)
            self.process.expect(re.escape(self.config.prompt), timeout=2.0)
            pwd_output = self.process.before or ""
            # Clean and parse
            pwd_output = pwd_output.replace('\r', '').strip()
            for line in pwd_output.split('\n'):
                line = line.strip()
                if line and line.startswith('/'):
                    self.state.cwd = Path(line)
                    break
            if not self.state.cwd:
                self.state.cwd = Path.cwd()

        # Send one more command to clear any buffering issues
        self.process.sendline("true")
        time.sleep(0.05)
        self.process.expect(re.escape(self.config.prompt), timeout=2.0)

        self._started = True

    def execute(self, command: str, timeout: Optional[float] = None) -> SessionResult:
        """Execute a command in the session.

        Args:
            command: Command to execute
            timeout: Override default timeout for this command

        Returns:
            SessionResult containing output and state

        Raises:
            RuntimeError: If session not started
            ValueError: If command is potentially dangerous
            pexpect.TIMEOUT: If command times out
        """
        if not self._started:
            raise RuntimeError("Session not started - call start() first")

        # Validate command for security
        self.validator.validate_command(command)

        start_time = time.time()
        cmd_timeout = timeout or self.config.timeout

        try:
            # Execute command and capture output
            wrapped_command = (
                f"{command}; "
                "__ORCHESTRO_STATUS__=$?; "
                "echo __ORCHESTRO_PWD__=$(pwd); "
                "echo __ORCHESTRO_EXIT__=${__ORCHESTRO_STATUS__}"
            )
            self.process.sendline(wrapped_command)

            # Small delay to ensure command is sent
            time.sleep(0.05)

            # Wait for exit marker to capture output and exit code
            self.process.expect(r"__ORCHESTRO_EXIT__=(\d+)", timeout=cmd_timeout)
            output = (self.process.before or "") + (self.process.after or "")
            exit_code_match = self.process.match
            exit_code = int(exit_code_match.group(1)) if exit_code_match else 0

            # Wait for prompt to return to ensure buffer is clear
            self.process.expect(re.escape(self.config.prompt), timeout=cmd_timeout)
            output += self.process.before or ""

            # Clean ANSI escape sequences from command output
            ansi_escape = re.compile(r'\x1b\[[\x30-\x3f]*[\x20-\x2f]*[\x40-\x7e]|\x1b\].*?(?:\x07|\x1b\\)')
            output = ansi_escape.sub('', output)

            # Remove carriage returns
            output = output.replace('\r', '')

            # Clean up command output
            lines = output.split('\n')
            # Remove empty lines at start
            while lines and not lines[0].strip():
                lines = lines[1:]
            # Remove command echo if present
            if lines and lines[0].strip() == wrapped_command.strip():
                lines = lines[1:]

            # Remove prompt prefix if it leaked into output
            processed_lines = []
            for line in lines:
                if line.startswith(self.config.prompt):
                    line = line[len(self.config.prompt):]
                processed_lines.append(line)
            lines = processed_lines

            # Extract exit code marker line and rebuild output
            current_cwd = self.state.cwd
            cleaned_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("__ORCHESTRO_EXIT__="):
                    try:
                        exit_code = int(stripped.split("=", 1)[1])
                    except ValueError:
                        exit_code = 0
                    continue
                if stripped.startswith("__ORCHESTRO_PWD__="):
                    cwd_value = stripped.split("=", 1)[1]
                    current_cwd = Path(cwd_value) if cwd_value else current_cwd
                    continue
                cleaned_lines.append(line)

            output = '\n'.join(cleaned_lines).strip()
            if current_cwd:
                self.state.cwd = Path(current_cwd)

            # Update state
            self.state.add_command(command, exit_code)

            # Track environment variable changes
            if match := re.match(r'export\s+(\w+)=(.+)', command):
                var_name, var_value = match.groups()
                # Remove quotes if present
                var_value = var_value.strip('"').strip("'")
                self.state.update_variable(var_name, var_value)

            duration = time.time() - start_time

            return SessionResult(
                output=output,
                exit_code=exit_code,
                state=self.state,
                success=(exit_code == 0),
                duration=duration
            )

        except pexpect.TIMEOUT as e:
            duration = time.time() - start_time
            return SessionResult(
                output=self.process.before or "",
                exit_code=-1,
                state=self.state,
                success=False,
                error=f"Command timed out after {cmd_timeout}s",
                duration=duration
            )
        except Exception as e:
            duration = time.time() - start_time
            return SessionResult(
                output="",
                exit_code=-1,
                state=self.state,
                success=False,
                error=str(e),
                duration=duration
            )

    def _execute_internal(self, command: str, timeout: Optional[float] = None) -> str:
        """Internal command execution without state tracking.

        Args:
            command: Command to execute
            timeout: Command timeout

        Returns:
            Command output
        """
        cmd_timeout = timeout or self.config.timeout

        # Send command
        self.process.sendline(command)

        # Wait for prompt to return
        self.process.expect(re.escape(self.config.prompt), timeout=cmd_timeout)

        # Get output (everything before the prompt)
        output = self.process.before or ""

        # Clean ANSI escape sequences
        ansi_escape = re.compile(r'\x1b\[[0-9;]*[mGKHJDCBA]|\x1b\].*?\x07|\x1b\[.*?[\x40-\x7e]')
        output = ansi_escape.sub('', output)

        # Remove carriage returns
        output = output.replace('\r', '')

        # Remove the command echo if present
        lines = output.split('\n')
        if lines and lines[0].strip() == command.strip():
            lines = lines[1:]

        return '\n'.join(lines).strip()

    def send_control(self, char: str) -> None:
        """Send control character to session.

        Args:
            char: Control character (e.g., 'c' for Ctrl+C)

        Raises:
            RuntimeError: If session not started
        """
        if not self._started:
            raise RuntimeError("Session not started")

        self.process.sendcontrol(char)

    def get_variable(self, name: str) -> Optional[str]:
        """Get value of environment variable.

        Args:
            name: Variable name

        Returns:
            Variable value or None if not set
        """
        if name in self.state.variables:
            return self.state.variables[name]

        # Query shell for variable value
        try:
            output = self._execute_internal(f"echo ${name}")
            value = output.strip()
            if value:
                self.state.update_variable(name, value)
                return value
        except Exception:
            pass

        return None

    def set_variable(self, name: str, value: str) -> SessionResult:
        """Set environment variable.

        Args:
            name: Variable name
            value: Variable value

        Returns:
            Result of export command
        """
        return self.execute(f'export {name}="{value}"')

    def change_directory(self, path: Path) -> SessionResult:
        """Change working directory.

        Args:
            path: Target directory

        Returns:
            Result of cd command
        """
        return self.execute(f'cd "{path}"')

    def reset(self) -> None:
        """Reset session to clean state.

        Clears environment variables and returns to initial directory.
        """
        if not self._started:
            return

        # Clear all custom variables
        for var_name in self.state.variables:
            self._execute_internal(f"unset {var_name}")

        # Return to initial directory
        if self.config.working_dir:
            self._execute_internal(f'cd "{self.config.working_dir}"')

        # Reset state tracking
        self.state = SessionState(cwd=self.config.working_dir)

    def is_alive(self) -> bool:
        """Check if session process is still running.

        Returns:
            True if process is alive
        """
        return self.process is not None and self.process.isalive()

    def close(self) -> None:
        """Close the session gracefully.

        Sends exit command and terminates process if needed.
        """
        if not self._started:
            return

        try:
            if self.is_alive():
                self.process.sendline("exit")
                self.process.expect(pexpect.EOF, timeout=5.0)
        except Exception:
            pass
        finally:
            if self.process and self.is_alive():
                self.process.terminate(force=True)

            self.process = None
            self._started = False

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
