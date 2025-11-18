"""Security controls for session testing."""

import re
import resource
from pathlib import Path
from typing import List, Optional, Set


class InputValidator:
    """Validates commands for security risks.

    Prevents execution of potentially dangerous commands in test sessions.
    """

    # Commands that are always blocked
    BLOCKED_COMMANDS: Set[str] = {
        "rm", "rmdir", "shred", "dd", "mkfs",
        "fdisk", "parted", "mount", "umount",
        "kill", "killall", "pkill",
        "shutdown", "reboot", "halt", "poweroff",
        "init", "telinit",
        "chmod", "chown", "chgrp",  # Can be dangerous
        "sudo", "su",  # Privilege escalation
        ":(){:|:&};:",  # Fork bomb pattern
    }

    # Dangerous patterns to block
    DANGEROUS_PATTERNS: List[re.Pattern] = [
        re.compile(r'\brm\s+(-[rf]+\s+)?/'),  # rm targeting root or near-root
        re.compile(r'>\s*/dev/sd[a-z]'),  # Write to block devices
        re.compile(r'\|.*\bdd\b'),  # Piping to dd
        re.compile(r'wget.*\|\s*bash'),  # Remote code execution
        re.compile(r'curl.*\|\s*bash'),  # Remote code execution
        re.compile(r'eval\s+\$\('),  # Command substitution eval
        re.compile(r'exec\s+[<>]'),  # File descriptor manipulation
        re.compile(r'\$\(.*wget.*\)'),  # Command substitution with wget
        re.compile(r'\$\(.*curl.*\)'),  # Command substitution with curl
    ]

    def __init__(self, strict: bool = True):
        """Initialize validator.

        Args:
            strict: Enable strict validation (blocks more commands)
        """
        self.strict = strict

    def validate_command(self, command: str) -> None:
        """Validate a command for safety.

        Args:
            command: Command to validate

        Raises:
            ValueError: If command is potentially dangerous
        """
        cmd_lower = command.lower().strip()

        # Check for blocked commands
        first_word = cmd_lower.split()[0] if cmd_lower else ""
        if first_word in self.BLOCKED_COMMANDS:
            raise ValueError(
                f"Command blocked for security: '{first_word}'\n"
                f"This command is not allowed in test sessions."
            )

        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.search(command):
                raise ValueError(
                    f"Command contains dangerous pattern: {pattern.pattern}\n"
                    f"Command: {command}"
                )

        # Strict mode: additional checks
        if self.strict:
            self._validate_strict(command)

    def _validate_strict(self, command: str) -> None:
        """Additional strict validation.

        Args:
            command: Command to validate

        Raises:
            ValueError: If command fails strict checks
        """
        # Block commands with suspicious redirects
        if re.search(r'>\s*/etc/', command):
            raise ValueError("Writing to /etc/ is not allowed in test sessions")

        # Block background jobs that could outlive the test
        if command.strip().endswith('&'):
            raise ValueError("Background jobs are not allowed in test sessions")

        # Warn about long-running commands
        if any(word in command for word in ['sleep', 'wait', 'watch']):
            # This is just a soft warning - we allow these
            pass


class ResourceLimiter:
    """Manages resource limits for test sessions.

    Prevents test sessions from consuming excessive resources.
    """

    def __init__(
        self,
        max_memory_mb: int = 1024,
        max_processes: int = 100,
        max_cpu_time_sec: int = 300
    ):
        """Initialize resource limiter.

        Args:
            max_memory_mb: Maximum memory in MB
            max_processes: Maximum number of processes
            max_cpu_time_sec: Maximum CPU time in seconds
        """
        self.max_memory_mb = max_memory_mb
        self.max_processes = max_processes
        self.max_cpu_time_sec = max_cpu_time_sec

    def apply_limits(self) -> None:
        """Apply resource limits to current process.

        Note: This should be called before spawning test processes.
        """
        try:
            # Memory limit
            max_memory_bytes = self.max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (max_memory_bytes, max_memory_bytes))

            # Process limit
            resource.setrlimit(resource.RLIMIT_NPROC, (self.max_processes, self.max_processes))

            # CPU time limit
            resource.setrlimit(resource.RLIMIT_CPU, (self.max_cpu_time_sec, self.max_cpu_time_sec))

        except (ValueError, OSError) as e:
            # Limits might not be supported on all platforms
            import warnings
            warnings.warn(f"Could not apply resource limits: {e}")


class WorkspaceIsolator:
    """Manages isolated workspaces for test sessions.

    Creates temporary, isolated directories for test execution.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize workspace isolator.

        Args:
            base_dir: Base directory for workspaces (uses temp if None)
        """
        self.base_dir = base_dir or Path("/tmp/orchestro_test_workspaces")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_workspace(self, name: str) -> Path:
        """Create an isolated workspace.

        Args:
            name: Workspace identifier

        Returns:
            Path to workspace directory
        """
        # Sanitize name
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
        workspace = self.base_dir / safe_name
        workspace.mkdir(parents=True, exist_ok=True)

        # Create standard directories
        (workspace / "home").mkdir(exist_ok=True)
        (workspace / "data").mkdir(exist_ok=True)
        (workspace / "tmp").mkdir(exist_ok=True)

        return workspace

    def cleanup_workspace(self, workspace: Path) -> None:
        """Clean up a workspace.

        Args:
            workspace: Workspace to clean up
        """
        import shutil
        if workspace.exists() and workspace.is_relative_to(self.base_dir):
            shutil.rmtree(workspace, ignore_errors=True)


class CommandAuditor:
    """Audits commands executed in test sessions.

    Maintains a log of all commands for security review.
    """

    def __init__(self, log_file: Optional[Path] = None):
        """Initialize command auditor.

        Args:
            log_file: Path to audit log file
        """
        self.log_file = log_file
        self.commands: List[tuple[str, str]] = []  # (timestamp, command)

    def log_command(self, command: str) -> None:
        """Log a command execution.

        Args:
            command: Command that was executed
        """
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        self.commands.append((timestamp, command))

        if self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(f"{timestamp} | {command}\n")

    def get_audit_log(self) -> List[tuple[str, str]]:
        """Get the audit log.

        Returns:
            List of (timestamp, command) tuples
        """
        return self.commands.copy()
