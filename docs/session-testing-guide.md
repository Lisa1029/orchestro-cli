# Session State Testing Guide

This guide explains how to use Orchestro's session state testing infrastructure for multi-step workflow tests.

## Overview

Session state testing enables you to write tests for complex, multi-step workflows where state must persist between commands. Unlike traditional test approaches that spawn a new process for each command, session-based testing provides a long-lived shell environment.

## Key Features

- **Persistent State**: Environment variables, working directory, and command history persist between commands
- **Shell Sessions**: Full bash session for command-line workflows
- **TUI Sessions**: Extended support for testing Text User Interface applications
- **Security Controls**: Built-in validation to prevent dangerous commands
- **Pytest Integration**: Ready-to-use fixtures for common testing patterns
- **Custom Assertions**: Domain-specific assertions for cleaner test code

## Quick Start

### Basic Shell Session

```python
def test_basic_workflow(shell_session):
    # Set environment variable
    shell_session.execute("export API_KEY=test123")

    # Use variable (state persists!)
    result = shell_session.execute("echo $API_KEY")
    assert "test123" in result.output

    # Change directory
    shell_session.execute("cd /tmp")
    result = shell_session.execute("pwd")
    assert "/tmp" in result.output
```

### Multi-Step Git Workflow

```python
from orchestro_cli.testing.assertions import assert_success, assert_file_exists

def test_git_workflow(shell_session, temp_workspace):
    shell_session.change_directory(temp_workspace)

    # Initialize repo
    result = shell_session.execute("git init")
    assert_success(result)

    # Create and commit file
    shell_session.execute("echo 'test' > README.md")
    assert_file_exists(shell_session, "README.md")

    shell_session.execute("git add README.md")
    result = shell_session.execute("git commit -m 'Initial commit'")
    assert_success(result)

    # Verify commit
    result = shell_session.execute("git log --oneline")
    assert "Initial commit" in result.output
```

### Build Pipeline Workflow

```python
def test_build_pipeline(shell_session, temp_workspace):
    shell_session.change_directory(temp_workspace)

    # Set up build environment
    shell_session.set_variable("BUILD_DIR", "build")
    shell_session.set_variable("NODE_ENV", "production")

    # Create structure
    shell_session.execute("mkdir -p src $BUILD_DIR")
    shell_session.execute("echo 'console.log(\"app\")' > src/index.js")

    # Run build (example - adapt to your build system)
    result = shell_session.execute("cp src/* $BUILD_DIR/")
    assert_success(result)

    # Verify output
    assert_file_exists(shell_session, "build/index.js")
```

## Core Concepts

### Session State

The `SessionState` object tracks:
- **variables**: Environment variables set during session
- **cwd**: Current working directory
- **exit_codes**: History of exit codes from commands
- **history**: List of executed commands

### Session Configuration

Customize session behavior with `SessionConfig`:

```python
from orchestro_cli.testing import SessionConfig, ShellSession

config = SessionConfig(
    timeout=60.0,  # Command timeout in seconds
    working_dir=Path("/tmp/test"),  # Initial directory
    env={"CUSTOM_VAR": "value"},  # Initial environment
    prompt="ORCHESTRO_PROMPT>",  # Custom prompt for parsing
)

session = ShellSession(config)
session.start()
# ... use session
session.close()
```

### Session Result

Each command execution returns a `SessionResult`:

```python
result = shell_session.execute("echo test")

print(result.output)        # Command output
print(result.exit_code)     # Exit code
print(result.success)       # True if exit_code == 0
print(result.error)         # Error message (if any)
print(result.duration)      # Execution time in seconds

# Built-in assertions
result.assert_success()
result.assert_exit_code(0)
result.assert_output_contains("test")
```

## Available Fixtures

### `shell_session` (Function-scoped)

Fresh shell session for each test function:

```python
def test_something(shell_session):
    result = shell_session.execute("echo test")
    assert result.success
```

### `persistent_shell` (Module-scoped)

Shared session across all tests in a module (use with caution):

