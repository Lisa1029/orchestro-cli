# Orchestro Intelligence System Demo

This directory contains a complete demonstration of Orchestro's intelligent test generation capabilities.

## Overview

The Orchestro Intelligence System can:

1. **Analyze** TUI applications to discover their structure
2. **Extract** screens, keybindings, widgets, and navigation paths
3. **Generate** comprehensive test scenarios automatically
4. **Execute** the generated tests

## Quick Start

```bash
# Run the demo
python examples/demo_intelligence.py

# Run with test execution (requires textual)
pip install textual
python examples/demo_intelligence.py --execute
```

## What's Included

### Sample TUI Application

**Location**: `examples/sample_tui_app/app.py`

A complete Textual application featuring:
- **3 Screens**: MainMenu, Settings, Dashboard
- **Keybindings**: Navigate with keyboard shortcuts (s, d, q, escape)
- **Widgets**: Buttons, Switches, DataTable, Header, Footer
- **Navigation**: Screen transitions with push/pop

You can run it standalone:

```bash
python examples/sample_tui_app/app.py
```

### Intelligence Demo Script

**Location**: `examples/demo_intelligence.py`

Demonstrates the complete workflow:

1. **Analysis Phase**
   - Scans Python files for Textual components
   - Discovers screens using AST analysis
   - Extracts keybindings from BINDINGS declarations
   - Identifies widgets from compose() methods
   - Maps navigation paths between screens

2. **Knowledge Extraction**
   - Builds complete application model
   - Saves knowledge to JSON for inspection
   - Supports serialization/deserialization

3. **Test Generation**
   - Creates smoke tests (visit all screens)
   - Generates keybinding tests (verify shortcuts)
   - Produces navigation tests (screen transitions)

4. **Test Execution** (optional)
   - Runs generated scenarios with Orchestro
   - Validates application behavior
   - Captures screenshots

## Sample Output

```
================================================================================
            🧠 Orchestro Intelligence System Demonstration
================================================================================

This demo shows how Orchestro can automatically analyze a TUI app
and generate comprehensive test scenarios.

📂 Sample App: /path/to/examples/sample_tui_app
📂 Output Dir: /path/to/examples/generated_tests

────────────────────────────────────────────────────────────────────────────────
📍 STEP 1: Analyzing TUI Application
────────────────────────────────────────────────────────────────────────────────

🔍 Scanning Python files for Textual components...

✅ Analysis Complete!

📊 Discovery Results:
   • Total Screens: 3
   • Entry Screen: MainMenuScreen
   • Navigation Paths: 4

🖥️  Discovered Screens:

   MainMenuScreen:
      Class: MainMenuScreen
      File: app.py
      Keybindings: 3
         • s          → Settings
         • d          → Dashboard
         • q          → Quit
      Widgets: 7
         • 1× Header
         • 1× Footer
         • 1× Container
         • 2× Static
         • 1× Horizontal
         • 3× Button
      Navigation Targets: settings, dashboard

   SettingsScreen:
      Class: SettingsScreen
      File: app.py
      Keybindings: 2
         • escape     → Back
         • q          → Quit
      Widgets: 9
         • 1× Header
         • 1× Footer
         • 3× Switch
         • 3× Label
         • ...

   DashboardScreen:
      Class: DashboardScreen
      File: app.py
      Keybindings: 3
         • escape     → Back
         • r          → Refresh
         • q          → Quit
      Widgets: 8
         • 1× Header
         • 1× Footer
         • 1× DataTable
         • ...

────────────────────────────────────────────────────────────────────────────────
📍 STEP 3: Generating Test Scenarios
────────────────────────────────────────────────────────────────────────────────

🎭 Creating test scenarios based on discovered structure...

📝 Generating:
   1. Smoke Test (visit all screens)
   2. Keybinding Test (verify all shortcuts)
   3. Navigation Test (test screen transitions)

✅ Generated 3 test files:

   📄 smoke_test.yaml (1428 bytes)
   📄 keybinding_test.yaml (2156 bytes)
   📄 navigation_test.yaml (1834 bytes)
```

## Generated Test Files

All generated tests are saved to `examples/generated_tests/`:

### 1. Smoke Test

**Purpose**: Visit every screen and capture screenshots

```yaml
name: Smoke Test - Visit All Screens
description: Automatically generated smoke test...
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

  - name: Return from SettingsScreen
    keystroke: escape

  # ... more screens ...

  - name: Quit application
    keystroke: q
```

### 2. Keybinding Test

**Purpose**: Verify all keyboard shortcuts work

```yaml
name: Keybinding Test - Verify All Shortcuts
steps:
  - name: Test s -> Settings
    keystroke: s

  - name: Capture after s
    screenshot: mainmenuscreen_s.png

  - name: Return to previous screen
    keystroke: escape

  # ... more keybindings ...
```

### 3. Navigation Test

**Purpose**: Test screen transition paths

```yaml
name: Navigation Test - Verify Screen Transitions
steps:
  - name: Navigate: MainMenuScreen → settings
    comment: Path cost: 1

  - name: Press s
    keystroke: s

  - name: Verify settings reached
    screenshot: nav_MainMenuScreen_to_settings.png

  # ... more paths ...
```

## Running Generated Tests

### Manual Execution

