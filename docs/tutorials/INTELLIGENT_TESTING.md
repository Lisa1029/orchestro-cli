# Intelligent Testing Tutorial

**Time Required:** 30 minutes
**Difficulty:** Beginner-Intermediate

Learn how to use Orchestro CLI's intelligent test generation to automatically create comprehensive test scenarios for your TUI applications.

---

## What You'll Build

By the end of this tutorial, you'll have:
- A simple Textual TUI application
- An automatically generated knowledge base
- Comprehensive test scenarios (smoke + coverage)
- Running automated tests
- Integration with CI/CD

## Prerequisites

- Python 3.8+
- Orchestro CLI installed (`pip install orchestro-cli`)
- Basic familiarity with Textual (helpful but not required)

---

## Step 1: Create a Sample TUI Application

Let's build a simple task management TUI app that we'll test.

### Create Project Structure

```bash
mkdir task_app
cd task_app

# Create directory structure
mkdir -p task_app/screens
touch task_app/__init__.py
touch task_app/__main__.py
touch task_app/screens/__init__.py
touch task_app/screens/main_screen.py
touch task_app/screens/settings_screen.py
```

### Main Application (task_app/__main__.py)

```python
"""Task Manager TUI Application."""
import os
import tempfile
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from task_app.screens.main_screen import MainScreen

class TaskManagerApp(App):
    """A simple task management TUI app."""

    TITLE = "Task Manager"
    CSS = """
    Screen {
        background: $surface;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("?", "help", "Help"),
    ]

    def __init__(self):
        super().__init__()
        self.setup_screenshot_support()

    def setup_screenshot_support(self):
        """Enable Orchestro screenshot support."""
        if os.getenv("VYB_AUTO_SCREENSHOT"):
            self.set_interval(0.5, self._check_screenshot_triggers)

    def _check_screenshot_triggers(self) -> None:
        """Check for screenshot trigger files (Orchestro integration)."""
        trigger_dir = Path(tempfile.gettempdir()) / ".vyb_orchestro" / "screenshot_triggers"
        if not trigger_dir.exists():
            return

        for trigger_file in trigger_dir.glob("*.trigger"):
            try:
                screenshot_name = trigger_file.stem
                screenshot_dir = Path.cwd() / "artifacts" / "screenshots"
                screenshot_dir.mkdir(parents=True, exist_ok=True)
                filename = f"{screenshot_name}.svg"
                self.save_screenshot(filename=filename, path=str(screenshot_dir))
                trigger_file.unlink()
            except Exception as e:
                self.log(f"Screenshot error: {e}")

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        """Push main screen on startup."""
        self.push_screen(MainScreen())

    def action_help(self) -> None:
        """Show help message."""
        self.notify("Task Manager v1.0 - Use arrow keys to navigate")

if __name__ == "__main__":
    app = TaskManagerApp()
    app.run()
```

### Main Screen (task_app/screens/main_screen.py)

```python
"""Main task list screen."""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Static, ListView, ListItem, Label
from textual.containers import Container, Vertical

class MainScreen(Screen):
    """Main screen showing task list."""

    BINDINGS = [
        ("a", "add_task", "Add Task"),
        ("d", "delete_task", "Delete Task"),
        ("s", "settings", "Settings"),
        ("r", "refresh", "Refresh"),
    ]

    def __init__(self):
        super().__init__()
        self.tasks = ["Review PRs", "Write docs", "Fix bug #42"]

    def compose(self) -> ComposeResult:
        """Create main screen widgets."""
        yield Static("📋 My Tasks", id="title")
        yield Container(
            ListView(
                *[ListItem(Label(task)) for task in self.tasks],
                id="task-list"
            ),
            id="task-container"
        )
        yield Container(
            Button("Add", id="btn-add", variant="success"),
            Button("Delete", id="btn-delete", variant="error"),
            Button("Settings", id="btn-settings", variant="primary"),
            id="button-row"
        )

    def action_add_task(self) -> None:
        """Add a new task."""
        self.tasks.append(f"New Task {len(self.tasks) + 1}")
        self.notify("Task added!")
        self.action_refresh()

    def action_delete_task(self) -> None:
        """Delete selected task."""
        if self.tasks:
            self.tasks.pop()
            self.notify("Task deleted!")
            self.action_refresh()
        else:
            self.notify("No tasks to delete", severity="warning")

    def action_settings(self) -> None:
        """Open settings screen."""
        from task_app.screens.settings_screen import SettingsScreen
        self.app.push_screen(SettingsScreen())

    def action_refresh(self) -> None:
        """Refresh the task list."""
        # Refresh the list view
        self.notify("Refreshed!")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        if button_id == "btn-add":
            self.action_add_task()
        elif button_id == "btn-delete":
            self.action_delete_task()
        elif button_id == "btn-settings":
            self.action_settings()
```

