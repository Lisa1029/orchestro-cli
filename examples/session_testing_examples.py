"""Examples of session state testing patterns.

This module demonstrates various patterns and use cases for Orchestro's
session state testing infrastructure.
"""

import pytest
from pathlib import Path
from orchestro_cli.testing import ShellSession, TUISession, SessionConfig
from orchestro_cli.testing.assertions import (
    assert_success,
    assert_failure,
    assert_output_contains,
    assert_variable_set,
    assert_file_exists,
)


# =============================================================================
# BASIC PATTERNS
# =============================================================================

def example_basic_command(shell_session):
    """Example: Execute a simple command."""
    result = shell_session.execute("echo 'Hello, World!'")

    assert result.success
    assert result.exit_code == 0
    assert "Hello, World!" in result.output


def example_state_persistence(shell_session):
    """Example: Demonstrate state persistence."""
    # Set an environment variable
    shell_session.execute("export API_TOKEN=secret123")

    # Variable persists in next command
    result = shell_session.execute("echo $API_TOKEN")
    assert "secret123" in result.output

    # Change directory
    shell_session.execute("cd /tmp")

    # Still in /tmp for next command
    result = shell_session.execute("pwd")
    assert "/tmp" in result.output


def example_helper_methods(shell_session):
    """Example: Use helper methods for cleaner code."""
    # Set variable using helper
    shell_session.set_variable("PROJECT_NAME", "my-project")

    # Get variable value
    name = shell_session.get_variable("PROJECT_NAME")
    assert name == "my-project"

    # Change directory using helper
    shell_session.change_directory(Path("/tmp"))
    assert shell_session.state.cwd == Path("/tmp")


# =============================================================================
# REALISTIC WORKFLOWS
# =============================================================================

def example_git_workflow(shell_session, temp_workspace):
    """Example: Test a complete git workflow."""
    shell_session.change_directory(temp_workspace)

    # Initialize repository
    result = shell_session.execute("git init")
    assert_success(result)

    # Configure git
    shell_session.execute("git config user.email 'test@example.com'")
    shell_session.execute("git config user.name 'Test User'")

    # Create and stage file
    shell_session.execute("echo '# My Project' > README.md")
    assert_file_exists(shell_session, "README.md")

    result = shell_session.execute("git add README.md")
    assert_success(result)

    # Commit
    result = shell_session.execute("git commit -m 'Initial commit'")
    assert_success(result)
    assert "1 file changed" in result.output

    # Verify
    result = shell_session.execute("git log --oneline")
    assert "Initial commit" in result.output


def example_npm_workflow(shell_session, temp_workspace):
    """Example: Test npm project workflow."""
    shell_session.change_directory(temp_workspace)

    # Initialize npm project
    result = shell_session.execute("npm init -y")
    assert_success(result)
    assert_file_exists(shell_session, "package.json")

    # Create source file
    shell_session.execute("mkdir -p src")
    shell_session.execute("echo 'console.log(\"Hello\");' > src/index.js")

    # Add scripts to package.json (simplified)
    shell_session.execute("cat package.json")

    # In real test, you'd install dependencies and run tests
    # result = shell_session.execute("npm install")
    # result = shell_session.execute("npm test")


def example_docker_workflow(shell_session, temp_workspace):
    """Example: Test Docker workflow."""
    shell_session.change_directory(temp_workspace)

    # Create Dockerfile
    dockerfile = """
    FROM alpine:latest
    RUN echo 'Hello from Docker' > /hello.txt
    CMD cat /hello.txt
    """

    shell_session.execute(f"cat > Dockerfile << 'EOF'\n{dockerfile}\nEOF")
    assert_file_exists(shell_session, "Dockerfile")

    # Set image name
    shell_session.set_variable("IMAGE_NAME", "test-image")

    # In real test with Docker available:
    # result = shell_session.execute("docker build -t $IMAGE_NAME .")
    # assert_success(result)
    #
    # result = shell_session.execute("docker run $IMAGE_NAME")
    # assert "Hello from Docker" in result.output


def example_ci_pipeline(shell_session, temp_workspace):
    """Example: Test CI/CD pipeline steps."""
    shell_session.change_directory(temp_workspace)

    # Set environment
    shell_session.set_variable("CI", "true")
    shell_session.set_variable("BUILD_NUMBER", "123")
    shell_session.set_variable("BRANCH", "main")

    # Create project structure
    shell_session.execute("mkdir -p src tests build")
    shell_session.execute("echo 'source code' > src/app.py")
    shell_session.execute("echo 'tests' > tests/test_app.py")

    # Linting step
    result = shell_session.execute("echo 'Linting passed' && exit 0")
    assert_success(result)

    # Build step
    result = shell_session.execute("cp -r src/* build/")
    assert_success(result)
    assert_file_exists(shell_session, "build/app.py")

    # Package step
    shell_session.execute("cd build")
    result = shell_session.execute("tar czf ../dist-${BUILD_NUMBER}.tar.gz .")
    assert_success(result)


