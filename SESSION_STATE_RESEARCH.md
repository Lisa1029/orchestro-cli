# Session State Testing Patterns - Research Report

**Date:** 2025-11-16  
**Project:** Orchestro CLI  
**Objective:** Research persistent shell session testing patterns for multi-step workflow tests

---

## Executive Summary

This research analyzes implementation approaches for persistent shell session testing, where state (variables, working directory, environment) persists between commands - similar to clitest's single-shell-session model. The goal is to enable multi-step workflow tests in Orchestro CLI.

**Key Findings:**
- **Recommended Approach:** Persistent pexpect Process Pattern (Option 2) with session-scoped fixtures
- **Best Fit:** Aligns with Orchestro's existing architecture and testing needs
- **Implementation Complexity:** Medium (leverage existing pexpect infrastructure)
- **Security Considerations:** Lower risk than eval-based approaches, controllable via test isolation

---

## 1. Current Orchestro Architecture Analysis

### 1.1 Existing Process Management

**File:** `/home/jonbrookings/vibe_coding_projects/my-orchestro-copy/orchestro_cli/drivers/pexpect_driver.py`

```python
class PexpectDriver:
    """Process driver using pexpect (POSIX systems: Linux, macOS, BSD)."""
    
    def spawn(self, command, env, timeout, cwd):
        self.process = pexpect.spawn(
            command[0], command[1:],
            env=env, encoding="utf-8",
            timeout=timeout, dimensions=(80, 120),
            echo=False, cwd=str(cwd)
        )
```

**Key Observations:**
- Already uses pexpect for process control
- Process lifecycle: spawn → interact → terminate
- **Current Model:** One process per scenario (defined in YAML)
- **Limitation:** No multi-step test support - each test spawns fresh process

### 1.2 Test Infrastructure

**File:** `/home/jonbrookings/vibe_coding_projects/my-orchestro-copy/tests/conftest.py`

```python
@pytest.fixture
def temp_workspace() -> Generator[Path, None, None]:
    """Create a temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        yield workspace
```

**Key Observations:**
- Uses pytest fixtures for resource management
- Test isolation via temporary directories
- **Opportunity:** Can extend fixture system for session management

### 1.3 Step Execution Model

**File:** `/home/jonbrookings/vibe_coding_projects/my-orchestro-copy/orchestro_cli/execution/step_executor.py`

```python
class StepExecutor:
    """Executes individual scenario steps."""
    
    async def execute_step(self, step: Step, default_timeout: float):
        if step.expect:
            await self._handle_expect(step.expect, timeout)
        if step.send is not None:
            self.process.sendline(step.send)
```

**Key Observations:**
- Steps executed sequentially against single process
- Async support for expect/wait operations
- **Current Use Case:** Scenario-level steps (not test-level)

---

## 2. Implementation Patterns - Detailed Analysis

### Pattern 1: Single Shell Session (clitest)

**Source Analysis:** `/tmp/clitest/clitest` (lines 21-23, 306)

```sh
# Test environment:
#   All tests are executed in the same shell session, using eval. Test
#   data such as variables and working directory will persist between tests.

# Execute the test command, saving output (STDOUT and STDERR)
eval "$tt_test_command" > "$tt_test_output_file" 2>&1 < /dev/null
```

**How It Works:**
1. Shell script loops through test file
2. Each command line executed via `eval` in same shell
3. Variables, PWD, functions persist across tests
4. No process boundaries between tests

**Strengths:**
- ✅ True state persistence (shell variables, functions, aliases)
- ✅ Minimal overhead (no process spawning)
- ✅ Simple mental model (just like interactive shell)
- ✅ Proven design (clitest used in production)

**Weaknesses:**
- ❌ Shell script only (not Python-native)
- ❌ Security risk with eval (arbitrary code execution)
- ❌ Limited output capture (no per-command streaming)
- ❌ No support for interactive programs (TUIs)
- ❌ Hard to integrate with pytest