```python
def test_step_1(persistent_shell):
    persistent_shell.execute("export SHARED_VAR=value")

def test_step_2(persistent_shell):
    # SHARED_VAR still exists
    result = persistent_shell.execute("echo $SHARED_VAR")
    assert "value" in result.output
```

### `isolated_shell_session`

Session with isolated temporary workspace:

```python
def test_isolated(isolated_shell_session, temp_workspace):
    # Session runs in temp_workspace
    result = isolated_shell_session.execute("pwd")
    assert str(temp_workspace) in result.output
```

### `tui_session`

Session for testing TUI applications:

```python
def test_vim(tui_session, temp_workspace):
    tui_session.change_directory(temp_workspace)

    # Launch vim
    tui_session.launch_tui("vim test.txt")

    # Send keystrokes
    tui_session.send_keys("iHello World<Escape>")
    tui_session.send_keys(":wq<Enter>")

    # Exit and verify
    result = tui_session.exit_tui()
    assert result.success
```

### `custom_shell_session` (Factory)

Create multiple sessions with custom configurations:

```python
def test_multiple_sessions(custom_shell_session):
    config1 = SessionConfig(timeout=30.0)
    config2 = SessionConfig(timeout=60.0)

    session1 = custom_shell_session(config1)
    session2 = custom_shell_session(config2)

    # Both sessions available
    # Cleanup is automatic
```

## Custom Assertions

### Output Assertions

```python
from orchestro_cli.testing.assertions import (
    assert_output_contains,
    assert_output_matches,
)

result = shell_session.execute("ls -la")

# String or regex search
assert_output_contains(result, "total")
assert_output_matches(result, r"drwx.*")
```

### Exit Code Assertions

```python
from orchestro_cli.testing.assertions import (
    assert_exit_code,
    assert_success,
    assert_failure,
)

result = shell_session.execute("true")
assert_success(result)
assert_exit_code(result, 0)

result = shell_session.execute("false")
assert_failure(result)
```

### State Assertions

```python
from orchestro_cli.testing.assertions import (
    assert_variable_set,
    assert_cwd,
    assert_file_exists,
    assert_command_in_history,
)

shell_session.execute("export MY_VAR=value")
assert_variable_set(shell_session, "MY_VAR", "value")

shell_session.execute("cd /tmp")
assert_cwd(shell_session, "/tmp")

shell_session.execute("touch test.txt")
assert_file_exists(shell_session, "test.txt")

assert_command_in_history(shell_session, "touch test.txt")
```

### Performance Assertions

```python
from orchestro_cli.testing.assertions import assert_execution_time

result = shell_session.execute("sleep 0.1")
assert_execution_time(result, max_seconds=1.0)
```

## TUI Testing

### Launching TUI Applications

```python
def test_tui_app(tui_session):
    # Launch app
    tui_session.launch_tui("./my-tui-app")

    # Interact
    tui_session.send_keys("hello")
    tui_session.send_control('c')

    # Exit
    tui_session.exit_tui()
```

### Special Keys

Use angle bracket notation for special keys:

```python
tui_session.send_keys("text<Enter>more<Tab>keys<Escape>")

# Supported keys:
# <Enter>, <Tab>, <Space>, <Escape>
# <Up>, <Down>, <Left>, <Right>
# <Home>, <End>, <PageUp>, <PageDown>
# <Delete>, <Backspace>
```

### Screenshot Capture

```python
@pytest.mark.asyncio
async def test_with_screenshot(tui_session_with_screenshots):
    session, trigger_dir, artifacts_dir = tui_session_with_screenshots

    session.launch_tui("./my-app")
    session.send_keys("navigate to view")

    # Capture screenshot
    screenshot_path = await session.capture_screenshot(
        "main-view",
        trigger_dir,
        artifacts_dir
    )

    assert screenshot_path.exists()
```

## Security Features

### Input Validation

Commands are automatically validated to prevent:
- File system destruction (`rm -rf /`, `mkfs`, etc.)
- Privilege escalation (`sudo`, `su`)
- Remote code execution (`curl | bash`)
- Dangerous redirects (`> /dev/sda`)