# =============================================================================
# TUI TESTING
# =============================================================================

def example_tui_basic(tui_session):
    """Example: Test basic TUI interaction."""
    # Launch a simple TUI app (cat for demonstration)
    tui_session.launch_tui("cat", timeout=0.5)

    assert tui_session.tui_active
    assert tui_session.app_name == "cat"

    # Send some text
    tui_session.send_keys("hello world")

    # Exit
    result = tui_session.exit_tui()
    assert_success(result)


def example_vim_editing(tui_session, temp_workspace):
    """Example: Test vim editing workflow."""
    tui_session.change_directory(temp_workspace)

    # Launch vim
    tui_session.launch_tui("vim test.txt")

    # Enter insert mode and type
    tui_session.send_keys("i")  # Insert mode
    tui_session.send_keys("Hello, Vim!")
    tui_session.send_control('c')  # Exit insert mode

    # Save and quit
    tui_session.send_keys(":wq<Enter>")

    # Verify file was created
    result = tui_session.execute("cat test.txt")
    assert "Hello, Vim!" in result.output


@pytest.mark.asyncio
async def example_tui_screenshot(tui_session_with_screenshots):
    """Example: Capture TUI screenshot."""
    session, trigger_dir, artifacts_dir = tui_session_with_screenshots

    # Launch app
    session.launch_tui("htop", timeout=1.0)

    # Capture screenshot
    screenshot = await session.capture_screenshot(
        "htop-main-view",
        trigger_dir,
        artifacts_dir,
        timeout=5.0
    )

    assert screenshot.exists()
    assert screenshot.suffix == ".svg"

    session.exit_tui()


# =============================================================================
# ADVANCED PATTERNS
# =============================================================================

def example_custom_assertions(shell_session):
    """Example: Use custom assertion helpers."""
    from orchestro_cli.testing.assertions import (
        assert_exit_code,
        assert_output_contains,
        assert_command_in_history,
    )

    result = shell_session.execute("echo 'test output'")

    # Custom assertions provide better error messages
    assert_exit_code(result, 0)
    assert_output_contains(result, "test output")

    # History tracking
    shell_session.execute("ls -la")
    shell_session.execute("pwd")
    assert_command_in_history(shell_session, "ls -la")


def example_timeout_handling(shell_session):
    """Example: Handle command timeouts."""
    # This command will timeout
    result = shell_session.execute("sleep 10", timeout=1.0)

    assert not result.success
    assert result.exit_code == -1
    assert "timed out" in result.error.lower()


def example_error_handling(shell_session):
    """Example: Handle command failures gracefully."""
    # Command that fails
    result = shell_session.execute("false")

    assert not result.success
    assert result.exit_code != 0

    # Use assert_failure for expected failures
    assert_failure(result)

    # Session continues after failure
    result = shell_session.execute("true")
    assert_success(result)


def example_session_reset(shell_session):
    """Example: Reset session to clean state."""
    # Set some state
    shell_session.execute("export TEMP_VAR=temporary")
    shell_session.execute("cd /tmp")

    # Reset clears state
    shell_session.reset()

    # Variable is gone
    result = shell_session.execute("echo $TEMP_VAR")
    assert result.output.strip() == ""


def example_context_manager():
    """Example: Use session as context manager."""
    with ShellSession() as session:
        result = session.execute("echo test")
        assert result.success

    # Session automatically closed
    assert not session.is_alive()


def example_custom_configuration():
    """Example: Create session with custom config."""
    config = SessionConfig(
        timeout=60.0,  # Longer timeout
        env={"CUSTOM_ENV": "custom_value"},  # Custom environment
        working_dir=Path("/tmp"),  # Start in /tmp
    )

    with ShellSession(config) as session:
        result = session.execute("echo $CUSTOM_ENV")
        assert "custom_value" in result.output

        result = session.execute("pwd")
        assert "/tmp" in result.output


def example_multiple_sessions(custom_shell_session):
    """Example: Create multiple sessions."""
    config1 = SessionConfig(timeout=30.0)
    config2 = SessionConfig(timeout=60.0)

    session1 = custom_shell_session(config1)
    session2 = custom_shell_session(config2)

    # Both sessions are independent
    session1.execute("export VAR1=session1")
    session2.execute("export VAR2=session2")

    # Variables don't cross sessions
    result1 = session1.execute("echo $VAR2")
    assert result1.output.strip() == ""  # VAR2 not in session1

    result2 = session2.execute("echo $VAR1")
    assert result2.output.strip() == ""  # VAR1 not in session2