**Use Cases:**
- Shell script testing
- Command-line tool validation
- Simple workflow tests (no TUI interaction)

**Orchestro Fit:** ⚠️ **Poor** - Orchestro targets TUI apps, needs pexpect interaction

---

### Pattern 2: Persistent pexpect Process ⭐ RECOMMENDED

**Implementation Concept:**

```python
import pytest
import pexpect

@pytest.fixture(scope="session")
def persistent_shell():
    """Long-lived shell session for sequential tests."""
    shell = pexpect.spawn('/bin/bash', timeout=30, encoding='utf-8')
    shell.sendline('PS1="READY> "')  # Custom prompt
    shell.expect('READY> ')
    
    yield shell
    
    shell.close()

def test_step_1(persistent_shell):
    """First test step - creates state."""
    persistent_shell.sendline('export MY_VAR=hello')
    persistent_shell.expect('READY> ')
    
def test_step_2(persistent_shell):
    """Second test step - uses state from step 1."""
    persistent_shell.sendline('echo $MY_VAR')
    persistent_shell.expect('hello')
    persistent_shell.expect('READY> ')
```

**How It Works:**
1. Pytest fixture creates pexpect shell at session/module scope
2. Tests sequentially interact with same shell process
3. State (env vars, cwd, etc.) persists between tests
4. Cleanup via fixture teardown

**Strengths:**
- ✅ Works with Orchestro's existing pexpect infrastructure
- ✅ Supports interactive programs (TUIs, REPLs)
- ✅ Python-native, pytest integration
- ✅ Full stdout/stderr capture per command
- ✅ Controllable isolation via fixture scope
- ✅ Async/await compatible
- ✅ Timeout management per step

**Weaknesses:**
- ⚠️ State pollution risk (tests affect each other)
- ⚠️ Process cleanup complexity
- ⚠️ Harder to parallelize tests
- ⚠️ Debugging complexity (order-dependent failures)

**Mitigation Strategies:**

1. **Explicit Reset Points:**
```python
@pytest.fixture
def shell_with_reset(persistent_shell):
    """Reset shell state before each test."""
    yield persistent_shell
    # Reset after test
    persistent_shell.sendline('cd $HOME')
    persistent_shell.sendline('unset MY_VAR')
```

2. **State Validation:**
```python
def test_step_with_validation(persistent_shell):
    # Pre-condition check
    persistent_shell.sendline('echo $MY_VAR')
    assert_empty_or_value(persistent_shell)
    
    # Test logic
    persistent_shell.sendline('export MY_VAR=test')
```

3. **Scoped Sessions:**
```python
@pytest.fixture(scope="module")  # Per-module isolation
def feature_shell():
    # Each test module gets fresh shell
    pass
```

