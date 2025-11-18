# Orchestro Intelligence System - Quick Start

## 30-Second Demo

```bash
# 1. Run the demo
python examples/demo_intelligence.py

# 2. Check the output
ls examples/generated_tests/
# smoke_test.yaml
# keybinding_test.yaml
# navigation_test.yaml
# app_knowledge.json
```

## 5-Minute Tutorial

### Step 1: Try the Sample App

```bash
pip install textual
python examples/sample_tui_app/app.py
```

**Navigate**:
- Press `s` for Settings
- Press `d` for Dashboard
- Press `escape` to go back
- Press `q` to quit

### Step 2: Analyze the App

```python
from pathlib import Path
from orchestro_cli.intelligence import ASTAnalyzer

analyzer = ASTAnalyzer()
knowledge = await analyzer.analyze_project(Path("examples/sample_tui_app"))

print(f"Found {len(knowledge.screens)} screens")
# Output: Found 3 screens
```

### Step 3: Generate Tests

```python
from orchestro_cli.intelligence import ScenarioGenerator

generator = ScenarioGenerator(knowledge)
smoke_test = generator.generate_smoke_test()

Path("my_smoke_test.yaml").write_text(smoke_test)
```

### Step 4: Run Tests

```bash
orchestro examples/generated_tests/smoke_test.yaml
```

## Use With Your Own App

### Analyze Your TUI

```python
import asyncio
from pathlib import Path
from orchestro_cli.intelligence import ASTAnalyzer

async def analyze_my_app():
    analyzer = ASTAnalyzer()
    knowledge = await analyzer.analyze_project(Path("./my_tui_app"))

    # Inspect results
    for screen_name, screen in knowledge.screens.items():
        print(f"\n{screen_name}:")
        print(f"  Keybindings: {len(screen.keybindings)}")
        for kb in screen.keybindings:
            print(f"    {kb.key} -> {kb.action}")

asyncio.run(analyze_my_app())
```

### Generate Tests

```python
from orchestro_cli.intelligence import ScenarioGenerator

generator = ScenarioGenerator(knowledge)

# Generate all tests
output_dir = Path("./tests")
generated_files = generator.generate_all_tests(output_dir)

print(f"Generated {len(generated_files)} test files")
# Output: Generated 3 test files
```

### Save Knowledge

```python
import json

# Save for later use
knowledge_file = Path("app_knowledge.json")
knowledge_file.write_text(json.dumps(knowledge.to_dict(), indent=2))

# Load later
data = json.loads(knowledge_file.read_text())
loaded_knowledge = AppKnowledge.from_dict(data)
```

## API Quick Reference

### ASTAnalyzer

```python
from orchestro_cli.intelligence import ASTAnalyzer

analyzer = ASTAnalyzer()

# Check framework support
if analyzer.supports_framework("textual"):
    knowledge = await analyzer.analyze_project(app_path)

# Analyze single file
file_info = await analyzer.analyze_file(Path("screen.py"))
```

### ScenarioGenerator

```python
from orchestro_cli.intelligence import ScenarioGenerator

generator = ScenarioGenerator(knowledge)

# Generate specific test types
smoke = generator.generate_smoke_test()        # Visit all screens
keys = generator.generate_keybinding_test()    # Test shortcuts
nav = generator.generate_navigation_test()     # Test navigation

# Generate all at once
files = generator.generate_all_tests(output_dir)
```

### AppKnowledge

```python
# Access discovered information
screens = knowledge.screens
entry = knowledge.entry_screen
paths = knowledge.navigation_paths

# Find specific screen
main_screen = knowledge.get_screen("MainMenuScreen")

# Get all keybindings
all_keys = knowledge.get_all_keybindings()

# Find navigation path
path = knowledge.find_navigation_path("MainMenu", "Settings")
```

## Common Patterns

### Analyze Multiple Apps

```python
apps = ["app1", "app2", "app3"]

for app_name in apps:
    knowledge = await analyzer.analyze_project(Path(f"./{app_name}"))
    generator = ScenarioGenerator(knowledge)
    generator.generate_all_tests(Path(f"./tests/{app_name}"))
```

### Custom Test Generation

```python
class MyGenerator(ScenarioGenerator):
    def generate_accessibility_test(self) -> str:
        """Custom test for accessibility features."""
        scenario = {
            "name": "Accessibility Test",
            "steps": []
        }

        # Add custom logic
        for screen_name, screen in self.knowledge.screens.items():
            # Test screen reader compatibility
            # Verify keyboard navigation
            # Check color contrast
            pass

        return yaml.dump(scenario)
```

### CI/CD Integration

```yaml
# .github/workflows/tui-tests.yml
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

## Troubleshooting

### Demo Won't Run

```bash
# Install in development mode
pip install -e .

# Run from project root
cd /path/to/orchestro
python examples/demo_intelligence.py
```

### Import Errors

```bash
# Make sure you're in the right directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from orchestro_cli.intelligence import ASTAnalyzer
```

### No Screens Found

```python
# Check framework detection
analyzer = ASTAnalyzer()
if not analyzer.supports_framework("textual"):
    print("Only Textual framework supported currently")

# Check file paths
python_files = list(app_path.rglob("*.py"))
print(f"Found {len(python_files)} Python files")
```

### Tests Fail

```bash
# Run with integration flag
pytest tests/integration/test_intelligence_e2e.py --integration -v

# Check dependencies
pip install -e ".[dev]"
pip install textual
```

## Next Steps

1. **Read the Docs**: See [INTELLIGENCE_DEMO.md](../examples/INTELLIGENCE_DEMO.md)
2. **Try the Demo**: Run `python examples/demo_intelligence.py`
3. **Analyze Your App**: Point the analyzer at your TUI
4. **Customize**: Extend the generator for your needs
5. **Contribute**: Share improvements with the community

## Key Files

- **Demo**: `examples/demo_intelligence.py`
- **Sample App**: `examples/sample_tui_app/app.py`
- **Analyzer**: `orchestro_cli/intelligence/indexing/ast_analyzer.py`
- **Generator**: `orchestro_cli/intelligence/generation/scenario_generator.py`
- **Tests**: `tests/integration/test_intelligence_e2e.py`
- **Docs**: `examples/INTELLIGENCE_DEMO.md`

## Support

- **Issues**: Report bugs on GitHub
- **Docs**: See `docs/` directory
- **Examples**: See `examples/` directory
- **Tests**: Run with `--integration` flag