### Settings Screen (task_app/screens/settings_screen.py)

```python
"""Settings configuration screen."""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Static, Switch, Label
from textual.containers import Container, Vertical

class SettingsScreen(Screen):
    """Settings configuration screen."""

    BINDINGS = [
        ("escape", "back", "Back"),
        ("b", "back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        """Create settings widgets."""
        yield Static("⚙️  Settings", id="settings-title")
        yield Container(
            Label("Dark Mode:"),
            Switch(value=True, id="dark-mode"),
            Label("Notifications:"),
            Switch(value=True, id="notifications"),
            Label("Auto-save:"),
            Switch(value=False, id="autosave"),
            id="settings-container"
        )
        yield Button("Back", id="btn-back", variant="primary")

    def action_back(self) -> None:
        """Return to main screen."""
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-back":
            self.action_back()

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle switch toggles."""
        setting_name = event.switch.id.replace("-", " ").title()
        status = "enabled" if event.value else "disabled"
        self.notify(f"{setting_name} {status}")
```

### Make it Runnable

```bash
# Create __main__.py at package level
cat > task_app/__main__.py << 'EOF'
from task_app.__main__ import TaskManagerApp

if __name__ == "__main__":
    app = TaskManagerApp()
    app.run()
EOF
```

### Test Your App Manually

```bash
# Run the app to verify it works
python -m task_app

# Try the keybindings:
# - 'a' to add task
# - 'd' to delete task
# - 's' to open settings
# - 'b' or ESC to go back
# - 'q' to quit
```

**Expected Output**: A working TUI with task list, buttons, and settings screen.

---

## Step 2: Analyze the Application

Now let's use Orchestro's intelligence to analyze our app.

### Run the Indexer

```bash
# Create directory for Orchestro files
mkdir -p .orchestro

# Analyze the application
orchestro index ./task_app --framework textual --output .orchestro/index.json --verbose
```

**Expected Output:**
```
Analyzing application...
  Scanning: task_app/
  Found: 2 screens
    - MainScreen (task_app/screens/main_screen.py:8)
    - SettingsScreen (task_app/screens/settings_screen.py:7)
  Found: 6 keybindings
    - Global: q (quit), ? (help)
    - MainScreen: a (add_task), d (delete_task), s (settings), r (refresh)
    - SettingsScreen: escape (back), b (back)
  Found: 3 actions
    - add_task, delete_task, settings
  Found: 1 navigation path
    - MainScreen → SettingsScreen (via key:s or button)

Analysis complete!
Index saved to: .orchestro/index.json
```

### Inspect the Index

```bash
# View the generated index
cat .orchestro/index.json | jq '.'
```