**Use Cases:**
- ✅ Multi-step CLI workflows
- ✅ TUI application testing (Orchestro's primary use case)
- ✅ REPL/interactive session testing
- ✅ Database session tests
- ✅ Configuration-dependent workflows

**Orchestro Fit:** ⭐ **Excellent** - Aligns with architecture, meets requirements

---

### Pattern 3: Session Pool Pattern

**Implementation Concept:**

```python
class ShellSessionPool:
    """Manages pool of reusable shell sessions."""
    
    def __init__(self, size=3):
        self.pool = [self._create_session() for _ in range(size)]
        self.available = self.pool.copy()
        
    def acquire(self):
        session = self.available.pop()
        return session
        
    def release(self, session):
        self._reset_session(session)
        self.available.append(session)
        
    def _reset_session(self, session):
        """Reset session to clean state."""
        session.sendline('cd $HOME')
        session.sendline('export -n $(compgen -e | grep -v "^PATH$")')
        session.expect('$ ')

@pytest.fixture
def pooled_shell(session_pool):
    shell = session_pool.acquire()
    yield shell
    session_pool.release(shell)
```

**How It Works:**
1. Pre-create pool of shell sessions
2. Allocate session to test, mark unavailable
3. After test, reset session state
4. Return to pool for reuse

**Strengths:**
- ✅ Good balance of reuse and isolation
- ✅ Can run tests in parallel (if pool large enough)
- ✅ Resource efficient (reuse sessions)
- ✅ Faster than fresh spawns

**Weaknesses:**
- ❌ Complex reset logic (hard to reset ALL state)
- ❌ State leaks between tests possible
- ❌ Pool sizing complexity
- ❌ Harder to debug (shared resource)

**Use Cases:**
- Parallel test execution with state management
- High-volume test suites
- Resource-constrained environments

**Orchestro Fit:** ⚠️ **Medium** - Overkill for current needs, but scalable

---

### Pattern 4: Snapshot/Restore Pattern

**Implementation Concept:**

```python
class ShellSnapshot:
    """Capture and restore shell state."""
    
    def __init__(self, shell):
        self.shell = shell
        self.snapshot = None
        
    def capture(self):
        """Capture current shell state."""
        shell = self.shell
        
        # Capture environment
        shell.sendline('export -p > /tmp/env_snapshot')
        
        # Capture working directory
        shell.sendline('pwd > /tmp/pwd_snapshot')
        
        # Capture shell options
        shell.sendline('set > /tmp/set_snapshot')
        
        self.snapshot = {
            'env': self._read_file('/tmp/env_snapshot'),
            'pwd': self._read_file('/tmp/pwd_snapshot'),
            'set': self._read_file('/tmp/set_snapshot'),
        }
        
    def restore(self):
        """Restore shell to snapshot state."""
        # Restore environment
        self.shell.sendline(f'source /tmp/env_snapshot')
        
        # Restore directory
        pwd = self.snapshot['pwd'].strip()
        self.shell.sendline(f'cd {pwd}')

@pytest.fixture
def shell_with_snapshot(persistent_shell):
    snapshot = ShellSnapshot(persistent_shell)
    snapshot.capture()
    
    yield persistent_shell
    
    snapshot.restore()
```

**Strengths:**
- ✅ True isolation via explicit state management
- ✅ Predictable test behavior
- ✅ Can audit state changes
- ✅ Works with existing pexpect

**Weaknesses:**
- ❌ Not all state is capturable (open files, background jobs)
- ❌ Performance overhead (snapshot operations)
- ❌ Complex implementation
- ❌ Platform-specific snapshot logic

**Use Cases:**
- Tests requiring guaranteed isolation
- Debugging state-related failures
- Auditing state changes

**Orchestro Fit:** ⚠️ **Medium** - Complex, but useful for specific scenarios

---

### Pattern 5: Container/VM Pattern

**Implementation Concept:**

```python
import docker

@pytest.fixture(scope="module")
def docker_shell():
    """Shell session in fresh Docker container."""
    client = docker.from_env()
    container = client.containers.run(
        'alpine:latest',
        command='/bin/sh',
        stdin_open=True,
        tty=True,
        detach=True
    )
    
    # Attach pexpect to container
    shell = pexpect.spawn(f'docker attach {container.id}')
    
    yield shell
    
    container.stop()
    container.remove()
```

**Strengths:**
- ✅ Perfect isolation (OS-level)
- ✅ Reproducible environments
- ✅ Clean state guaranteed
- ✅ Can snapshot entire filesystem

**Weaknesses:**
- ❌ Heavy overhead (container startup: ~1-2 seconds)
- ❌ Complex setup (Docker daemon required)
- ❌ Platform limitations (Docker on macOS/Windows)
- ❌ Network complexity

**Use Cases:**
- Integration testing
- Multi-service testing
- Production-like environments

**Orchestro Fit:** ❌ **Poor** - Too heavy for unit/functional tests

---

### Pattern 6: Subprocess Chain Pattern

**Implementation Concept:**

```python
import subprocess

def test_workflow_stateless():
    """Stateless workflow using subprocess chain."""
    
    # Step 1
    result1 = subprocess.run(
        ['./setup_script.sh'],
        capture_output=True,
        text=True
    )
    
    # Step 2 - uses artifacts from step 1
    result2 = subprocess.run(
        ['./process_data.sh', result1.stdout.strip()],
        capture_output=True,
        text=True
    )
    
    assert result2.returncode == 0
```

**Strengths:**
- ✅ Simple implementation
- ✅ Complete process isolation
- ✅ Easy debugging (each step independent)
- ✅ No state pollution

**Weaknesses:**
- ❌ No state persistence (defeats purpose)
- ❌ High overhead (process spawn per step)
- ❌ Only works for stateless workflows
- ❌ Can't test interactive programs

**Use Cases:**
- Stateless command pipelines
- CI/CD script testing
- Simple integration tests

**Orchestro Fit:** ❌ **Poor** - Doesn't support persistent state (main requirement)

---

## 3. Security Considerations

### Risk Matrix

| Pattern | Arbitrary Code | State Pollution | Resource Leaks | Attack Surface |
|---------|---------------|----------------|----------------|----------------|
| clitest eval | 🔴 High | 🔴 High | 🟡 Medium | 🔴 High |
| Persistent pexpect | 🟡 Medium | 🟢 Low-Medium | 🟡 Medium | 🟡 Medium |
| Session Pool | 🟡 Medium | 🟡 Medium | 🟢 Low | 🟡 Medium |
| Snapshot/Restore | 🟡 Medium | 🟢 Low | 🟡 Medium | 🟡 Medium |
| Container | 🟢 Low | 🟢 Low | 🔴 High | 🟢 Low |
| Subprocess Chain | 🟢 Low | 🟢 Low | 🟢 Low | 🟢 Low |

### Security Recommendations

1. **Input Sanitization:**
   - Validate all test commands before sending to shell
   - Use parameterized commands where possible
   - Avoid string interpolation in shell commands

2. **Process Isolation:**
   - Run tests in isolated workspaces (Orchestro already does this)
   - Use non-privileged users for test execution
   - Limit resource usage (ulimit, cgroups)

3. **State Management:**
   - Clear sensitive data after tests
   - Don't persist credentials in session state
   - Reset environment variables between tests

4. **Audit Trail:**
   - Log all commands sent to shell session
   - Track state changes for debugging
   - Monitor for unexpected process spawns

---

## 4. Orchestro-Specific Use Cases

### Use Case 1: Multi-Step TUI Navigation

**Scenario:** Test complex menu navigation with state

```yaml
# Current Orchestro YAML (single scenario)
name: Navigation Test
command: ./my_tui_app
steps:
  - send: "m"  # Open menu
  - send: "1"  # Select item 1
  - screenshot: "menu-item-1"
```

**Desired:** Multi-scenario test suite with shared session

```python
# Proposed pytest approach
def test_01_startup(tui_session):
    """First test: app starts and shows menu."""
    tui_session.expect("Main Menu")
    tui_session.screenshot("startup")

def test_02_navigate_settings(tui_session):
    """Second test: navigate to settings (uses session from test_01)."""
    tui_session.send("s")  # Settings
    tui_session.expect("Settings Menu")
    tui_session.screenshot("settings")
    
def test_03_change_config(tui_session):
    """Third test: change config (session state persists)."""
    tui_session.send("t")  # Toggle option
    tui_session.expect("Option enabled")
```

**Benefits:**
- Tests build on previous state (realistic user workflow)
- Faster execution (no restart per test)
- Can test complex multi-step interactions

### Use Case 2: Database Session Testing

**Scenario:** Test CLI tool that maintains database connection

```python
def test_01_connect(db_cli_session):
    """Connect to database."""
    db_cli_session.send("CONNECT localhost")
    db_cli_session.expect("Connected successfully")
    
def test_02_create_table(db_cli_session):
    """Create table (uses connection from test_01)."""
    db_cli_session.send("CREATE TABLE users (id INT, name TEXT)")
    db_cli_session.expect("Table created")
    
def test_03_insert_data(db_cli_session):
    """Insert data into existing table."""
    db_cli_session.send("INSERT INTO users VALUES (1, 'Alice')")
    db_cli_session.expect("1 row inserted")
```

### Use Case 3: Configuration Workflow

**Scenario:** Test app configuration that affects runtime behavior

```python
def test_01_set_config(app_session):
    """Set configuration value."""
    app_session.send("config set debug=true")
    app_session.expect("Config updated")
    
def test_02_verify_debug_mode(app_session):
    """Verify debug mode active (depends on test_01)."""
    app_session.send("status")
    app_session.expect("Debug: enabled")
    
def test_03_use_debug_feature(app_session):
    """Use feature that requires debug mode."""
    app_session.send("trace")
    app_session.expect("Stack trace:")
```

---

## 5. Recommended Architecture for Orchestro

### 5.1 High-Level Design

```
orchestro_cli/
├── testing/                    # New module
│   ├── __init__.py
│   ├── session.py             # Session management
│   ├── fixtures.py            # Pytest fixtures
│   └── assertions.py          # Custom assertions
├── drivers/
│   ├── pexpect_driver.py      # Existing (extend for sessions)
│   └── subprocess_driver.py
└── execution/
    └── step_executor.py       # Existing (reuse for test steps)
```

### 5.2 Core Components

#### Component 1: ShellSession

```python
# orchestro_cli/testing/session.py

class ShellSession:
    """Persistent shell session for multi-step tests."""
    
    def __init__(self, shell_cmd='/bin/bash', timeout=30):
        self.driver = PexpectDriver()
        self.process = self.driver.spawn(
            command=[shell_cmd],
            env=os.environ.copy(),
            timeout=timeout
        )
        self._setup_prompt()
        
    def _setup_prompt(self):
        """Set custom prompt for reliable expect matching."""
        self.driver.sendline('PS1="ORCHESTRO_READY> "')
        self.driver.expect('ORCHESTRO_READY> ')
        
    def send(self, command: str) -> str:
        """Send command and return output."""
        self.driver.sendline(command)
        self.driver.expect('ORCHESTRO_READY> ')
        return self.driver.before
        
    def expect(self, pattern: str, timeout: float = None):
        """Wait for pattern in output."""
        self.driver.expect(pattern, timeout=timeout)
        return self.driver.after
        
    def reset(self):
        """Reset session to clean state."""
        self.send('cd $HOME')
        self.send('export -n $(compgen -e | grep -v "^PATH$")')
        
    def close(self):
        """Close session."""
        self.process.terminate()
```

#### Component 2: Pytest Fixtures

```python
# orchestro_cli/testing/fixtures.py

@pytest.fixture(scope="session")
def shell_session():
    """Long-lived shell session for test suite."""
    session = ShellSession()
    yield session
    session.close()

@pytest.fixture(scope="module")
def module_shell():
    """Shell session scoped to test module."""
    session = ShellSession()
    yield session
    session.close()

@pytest.fixture
def clean_shell(shell_session):
    """Shell session with reset after test."""
    yield shell_session
    shell_session.reset()
```

#### Component 3: TUI Session (Orchestro-Specific)

```python
# orchestro_cli/testing/session.py

class TUISession(ShellSession):
    """Specialized session for TUI applications."""
    
    def __init__(self, command, **kwargs):
        super().__init__(**kwargs)
        self.app_command = command
        self._start_app()
        
    def _start_app(self):
        """Start TUI application."""
        self.send(self.app_command)
        # Wait for app to initialize
        time.sleep(0.5)
        
    def screenshot(self, name: str, timeout: float = 10):
        """Trigger screenshot capture."""
        trigger_dir = Path(tempfile.gettempdir()) / ".vyb_orchestro" / "screenshot_triggers"
        trigger_file = trigger_dir / f"{name}.trigger"
        trigger_file.touch()
        
        # Wait for screenshot
        screenshot_path = Path.cwd() / "artifacts" / "screenshots" / f"{name}.svg"
        deadline = time.time() + timeout
        while time.time() < deadline:
            if screenshot_path.exists():
                return str(screenshot_path)
            time.sleep(0.2)
            
        raise TimeoutError(f"Screenshot '{name}' not created")
        
    def send_key(self, key: str):
        """Send single key press (for TUI navigation)."""
        self.driver.send(key)
```

### 5.3 Usage Example

```python
# tests/test_multi_step_workflow.py

import pytest
from orchestro_cli.testing import TUISession

@pytest.fixture(scope="module")
def app_session():
    """TUI app session for entire test module."""
    session = TUISession(command="./my_tui_app")
    yield session
    session.close()

class TestWorkflow:
    """Multi-step workflow test suite."""
    
    def test_01_startup(self, app_session):
        """Test app starts successfully."""
        app_session.expect("Welcome")
        screenshot_path = app_session.screenshot("01-startup")
        assert Path(screenshot_path).exists()
        
    def test_02_navigate_menu(self, app_session):
        """Navigate to menu (uses session from test_01)."""
        app_session.send_key("m")
        app_session.expect("Main Menu")
        app_session.screenshot("02-menu")
        
    def test_03_select_item(self, app_session):
        """Select menu item (uses session from test_02)."""
        app_session.send_key("1")
        app_session.expect("Item 1 Selected")
        app_session.screenshot("03-item-selected")
```

### 5.4 Integration with Existing Orchestro

**Backward Compatibility:**
- Keep existing YAML-based scenario runner (runner.py)
- Add session testing as separate module (testing/)
- Both can coexist and use same drivers

**Migration Path:**
1. Phase 1: Implement ShellSession and fixtures (new module)
2. Phase 2: Add TUISession for Orchestro-specific features
3. Phase 3: Document usage patterns, examples
4. Phase 4: (Optional) Add YAML syntax for multi-scenario tests

---

## 6. Comparison Summary

| Criterion | clitest | Persistent pexpect ⭐ | Session Pool | Snapshot/Restore | Container | Subprocess |
|-----------|---------|---------------------|--------------|------------------|-----------|------------|
| **State Persistence** | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ❌ None |
| **TUI Support** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| **Orchestro Integration** | ❌ Poor | ✅ Excellent | ⚠️ Medium | ⚠️ Medium | ❌ Poor | ❌ Poor |
| **Implementation Complexity** | 🟢 Low | 🟡 Medium | 🔴 High | 🔴 High | 🔴 High | 🟢 Low |
| **Performance** | ✅ Fast | ✅ Fast | ✅ Fast | ⚠️ Medium | ❌ Slow | ⚠️ Medium |
| **Isolation** | ❌ None | ⚠️ Test-level | ✅ Test-level | ✅ Full | ✅ Full | ✅ Full |
| **Security Risk** | 🔴 High | 🟡 Medium | 🟡 Medium | 🟡 Medium | 🟢 Low | 🟢 Low |
| **Debugging** | ✅ Easy | ⚠️ Medium | ❌ Hard | ⚠️ Medium | ⚠️ Medium | ✅ Easy |

**Legend:**
- ✅ Excellent / 🟢 Low risk
- ⚠️ Medium / 🟡 Medium risk  
- ❌ Poor / 🔴 High risk

---

## 7. Recommendations

### Primary Recommendation: **Persistent pexpect Process Pattern**

**Rationale:**
1. ✅ **Architectural Fit** - Leverages Orchestro's existing pexpect infrastructure
2. ✅ **Use Case Match** - Supports TUI testing (Orchestro's core use case)
3. ✅ **Balanced Trade-offs** - Good performance, manageable complexity
4. ✅ **Pytest Integration** - Native Python, works with existing test framework
5. ✅ **Incremental Adoption** - Can implement without breaking existing features

**Implementation Priority:**

**Phase 1: Foundation (1-2 days)**
- Create `orchestro_cli/testing/session.py` with ShellSession class
- Implement basic fixtures in `orchestro_cli/testing/fixtures.py`
- Write unit tests for session management

**Phase 2: TUI Support (2-3 days)**
- Extend ShellSession to TUISession
- Add screenshot support to session
- Integrate with existing screenshot trigger mechanism

**Phase 3: Documentation & Examples (1-2 days)**
- Write usage guide with examples
- Create example test suites demonstrating patterns
- Document best practices and gotchas

**Phase 4: Advanced Features (optional)**
- Session reset strategies
- State validation helpers
- Performance optimizations

### Alternative Recommendation: **Session Pool Pattern** (If Needed)

**When to use:**
- High-volume test suites (100+ tests)
- Need parallel test execution
- Resource constraints (limited RAM/CPU)

**Defer until:**
- Persistent pexpect proves insufficient
- Performance becomes bottleneck
- Parallel testing requirement emerges

### NOT Recommended:

1. **clitest Pattern** - Doesn't support TUI interaction
2. **Container Pattern** - Too heavy for unit/functional tests
3. **Subprocess Chain** - Defeats purpose (no state persistence)

---

## 8. Security Best Practices

### Essential Controls

1. **Input Validation:**
```python
def send_command(self, command: str):
    """Send command with validation."""
    # Reject dangerous patterns
    dangerous = ['rm -rf /', ':(){ :|:& };:', 'sudo']
    if any(pattern in command for pattern in dangerous):
        raise ValueError(f"Dangerous command rejected: {command}")
    
    self.driver.sendline(command)
```

2. **Resource Limits:**
```python
import resource

def setup_session():
    # Limit CPU time
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    
    # Limit memory
    resource.setrlimit(resource.RLIMIT_AS, (512*1024*1024, 512*1024*1024))
```

3. **Workspace Isolation:**
```python
@pytest.fixture
def isolated_shell():
    with tempfile.TemporaryDirectory() as tmpdir:
        session = ShellSession()
        session.send(f'cd {tmpdir}')
        session.send('export HOME={tmpdir}')
        yield session
```

4. **Audit Logging:**
```python
class AuditedSession(ShellSession):
    def send(self, command: str):
        logger.info(f"Command: {command}")
        result = super().send(command)
        logger.info(f"Output: {result[:100]}")  # Log first 100 chars
        return result
```

---

## 9. Example Use Cases

### Example 1: Database CLI Testing

```python
# tests/test_database_workflow.py

@pytest.fixture(scope="module")
def db_session():
    """Database CLI session."""
    session = ShellSession()
    session.send('./db_cli')
    session.expect('db>')
    yield session
    session.send('exit')

def test_01_connect(db_session):
    db_session.send('connect localhost')
    assert 'Connected' in db_session.expect('db>')

def test_02_create_schema(db_session):
    db_session.send('create table users (id int, name text)')
    assert 'Table created' in db_session.expect('db>')
    
def test_03_insert_data(db_session):
    # Uses table created in test_02
    db_session.send("insert into users values (1, 'Alice')")
    assert 'inserted' in db_session.expect('db>')
```

### Example 2: Configuration Workflow

```python
# tests/test_config_workflow.py

@pytest.fixture(scope="module")
def configured_app():
    """App with persistent configuration."""
    session = TUISession(command='./config_app')
    yield session
    session.close()

def test_01_enable_debug(configured_app):
    configured_app.send_key('d')  # Debug menu
    configured_app.send_key('e')  # Enable
    configured_app.expect('Debug mode: ON')
    configured_app.screenshot('debug-enabled')
    
def test_02_verify_debug_output(configured_app):
    # Debug mode persists from test_01
    configured_app.send_key('t')  # Trigger action
    configured_app.expect('[DEBUG]')  # Should see debug logs
    
def test_03_use_debug_feature(configured_app):
    # Can use debug-only features
    configured_app.send_key('x')  # Debug export
    configured_app.expect('Export complete')
```

### Example 3: Multi-Step TUI Navigation

```python
# tests/test_tui_navigation.py

class TestMenuNavigation:
    """Test complex menu navigation with state."""
    
    @pytest.fixture(scope="class")
    def tui_app(self):
        session = TUISession(command='./my_app')
        yield session
        session.close()
    
    def test_01_main_menu(self, tui_app):
        tui_app.expect('Main Menu')
        tui_app.screenshot('01-main-menu')
        
    def test_02_enter_settings(self, tui_app):
        tui_app.send_key('s')
        tui_app.expect('Settings')
        tui_app.screenshot('02-settings')
        
    def test_03_change_theme(self, tui_app):
        tui_app.send_key('t')  # Theme submenu
        tui_app.send_key('d')  # Dark theme
        tui_app.expect('Theme: Dark')
        tui_app.screenshot('03-dark-theme')
        
    def test_04_back_to_main(self, tui_app):
        tui_app.send_key('q')  # Back
        tui_app.send_key('q')  # Back to main
        tui_app.expect('Main Menu')
        # Theme should persist
        assert 'Dark' in tui_app.send('')
```

---

## 10. Integration Complexity Assessment

### Low Complexity ✅

**What's Already There:**
- pexpect integration (drivers/)
- Process management (execution/)
- Pytest infrastructure (tests/)
- Fixture patterns (conftest.py)

**What Needs Building:**
- ShellSession wrapper (100-150 lines)
- Pytest fixtures (50-75 lines)
- TUISession extension (75-100 lines)
- Documentation/examples (varies)

**Estimated Implementation Time:**
- Core functionality: 2-3 days
- TUI integration: 2-3 days
- Testing & docs: 2-3 days
- **Total: 6-9 days**

### Medium Complexity ⚠️

**If Adding:**
- Session pool management
- Advanced state reset
- Performance monitoring
- Cross-platform compatibility edge cases

**Additional Time: +3-5 days**

### High Complexity 🔴

**If Adding:**
- Container-based isolation
- Distributed test execution
- Advanced security sandboxing
- Full state snapshotting

**Additional Time: +10-15 days**

---

## 11. Conclusion

**Recommended Path Forward:**

1. **Implement Persistent pexpect Pattern** using session-scoped pytest fixtures
2. **Start Simple** with basic ShellSession class
3. **Extend for TUI** with TUISession subclass
4. **Document Patterns** with clear examples and best practices
5. **Iterate Based on Usage** - add pooling/snapshotting only if needed

**Key Success Factors:**
- Leverage existing pexpect infrastructure
- Maintain backward compatibility with YAML scenarios
- Provide clear isolation boundaries (fixture scopes)
- Document state management patterns
- Include security controls from day one

**Risk Mitigation:**
- Start with module-scoped sessions (avoid session scope initially)
- Implement explicit reset mechanisms
- Add state validation helpers
- Monitor for state pollution in tests

---

## 12. References

**Analyzed Codebases:**
- `/tmp/clitest/clitest` - clitest shell-based testing framework
- `/home/jonbrookings/vibe_coding_projects/my-orchestro-copy/` - Orchestro CLI codebase

**Key Files Examined:**
- `orchestro_cli/drivers/pexpect_driver.py` - Process driver
- `orchestro_cli/execution/step_executor.py` - Step execution
- `tests/conftest.py` - Test fixtures
- `tests/test_runner.py` - Runner tests
- `tests/integration/test_real_execution.py` - Integration tests

**External Resources:**
- pexpect documentation: https://pexpect.readthedocs.io/
- pytest fixtures: https://docs.pytest.org/en/stable/fixture.html
- clitest project: https://github.com/aureliojargas/clitest

---

**Report Compiled:** 2025-11-16  
**Researcher:** Claude (Sonnet 4.5)  
**Next Steps:** Review findings with team, approve implementation approach, begin Phase 1 development
