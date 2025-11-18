# Orchestro CLI 🎭

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-550%20passing-success)](https://github.com/jonthemediocre/orchestro-cli)
[![Coverage](https://img.shields.io/badge/coverage-63%25-green)](https://github.com/jonthemediocre/orchestro-cli)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![GitHub Stars](https://img.shields.io/github/stars/jonthemediocre/orchestro-cli?style=social)](https://github.com/jonthemediocre/orchestro-cli)

**Playwright for Terminal Applications — orchestrated CLI/TUI testing with screenshots and AI-generated scenarios**

Orchestro CLI is an orchestration-first testing framework that automates interactive command-line and TUI applications, pairing screenshot-driven validation with intelligence-assisted scenario generation for Textual, Rich, curses, and beyond.

## ✨ Features

- 🎯 **YAML-based scenarios** - Define complex test workflows in simple YAML
- 📸 **Screenshot capture** - Automated SVG screenshot support for TUI apps
- 🔄 **File-based triggers** - Inject events into running apps via trigger files
- ⏱️ **Sentinel monitoring** - Wait for async events with pattern matching
- 🐚 **pexpect integration** - Full control over interactive CLI processes
- 🔍 **Validation system** - Verify file existence and content automatically
- 🎨 **Workspace isolation** - Run tests in isolated environments
- 📊 **JUnit XML reports** - CI/CD integration with standard test reporting
- 🧠 **Intelligent test generation** - Automatically analyze apps and generate test scenarios (NEW!)

## 🚀 Quick Start

### Installation

```bash
# From PyPI (when published)
pip install orchestro-cli

# From source
git clone https://github.com/vyb/orchestro-cli
cd orchestro-cli
pip install -e .
```

### Your First Test

Create a scenario file `my_test.yaml`:

```yaml
name: Simple CLI Test
description: Test a basic command-line app
command: ./my_app
timeout: 30

steps:
  # Wait for app to start
  - note: "Waiting for app initialization..."

  # Capture a screenshot
  - screenshot: "startup-state"
    timeout: 10
    note: "Capturing startup screen..."

  # Send a command
  - send: "help"
    note: "Requesting help..."

  # Capture result
  - screenshot: "help-screen"
    timeout: 10

validations:
  - type: path_exists
    path: artifacts/screenshots/startup-state.svg
    description: "Startup screenshot created"

  - type: path_exists
    path: artifacts/screenshots/help-screen.svg
    description: "Help screenshot created"
```

Run it:

```bash
# Basic run
orchestro my_test.yaml --verbose

# With JUnit XML report for CI/CD
orchestro my_test.yaml --junit-xml=test-results/junit.xml
```

## 🧠 Intelligent Test Generation (NEW!)

Orchestro CLI can now automatically analyze your TUI application and generate test scenarios:

```bash
# Analyze your Textual app
orchestro index ./my_app --framework textual

# Generate test scenarios
orchestro generate .orchestro/index.json --type smoke

# Run generated tests
orchestro tests/generated/*.yaml
```

**Learn more**: See [Intelligence Guide](docs/INTELLIGENCE.md) for complete documentation.

**Key capabilities:**
- AST-based code analysis for Python apps
- Automatic screen and keybinding detection
- Test scenario generation from code structure
- Support for Textual, Click, and Argparse frameworks
- Customizable generation templates

## 📚 Scenario Reference

### Basic Structure

```yaml
name: Scenario Name
description: What this scenario tests
command: ./executable  # Can be string or list
timeout: 30  # Global timeout in seconds

env:  # Optional environment variables
  MY_VAR: value

steps:
  - # ... step definitions

validations:
  - # ... validation definitions
```

### Step Types

#### 1. Wait for Pattern (expect)

```yaml
- expect: "Ready|Started"  # Regex pattern
  timeout: 10
  note: "Waiting for app to be ready..."
```

Alias: `pattern` can be used instead of `expect`

#### 2. Send Input

```yaml
- send: "/help"
  note: "Sending help command"

- send: "raw input"
  raw: true  # Don't add newline
```

#### 3. Send Control Character

```yaml
- control: "c"  # Ctrl+C
  note: "Interrupting process"
```

#### 4. Capture Screenshot

```yaml
- screenshot: "my-screenshot"
  timeout: 15
  note: "Capturing current state..."
```

Screenshots are saved to `artifacts/screenshots/{name}.svg`

### Validations

#### Path Exists

```yaml
- type: path_exists
  path: artifacts/screenshots/screenshot.svg
  description: "Screenshot was created"
```

#### File Contains

```yaml
- type: file_contains
  path: output.log
  text: "Success.*completed"  # Regex pattern
  description: "Log shows success"
```

## 🎨 Screenshot & Sentinel Support

Orchestro CLI supports automated screenshot capture and sentinel-based waiting for TUI apps using a file-based trigger mechanism. The end-to-end contract, metrics, and telemetry requirements are defined in [`docs/SCREENSHOT_SENTINEL_SPEC.md`](docs/SCREENSHOT_SENTINEL_SPEC.md).

### How It Works

1. **App Setup** - Your TUI app monitors the screenshot trigger directory
2. **Trigger** - Orchestro creates `{name}.trigger` files
3. **Capture** - App detects trigger and saves screenshot
4. **Verify** - Orchestro validates screenshot was created

Every screenshot and sentinel wait step emits a structured JSON event to `runlog.jsonl`, including the trigger timestamp, detection timestamp, and latency (in seconds). This telemetry enables CI pipelines to enforce the latency guardrails described in the spec.

**Cross-Platform Support:** Orchestro automatically uses the appropriate temporary directory for your OS:
- Linux/macOS: `$TMPDIR/.vyb_orchestro/screenshot_triggers/` (usually `/tmp/.vyb_orchestro/`)
- Windows: `%TEMP%\.vyb_orchestro\screenshot_triggers\`

### Integrating with Your App

For Textual apps:

```python
import os
import tempfile
from pathlib import Path
from textual.app import App

class MyApp(App):
    def on_mount(self) -> None:
        # Enable screenshot monitoring
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
                trigger_file.unlink()
            except Exception:
                pass

    def _capture_screenshot(self, name: str) -> None:
        """Capture screenshot SVG."""
        screenshot_dir = Path.cwd() / "artifacts" / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{name}.svg" if not name.endswith(".svg") else name
        self.save_screenshot(filename=filename, path=str(screenshot_dir))
```

## 🔧 Advanced Usage

### CI/CD Integration

Generate JUnit XML reports for continuous integration:

```bash
orchestro test.yaml --junit-xml=test-results/junit.xml
```

Perfect for:
- GitHub Actions
- GitLab CI
- Jenkins
- Azure DevOps
- CircleCI

See [`docs/JUNIT_INTEGRATION.md`](docs/JUNIT_INTEGRATION.md) for detailed CI/CD integration guides.

### Workspace Isolation

Run tests in isolated environments:

```bash
orchestro test.yaml --workspace /tmp/test-workspace
```

This creates:
- `/tmp/test-workspace/home` - Isolated HOME directory
- `/tmp/test-workspace/data` - Isolated data directory

### Programmatic Usage

```python
from orchestro_cli import ScenarioRunner
from pathlib import Path

runner = ScenarioRunner(
    scenario_path=Path("my_scenario.yaml"),
    workspace=Path("/tmp/test-workspace"),
    verbose=True,
    junit_xml_path=Path("test-results/junit.xml")  # Optional: Generate JUnit XML
)

runner.run()
```

### Sentinel Monitoring

Wait for async events with sentinel patterns:

```yaml
steps:
  - expect: "[PROMPT]"  # Sentinel pattern
    timeout: 20
    note: "Waiting for prompt sentinel..."
```

Requires your app to write sentinel markers to `/tmp/.vyb_orchestro_sentinels`

## 📖 Examples

### Example 1: Screenshot Gallery

```yaml
name: Screenshot Gallery Test
command: ./my_tui_app
timeout: 60

steps:
  - screenshot: "01-startup"
    timeout: 10

  - send: "/settings"
  - screenshot: "02-settings"
    timeout: 10

  - send: "/dashboard"
  - screenshot: "03-dashboard"
    timeout: 10

validations:
  - type: path_exists
    path: artifacts/screenshots/01-startup.svg
  - type: path_exists
    path: artifacts/screenshots/02-settings.svg
  - type: path_exists
    path: artifacts/screenshots/03-dashboard.svg
```

### Example 2: Interactive Session

```yaml
name: Interactive CLI Test
command: ["python", "-i"]
timeout: 30

steps:
  - expect: ">>>"
    timeout: 5
    note: "Waiting for Python prompt..."

  - send: "print('Hello, World!')"
    note: "Executing Python code..."

  - expect: "Hello, World!"
    timeout: 2

  - send: "exit()"
    note: "Exiting Python..."
```

### Example 3: File Validation

```yaml
name: Output Validation Test
command: ./data_processor
timeout: 60

steps:
  - send: "process --input data.csv"
  - expect: "Processing complete"
    timeout: 30

validations:
  - type: path_exists
    path: output/results.csv
    description: "Results file created"

  - type: file_contains
    path: output/results.csv
    text: "Success,\\d+ records processed"
    description: "Results show success"
```

## 🏗️ Architecture

```
orchestro-cli/
├── orchestro_cli/
│   ├── __init__.py          # Package exports
│   ├── cli.py               # CLI entry point
│   ├── runner.py            # Core scenario runner
│   └── sentinel_monitor.py  # Async event monitoring
├── examples/
│   └── screenshot_example.yaml
├── docs/
│   └── API.md
├── pyproject.toml
└── README.md
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🐛 Troubleshooting

### Screenshots not capturing

1. Ensure `VYB_AUTO_SCREENSHOT=1` environment variable is set (Orchestro sets this automatically)
2. Verify your app monitors the correct trigger directory (use `tempfile.gettempdir()`)
3. Check app has screenshot monitoring enabled
4. Increase timeout values in scenario

### Process hangs on expect

1. Use `.*` pattern to match any output
2. Increase timeout value
3. Enable verbose mode to see what's happening
4. For TUI apps, avoid expect patterns - use time delays instead

### Validation fails

1. Check paths are relative to correct base directory
2. Use `artifacts/` prefix for screenshot paths
3. Verify files are created before validation runs
4. Check regex patterns in `file_contains` validations

## 🔗 Related Projects

- [pexpect](https://pexpect.readthedocs.io/) - Python expect library
- [Textual](https://textual.textualize.io/) - TUI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting

## 💬 Support

- Issues: https://github.com/vyb/orchestro-cli/issues
- Discussions: https://github.com/vyb/orchestro-cli/discussions
- Documentation: https://orchestro-cli.readthedocs.io/

---

Made with ❤️ by the VyB Project