**Expected Structure:**
```json
{
  "framework": "textual",
  "version": "0.3.0",
  "analyzed_at": "2025-11-17T10:30:00Z",
  "screens": [
    {
      "name": "MainScreen",
      "file": "task_app/screens/main_screen.py",
      "line": 8,
      "widgets": ["Static", "ListView", "Button"],
      "keybindings": [
        {"key": "a", "action": "add_task", "description": "Add Task"},
        {"key": "d", "action": "delete_task", "description": "Delete Task"},
        {"key": "s", "action": "settings", "description": "Settings"},
        {"key": "r", "action": "refresh", "description": "Refresh"}
      ]
    },
    {
      "name": "SettingsScreen",
      "file": "task_app/screens/settings_screen.py",
      "line": 7,
      "widgets": ["Static", "Switch", "Button"],
      "keybindings": [
        {"key": "escape", "action": "back", "description": "Back"},
        {"key": "b", "action": "back", "description": "Back"}
      ]
    }
  ],
  "keybindings": {
    "global": [
      {"key": "q", "action": "quit", "description": "Quit"},
      {"key": "?", "action": "help", "description": "Help"}
    ]
  },
  "navigation": {
    "MainScreen": ["SettingsScreen"],
    "SettingsScreen": ["MainScreen"]
  },
  "metadata": {
    "app_name": "TaskManagerApp",
    "entry_point": "task_app/__main__.py"
  }
}
```

---

## Step 3: Generate Test Scenarios

Now let's generate automated tests from our analysis.

### Generate Smoke Tests

Basic sanity checks:

```bash
# Create test directories
mkdir -p tests/smoke

# Generate smoke tests
orchestro generate .orchestro/index.json --type smoke --output tests/smoke/ --verbose
```

**Expected Output:**
```
Generating smoke tests...
  Strategy: smoke
  Quality threshold: 0.6

Generated scenarios:
  ✓ tests/smoke/01_app_startup.yaml (confidence: 0.95)
  ✓ tests/smoke/02_main_navigation.yaml (confidence: 0.87)
  ✓ tests/smoke/03_screen_rendering.yaml (confidence: 0.92)
  ✓ tests/smoke/04_teardown.yaml (confidence: 0.98)

Summary:
  Total: 4 scenarios
  Avg confidence: 0.93
  Estimated coverage: 45%
```

### Generate Coverage Tests

Comprehensive tests for all features:

```bash
mkdir -p tests/coverage

orchestro generate .orchestro/index.json --type coverage --output tests/coverage/ --verbose
```

**Expected Output:**
```
Generating coverage tests...
  Strategy: coverage
  Quality threshold: 0.6

Generated scenarios:
  ✓ tests/coverage/main_screen_complete.yaml (confidence: 0.89)
  ✓ tests/coverage/settings_screen_complete.yaml (confidence: 0.91)
  ✓ tests/coverage/keybindings_test.yaml (confidence: 0.85)
  ✓ tests/coverage/navigation_flow.yaml (confidence: 0.88)
  ✓ tests/coverage/screenshot_gallery.yaml (confidence: 0.90)

Summary:
  Total: 5 scenarios
  Avg confidence: 0.89
  Estimated coverage: 85%
```

### Inspect Generated Scenarios

Let's look at what was generated:

```bash
cat tests/smoke/01_app_startup.yaml
```

**Example Output:**
```yaml
# Auto-generated by Orchestro CLI v0.3.0
# Strategy: smoke
# Confidence: 0.95
# Coverage: 15%

name: Smoke Test - Application Startup
description: |
  Verify Task Manager starts successfully and renders main screen.
  This is a basic sanity check for application initialization.

command: python -m task_app
timeout: 30

steps:
  - screenshot: "01-app-startup"
    timeout: 10
    note: "Capture initial application state"

  - expect: "Task Manager|My Tasks"
    timeout: 5
    note: "Wait for main screen to render"

  - screenshot: "02-main-screen-loaded"
    timeout: 10
    note: "Verify main screen rendered"

validations:
  - type: path_exists
    path: artifacts/screenshots/01-app-startup.svg
    description: "Startup screenshot captured"

  - type: path_exists
    path: artifacts/screenshots/02-main-screen-loaded.svg
    description: "Main screen screenshot captured"

_orchestro_metadata:
  generated_by: orchestro_cli v0.3.0
  generated_at: 2025-11-17T10:30:00Z
  strategy: smoke
  confidence: 0.95
  coverage: 0.15
  source_screen: MainScreen
```

---

## Step 4: Run Generated Tests

Time to execute our automatically generated tests!

### Run Smoke Tests

```bash
# Run all smoke tests
orchestro tests/smoke/*.yaml --verbose
```