```bash
# Run individual tests
orchestro examples/generated_tests/smoke_test.yaml
orchestro examples/generated_tests/keybinding_test.yaml
orchestro examples/generated_tests/navigation_test.yaml

# With verbose output
orchestro examples/generated_tests/smoke_test.yaml --verbose

# Save screenshots
orchestro examples/generated_tests/smoke_test.yaml --screenshot-dir ./screenshots
```

### Automated Execution

```bash
# Run all tests in directory
for test in examples/generated_tests/*.yaml; do
    orchestro "$test"
done

# Or use the demo script
python examples/demo_intelligence.py --execute
```

## Understanding the Analysis

### AST Analyzer

The `ASTAnalyzer` uses Python's Abstract Syntax Tree to:

- **Find Screen classes**: Identifies classes inheriting from `Screen`
- **Parse BINDINGS**: Extracts keybindings from class variables
- **Analyze compose()**: Discovers widgets yielded in compose methods
- **Track navigation**: Identifies `push_screen()` and `pop_screen()` calls

### Knowledge Model

The extracted knowledge is stored in structured models:

```python
AppKnowledge
├── screens: Dict[str, ScreenInfo]
│   ├── MainMenuScreen
│   │   ├── keybindings: List[KeybindingInfo]
│   │   ├── widgets: List[WidgetInfo]
│   │   └── navigation_targets: Set[str]
│   ├── SettingsScreen
│   └── DashboardScreen
├── entry_screen: str
└── navigation_paths: List[NavigationPath]
```

### Scenario Generator

The `ScenarioGenerator` creates tests by:

1. **Smoke Tests**: Traverse all screens using discovered navigation
2. **Keybinding Tests**: Exercise each keybinding and verify response
3. **Navigation Tests**: Validate screen transition paths

## Customization

### Modify the Sample App

Edit `examples/sample_tui_app/app.py` to:
- Add more screens
- Create new keybindings
- Add different widgets
- Change navigation logic

Then re-run the demo to see updated test generation.

### Extend the Generator

Edit `orchestro_cli/intelligence/generation/scenario_generator.py` to:
- Add new test types
- Customize scenario structure
- Include validation steps
- Add setup/teardown logic

### Custom Analysis

Create your own analyzer by:

```python
from orchestro_cli.intelligence import ASTAnalyzer
from pathlib import Path

analyzer = ASTAnalyzer()
knowledge = await analyzer.analyze_project(Path("./my_app"))

# Inspect discovered structure
for screen_name, screen in knowledge.screens.items():
    print(f"Screen: {screen_name}")
    for kb in screen.keybindings:
        print(f"  {kb.key} -> {kb.action}")
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: TUI Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Install dependencies
        run: |
          pip install -e .
          pip install textual

      - name: Generate tests
        run: python examples/demo_intelligence.py

      - name: Run smoke test
        run: orchestro examples/generated_tests/smoke_test.yaml

      - name: Upload screenshots
        uses: actions/upload-artifact@v2
        with:
          name: screenshots
          path: test_output/*.png
```

## Best Practices

1. **Version Control**: Commit generated tests to track changes
2. **Regular Updates**: Regenerate tests when UI changes
3. **Manual Review**: Review generated tests before production use
4. **Customization**: Extend generated tests with app-specific validations
5. **Screenshots**: Compare screenshots for visual regression testing

## Troubleshooting

### Demo Won't Run

```bash
# Make sure you're in the project root
cd /path/to/orchestro

# Install in development mode
pip install -e .

# Run demo
python examples/demo_intelligence.py
```

### Sample App Won't Start

```bash
# Install Textual
pip install textual

# Test the app directly
python examples/sample_tui_app/app.py
```

### Generated Tests Fail

- Ensure sample app is installed: `pip install textual`
- Check Orchestro is installed: `pip install -e .`
- Verify Python path includes orchestro_cli
- Try running with `--verbose` flag

## Next Steps

1. **Try with Your App**: Point the analyzer at your own TUI application
2. **Customize Tests**: Modify generated scenarios for your needs
3. **Add Validations**: Include assertions and checks
4. **Automate**: Integrate into your CI/CD pipeline
5. **Contribute**: Share improvements with the community

## API Reference

### ASTAnalyzer

```python
class ASTAnalyzer:
    async def analyze_project(self, project_path: Path) -> AppKnowledge:
        """Analyze a project directory."""
```

### ScenarioGenerator

```python
class ScenarioGenerator:
    def __init__(self, knowledge: AppKnowledge):
        """Initialize with app knowledge."""

    def generate_smoke_test(self) -> str:
        """Generate smoke test YAML."""

    def generate_keybinding_test(self) -> str:
        """Generate keybinding test YAML."""

    def generate_navigation_test(self) -> str:
        """Generate navigation test YAML."""

    def generate_all_tests(self, output_dir: Path) -> List[Path]:
        """Generate all tests to directory."""
```

### AppKnowledge

```python
class AppKnowledge:
    project_path: Path
    screens: Dict[str, ScreenInfo]
    entry_screen: Optional[str]
    navigation_paths: List[NavigationPath]

    def to_dict(self) -> dict:
        """Serialize to dictionary."""

    @classmethod
    def from_dict(cls, data: dict) -> AppKnowledge:
        """Deserialize from dictionary."""
```

## Support

- **Documentation**: See `docs/INTELLIGENCE_SYSTEM.md`
- **Issues**: Report bugs on GitHub
- **Discussions**: Join the community forum
- **Examples**: More examples in `examples/` directory
