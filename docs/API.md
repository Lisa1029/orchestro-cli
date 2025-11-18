# Orchestro CLI API Documentation

**Version:** 1.0.0

This document provides comprehensive API reference for developers integrating or extending the Orchestro CLI framework.

---

## Table of Contents

- [Core Classes](#core-classes)
  - [ScenarioRunner](#scenariorunner)
  - [SentinelMonitor](#sentinelmonitor)
- [Data Classes](#data-classes)
  - [ScenarioStep](#scenariostep)
  - [Validation](#validation)
- [CLI Interface](#cli-interface)
- [Environment Variables](#environment-variables)
- [File System Conventions](#file-system-conventions)
- [Integration Examples](#integration-examples)

---

## Core Classes

### ScenarioRunner

**Module:** `orchestro_cli.runner`

The main class responsible for executing YAML-based test scenarios. Handles process spawning, step execution, screenshot coordination, and validation.

#### Constructor

```python
ScenarioRunner(
    scenario_path: Path,
    workspace: Optional[Path] = None,
    verbose: bool = False
) -> None
```

**Parameters:**

- `scenario_path` (Path): Absolute path to the YAML scenario file
- `workspace` (Optional[Path]): Directory for isolated test environment. If provided:
  - Creates `{workspace}/home` as isolated HOME directory
  - Creates `{workspace}/data` as isolated data directory
  - Sets environment variables accordingly
- `verbose` (bool): Enable detailed logging output. Default: `False`

**Attributes:**

- `scenario_path` (Path): Resolved absolute path to scenario file
- `verbose` (bool): Verbose logging flag
- `workspace` (Optional[Path]): Resolved workspace directory or None
- `spec` (Dict[str, Any]): Parsed YAML scenario specification
- `process` (Optional[pexpect.spawn]): Active process handle
- `sentinel_monitor` (SentinelMonitor): Async file monitor for sentinel patterns
- `trigger_dir` (Path): Cross-platform screenshot trigger directory

**Example:**

```python
from orchestro_cli import ScenarioRunner
from pathlib import Path

runner = ScenarioRunner(
    scenario_path=Path("/path/to/scenario.yaml"),
    workspace=Path("/tmp/test-workspace"),
    verbose=True
)

runner.run()
```

---

#### Methods

##### `run() -> None`

Execute the scenario synchronously. This is the main entry point for running tests.

**Behavior:**

1. Loads and parses the YAML scenario
2. Spawns the target CLI process with pexpect
3. Executes steps sequentially
4. Handles screenshots via file triggers
5. Monitors sentinel patterns asynchronously
6. Validates results after process completion

**Raises:**

- `ValueError`: If scenario is malformed or missing required fields
- `TimeoutError`: If expect patterns or screenshots timeout
- `AssertionError`: If validations fail
- `RuntimeError`: If process fails to start

**Example:**

```python
try:
    runner.run()
    print("Test passed!")
except TimeoutError as e:
    print(f"Test timed out: {e}")
except AssertionError as e:
    print(f"Validation failed: {e}")
```

---

##### `_prepare_env() -> Dict[str, str]`

Prepare environment variables for the spawned process.

**Returns:** Dictionary of environment variables

**Behavior:**

- Copies current environment
- Applies scenario-defined `env` variables
- Sets `HOME` to `{workspace}/home` if workspace provided
- Sets `VYB_DATA_ROOT` to `{workspace}/data` if workspace provided
- Sets `VYB_AUTO_SCREENSHOT=1` to enable screenshot monitoring

**Example Environment:**

```python
{
    "HOME": "/tmp/test-workspace/home",
    "VYB_DATA_ROOT": "/tmp/test-workspace/data",
    "VYB_AUTO_SCREENSHOT": "1",
    "CUSTOM_VAR": "value_from_yaml"
}
```

---

##### `_parse_steps() -> List[ScenarioStep]`

Parse scenario steps from YAML specification.

**Returns:** List of ScenarioStep objects

**Supports:**

- `expect` and `pattern` (aliases for pattern matching)
- `send` (input text)
- `control` (control character)
- `screenshot` (screenshot trigger)
- `note` (logging message)
- `timeout` (step-specific timeout)
- `raw` (send without newline)

**Example YAML:**

```yaml
steps:
  - expect: "Ready"
    timeout: 10
    note: "Waiting for startup..."

  - send: "help"
    raw: false

  - screenshot: "help-screen"
    timeout: 15
```

---

##### `_parse_validations() -> List[Validation]`

Parse validation rules from YAML specification.

**Returns:** List of Validation objects

**Supported Types:**

- `path_exists`: Verify file/directory exists
- `file_contains`: Verify file contains regex pattern

**Example YAML:**

```yaml
validations:
  - type: path_exists
    path: artifacts/screenshots/screen.svg

  - type: file_contains
    path: output.log
    text: "Success.*complete"
```

---

##### `async _handle_expect(pattern: str, timeout: float) -> None`

Handle expect step with support for both pexpect patterns and sentinel patterns.

**Parameters:**

- `pattern` (str): Regex pattern or sentinel marker
- `timeout` (float): Maximum wait time in seconds

**Behavior:**

- Detects sentinel patterns (containing `[PROMPT]`, `[WIDGET]`, etc.)
- For sentinels: Uses SentinelMonitor for async file monitoring
- For regular patterns: Uses pexpect's expect mechanism

**Sentinel Examples:**

```python
# Wait for sentinel marker
await runner._handle_expect(r"\[PROMPT\] main_menu", timeout=5.0)

# Wait for widget event
await runner._handle_expect(r"\[WIDGET\] file_tree", timeout=3.0)
```

**Raises:**

- `TimeoutError`: If pattern not found within timeout

---

##### `async _handle_screenshot(name: str, timeout: float) -> None`

Trigger and wait for screenshot capture via file-based mechanism.

**Parameters:**

- `name` (str): Screenshot name (sanitized to slug)
- `timeout` (float): Maximum wait time in seconds

**Behavior:**

1. Sanitizes name to filesystem-safe slug
2. Creates trigger file in cross-platform temp directory
3. Polls for screenshot file in `artifacts/screenshots/`
4. Removes trigger file after capture or timeout

**File Paths:**

- Trigger: `{tempdir}/.vyb_orchestro/screenshot_triggers/{slug}.trigger`
- Screenshot: `{cwd}/artifacts/screenshots/{slug}.svg`

**Example:**

```python
# Captures to artifacts/screenshots/main-screen.svg
await runner._handle_screenshot("main screen", timeout=15.0)
```

**Raises:**

- `TimeoutError`: If screenshot not created within timeout

---

##### `_run_validations(env: Dict[str, str]) -> None`

Execute validation rules after scenario completion.

**Parameters:**

- `env` (Dict[str, str]): Environment variables used during execution

**Path Resolution:**

- Uses workspace as base if provided, otherwise current directory
- Absolute paths used as-is
- Paths starting with `artifacts/`, `tmp/`, or `.` resolved from CWD
- Other paths resolved relative to workspace/CWD

**Raises:**

- `ValueError`: If validation has invalid configuration
- `AssertionError`: If validation fails

**Example:**

```python
# After scenario completion
runner._run_validations(env)
# Raises AssertionError if any validation fails
```

---

### SentinelMonitor

**Module:** `orchestro_cli.sentinel_monitor`

Asynchronous file monitor for sentinel pattern detection. Provides tail-f style monitoring with pattern matching, timeouts, and context manager support.

#### Constructor

```python
SentinelMonitor(
    sentinel_file: str | Path = "/tmp/.vyb_orchestro_sentinels"
) -> None
```

**Parameters:**

- `sentinel_file` (str | Path): Path to sentinel file to monitor. Default: `/tmp/.vyb_orchestro_sentinels`

**Attributes:**

- `sentinel_file` (Path): Resolved sentinel file path
- `running` (bool): Monitor active status
- `monitor_task` (Optional[asyncio.Task]): Background monitoring task
- `lines` (list[str]): Captured sentinel lines (last 1000)
- `last_position` (int): File read position cursor
- `_lock` (asyncio.Lock): Thread-safe access control

**Example:**

```python
from orchestro_cli import SentinelMonitor

monitor = SentinelMonitor("/tmp/.vyb_orchestro_sentinels")
```

---

#### Methods

##### `async start() -> None`

Start background monitoring of sentinel file.

**Behavior:**

- Creates background asyncio task for file monitoring
- Polls file every 100ms for new content
- Thread-safe with asyncio Lock

**Example:**

```python
monitor = SentinelMonitor()
await monitor.start()
```

---

##### `async stop() -> None`

Stop monitoring and cleanup background task.

**Behavior:**

- Cancels monitoring task gracefully
- Waits for task completion
- Safe to call multiple times

**Example:**

```python
await monitor.stop()
```

---

##### `clear() -> None`

Clear sentinel file contents and reset monitor state.

**Behavior:**

- Truncates sentinel file
- Clears captured lines
- Resets file position cursor

**Example:**

```python
monitor.clear()
# Fresh state, ready for new sentinels
```

---

##### `cleanup() -> None`

Synchronous cleanup wrapper for compatibility.

**Behavior:**

- Attempts to stop monitoring in running event loop
- Falls back to immediate cancellation if no loop

**Example:**

```python
try:
    runner.run()
finally:
    monitor.cleanup()
```

---

##### `async wait_for(pattern: str, timeout: float = 5.0) -> bool`

Wait for sentinel matching regex pattern.

**Parameters:**

- `pattern` (str): Regex pattern to match
- `timeout` (float): Maximum wait time in seconds. Default: 5.0

**Returns:** `True` if pattern found, `False` if timeout

**Behavior:**

- Auto-starts monitoring if not running
- Checks existing lines first
- Polls every 50ms for new lines
- Compiles regex once for efficiency

**Examples:**

```python
# Wait for specific prompt
found = await monitor.wait_for(r"\[PROMPT\] settings", timeout=3.0)

# Wait for widget with wildcard
found = await monitor.wait_for(r"\[WIDGET\] file_tree_.*", timeout=5.0)

# Wait for error
if await monitor.wait_for(r"\[ERROR\]", timeout=1.0):
    print("Error detected!")
```

---

##### `async wait_for_any(patterns: list[str], timeout: float = 5.0) -> tuple[bool, Optional[str]]`

Wait for any of multiple patterns to match.

**Parameters:**

- `patterns` (list[str]): List of regex patterns
- `timeout` (float): Maximum wait time in seconds. Default: 5.0

**Returns:** Tuple of `(found, matched_pattern)`

- `found` (bool): True if any pattern matched
- `matched_pattern` (Optional[str]): The pattern that matched, or None

**Example:**

```python
found, pattern = await monitor.wait_for_any([
    r"\[PROMPT\] main_menu",
    r"\[PROMPT\] settings",
    r"\[ERROR\] .*"
], timeout=5.0)

if found:
    print(f"Matched: {pattern}")
```

---

##### `get_all_sentinels() -> list[str]`

Get all captured sentinel lines for debugging.

**Returns:** List of all sentinel lines (last 1000)

**Example:**

```python
lines = monitor.get_all_sentinels()
for line in lines:
    print(f"Sentinel: {line}")
```

---

##### `@classmethod async create(cls, sentinel_file: str | Path = "/tmp/.vyb_orchestro_sentinels") -> SentinelMonitor`

Factory method for context manager usage.

**Parameters:**

- `sentinel_file` (str | Path): Path to sentinel file

**Returns:** Started SentinelMonitor instance

**Example:**

```python
async with SentinelMonitor.create() as monitor:
    found = await monitor.wait_for(r"\[PROMPT\] menu")
# Auto-cleanup on exit
```

---

##### Context Manager Support

SentinelMonitor supports async context manager protocol.

**Methods:**

- `async __aenter__() -> SentinelMonitor`: Starts monitoring
- `async __aexit__(*args) -> None`: Stops monitoring

**Example:**

```python
async with SentinelMonitor("/tmp/sentinels") as monitor:
    await monitor.wait_for(r"\[READY\]")
    # Monitoring active
# Auto-stopped and cleaned up
```

---

## Data Classes

### ScenarioStep

**Module:** `orchestro_cli.runner`

Represents a single step in a test scenario.

```python
@dataclass
class ScenarioStep:
    expect: Optional[str] = None
    send: Optional[str] = None
    control: Optional[str] = None
    note: Optional[str] = None
    timeout: Optional[float] = None
    raw: bool = False
    screenshot: Optional[str] = None
```

**Fields:**

- `expect` (Optional[str]): Pattern to match (pexpect regex or sentinel)
- `send` (Optional[str]): Text to send to process
- `control` (Optional[str]): Control character to send (e.g., "c" for Ctrl+C)
- `note` (Optional[str]): Logging message for this step
- `timeout` (Optional[float]): Step-specific timeout override
- `raw` (bool): If True, send without newline. Default: False
- `screenshot` (Optional[str]): Screenshot name to capture

**Example:**

```python
from orchestro_cli.runner import ScenarioStep

step = ScenarioStep(
    expect=r"\[PROMPT\] menu",
    send="help",
    note="Requesting help menu",
    timeout=10.0,
    raw=False
)
```

---

### Validation

**Module:** `orchestro_cli.runner`

Represents a validation rule to execute after scenario completion.

```python
@dataclass
class Validation:
    type: str
    path: Optional[str] = None
    text: Optional[str] = None
```

**Fields:**

- `type` (str): Validation type (`"path_exists"` or `"file_contains"`)
- `path` (Optional[str]): File path to validate (required for both types)
- `text` (Optional[str]): Regex pattern to match (required for `file_contains`)

**Examples:**

```python
from orchestro_cli.runner import Validation

# Path existence
val1 = Validation(
    type="path_exists",
    path="artifacts/screenshots/screen.svg"
)

# Content validation
val2 = Validation(
    type="file_contains",
    path="output.log",
    text=r"Success.*\d+ records"
)
```

---

## CLI Interface

### Command-Line Arguments

```bash
orchestro [-h] [-w WORKSPACE] [-v] [--version] scenario
```

**Positional Arguments:**

- `scenario`: Path to YAML scenario file

**Optional Arguments:**

- `-h, --help`: Show help message and exit
- `-w WORKSPACE, --workspace WORKSPACE`: Workspace directory for isolated testing
- `-v, --verbose`: Enable verbose logging
- `--version`: Show version and exit

**Examples:**

```bash
# Basic execution
orchestro test.yaml

# With verbose logging
orchestro test.yaml --verbose

# With isolated workspace
orchestro test.yaml --workspace /tmp/test-env

# Combined
orchestro test.yaml -v -w /tmp/test-env
```

---

### Exit Codes

- `0`: Success - all steps and validations passed
- `1`: Failure - scenario error, timeout, or validation failure

**Example Usage in Scripts:**

```bash
#!/bin/bash
orchestro test.yaml
if [ $? -eq 0 ]; then
    echo "Tests passed!"
else
    echo "Tests failed!"
    exit 1
fi
```

---

## Environment Variables

### Set by Orchestro

These are automatically set by ScenarioRunner:

| Variable | Value | Purpose |
|----------|-------|---------|
| `VYB_AUTO_SCREENSHOT` | `"1"` | Enable screenshot monitoring in target app |
| `HOME` | `{workspace}/home` | Isolated home directory (if workspace used) |
| `VYB_DATA_ROOT` | `{workspace}/data` | Isolated data directory (if workspace used) |

### Custom Environment Variables

Define in scenario YAML:

```yaml
env:
  MY_API_KEY: "test-key-12345"
  DEBUG_MODE: "true"
  LOG_LEVEL: "DEBUG"
```

These are merged with system environment and passed to spawned process.

---

## File System Conventions

### Directory Structure

```
project/
├── artifacts/
│   └── screenshots/          # Screenshot output directory
│       ├── 01-startup.svg
│       ├── 02-menu.svg
│       └── 03-settings.svg
├── scenarios/
│   ├── test1.yaml
│   └── test2.yaml
└── {workspace}/              # Optional isolated environment
    ├── home/                 # Isolated HOME
    └── data/                 # Isolated data
```

### Cross-Platform Temporary Files

Orchestro uses platform-appropriate temporary directories:

**Linux/macOS:**
```
/tmp/.vyb_orchestro/
├── sentinels                 # Sentinel marker file
└── screenshot_triggers/      # Screenshot trigger files
    ├── screenshot-1.trigger
    └── screenshot-2.trigger
```

**Windows:**
```
C:\Users\{user}\AppData\Local\Temp\.vyb_orchestro\
├── sentinels
└── screenshot_triggers\
    ├── screenshot-1.trigger
    └── screenshot-2.trigger
```

**Access in Code:**

```python
import tempfile
from pathlib import Path

temp_dir = Path(tempfile.gettempdir()) / ".vyb_orchestro"
sentinel_file = temp_dir / "sentinels"
trigger_dir = temp_dir / "screenshot_triggers"
```

---

## Integration Examples

### Example 1: Basic Test Automation

```python
from orchestro_cli import ScenarioRunner
from pathlib import Path

def test_cli_app():
    """Run automated CLI test."""
    runner = ScenarioRunner(
        scenario_path=Path("scenarios/basic_test.yaml"),
        verbose=True
    )

    try:
        runner.run()
        print("Test passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        raise
```

---

### Example 2: Textual App Integration

Integrate screenshot support into a Textual application:

```python
import os
import tempfile
from pathlib import Path
from textual.app import App

class MyTuiApp(App):
    """Textual app with Orchestro screenshot support."""

    def on_mount(self) -> None:
        """Setup screenshot monitoring if enabled."""
        if os.getenv("VYB_AUTO_SCREENSHOT"):
            self.set_interval(0.5, self._check_screenshot_triggers)

    def _check_screenshot_triggers(self) -> None:
        """Check for screenshot trigger files (cross-platform)."""
        trigger_dir = Path(tempfile.gettempdir()) / ".vyb_orchestro" / "screenshot_triggers"
        if not trigger_dir.exists():
            return

        for trigger_file in trigger_dir.glob("*.trigger"):
            try:
                screenshot_name = trigger_file.stem
                self._capture_screenshot(screenshot_name)
                trigger_file.unlink()  # Consume trigger
            except Exception as e:
                self.log(f"Screenshot error: {e}")

    def _capture_screenshot(self, name: str) -> None:
        """Capture screenshot to artifacts directory."""
        screenshot_dir = Path.cwd() / "artifacts" / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{name}.svg" if not name.endswith(".svg") else name
        screenshot_path = screenshot_dir / filename

        self.save_screenshot(str(screenshot_path))
        self.log(f"Screenshot saved: {screenshot_path}")
```

**Corresponding Scenario:**

```yaml
name: TUI App Test
command: python my_tui_app.py
timeout: 30

steps:
  - screenshot: "01-startup"
    timeout: 10
    note: "Capture startup screen"

  - send: "q"
    note: "Quit app"

validations:
  - type: path_exists
    path: artifacts/screenshots/01-startup.svg
```

---

### Example 3: Custom Sentinel Integration

Integrate sentinel monitoring into your application:

```python
import tempfile
from pathlib import Path

class MyApp:
    """CLI app with sentinel support."""

    def __init__(self):
        self.sentinel_file = Path(tempfile.gettempdir()) / ".vyb_orchestro" / "sentinels"
        self.sentinel_file.parent.mkdir(parents=True, exist_ok=True)

    def emit_sentinel(self, marker: str, identifier: str) -> None:
        """Emit sentinel marker for testing.

        Args:
            marker: Sentinel type (e.g., "PROMPT", "WIDGET", "ERROR")
            identifier: Unique identifier (e.g., "main_menu", "status_bar")
        """
        with open(self.sentinel_file, "a", encoding="utf-8") as f:
            f.write(f"[{marker}] {identifier}\n")

    def show_menu(self) -> None:
        """Display main menu."""
        print("Main Menu:")
        print("1. Settings")
        print("2. Help")
        print("3. Quit")

        # Emit sentinel for testing
        self.emit_sentinel("PROMPT", "main_menu")

    def show_settings(self) -> None:
        """Display settings screen."""
        print("Settings:")
        print("...")

        # Emit sentinel
        self.emit_sentinel("WIDGET", "settings_panel")
```

**Corresponding Scenario:**

```yaml
name: Sentinel Test
command: python my_app.py
timeout: 30

steps:
  - expect: "[PROMPT] main_menu"
    timeout: 10
    note: "Wait for main menu to appear"

  - send: "1"
    note: "Select settings"

  - expect: "[WIDGET] settings_panel"
    timeout: 5
    note: "Wait for settings to load"
```

---

### Example 4: Programmatic Scenario Creation

Generate scenarios programmatically:

```python
from pathlib import Path
import yaml

def create_screenshot_scenario(app_command: str, num_screenshots: int) -> Path:
    """Generate a screenshot gallery scenario.

    Args:
        app_command: Command to launch app
        num_screenshots: Number of screenshots to capture

    Returns:
        Path to created scenario file
    """
    steps = []
    validations = []

    for i in range(1, num_screenshots + 1):
        screenshot_name = f"{i:02d}-screen"

        steps.append({
            "screenshot": screenshot_name,
            "timeout": 15,
            "note": f"Capturing screenshot {i}/{num_screenshots}"
        })

        validations.append({
            "type": "path_exists",
            "path": f"artifacts/screenshots/{screenshot_name}.svg"
        })

    scenario = {
        "name": f"Screenshot Gallery ({num_screenshots} shots)",
        "command": app_command,
        "timeout": 60,
        "steps": steps,
        "validations": validations
    }

    scenario_path = Path("generated_scenario.yaml")
    with open(scenario_path, "w") as f:
        yaml.dump(scenario, f, default_flow_style=False)

    return scenario_path

# Usage
scenario_path = create_screenshot_scenario("./my_app", num_screenshots=5)
runner = ScenarioRunner(scenario_path, verbose=True)
runner.run()
```

---

### Example 5: Async Sentinel Monitoring

Use SentinelMonitor independently:

```python
import asyncio
from orchestro_cli import SentinelMonitor

async def monitor_app_events():
    """Monitor application events via sentinels."""
    async with SentinelMonitor.create() as monitor:
        print("Monitoring app events...")

        # Wait for startup
        if await monitor.wait_for(r"\[READY\]", timeout=10.0):
            print("App started!")

        # Wait for user action
        found, pattern = await monitor.wait_for_any([
            r"\[ACTION\] login",
            r"\[ACTION\] register",
            r"\[ERROR\] .*"
        ], timeout=30.0)

        if found:
            if "ERROR" in pattern:
                print("Error occurred!")
            else:
                print(f"User action: {pattern}")

        # Get all events
        all_sentinels = monitor.get_all_sentinels()
        print(f"Total events: {len(all_sentinels)}")

# Run
asyncio.run(monitor_app_events())
```

---

## Advanced Topics

### Custom Step Types

Extend ScenarioRunner with custom step handlers:

```python
from orchestro_cli import ScenarioRunner
from pathlib import Path

class CustomScenarioRunner(ScenarioRunner):
    """Extended runner with custom step types."""

    async def _run_async(self) -> None:
        """Override to add custom step handling."""
        # ... existing setup code ...

        steps = self._parse_steps()
        for step in steps:
            # Custom step type
            if hasattr(step, 'custom_action'):
                await self._handle_custom_action(step)
            else:
                # Use base class handling
                await super()._handle_step(step)

    async def _handle_custom_action(self, step):
        """Custom step handler."""
        # Your custom logic here
        pass
```

### Timeout Strategies

Configure timeouts at multiple levels:

```yaml
# Global timeout
timeout: 60

steps:
  # Step-specific timeout (overrides global)
  - expect: "Ready"
    timeout: 10

  # Screenshot with longer timeout
  - screenshot: "large-render"
    timeout: 30

  # Default to global timeout
  - send: "help"
```

### Error Handling Best Practices

```python
from orchestro_cli import ScenarioRunner
from pathlib import Path
import logging

def run_test_with_recovery(scenario_path: Path):
    """Run test with comprehensive error handling."""
    runner = ScenarioRunner(scenario_path, verbose=True)

    try:
        runner.run()
        logging.info("Test passed successfully")
        return 0

    except TimeoutError as e:
        logging.error(f"Test timeout: {e}")
        # Cleanup resources
        runner.sentinel_monitor.cleanup()
        return 1

    except AssertionError as e:
        logging.error(f"Validation failed: {e}")
        # Log captured output
        if runner.process:
            logging.debug(f"Process output: {runner.process.before}")
        return 1

    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        return 2

    finally:
        # Ensure cleanup
        if hasattr(runner, 'sentinel_monitor'):
            runner.sentinel_monitor.cleanup()
```

---

## FAQ

### Q: How do I debug failed expect patterns?

**A:** Enable verbose mode and check process output:

```python
runner = ScenarioRunner(scenario_path, verbose=True)
try:
    runner.run()
except Exception as e:
    print(f"Process output: {runner.process.before}")
    print(f"Last matched: {runner.process.after}")
    raise
```

### Q: Can I use Orchestro with non-Python CLI apps?

**A:** Yes! Orchestro works with any CLI application. Just specify the command:

```yaml
command: ["node", "app.js"]
# or
command: "./compiled_binary"
# or
command: "ruby script.rb --config test.yml"
```

### Q: How do I wait for multiple conditions?

**A:** Use `wait_for_any()` or chain multiple expect steps:

```python
# Option 1: Multiple conditions
found, pattern = await monitor.wait_for_any([
    r"\[READY\]",
    r"\[ERROR\]"
])

# Option 2: Chain expects
steps:
  - expect: "Loading"
  - expect: "Complete"
```

### Q: Can I capture screenshots on Windows?

**A:** Yes! Orchestro automatically handles cross-platform paths using `tempfile.gettempdir()`.

---

## Intelligence API

**Version:** 0.3.0 (NEW)

Orchestro CLI now includes intelligent test generation APIs for automatic scenario creation from code analysis.

### Analyzing Applications

Extract application structure using AST analysis:

```python
from orchestro_cli.intelligence import ASTAnalyzer, AppKnowledge
from pathlib import Path

# Create analyzer
analyzer = ASTAnalyzer()

# Analyze single file
knowledge = await analyzer.analyze_file(
    Path("my_app/main.py"),
    framework="textual"
)

# Analyze entire project
knowledge = await analyzer.analyze_project(
    Path("./my_app"),
    framework="textual",
    exclude_patterns=["tests/*", "venv/*"],
    follow_imports=True,
    max_depth=10
)

# Access results
print(f"Found {len(knowledge.screens)} screens")
for screen in knowledge.screens:
    print(f"  {screen.name}: {len(screen.keybindings)} keybindings")
```

### Generating Scenarios

Create test scenarios from knowledge base:

```python
from orchestro_cli.intelligence import ScenarioGenerator

# Create generator
generator = ScenarioGenerator(knowledge)

# Generate smoke tests
smoke_yaml = generator.generate_smoke_test()
Path("tests/smoke.yaml").write_text(smoke_yaml)

# Generate coverage tests
coverage_tests = generator.generate_coverage_tests()
for i, test_yaml in enumerate(coverage_tests):
    Path(f"tests/coverage_{i:02d}.yaml").write_text(test_yaml)

# Generate test for specific screen
screen = knowledge.get_screen("MainScreen")
screen_yaml = generator.generate_screen_test(screen)
Path("tests/main_screen.yaml").write_text(screen_yaml)

# Generate navigation test
nav_yaml = generator.generate_navigation_test(
    from_screen="MainScreen",
    to_screen="SettingsScreen"
)
Path("tests/navigation.yaml").write_text(nav_yaml)
```

### Using Custom Templates

Generate with Jinja2 templates:

```python
from jinja2 import Template

# Load custom template
template_text = Path("my_template.jinja2").read_text()
template = Template(template_text)

# Generate with custom template
custom_yaml = generator.generate_from_template(
    template,
    screen=knowledge.screens[0],
    app=knowledge.metadata,
    custom_var="custom_value"
)

Path("tests/custom.yaml").write_text(custom_yaml)
```

### Knowledge Base Management

Work with application knowledge:

```python
from orchestro_cli.intelligence import AppKnowledge, Screen, Keybinding

# Create knowledge manually
knowledge = AppKnowledge(
    framework="textual",
    version="0.3.0",
    metadata={"app_name": "MyApp", "version": "1.0"}
)

# Add screen
screen = Screen(
    name="MainScreen",
    file=Path("app.py"),
    line=42,
    widgets=["Header", "Footer", "ContentView"],
    keybindings=[
        Keybinding(key="q", action="quit", description="Exit"),
        Keybinding(key="h", action="help", description="Help"),
    ],
    navigation={"to": ["SettingsScreen", "HelpScreen"]}
)
knowledge.screens.append(screen)

# Save knowledge base
knowledge.save(".orchestro/index.json")

# Load knowledge base
loaded = AppKnowledge.load(".orchestro/index.json")

# Query knowledge
main_screen = knowledge.get_screen("MainScreen")
all_keys = knowledge.get_all_keybindings()
nav_graph = knowledge.get_navigation_graph()
```

### Learning from Test Results

Improve knowledge base from execution results:

```python
from orchestro_cli.intelligence import LearningEngine
from orchestro_cli.junit_reporter import JUnitResults

# Load knowledge and results
knowledge = AppKnowledge.load(".orchestro/index.json")
results = JUnitResults.load("test-results/junit.xml")

# Create learning engine
engine = LearningEngine(knowledge)

# Analyze results and learn patterns
improvements = engine.learn_from_results(results)

print(f"Learned {len(improvements)} improvements:")
for improvement in improvements:
    print(f"  - {improvement.description}")
    print(f"    Confidence: {improvement.confidence:.2f}")
    print(f"    Impact: {improvement.impact}")

# Apply improvements
engine.apply_improvements(improvements)

# Save updated knowledge
knowledge.save(".orchestro/index.json")
```

### Custom Framework Extractors

Add support for new frameworks:

```python
from orchestro_cli.intelligence import (
    FrameworkExtractor,
    AppKnowledge,
    Screen,
    register_extractor
)
import ast

class MyFrameworkExtractor(FrameworkExtractor):
    """Extract structure from MyFramework apps."""

    @classmethod
    def can_handle(cls, code: str) -> bool:
        """Check if code uses MyFramework."""
        return "from myframework import App" in code

    def extract(self, tree: ast.AST, source_file: Path) -> AppKnowledge:
        """Extract app structure from AST."""
        knowledge = AppKnowledge(framework="myframework")

        # Walk AST and extract structure
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if self._is_screen_class(node):
                    screen = self._extract_screen(node, source_file)
                    knowledge.screens.append(screen)

        return knowledge

    def _is_screen_class(self, node: ast.ClassDef) -> bool:
        """Check if class is a Screen."""
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in ["Screen", "View"]:
                return True
        return False

    def _extract_screen(self, node: ast.ClassDef, source_file: Path) -> Screen:
        """Extract screen information."""
        return Screen(
            name=node.name,
            file=source_file,
            line=node.lineno,
            widgets=self._extract_widgets(node),
            keybindings=self._extract_keybindings(node)
        )

    def _extract_widgets(self, node: ast.ClassDef) -> list[str]:
        """Extract widget names from compose method."""
        # Implementation details
        pass

    def _extract_keybindings(self, node: ast.ClassDef) -> list[Keybinding]:
        """Extract keybindings from BINDINGS or decorators."""
        # Implementation details
        pass

# Register extractor
register_extractor(MyFrameworkExtractor)

# Now use it
analyzer = ASTAnalyzer()
knowledge = await analyzer.analyze_project(
    Path("./my_app"),
    framework="myframework"  # Uses your custom extractor
)
```

### Code Annotations

Guide generation with decorator hints:

```python
from orchestro_cli import orchestro_hint

class MyScreen(Screen):
    """Application screen with Orchestro hints."""

    # Mark critical paths
    @orchestro_hint("critical-path")
    def action_save_data(self):
        """Save user data - critical functionality."""
        pass

    # Specify edge cases
    @orchestro_hint("edge-case", input="empty-string")
    def validate_input(self, value: str):
        """Validate input - test with empty string."""
        pass

    # Mark slow operations
    @orchestro_hint("slow-test", timeout=60)
    def action_generate_report(self):
        """Generate report - takes time."""
        pass

    # Skip unstable features
    @orchestro_hint("skip-test", reason="Feature under development")
    def experimental_feature(self):
        """Experimental - skip in generated tests."""
        pass

    # Provide keybinding hints
    @orchestro_hint("keybinding", key="ctrl+s", action="save")
    def setup_custom_bindings(self):
        """Setup dynamic keybindings."""
        pass
```

### Data Classes

#### AppKnowledge

```python
@dataclass
class AppKnowledge:
    """Application structure knowledge base."""
    framework: str
    version: str
    screens: List[Screen]
    keybindings: List[Keybinding]
    navigation: Dict[str, List[str]]
    metadata: Dict[str, Any]

    def save(self, path: Path) -> None:
        """Save to JSON/YAML file."""

    @classmethod
    def load(cls, path: Path) -> "AppKnowledge":
        """Load from JSON/YAML file."""

    def get_screen(self, name: str) -> Optional[Screen]:
        """Get screen by name."""

    def get_all_keybindings(self) -> List[Keybinding]:
        """Get all keybindings (global + screen-specific)."""

    def get_navigation_graph(self) -> Dict[str, List[str]]:
        """Get navigation graph."""
```

#### Screen

```python
@dataclass
class Screen:
    """Screen/view definition."""
    name: str
    file: Path
    line: int
    widgets: List[str]
    keybindings: List[Keybinding]
    navigation: Dict[str, List[str]]
    metadata: Dict[str, Any] = field(default_factory=dict)
```

#### Keybinding

```python
@dataclass
class Keybinding:
    """Keyboard binding definition."""
    key: str
    action: str
    description: str
    scope: str = "screen"  # or "global"
```

### CLI Integration

Use intelligence features from command line:

```bash
# Analyze application
orchestro index ./my_app --framework textual --output .orchestro/index.json

# Generate tests
orchestro generate .orchestro/index.json --type smoke --output tests/smoke/
orchestro generate .orchestro/index.json --type coverage --output tests/coverage/

# Analyze coverage
orchestro coverage .orchestro/index.json tests/ --report html --output coverage.html

# Learn from results
orchestro learn .orchestro/index.json test-results/junit.xml --update
```

See [Intelligence Guide](INTELLIGENCE.md) for complete CLI documentation.

---

## Version History

### 1.0.0 (Current)

- Initial stable release
- ScenarioRunner with pexpect integration
- SentinelMonitor for async pattern matching
- Screenshot capture via file triggers
- Cross-platform support
- Workspace isolation
- YAML scenario format
- CLI interface

---

## Contributing

To extend or contribute to Orchestro CLI:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update API documentation
5. Submit a pull request

**Key Extension Points:**

- Custom step types (extend ScenarioRunner)
- Additional validation types (extend `_run_validations`)
- New sentinel patterns (extend SentinelMonitor)
- Alternative scenario formats (extend `_load_spec`)

---

## License

MIT License - See LICENSE file for details

---

**Documentation Version:** 1.0.0
**Last Updated:** 2025-11-13
**Orchestro CLI Version:** 1.0.0