**Expected Output:**
```
Running scenario: 01_app_startup.yaml
  ✓ Screenshot: 01-app-startup
  ✓ Expect: Task Manager|My Tasks
  ✓ Screenshot: 02-main-screen-loaded
  ✓ Validation: artifacts/screenshots/01-app-startup.svg exists
  ✓ Validation: artifacts/screenshots/02-main-screen-loaded.svg exists
PASSED (3.2s)

Running scenario: 02_main_navigation.yaml
  ✓ Screenshot: navigation-start
  ✓ Send: s (open settings)
  ✓ Screenshot: settings-screen
  ✓ Send: b (back to main)
  ✓ Screenshot: back-to-main
PASSED (5.1s)

Running scenario: 03_screen_rendering.yaml
  ✓ All widgets rendered
PASSED (2.3s)

Running scenario: 04_teardown.yaml
  ✓ Send: q (quit)
  ✓ App exited cleanly
PASSED (1.1s)

========================================
Summary: 4/4 passed (11.7s total)
```

### Run Coverage Tests

```bash
orchestro tests/coverage/*.yaml --verbose
```

### Generate JUnit Report

For CI/CD integration:

```bash
# Run all tests with JUnit output
orchestro tests/**/*.yaml --junit-xml=test-results/junit.xml

# Check results
cat test-results/junit.xml
```

---

## Step 5: View Screenshots

Orchestro automatically captured screenshots during testing.

```bash
# List generated screenshots
ls -lh artifacts/screenshots/

# View in browser (if SVG viewer available)
firefox artifacts/screenshots/01-app-startup.svg
# or
open artifacts/screenshots/01-app-startup.svg  # macOS
```

**You should see:**
- `01-app-startup.svg` - Initial app state
- `02-main-screen-loaded.svg` - Main screen
- `navigation-start.svg` - Before navigation
- `settings-screen.svg` - Settings screen
- `back-to-main.svg` - Return to main
- ... and more

These provide visual regression testing!

---

## Step 6: Refine and Learn

Now let's improve our tests based on execution results.

### Analyze Coverage

```bash
orchestro coverage .orchestro/index.json tests/ --report text
```

**Output:**
```
Test Coverage Report
====================

Overall Coverage: 85%

Screens:
  ✓ MainScreen: 90% (4/4 keybindings tested)
  ✓ SettingsScreen: 80% (2/2 keybindings tested)

Keybindings:
  ✓ Global quit (q): tested
  ✓ Global help (?): tested
  ✓ add_task (a): tested
  ✓ delete_task (d): tested
  ✓ settings (s): tested
  ✓ refresh (r): tested
  ✓ back (b, escape): tested

Navigation Paths:
  ✓ MainScreen → SettingsScreen: tested
  ✓ SettingsScreen → MainScreen: tested

Untested Areas:
  ⚠ Button click paths (vs keyboard)
  ⚠ Switch toggle interactions
  ⚠ Error cases (delete when empty)

Recommendations:
  1. Add test for button interactions
  2. Add test for switch toggles
  3. Add edge case tests (empty list, etc.)
```

### Learn from Results

```bash
# Improve index based on test execution
orchestro learn .orchestro/index.json test-results/junit.xml --update --verbose
```

**Output:**
```
Learning from test results...
  Analyzed: 9 test executions
  Success rate: 100%

Learned patterns:
  ✓ MainScreen loads in 0.8s (adjusted timeout: 3s → 2s)
  ✓ Settings screen transition: 0.3s (adjusted timeout: 5s → 1s)
  ✓ Screenshot capture reliable at 0.5s interval

Updated index with improvements.
Confidence boost: +12%
```

### Re-generate with Improved Knowledge

```bash
# Generate new tests with learned parameters
orchestro generate .orchestro/index.json --type coverage --output tests/coverage-v2/
```

---

## Step 7: Add to CI/CD

Integrate with GitHub Actions:

### Create Workflow File

