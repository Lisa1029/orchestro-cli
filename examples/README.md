# Orchestro CLI Examples

This directory contains comprehensive, production-quality examples demonstrating various capabilities of the Orchestro CLI testing framework.

## 🆕 Intelligence System Demo

**NEW**: Orchestro can now automatically analyze TUI applications and generate test scenarios!

```bash
# Run the intelligence demo
python examples/demo_intelligence.py

# See detailed documentation
cat examples/INTELLIGENCE_DEMO.md
```

See the [Intelligence Demo](#intelligence-system-demo) section below for details.

## Quick Start

Run any example with:

```bash
orchestro examples/<example-name>.yaml --verbose
```

## Example Catalog

### 1. **basic_echo.yaml** - Simplest Test
**Difficulty**: Beginner
**Runtime**: ~5 seconds
**Requirements**: Standard Unix `echo` command

Demonstrates the absolute basics of Orchestro testing:
- Running a simple command
- Using `expect` to wait for output
- Basic timeout configuration
- Pattern matching with regex

**Learn**: Fundamentals of expect patterns and timeouts

**Run**:
```bash
orchestro examples/basic_echo.yaml --verbose
```

---

### 2. **python_repl.yaml** - Interactive Session
**Difficulty**: Beginner
**Runtime**: ~30 seconds
**Requirements**: Python 3.x

Demonstrates interactive command-line testing:
- Waiting for prompts with expect patterns
- Sending commands to interactive shells
- Multiple expect/send cycles
- Proper session cleanup

**Learn**: How to test interactive CLI applications with continuous expect/send patterns

**Run**:
```bash
orchestro examples/python_repl.yaml --verbose
```

**What it does**:
- Starts Python REPL
- Performs calculations
- Defines and calls functions
- Imports modules
- Validates outputs
- Exits cleanly

---

### 3. **file_validation.yaml** - File Operations & Validation
**Difficulty**: Beginner-Intermediate
**Runtime**: ~10 seconds
**Requirements**: Bash shell, standard Unix utilities

Demonstrates file creation and validation:
- Creating files via shell commands
- `path_exists` validation type
- `file_contains` validation with regex patterns
- Multi-file validation workflows

**Learn**: How to validate file creation and content in tests

**Run**:
```bash
orchestro examples/file_validation.yaml --verbose
```

**Validates**:
- File existence checks
- Content pattern matching
- Multiple file validation
- Regex-based content validation

**Cleanup**:
```bash
rm -rf test_output/
```

---

### 4. **multi_step_workflow.yaml** - Complex Pipeline
**Difficulty**: Intermediate-Advanced
**Runtime**: ~60 seconds
**Requirements**: Bash shell with standard utilities

Demonstrates a complete data processing pipeline:
- Multi-phase workflow execution
- Directory creation and management
- Data transformation
- Environment variable usage
- Comprehensive validation

**Learn**: How to build complex, real-world testing scenarios

**Run**:
```bash
orchestro examples/multi_step_workflow.yaml --verbose
```

**Pipeline Phases**:
1. **Setup**: Create directory structure
2. **Data Creation**: Generate sample CSV data
3. **Processing**: Transform and analyze data
4. **Reporting**: Generate summary statistics
5. **Validation**: Verify outputs

**What it creates**:
- `pipeline/input/data.csv` - Sample data
- `pipeline/output/transformed.csv` - Processed data
- `pipeline/output/summary.txt` - Statistics report
- `pipeline/logs/execution.log` - Execution log

**Cleanup**:
```bash
rm -rf pipeline/
```

---

### 5. **screenshot_gallery.yaml** - TUI Screenshot Testing
**Difficulty**: Advanced
**Runtime**: ~90 seconds
**Requirements**: TUI application with screenshot support

Demonstrates automated screenshot capture for Terminal User Interfaces:
- Automated screenshot capture at different stages
- Screenshot trigger mechanism
- Screenshot file validation
- TUI navigation patterns

**Learn**: How to test TUI applications with visual verification

**IMPORTANT**: This is a **template example**. You must:
1. Replace `./your_tui_app` with your actual TUI application
2. Customize the `send` steps to match your app's key bindings
3. Ensure your app implements screenshot trigger monitoring

**Integration Required**: Your TUI app needs to monitor for trigger files and save screenshots. See the example for implementation code.

**Run** (after customization):
```bash
orchestro examples/screenshot_gallery.yaml --verbose
```

**Screenshots captured**:
- Startup state
- Main screen
- Settings/menu
- Dashboard
- Action results
- Help screen
- Final state

All screenshots saved to: `artifacts/screenshots/*.svg`

---

### 6. **timeout_handling.yaml** - Timeout Configuration
**Difficulty**: Intermediate
**Runtime**: ~120 seconds
**Requirements**: Bash shell with `sleep` command

Demonstrates timeout configuration and best practices:
- Global vs step-specific timeouts
- Quick operations (1-5s timeouts)
- Medium operations (5-15s timeouts)
- Long operations (15-30s timeouts)
- Very slow operations (30-60s timeouts)

**Learn**: How to properly configure timeouts for different operation types

**Run**:
```bash
orchestro examples/timeout_handling.yaml --verbose
```

**Demonstrates**:
- Instant operations with 1-2s timeouts
- Sleep commands with appropriate timeout buffers
- Sequential multi-step operations
- Extended timeouts for slow operations
- Best practices for timeout selection

**Creates**: `timeout_test_results.txt` with timing information

**Cleanup**:
```bash
rm -f timeout_test_results.txt
rm -rf artifacts/
```

---

### 7. **environment_vars.yaml** - Environment Variables
**Difficulty**: Intermediate
**Runtime**: ~30 seconds
**Requirements**: Bash shell

Demonstrates environment variable usage:
- Setting custom environment variables
- Using variables in commands
- Accessing Orchestro auto-set variables
- Environment-based configuration
- Variable validation

**Learn**: How to configure and use environment variables in scenarios

**Run**:
```bash
orchestro examples/environment_vars.yaml --verbose
```

**Environment Variables Demonstrated**:
- **Application Config**: APP_NAME, APP_VERSION, APP_ENV
- **Feature Flags**: ENABLE_LOGGING, ENABLE_DEBUG, ENABLE_METRICS
- **Paths**: DATA_DIR, LOG_FILE, CONFIG_PATH
- **API Config**: API_ENDPOINT, API_KEY, API_TIMEOUT
- **Database Config**: DB_HOST, DB_PORT, DB_NAME, DB_USER
- **Performance**: MAX_WORKERS, BATCH_SIZE, RETRY_COUNT

**Creates**:
- `env_test_config.ini` - Generated configuration file
- `env_test_report.txt` - Comprehensive environment report
- `/tmp/orchestro-data/` - Data directory

**Cleanup**:
```bash
rm -f env_test_config.ini env_test_report.txt
rm -rf /tmp/orchestro-data/
```

---

### 8. **screenshot_example.yaml** - VyB Continue (Original)
**Difficulty**: Advanced
**Runtime**: ~30 seconds
**Requirements**: VyB Continue TUI application (`./vyb_cn`)

Original example for the VyB Continue application. Demonstrates:
- Screenshot-only testing (no expect patterns)
- File trigger mechanism
- Time-based screenshot capture

**Run** (requires VyB Continue app):
```bash
orchestro examples/screenshot_example.yaml --verbose
```

---

## Example Progression Path

### Learning Path for New Users:

1. **Start Here**: `basic_echo.yaml`
   - Learn expect patterns and basic scenarios

2. **Interactive Sessions**: `python_repl.yaml`
   - Learn expect/send cycles for interactive apps

3. **File Operations**: `file_validation.yaml`
   - Learn file creation and content validation

4. **Environment Setup**: `environment_vars.yaml`
   - Learn environment variable configuration

5. **Timeout Mastery**: `timeout_handling.yaml`
   - Learn proper timeout configuration

6. **Complex Workflows**: `multi_step_workflow.yaml`
   - Learn multi-phase testing scenarios

7. **TUI Testing**: `screenshot_gallery.yaml`
   - Learn screenshot-based TUI testing

---

## Common Patterns

### Expect/Send Pattern
```yaml
steps:
  - expect: "prompt>"
    timeout: 5
  - send: "command"
  - expect: "output"
    timeout: 3
```

### Screenshot Pattern
```yaml
steps:
  - screenshot: "screen-name"
    timeout: 15
    note: "Capturing screen..."
```

### Validation Pattern
```yaml
validations:
  - type: path_exists
    path: output/file.txt
  - type: file_contains
    path: output/file.txt
    text: "expected.*pattern"
```

### Environment Variables Pattern
```yaml
env:
  VAR_NAME: "value"
  ENABLE_FEATURE: "true"
```

---

## Testing Tips

### Debugging Tests

Run with verbose output to see what's happening:
```bash
orchestro examples/example.yaml --verbose
```

### Common Issues

**Screenshots not captured**:
- Ensure `VYB_AUTO_SCREENSHOT=1` is set (Orchestro does this automatically)
- Verify your app monitors trigger directory
- Increase screenshot timeouts
- Check app logs for errors

**Expect timeouts**:
- Increase timeout values
- Check pattern regex is correct
- Use `.*` to match any output for debugging
- Enable verbose mode to see actual output

**File validations fail**:
- Check paths are relative to correct base
- Use `artifacts/` prefix for screenshots
- Verify files created before validation runs
- Check regex patterns are escaped correctly

### Best Practices

1. **Start simple**: Begin with basic examples and add complexity
2. **Use verbose mode**: Always use `--verbose` during development
3. **Test timeouts**: Add 20-30% buffer to expected operation times
4. **Validate liberally**: Add validations for all important outputs
5. **Document scenarios**: Add clear `description` and `note` fields
6. **Clean up**: Remove test artifacts after running examples
7. **Version control**: Commit working scenarios to track changes

---

## Creating Your Own Scenarios

### Scenario Template

```yaml
name: My Test Scenario
description: |
  What this test does and what it demonstrates.
  Requirements and prerequisites.

command: ./my_command
timeout: 30

env:
  MY_VAR: "value"

steps:
  - expect: "pattern"
    timeout: 5
    note: "What this step does..."

  - send: "input"
    note: "Sending input..."

  - screenshot: "name"
    timeout: 15
    note: "Capturing screenshot..."

validations:
  - type: path_exists
    path: output/file.txt
    description: "File was created"

  - type: file_contains
    path: output/file.txt
    text: "expected.*content"
    description: "File has correct content"
```

### Step Types Reference

| Step Type | Usage | Purpose |
|-----------|-------|---------|
| `expect` | Wait for pattern | Match output with regex |
| `send` | Send input | Provide input to process |
| `control` | Send Ctrl+X | Send control characters |
| `screenshot` | Capture screen | Save TUI screenshot |
| `note` | Add comment | Document step purpose |

### Validation Types Reference

| Validation | Required Fields | Purpose |
|------------|----------------|---------|
| `path_exists` | `path` | Verify file/directory exists |
| `file_contains` | `path`, `text` | Verify file content with regex |

---

## Advanced Topics

### Workspace Isolation

Run tests in isolated environments:

```bash
orchestro examples/example.yaml --workspace /tmp/test-workspace
```

This creates:
- `/tmp/test-workspace/home` - Isolated HOME directory
- `/tmp/test-workspace/data` - Isolated data directory

### Programmatic Usage

```python
from orchestro_cli import ScenarioRunner
from pathlib import Path

runner = ScenarioRunner(
    scenario_path=Path("examples/basic_echo.yaml"),
    workspace=Path("/tmp/test-workspace"),
    verbose=True
)

runner.run()
```

### Sentinel Monitoring

For advanced async event handling, use sentinel patterns:

```yaml
steps:
  - expect: "[PROMPT]"  # Sentinel pattern
    timeout: 20
    note: "Waiting for prompt sentinel..."
```

Requires your app to write sentinel markers to the sentinel file.

---

## Contributing Examples

Have a useful example? Please contribute!

1. Create a well-documented YAML file
2. Include comprehensive comments
3. Add validation checks
4. Test it works standalone
5. Update this README
6. Submit a pull request

---

## Intelligence System Demo

### Overview

Orchestro's Intelligence System can automatically analyze Textual TUI applications and generate comprehensive test scenarios. This eliminates the manual effort of writing tests and ensures complete coverage.

### Quick Start

```bash
# 1. Run the intelligence demo
python examples/demo_intelligence.py

# 2. Try the sample app
pip install textual
python examples/sample_tui_app/app.py

# 3. Run generated tests
orchestro examples/generated_tests/smoke_test.yaml
```

### What It Does

The intelligence system:

1. **Analyzes** your TUI app using AST (Abstract Syntax Tree) analysis
2. **Discovers** screens, keybindings, widgets, and navigation paths
3. **Generates** three types of test scenarios:
   - **Smoke Tests**: Visit all screens, capture screenshots
   - **Keybinding Tests**: Verify all keyboard shortcuts
   - **Navigation Tests**: Validate screen transitions

### Sample Output

```
🧠 Orchestro Intelligence System Demonstration

📍 STEP 1: Analyzing TUI Application
✅ Analysis Complete!
   • Total Screens: 3
   • Entry Screen: MainMenuScreen
   • Navigation Paths: 2

📍 STEP 3: Generating Test Scenarios
✅ Generated 3 test files:
   📄 smoke_test.yaml
   📄 keybinding_test.yaml
   📄 navigation_test.yaml
```

### Directory Structure

```
examples/
├── demo_intelligence.py          # Main demo script
├── sample_tui_app/              # Sample Textual app
│   ├── app.py                   # 3-screen TUI application
│   └── README.md               # App documentation
├── generated_tests/             # Auto-generated tests
│   ├── smoke_test.yaml         # Generated smoke test
│   ├── keybinding_test.yaml    # Generated keybinding test
│   ├── navigation_test.yaml    # Generated navigation test
│   └── app_knowledge.json      # Extracted knowledge
└── INTELLIGENCE_DEMO.md         # Detailed documentation
```

### Use With Your App

```python
from pathlib import Path
from orchestro_cli.intelligence import ASTAnalyzer, ScenarioGenerator

# Analyze your TUI app
analyzer = ASTAnalyzer()
knowledge = await analyzer.analyze_project(Path("./my_app"))

# Generate tests
generator = ScenarioGenerator(knowledge)
generated_files = generator.generate_all_tests(Path("./tests"))

# Run tests
# orchestro tests/smoke_test.yaml
```

### Integration Tests

```bash
# Verify the system works end-to-end
python -m pytest tests/integration/test_intelligence_e2e.py --integration -v
```

All 12 integration tests validate:
- ✅ Screen discovery
- ✅ Keybinding extraction
- ✅ Widget identification
- ✅ Navigation mapping
- ✅ Test generation
- ✅ YAML validation
- ✅ Knowledge serialization

### Documentation

- **Detailed Guide**: [INTELLIGENCE_DEMO.md](INTELLIGENCE_DEMO.md)
- **Sample App**: [sample_tui_app/README.md](sample_tui_app/README.md)
- **API Documentation**: See source code docstrings

### Requirements

- **Python**: 3.8+
- **For Demo**: `pip install textual`
- **For Testing**: Orchestro CLI installed

### Example Generated Test

```yaml
name: Smoke Test - Visit All Screens
steps:
  - name: Start application
    command: python /path/to/app.py
    timeout: 5
  - name: Capture MainMenuScreen screenshot
    screenshot: mainmenuscreen_screen.png
  - name: Navigate to SettingsScreen using s
    keystroke: s
  - name: Capture SettingsScreen screenshot
    screenshot: settingsscreen_screen.png
  # ... more screens ...
  - name: Quit application
    keystroke: q
```

---

## Support

- **Documentation**: [Main README](../README.md)
- **API Reference**: [docs/API.md](../docs/API.md)
- **Issues**: https://github.com/vyb/orchestro-cli/issues
- **Intelligence System**: [INTELLIGENCE_DEMO.md](INTELLIGENCE_DEMO.md)

---

**Happy Testing with Orchestro CLI!**