# =============================================================================
# SECURITY EXAMPLES
# =============================================================================

def example_dangerous_command_blocked(shell_session):
    """Example: Dangerous commands are blocked."""
    with pytest.raises(ValueError, match="blocked"):
        shell_session.execute("rm -rf /")


def example_workspace_isolation(workspace_isolator):
    """Example: Use isolated workspaces."""
    # Create isolated workspace
    workspace = workspace_isolator.create_workspace("my-test")

    assert workspace.exists()
    assert (workspace / "home").exists()
    assert (workspace / "data").exists()

    # Use workspace in session
    config = SessionConfig(working_dir=workspace)
    with ShellSession(config) as session:
        result = session.execute("pwd")
        assert str(workspace) in result.output

    # Clean up
    workspace_isolator.cleanup_workspace(workspace)
    assert not workspace.exists()


def example_command_auditing():
    """Example: Audit executed commands."""
    from orchestro_cli.testing.security import CommandAuditor

    auditor = CommandAuditor()

    # Log commands
    auditor.log_command("git init")
    auditor.log_command("git add .")
    auditor.log_command("git commit -m 'Initial'")

    # Review audit log
    log = auditor.get_audit_log()
    assert len(log) == 3

    for timestamp, command in log:
        print(f"{timestamp}: {command}")


# =============================================================================
# PERFORMANCE TESTING
# =============================================================================

def example_timing_assertions(shell_session):
    """Example: Assert on execution time."""
    from orchestro_cli.testing.assertions import assert_execution_time

    # Fast command
    result = shell_session.execute("echo fast")
    assert_execution_time(result, max_seconds=1.0)

    # Check duration directly
    assert result.duration < 1.0


def example_performance_comparison(shell_session):
    """Example: Compare performance of different approaches."""
    # Approach 1
    result1 = shell_session.execute("find /tmp -name '*.txt' 2>/dev/null | wc -l")
    time1 = result1.duration

    # Approach 2
    result2 = shell_session.execute("ls /tmp/*.txt 2>/dev/null | wc -l")
    time2 = result2.duration

    # Compare
    print(f"find: {time1:.3f}s, ls: {time2:.3f}s")


# =============================================================================
# INTEGRATION PATTERNS
# =============================================================================

def example_database_workflow(shell_session, temp_workspace):
    """Example: Test database workflow."""
    shell_session.change_directory(temp_workspace)

    # Set up environment
    shell_session.set_variable("DB_FILE", "test.db")

    # Create database (using sqlite as example)
    result = shell_session.execute("sqlite3 $DB_FILE 'CREATE TABLE users (id INTEGER, name TEXT);'")
    assert_success(result)

    # Insert data
    result = shell_session.execute("sqlite3 $DB_FILE \"INSERT INTO users VALUES (1, 'Alice');\"")
    assert_success(result)

    # Query
    result = shell_session.execute("sqlite3 $DB_FILE 'SELECT * FROM users;'")
    assert "Alice" in result.output


def example_api_testing_workflow(shell_session):
    """Example: Test API integration workflow."""
    # Set API configuration
    shell_session.set_variable("API_URL", "https://api.example.com")
    shell_session.set_variable("API_KEY", "test_key")

    # In real test with curl/httpie:
    # result = shell_session.execute(
    #     "curl -H 'Authorization: Bearer $API_KEY' $API_URL/status"
    # )
    # assert_success(result)
    # assert_output_contains(result, "\"status\": \"ok\"")


# =============================================================================
# TEST ORGANIZATION
# =============================================================================

class TestDeploymentPipeline:
    """Example: Organize related tests in a class."""

    def test_setup(self, shell_session, temp_workspace):
        """Set up deployment environment."""
        shell_session.change_directory(temp_workspace)

        shell_session.set_variable("DEPLOY_ENV", "staging")
        shell_session.execute("mkdir -p config deploy")

        assert_file_exists(shell_session, "config")
        assert_variable_set(shell_session, "DEPLOY_ENV")

    def test_build(self, shell_session, temp_workspace):
        """Build deployment package."""
        shell_session.change_directory(temp_workspace)

        shell_session.execute("mkdir -p build")
        shell_session.execute("echo 'app' > build/app.sh")

        result = shell_session.execute("tar czf deploy.tar.gz build/")
        assert_success(result)

    def test_validation(self, shell_session, temp_workspace):
        """Validate deployment package."""
        shell_session.change_directory(temp_workspace)

        # Create dummy package for test
        shell_session.execute("mkdir -p build")
        shell_session.execute("tar czf deploy.tar.gz build/")

        result = shell_session.execute("tar tzf deploy.tar.gz")
        assert_success(result)
        assert "build/" in result.output


if __name__ == "__main__":
    print("This module contains examples for pytest.")
    print("Run with: pytest examples/session_testing_examples.py -v")