```bash
mkdir -p .github/workflows
cat > .github/workflows/orchestro-tests.yml << 'EOF'
name: Orchestro TUI Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install orchestro-cli textual
          pip install -e .

      - name: Analyze application
        run: orchestro index ./task_app --framework textual --verbose

      - name: Generate tests
        run: |
          orchestro generate .orchestro/index.json --type smoke --output tests/smoke/
          orchestro generate .orchestro/index.json --type coverage --output tests/coverage/

      - name: Run smoke tests
        run: orchestro tests/smoke/*.yaml --junit-xml=results/smoke.xml

      - name: Run coverage tests
        run: orchestro tests/coverage/*.yaml --junit-xml=results/coverage.xml

      - name: Publish test results
        uses: EnricoMi/publish-unit-test-result-action@v2
        if: always()
        with:
          files: results/*.xml

      - name: Upload screenshots
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-screenshots
          path: artifacts/screenshots/

      - name: Check coverage
        run: |
          orchestro coverage .orchestro/index.json tests/ --report text
          orchestro coverage .orchestro/index.json tests/ --report html --output coverage.html

      - name: Upload coverage report
        uses: actions/upload-artifact@v3
        with:
          name: coverage-report
          path: coverage.html
EOF
```

### Commit and Push

```bash
git add .
git commit -m "Add automated TUI testing with Orchestro"
git push
```

Now every push will automatically:
1. Analyze your app
2. Generate tests
3. Run tests
4. Publish results
5. Upload screenshots

---

## What You've Learned

Congratulations! You now know how to:

- ✅ Create a testable Textual TUI application
- ✅ Use `orchestro index` to analyze app structure
- ✅ Generate test scenarios automatically
- ✅ Run and validate generated tests
- ✅ View screenshot-based visual regression tests
- ✅ Improve tests with learning
- ✅ Integrate with CI/CD pipelines

---

## Next Steps

### Extend Your App

Add more features and re-generate tests:

```python
# task_app/screens/main_screen.py

def action_complete_task(self) -> None:
    """Mark task as complete."""
    # Implementation...

BINDINGS = [
    # ... existing bindings
    ("c", "complete_task", "Complete"),
]
```

```bash
# Re-analyze
orchestro index ./task_app --framework textual

# Re-generate
orchestro generate .orchestro/index.json --type coverage
```

### Try Custom Templates

Create custom scenario templates:

```bash
cat > my_template.jinja2 << 'EOF'
name: {{ screen.name }} Custom Test
command: python -m task_app
timeout: 60

steps:
  - screenshot: "{{ screen.name|lower }}-start"

  {% for key in screen.keybindings %}
  - send: "{{ key.key }}"
    note: "Test {{ key.description }}"
  - screenshot: "{{ screen.name|lower }}-{{ key.action }}"
  {% endfor %}
EOF

orchestro generate .orchestro/index.json --template my_template.jinja2
```

### Explore Advanced Features

- Try different generation strategies
- Add manual annotations to your code
- Create custom framework extractors
- Implement learning pipelines

---

## Troubleshooting

### Tests Fail: "Screenshot timeout"

**Solution**: Increase timeout in generated scenarios or app loading speed.

```bash
# Re-generate with higher timeouts
orchestro generate .orchestro/index.json --type smoke --timeout-multiplier 2
```

### No Screens Detected

**Solution**: Ensure proper imports and inheritance:

```python
from textual.screen import Screen  # Must be explicit

class MyScreen(Screen):  # Must inherit Screen
    pass
```

### Low Confidence Scores

**Solution**: Add code annotations:

```python
from orchestro_cli import orchestro_hint

@orchestro_hint("critical-path")
def important_action(self):
    pass
```

---

## Resources

- [Intelligence Guide](../INTELLIGENCE.md) - Complete documentation
- [API Reference](../API.md) - Programmatic usage
- [Examples](../../examples/intelligence/) - Real-world examples
- [GitHub Discussions](https://github.com/vyb/orchestro-cli/discussions) - Community help

---

**Congratulations on completing the tutorial!**

You're now ready to use Orchestro's intelligent test generation in your own projects.

Happy testing! 🎭
