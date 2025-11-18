# Intelligent Test Generation Guide

**Version:** 0.3.0 (NEW)

Orchestro CLI includes intelligent test generation capabilities that automatically analyze your application code and generate comprehensive test scenarios. This guide covers everything you need to know about using Orchestro's intelligence features.

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Indexing Applications](#indexing-applications)
- [Test Generation](#test-generation)
- [CLI Reference](#cli-reference)
- [Integration](#integration)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

---

## Overview

### What is Intelligent Test Generation?

Orchestro's intelligence system analyzes your application's source code to understand its structure, then automatically generates test scenarios. This saves you time and ensures comprehensive test coverage.

**Key Features:**
- **AST-based Analysis**: Parse Python source code to extract application structure
- **Framework Detection**: Automatically identify Textual, Click, Argparse, and other frameworks
- **Screen Mapping**: Discover all screens, widgets, and navigation paths in TUI apps
- **Keybinding Detection**: Extract all keyboard shortcuts and commands
- **Smart Generation**: Create scenarios based on code patterns and best practices
- **Quality Scoring**: Rate generated tests by confidence and coverage

### Why Use It?

**Manual test writing:**
```yaml
# You write this by hand for every screen...
name: Test Main Menu
steps:
  - screenshot: "main-menu"
  - send: "s"
  - screenshot: "settings"
  # ... 50 more screens
```

**Intelligent generation:**
```bash
# Orchestro analyzes your app and generates all scenarios
orchestro index ./my_app --framework textual
orchestro generate .orchestro/index.json --type coverage

# Creates:
# - tests/smoke/01_startup.yaml
# - tests/smoke/02_main_menu.yaml
# - tests/coverage/settings_screen.yaml
# - tests/coverage/help_screen.yaml
# ... (all screens automatically discovered)
```

### Supported Frameworks

| Framework | Analysis Level | Features Detected |
|-----------|---------------|-------------------|
| **Textual** | Full | Screens, widgets, keybindings, actions, mounts |
| **Click** | Full | Commands, options, arguments, groups |
| **Argparse** | Full | Parsers, subcommands, arguments, flags |
| **Rich** | Partial | Layout, console output, panels |
| **Custom** | Extensible | Write your own extractors |

---

## Quick Start

### 5-Minute Tutorial

Let's automatically test a Textual application:

#### 1. Analyze Your App

```bash
# Point Orchestro at your app's source code
orchestro index ./my_tui_app --framework textual
```

Output:
```
Analyzing application...
  Found: 8 screens
  Found: 23 keybindings
  Found: 12 actions
  Found: 5 navigation paths

Index saved to: .orchestro/index.json
```

#### 2. Generate Tests

```bash
# Generate smoke tests (basic coverage)
orchestro generate .orchestro/index.json --type smoke --output tests/smoke/
```

Output:
```
Generated 5 scenarios:
  ✓ tests/smoke/01_app_startup.yaml
  ✓ tests/smoke/02_main_navigation.yaml
  ✓ tests/smoke/03_screen_rendering.yaml
  ✓ tests/smoke/04_keybindings.yaml
  ✓ tests/smoke/05_teardown.yaml

Quality: 87% confidence, 65% coverage
```

#### 3. Run Tests

```bash
# Execute generated scenarios
orchestro tests/smoke/*.yaml --verbose
```

**That's it!** You now have automated tests without writing a single line of YAML.

---

## Indexing Applications

### The `orchestro index` Command

Indexing analyzes your application and creates a knowledge base.

**Basic Usage:**
```bash
orchestro index <path> --framework <framework> [options]
```

### Framework-Specific Indexing

#### Textual Applications

```bash
orchestro index ./my_app --framework textual --output .orchestro/index.json
```

**What it extracts:**
- All `Screen` classes
- Widget hierarchy
- Keybindings (`@on(Key)` decorators)
- Actions (`action_*` methods)
- Mount points and composition
- CSS classes and IDs

**Example Output:**
```json
{
  "framework": "textual",
  "version": "0.3.0",
  "analyzed_at": "2025-11-17T10:30:00Z",
  "screens": [
    {
      "name": "MainScreen",
      "file": "my_app/screens/main.py",
      "line": 15,
      "widgets": ["Header", "Sidebar", "ContentView", "Footer"],
      "keybindings": [
        {"key": "q", "action": "quit", "description": "Exit app"},
        {"key": "h", "action": "show_help", "description": "Show help"},
        {"key": "ctrl+s", "action": "screenshot", "description": "Capture"}
      ],
      "navigation": {
        "from": "startup",
        "to": ["settings", "help", "dashboard"]
      }
    }
  ],
  "keybindings": {
    "global": [
      {"key": "q", "action": "app.quit"},
      {"key": "?", "action": "app.help"}
    ]
  },
  "metadata": {
    "app_name": "MyTuiApp",
    "version": "1.0.0",
    "entry_point": "my_app/main.py"
  }
}
```

#### Click Applications

```bash
orchestro index ./cli_app --framework click
```

**Extracts:**
- Commands and subcommands
- Options (`--flag`, `-f`)
- Arguments
- Help text
- Validation rules
- Command groups

#### Argparse Applications

```bash
orchestro index ./script.py --framework argparse
```

**Extracts:**
- ArgumentParser instances
- Subparsers
- Positional arguments
- Optional flags
- Default values
- Choices and constraints

### Index File Format

The index is stored as JSON/YAML:

```yaml
framework: textual
version: 0.3.0
analyzed_at: 2025-11-17T10:30:00Z

screens:
  - name: MainScreen
    file: my_app/screens/main.py
    line: 15
    widgets:
      - Header
      - ContentView
    keybindings:
      - key: q
        action: quit
        description: Exit

keybindings:
  global:
    - key: q
      action: app.quit

navigation:
  - from: MainScreen
    to: SettingsScreen
    trigger: key:s
```

### Indexing Options

```bash
# Full options
orchestro index ./app \
  --framework textual \
  --output .orchestro/index.json \
  --exclude "tests/*,venv/*" \
  --include "*.py" \
  --follow-imports \
  --max-depth 10 \
  --verbose
```

**Options:**

| Flag | Description | Default |
|------|-------------|---------|
| `--framework` | Framework to analyze | Auto-detect |
| `--output` | Index file path | `.orchestro/index.json` |
| `--exclude` | Patterns to exclude | `tests/*,venv/*` |
| `--include` | Patterns to include | `*.py` |
| `--follow-imports` | Analyze imported modules | `false` |
| `--max-depth` | Max directory depth | `10` |
| `--verbose` | Detailed logging | `false` |

### Manual Annotations

Enhance automatic analysis with code annotations:

```python
from textual.app import App
from orchestro_cli import orchestro_hint

class MyApp(App):
    # Orchestro will automatically test this flow
    @orchestro_hint("critical-path")
    def action_save_data(self):
        """Save user data."""
        pass

    # Orchestro will generate edge case tests
    @orchestro_hint("edge-case", input="empty-string")
    def validate_input(self, value: str):
        """Validate user input."""
        pass

    # Mark unstable features
    @orchestro_hint("skip-test", reason="Feature under development")
    def experimental_feature(self):
        """Experimental functionality."""
        pass
```

**Available Hints:**
- `critical-path` - High-priority test coverage
- `edge-case` - Generate boundary tests
- `skip-test` - Exclude from generation
- `slow-test` - Mark as requiring extended timeout
- `integration-test` - Requires external services

---

## Test Generation

### The `orchestro generate` Command

Generate test scenarios from an index file.

**Basic Usage:**
```bash
orchestro generate <index_file> --type <type> [options]
```

### Generation Strategies

#### 1. Smoke Tests

Quick sanity checks covering basic functionality:

```bash
orchestro generate .orchestro/index.json --type smoke --output tests/smoke/
```

**Generates:**
- App startup test
- Main screen rendering
- Basic navigation
- Clean shutdown

**Example Output:**
```yaml
# tests/smoke/01_app_startup.yaml
name: Smoke Test - Application Startup
description: Verify app starts and renders main screen
command: python -m my_app
timeout: 30

steps:
  - screenshot: "00-startup"
    timeout: 10
    note: "Capture initial state"

  - expect: "Ready|Started"
    timeout: 5

validations:
  - type: path_exists
    path: artifacts/screenshots/00-startup.svg
```

#### 2. Coverage Tests

Comprehensive tests covering all screens and features:

```bash
orchestro generate .orchestro/index.json --type coverage --output tests/coverage/
```

**Generates:**
- Test for every screen
- Test for every keybinding
- Test for every navigation path
- Screenshot gallery

#### 3. Keybinding Tests

Focus on keyboard interaction:

```bash
orchestro generate .orchestro/index.json --type keybindings --output tests/keys/
```

**Generates:**
- Test for each key combination
- Global vs screen-specific keys
- Key conflict detection

#### 4. Navigation Tests

Test all navigation paths:

```bash
orchestro generate .orchestro/index.json --type navigation --output tests/nav/
```

**Generates:**
- Path from screen A to screen B
- Breadth-first navigation
- Edge case navigation (back buttons, etc.)

#### 5. Custom Templates

Use your own generation templates:

```bash
orchestro generate .orchestro/index.json \
  --template ./my_template.jinja2 \
  --output tests/custom/
```

### Generation Options

```bash
orchestro generate .orchestro/index.json \
  --type coverage \
  --output tests/generated/ \
  --prefix "auto_" \
  --quality-threshold 0.7 \
  --max-scenarios 50 \
  --include-screenshots \
  --verbose
```

**Options:**

| Flag | Description | Default |
|------|-------------|---------|
| `--type` | Generation strategy | `smoke` |
| `--output` | Output directory | `tests/generated/` |
| `--prefix` | Filename prefix | `""` |
| `--quality-threshold` | Min confidence score | `0.6` |
| `--max-scenarios` | Max scenarios to generate | `100` |
| `--include-screenshots` | Add screenshot steps | `true` |
| `--verbose` | Detailed logging | `false` |

### Quality and Confidence Scores

Each generated scenario includes quality metrics:

```yaml
# Generated scenario metadata
_orchestro_metadata:
  generated_by: orchestro_cli v0.3.0
  strategy: coverage
  confidence: 0.87  # How sure we are this test is correct
  coverage: 0.65    # What % of app this test covers
  source_screen: MainScreen
  source_file: my_app/screens/main.py:15
```

**Confidence Scoring:**
- `0.9-1.0` - High confidence, directly extracted from code
- `0.7-0.9` - Medium confidence, inferred from patterns
- `0.5-0.7` - Low confidence, generated heuristically
- `<0.5` - Very low confidence, review recommended

**Coverage Scoring:**
- Based on what % of indexed features the test exercises
- A full navigation test might cover 80% of screens
- A single screen test might cover 10% of the app

### Templates and Customization

Create custom generation templates with Jinja2:

```jinja2
{# my_template.jinja2 #}
name: {{ screen.name }} Test
description: Auto-generated test for {{ screen.name }}
command: {{ app.command }}
timeout: {{ screen.timeout or 30 }}

steps:
  # Startup
  - screenshot: "{{ screen.name|slugify }}-startup"
    timeout: 15

  {% for key in screen.keybindings %}
  # Test {{ key.description }}
  - send: "{{ key.key }}"
    note: "Trigger: {{ key.action }}"
  - screenshot: "{{ screen.name|slugify }}-{{ key.action|slugify }}"
    timeout: 10
  {% endfor %}

validations:
  {% for step in steps if step.screenshot %}
  - type: path_exists
    path: artifacts/screenshots/{{ step.screenshot }}.svg
  {% endfor %}
```

**Available Template Variables:**
- `app` - Application metadata
- `screens` - List of all screens
- `screen` - Current screen (in loops)
- `keybindings` - All keybindings
- `navigation` - Navigation graph
- `metadata` - Index metadata

---

## CLI Reference

### Complete Command Reference

#### `orchestro index`

Analyze application and create knowledge base.

```bash
orchestro index <path> [options]

Arguments:
  path                  Path to application source code

Options:
  -f, --framework STR   Framework to analyze (textual, click, argparse)
  -o, --output PATH     Output index file [default: .orchestro/index.json]
  -e, --exclude PATTERN Exclude patterns (glob)
  -i, --include PATTERN Include patterns (glob)
  --follow-imports      Follow and analyze imports
  --max-depth INT       Maximum directory depth [default: 10]
  -v, --verbose         Verbose output
  -h, --help            Show help

Examples:
  orchestro index ./my_app --framework textual
  orchestro index ./cli.py --framework click --output index.json
  orchestro index ./project --exclude "tests/*,venv/*" --verbose
```

#### `orchestro generate`

Generate test scenarios from index.

```bash
orchestro generate <index_file> [options]

Arguments:
  index_file            Path to index JSON file

Options:
  -t, --type STR        Generation strategy (smoke, coverage, keybindings, navigation)
  -o, --output PATH     Output directory [default: tests/generated/]
  -p, --prefix STR      Filename prefix
  -q, --quality FLOAT   Minimum quality threshold [default: 0.6]
  -m, --max INT         Maximum scenarios to generate [default: 100]
  --template PATH       Custom Jinja2 template
  --no-screenshots      Disable screenshot generation
  -v, --verbose         Verbose output
  -h, --help            Show help

Examples:
  orchestro generate .orchestro/index.json --type smoke
  orchestro generate index.json --type coverage --output tests/
  orchestro generate index.json --template custom.jinja2 --quality 0.8
```

#### `orchestro coverage`

Analyze test coverage based on index.

```bash
orchestro coverage <index_file> <test_directory> [options]

Arguments:
  index_file            Path to index JSON file
  test_directory        Directory containing test scenarios

Options:
  --report FORMAT       Report format (text, json, html) [default: text]
  -o, --output PATH     Output file (for json/html)
  -v, --verbose         Verbose output
  -h, --help            Show help

Examples:
  orchestro coverage .orchestro/index.json tests/
  orchestro coverage index.json tests/ --report html --output coverage.html
```

#### `orchestro learn`

Improve index based on test execution results.

```bash
orchestro learn <index_file> <test_results> [options]

Arguments:
  index_file            Path to index JSON file
  test_results          Path to JUnit XML or test results

Options:
  --update              Update index file in-place
  -o, --output PATH     Save updated index to file
  -v, --verbose         Verbose output
  -h, --help            Show help

Examples:
  orchestro learn .orchestro/index.json test-results/junit.xml --update
  orchestro learn index.json results.xml --output index-updated.json
```

---

## Integration

### Using with Existing Tests

Combine manual and generated tests:

```bash
# Project structure
tests/
├── manual/              # Your hand-written scenarios
│   ├── critical_flow.yaml
│   └── edge_cases.yaml
├── generated/           # Auto-generated scenarios
│   ├── smoke/
│   └── coverage/
└── run_all.sh          # Run everything
```

**run_all.sh:**
```bash
#!/bin/bash
# Run manual tests first (critical paths)
orchestro tests/manual/*.yaml --junit-xml=results/manual.xml

# Run generated smoke tests
orchestro tests/generated/smoke/*.yaml --junit-xml=results/smoke.xml

# Run full coverage (if smoke passes)
if [ $? -eq 0 ]; then
    orchestro tests/generated/coverage/*.yaml --junit-xml=results/coverage.xml
fi
```

### CI/CD Integration

GitHub Actions example:

```yaml
# .github/workflows/test.yml
name: Orchestro Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install orchestro-cli
          pip install -e .

      - name: Analyze application
        run: orchestro index ./my_app --framework textual

      - name: Generate tests
        run: orchestro generate .orchestro/index.json --type smoke

      - name: Run generated tests
        run: orchestro tests/generated/*.yaml --junit-xml=test-results/junit.xml

      - name: Publish test results
        uses: EnricoMi/publish-unit-test-result-action@v2
        if: always()
        with:
          files: test-results/junit.xml
```

### Gradual Adoption Path

**Week 1**: Generate smoke tests only
```bash
orchestro index ./app --framework textual
orchestro generate .orchestro/index.json --type smoke
# Review and run smoke tests
```

**Week 2**: Add coverage tests
```bash
orchestro generate .orchestro/index.json --type coverage --quality 0.8
# Review high-confidence tests
```

**Week 3**: Refine with learning
```bash
orchestro learn .orchestro/index.json test-results/junit.xml --update
orchestro generate .orchestro/index.json --type coverage
# Re-generate with improved index
```

**Week 4**: Full automation
```bash
# Add to CI/CD pipeline
# Deprecate manual tests that are redundant
```

---

## Advanced Usage

### Programmatic API

Use intelligence features in Python code:

```python
from orchestro_cli.intelligence import ASTAnalyzer, ScenarioGenerator
from pathlib import Path

# Analyze application
analyzer = ASTAnalyzer()
knowledge = await analyzer.analyze_project(
    Path("./my_app"),
    framework="textual",
    follow_imports=True
)

print(f"Found {len(knowledge.screens)} screens")
print(f"Found {len(knowledge.keybindings)} keybindings")

# Generate scenarios
generator = ScenarioGenerator(knowledge)

# Smoke tests
smoke_yaml = generator.generate_smoke_test()
Path("tests/smoke.yaml").write_text(smoke_yaml)

# Coverage tests
for screen in knowledge.screens:
    yaml_content = generator.generate_screen_test(screen)
    output_path = Path(f"tests/{screen.name.lower()}.yaml")
    output_path.write_text(yaml_content)

# Custom generation
from jinja2 import Template
template = Template(Path("my_template.jinja2").read_text())
custom_yaml = generator.generate_from_template(template, screen=knowledge.screens[0])
```

### Creating Custom Extractors

Add support for new frameworks:

```python
from orchestro_cli.intelligence import FrameworkExtractor, AppKnowledge
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
            if isinstance(base, ast.Name) and base.id == "Screen":
                return True
        return False

    def _extract_screen(self, node: ast.ClassDef, source_file: Path):
        """Extract screen information."""
        # Implementation details...
        pass

# Register extractor
from orchestro_cli.intelligence import register_extractor
register_extractor(MyFrameworkExtractor)
```

### Learning from Execution

Improve test generation based on results:

```python
from orchestro_cli.intelligence import LearningEngine

# Load index and test results
index = AppKnowledge.load(".orchestro/index.json")
results = JUnitResults.load("test-results/junit.xml")

# Analyze and learn
engine = LearningEngine(index)
improvements = engine.learn_from_results(results)

print(f"Learned {len(improvements)} patterns:")
for improvement in improvements:
    print(f"  - {improvement.description}")
    print(f"    Confidence: {improvement.confidence}")
    print(f"    Applies to: {improvement.screens}")

# Update index
engine.apply_improvements(improvements)
index.save(".orchestro/index.json")
```

**What it learns:**
- Screens that take longer to load (adjust timeouts)
- Flaky keybindings (add retries)
- Navigation paths that fail (skip or fix)
- Screenshot timing issues (optimize delays)

---

## Troubleshooting

### Common Issues

#### "No framework detected"

**Problem**: Orchestro can't determine your framework.

**Solution**:
```bash
# Explicitly specify framework
orchestro index ./app --framework textual

# Check if imports are correct
grep -r "from textual" ./app
```

#### "Low confidence scores (<0.5)"

**Problem**: Generated tests have low quality scores.

**Solutions**:
1. Add code annotations:
   ```python
   @orchestro_hint("critical-path")
   def important_action(self):
       pass
   ```

2. Use custom templates with domain knowledge:
   ```bash
   orchestro generate index.json --template my_template.jinja2
   ```

3. Filter low-confidence tests:
   ```bash
   orchestro generate index.json --quality-threshold 0.7
   ```

#### "Generated tests fail immediately"

**Problem**: Auto-generated tests don't work.

**Debug steps**:

1. Check index accuracy:
   ```bash
   cat .orchestro/index.json | jq '.screens'
   ```

2. Run with verbose logging:
   ```bash
   orchestro tests/generated/test.yaml --verbose
   ```

3. Manually review first generated test:
   ```bash
   cat tests/generated/smoke/01_startup.yaml
   # Verify command, timeouts, expectations
   ```

4. Update index with corrections:
   ```bash
   # Edit index.json manually
   orchestro generate index.json --type smoke
   ```

#### "Screens not detected"

**Problem**: Index shows 0 screens for Textual app.

**Solutions**:

1. Ensure proper imports:
   ```python
   from textual.screen import Screen  # Must be explicit
   ```

2. Check class inheritance:
   ```python
   class MyScreen(Screen):  # Must inherit Screen
       pass
   ```

3. Use `--follow-imports`:
   ```bash
   orchestro index ./app --follow-imports --verbose
   ```

#### "Keybindings not extracted"

**Problem**: No keybindings in index.

**Solutions**:

1. Check binding format (Textual):
   ```python
   # Orchestro recognizes these patterns
   BINDINGS = [
       ("q", "quit", "Quit"),
       Binding("s", "settings", "Settings"),
   ]

   @on(Key.from_str("h"))
   def show_help(self):
       pass
   ```

2. Use annotations for complex bindings:
   ```python
   @orchestro_hint("keybinding", key="ctrl+s", action="save")
   def custom_save(self):
       pass
   ```

### Debug Mode

Enable detailed debugging:

```bash
# Maximum verbosity
orchestro index ./app --verbose --framework textual 2>&1 | tee index.log

# Check what was found
cat .orchestro/index.json | jq '.'

# Generate with debug info
orchestro generate .orchestro/index.json --verbose --type smoke 2>&1 | tee gen.log
```

### Getting Help

If issues persist:

1. Check existing issues: [GitHub Issues](https://github.com/vyb/orchestro-cli/issues)
2. Run diagnostics:
   ```bash
   orchestro diagnose ./app --framework textual
   ```
3. Share debug output:
   ```bash
   orchestro index ./app --verbose 2>&1 | tee debug.log
   # Attach debug.log to issue
   ```

---

## API Reference

### Programmatic Usage

#### ASTAnalyzer

Analyze Python source code using Abstract Syntax Trees.

```python
from orchestro_cli.intelligence import ASTAnalyzer
from pathlib import Path

analyzer = ASTAnalyzer()

# Analyze single file
knowledge = await analyzer.analyze_file(Path("app.py"), framework="textual")

# Analyze entire project
knowledge = await analyzer.analyze_project(
    Path("./my_app"),
    framework="textual",
    exclude_patterns=["tests/*", "venv/*"],
    follow_imports=True,
    max_depth=10
)

# Access results
print(f"Screens: {len(knowledge.screens)}")
for screen in knowledge.screens:
    print(f"  - {screen.name} ({len(screen.keybindings)} keys)")
```

**Methods:**

- `analyze_file(path, framework)` - Analyze single file
- `analyze_project(path, **kwargs)` - Analyze directory
- `extract_screens(ast_tree)` - Get all screens
- `extract_keybindings(ast_tree)` - Get all keybindings
- `extract_navigation(ast_tree)` - Get navigation graph

#### ScenarioGenerator

Generate test scenarios from knowledge base.

```python
from orchestro_cli.intelligence import ScenarioGenerator, AppKnowledge

# Load or create knowledge
knowledge = AppKnowledge.load(".orchestro/index.json")

# Create generator
generator = ScenarioGenerator(knowledge)

# Generate tests
smoke_test = generator.generate_smoke_test()
coverage_tests = generator.generate_coverage_tests()
nav_tests = generator.generate_navigation_tests()

# Use custom template
from jinja2 import Template
template = Template("...")
custom_test = generator.generate_from_template(
    template,
    screen=knowledge.screens[0],
    metadata={"author": "orchestro"}
)

# Save results
Path("tests/smoke.yaml").write_text(smoke_test)
```

**Methods:**

- `generate_smoke_test()` - Basic sanity check
- `generate_coverage_tests()` - Comprehensive coverage
- `generate_screen_test(screen)` - Single screen test
- `generate_navigation_test(from_screen, to_screen)` - Navigation path
- `generate_from_template(template, **context)` - Custom template

#### AppKnowledge

Knowledge base data structure.

```python
from orchestro_cli.intelligence import AppKnowledge, Screen, Keybinding

# Create knowledge manually
knowledge = AppKnowledge(
    framework="textual",
    version="0.3.0",
    metadata={"app_name": "MyApp"}
)

# Add screen
screen = Screen(
    name="MainScreen",
    file=Path("app.py"),
    line=42,
    widgets=["Header", "Footer"],
    keybindings=[
        Keybinding(key="q", action="quit", description="Exit")
    ]
)
knowledge.screens.append(screen)

# Save/load
knowledge.save(".orchestro/index.json")
loaded = AppKnowledge.load(".orchestro/index.json")

# Query
main_screen = knowledge.get_screen("MainScreen")
all_keys = knowledge.get_all_keybindings()
nav_graph = knowledge.get_navigation_graph()
```

**Data Classes:**

```python
@dataclass
class Screen:
    name: str
    file: Path
    line: int
    widgets: List[str]
    keybindings: List[Keybinding]
    navigation: Dict[str, List[str]]

@dataclass
class Keybinding:
    key: str
    action: str
    description: str
    scope: str = "screen"  # or "global"

@dataclass
class AppKnowledge:
    framework: str
    version: str
    screens: List[Screen]
    keybindings: List[Keybinding]
    navigation: Dict[str, List[str]]
    metadata: Dict[str, Any]
```

---

## Best Practices

### 1. Start Small

Generate smoke tests first, then expand:

```bash
# Week 1
orchestro index ./app
orchestro generate .orchestro/index.json --type smoke

# Week 2
orchestro generate .orchestro/index.json --type coverage --quality 0.8

# Week 3
orchestro generate .orchestro/index.json --type coverage --quality 0.6
```

### 2. Review Generated Tests

Always review before committing:

```bash
orchestro generate .orchestro/index.json --type smoke
# Review tests/generated/
git diff tests/generated/
# Make manual adjustments if needed
git add tests/generated/
```

### 3. Combine Manual and Generated

Use both approaches:

- **Manual**: Critical business flows, edge cases
- **Generated**: Screen coverage, regression testing

### 4. Keep Index Updated

Re-index after major changes:

```bash
# After adding new screens
orchestro index ./app --framework textual
orchestro generate .orchestro/index.json --type coverage
```

### 5. Use Quality Thresholds

Filter low-confidence tests:

```bash
# Only generate high-confidence tests
orchestro generate index.json --quality-threshold 0.8
```

### 6. Learn from Results

Improve generation over time:

```bash
# Run tests
orchestro tests/generated/*.yaml --junit-xml=results.xml

# Learn from results
orchestro learn .orchestro/index.json results.xml --update

# Re-generate improved tests
orchestro generate .orchestro/index.json --type coverage
```

---

## Next Steps

- Read the [Tutorial](tutorials/INTELLIGENT_TESTING.md) for hands-on practice
- Check [Examples](../examples/intelligence/) for real-world usage
- Explore the [API Documentation](API.md#intelligence-api)
- Join the [Discussion](https://github.com/vyb/orchestro-cli/discussions) to share tips

---

**Version:** 0.3.0
**Last Updated:** 2025-11-17
**Feedback**: [GitHub Issues](https://github.com/vyb/orchestro-cli/issues)