```python
def test_dangerous_command_blocked(shell_session):
    with pytest.raises(ValueError, match="blocked"):
        shell_session.execute("rm -rf /")
```

### Resource Limits

Control resource usage:

```python
from orchestro_cli.testing.security import ResourceLimiter

limiter = ResourceLimiter(
    max_memory_mb=1024,
    max_processes=100,
    max_cpu_time_sec=300
)
limiter.apply_limits()
```

### Workspace Isolation

Create isolated test workspaces:

```python
from orchestro_cli.testing.security import WorkspaceIsolator

isolator = WorkspaceIsolator()
workspace = isolator.create_workspace("test-name")

# Use workspace
# ...

# Cleanup
isolator.cleanup_workspace(workspace)
```

### Command Auditing

Track all executed commands:

```python
from orchestro_cli.testing.security import CommandAuditor

auditor = CommandAuditor(log_file=Path("audit.log"))
auditor.log_command("executed command")

# Review audit log
for timestamp, command in auditor.get_audit_log():
    print(f"{timestamp}: {command}")
```

## Advanced Patterns

### Context Manager Usage

```python
from orchestro_cli.testing import ShellSession

def test_with_context_manager():
    with ShellSession() as session:
        result = session.execute("echo test")
        assert result.success
    # Session automatically closed
```

### Session Reset

Reset session to clean state:

```python
def test_with_reset(shell_session):
    # First workflow
    shell_session.execute("export VAR1=value1")
    shell_session.execute("cd /tmp")

    # Reset to clean state
    shell_session.reset()

    # Variables cleared, back to initial directory
    result = shell_session.execute("echo $VAR1")
    assert result.output.strip() == ""
```

### Helper Methods

```python
# Set variable (cleaner than execute)
shell_session.set_variable("MY_VAR", "my_value")

# Get variable value
value = shell_session.get_variable("MY_VAR")

# Change directory
shell_session.change_directory(Path("/tmp"))

# Send control character
shell_session.send_control('c')  # Ctrl+C
```

## Best Practices

### 1. Use Function-Scoped Fixtures

Prefer `shell_session` over `persistent_shell` to ensure test isolation:

```python
# Good: Isolated
def test_one(shell_session):
    shell_session.execute("export VAR=1")

def test_two(shell_session):
    # Fresh session, VAR not set
    pass

# Risky: Shared state
def test_one(persistent_shell):
    persistent_shell.execute("export VAR=1")

def test_two(persistent_shell):
    # VAR is still set from test_one!
    pass
```

### 2. Use Custom Assertions

Custom assertions provide better error messages:

```python
# Better
from orchestro_cli.testing.assertions import assert_success, assert_output_contains

result = shell_session.execute("complex command")
assert_success(result)
assert_output_contains(result, "expected output")

# Works, but less informative on failure
assert result.success
assert "expected output" in result.output
```

### 3. Check Exit Codes

Always verify command success:

```python
# Good
result = shell_session.execute("important command")
assert_success(result)

# Risky: Ignoring failure
shell_session.execute("might fail")  # If this fails, test continues!
```

### 4. Timeout Long-Running Commands

Override default timeout for slow commands:

```python
result = shell_session.execute("slow command", timeout=120.0)
```

### 5. Clean Up Resources

Use fixtures for automatic cleanup:

```python
def test_with_temp_files(shell_session, temp_workspace):
    shell_session.change_directory(temp_workspace)
    shell_session.execute("touch many files")
    # temp_workspace cleaned up automatically
```

## Troubleshooting

### Command Times Out

Increase timeout or check if command is hanging:

```python
# Increase timeout
result = shell_session.execute("slow command", timeout=60.0)

# Or configure globally
config = SessionConfig(timeout=60.0)
session = ShellSession(config)
```

### Output Not Captured

Some programs detect if they're in a pipe and change behavior. Check if the command produces output interactively.

### Variable Not Tracked

Use `export` to set environment variables:

```python
# Tracked
shell_session.execute("export MY_VAR=value")

# Not tracked (shell-local variable)
shell_session.execute("MY_VAR=value")
```

### Session Hangs

If a command leaves the session in an odd state:

```python
# Send Ctrl+C to interrupt
shell_session.send_control('c')

# Or reset session
shell_session.reset()
```

## Examples

### Complete Test Suite Example

```python
"""Test suite for deployment workflow."""

import pytest
from pathlib import Path
from orchestro_cli.testing.assertions import (
    assert_success,
    assert_file_exists,
    assert_variable_set,
)


class TestDeploymentWorkflow:
    """Test complete deployment workflow."""

    def test_environment_setup(self, shell_session, temp_workspace):
        """Test setting up deployment environment."""
        shell_session.change_directory(temp_workspace)

        # Set environment
        shell_session.set_variable("DEPLOY_ENV", "staging")
        shell_session.set_variable("APP_NAME", "my-app")
        assert_variable_set(shell_session, "DEPLOY_ENV", "staging")

        # Create structure
        result = shell_session.execute("mkdir -p config deploy")
        assert_success(result)

        # Create config
        result = shell_session.execute(
            "echo 'env=$DEPLOY_ENV' > config/deploy.conf"
        )
        assert_success(result)
        assert_file_exists(shell_session, "config/deploy.conf")

    def test_build_and_package(self, shell_session, temp_workspace):
        """Test build and packaging."""
        shell_session.change_directory(temp_workspace)

        # Create source
        shell_session.execute("mkdir -p src")
        shell_session.execute("echo '#!/bin/bash' > src/app.sh")
        shell_session.execute("echo 'echo Running app' >> src/app.sh")
        shell_session.execute("chmod +x src/app.sh")

        # Build
        shell_session.set_variable("BUILD_DIR", "build")
        result = shell_session.execute("mkdir -p $BUILD_DIR")
        assert_success(result)

        result = shell_session.execute("cp -r src/* $BUILD_DIR/")
        assert_success(result)

        # Package
        result = shell_session.execute("tar czf deploy/app.tar.gz build/")
        assert_success(result)
        assert_file_exists(shell_session, "deploy/app.tar.gz")

    def test_validation(self, shell_session, temp_workspace):
        """Test deployment validation."""
        shell_session.change_directory(temp_workspace)

        # Create dummy package
        shell_session.execute("mkdir -p build deploy")
        shell_session.execute("touch build/app.sh")
        shell_session.execute("tar czf deploy/app.tar.gz build/")

        # Validate package
        result = shell_session.execute("tar tzf deploy/app.tar.gz")
        assert_success(result)
        assert "build/app.sh" in result.output
```

## API Reference

### Classes

- **`ShellSession`**: Persistent shell session with state tracking
- **`TUISession`**: Extended session for TUI applications
- **`SessionState`**: Tracks session state (variables, cwd, history)
- **`SessionConfig`**: Configuration for session creation
- **`SessionResult`**: Result from command execution

### Fixtures

- **`shell_session`**: Function-scoped shell session
- **`persistent_shell`**: Module-scoped shell session
- **`isolated_shell_session`**: Isolated session with temp workspace
- **`tui_session`**: TUI session
- **`tui_session_with_screenshots`**: TUI session with screenshot support
- **`custom_shell_session`**: Factory for creating custom sessions
- **`workspace_isolator`**: Workspace isolation manager

### Assertion Functions

- `assert_output_contains()`, `assert_output_matches()`
- `assert_exit_code()`, `assert_success()`, `assert_failure()`
- `assert_variable_set()`, `assert_variable_unset()`
- `assert_cwd()`, `assert_file_exists()`, `assert_file_contains()`
- `assert_command_in_history()`, `assert_execution_time()`

### Security Classes

- **`InputValidator`**: Validates commands for security
- **`ResourceLimiter`**: Manages resource limits
- **`WorkspaceIsolator`**: Creates isolated workspaces
- **`CommandAuditor`**: Audits executed commands

## Related Documentation

- [Orchestro CLI Documentation](../README.md)
- [Pytest Fixtures Guide](https://docs.pytest.org/en/stable/fixture.html)
- [Pexpect Documentation](https://pexpect.readthedocs.io/)
