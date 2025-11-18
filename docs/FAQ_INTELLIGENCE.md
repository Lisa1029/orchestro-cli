# Intelligent Test Generation FAQ

Common questions about Orchestro CLI's intelligent test generation features.

---

## General Questions

### Do I still need to write scenarios manually?

**Yes, for critical paths.** Intelligence features complement manual testing, not replace it.

**Use generated tests for:**
- Smoke testing and regression
- Broad coverage
- Screenshot galleries
- Repetitive scenarios

**Keep manual tests for:**
- Business-critical flows
- Edge cases and boundary conditions
- Integration tests with external services
- Performance-sensitive scenarios

**Best approach:** Combine both. Use generated tests for coverage, manual tests for expertise.

---

### What frameworks are supported?

**Currently supported:**
- **Textual** (Full support) - TUI framework
- **Click** (Full support) - CLI framework
- **Argparse** (Full support) - Argument parsing

**Coming soon:**
- Rich (Partial support)
- Custom frameworks via `FrameworkExtractor` protocol

**Can't find yours?** Create a custom extractor:
```python
from orchestro_cli.intelligence import FrameworkExtractor, register_extractor

class MyFrameworkExtractor(FrameworkExtractor):
    # Implementation

register_extractor(MyFrameworkExtractor)
```

---

### How accurate is the analysis?

**Depends on code structure:**

| Code Pattern | Accuracy | Confidence Score |
|--------------|----------|------------------|
| Explicit class inheritance | 95%+ | 0.9-1.0 |
| Decorator-based keybindings | 90%+ | 0.85-0.95 |
| Inferred navigation | 70-85% | 0.7-0.85 |
| Dynamic/runtime behavior | 50-70% | 0.5-0.7 |

**Improve accuracy with:**
- Clear code structure
- Explicit imports
- `@orchestro_hint` annotations
- Custom templates

**Check quality:**
```bash
orchestro generate index.json --quality-threshold 0.8
# Only generates high-confidence tests
```

---

### Can I customize generated tests?

**Absolutely!** Multiple customization levels:

1. **Quality filtering:**
   ```bash
   orchestro generate index.json --quality-threshold 0.8
   ```

2. **Custom templates:**
   ```bash
   orchestro generate index.json --template my_template.jinja2
   ```

3. **Code annotations:**
   ```python
   @orchestro_hint("critical-path", timeout=30)
   def important_action(self):
       pass
   ```

4. **Manual editing:**
   ```bash
   orchestro generate index.json --output tests/generated/
   # Edit YAML files as needed
   ```

5. **Hybrid approach:**
   ```yaml
   # Start with generated test, enhance manually
   _orchestro_metadata:
     generated_by: orchestro_cli v0.3.0
     enhanced_by: human

   # Add your custom validations
   ```

---

### Will it work with my custom framework?

**Yes**, if you create a custom extractor:

```python
from orchestro_cli.intelligence import (
    FrameworkExtractor,
    AppKnowledge,
    register_extractor
)
import ast

class MyFrameworkExtractor(FrameworkExtractor):
    @classmethod
    def can_handle(cls, code: str) -> bool:
        return "from my_framework import App" in code

    def extract(self, tree: ast.AST, source_file) -> AppKnowledge:
        knowledge = AppKnowledge(framework="my_framework")
        # Extract screens, keybindings, etc.
        return knowledge

register_extractor(MyFrameworkExtractor)
```

Then use it:
```bash
orchestro index ./my_app --framework my_framework
```

See [examples/intelligence/custom_extractor.py](../examples/intelligence/custom_extractor.py) for full example.

---

### How does learning work?

**Learning improves tests based on execution results:**

```bash
# 1. Run tests and collect results
orchestro tests/*.yaml --junit-xml=results.xml

# 2. Analyze results and learn
orchestro learn .orchestro/index.json results.xml --update

# 3. Re-generate with learned parameters
orchestro generate .orchestro/index.json --type coverage
```

**What it learns:**
- **Timeouts**: Actual load times vs estimates
- **Reliability**: Which tests are flaky
- **Patterns**: Success/failure patterns
- **Timing**: Screenshot capture timing

**Example improvement:**
```
Before learning:
  SettingsScreen timeout: 5s (default)
  Screenshot timeout: 15s (default)

After learning (from 10 test runs):
  SettingsScreen timeout: 1.2s (optimized)
  Screenshot timeout: 3s (optimized)
  Confidence boost: +12%
```

---

## Technical Questions

### Why are my screens not detected?

**Common causes:**

1. **Implicit imports:**
   ```python
   # ❌ Won't detect
   from textual import screen
   class MyScreen(screen.Screen):
       pass
   ```
   ```python
   # ✅ Will detect
   from textual.screen import Screen
   class MyScreen(Screen):
       pass
   ```

2. **Missing inheritance:**
   ```python
   # ❌ Won't detect
   class MyScreen:  # No inheritance
       pass
   ```
   ```python
   # ✅ Will detect
   from textual.screen import Screen
   class MyScreen(Screen):
       pass
   ```

3. **Dynamic screen creation:**
   ```python
   # ❌ Won't detect (runtime only)
   screens = [type(f"Screen{i}", (Screen,), {}) for i in range(10)]
   ```

**Solutions:**
- Use explicit imports
- Ensure proper inheritance
- Use `--follow-imports` flag
- Add `@orchestro_hint` for dynamic screens:
  ```python
  @orchestro_hint("screen", name="DynamicScreen")
  def create_screen():
      return type("DynamicScreen", (Screen,), {})
  ```

---

### Why are keybindings not extracted?

**Orchestro recognizes these patterns:**

```python
# ✅ Recognized: BINDINGS attribute
BINDINGS = [
    ("q", "quit", "Quit"),
    Binding("s", "settings", "Settings"),
]

# ✅ Recognized: @on decorator
from textual.on import on
from textual.events import Key

@on(Key.from_str("h"))
def show_help(self):
    pass

# ✅ Recognized: action_ methods
def action_quit(self):
    pass  # Infers "q" might trigger this

# ❌ Not recognized: Dynamic bindings
keys = {"q": "quit", "s": "settings"}
for key, action in keys.items():
    self.bind(key, action)  # Runtime only
```

**For dynamic bindings, use annotations:**
```python
@orchestro_hint("keybinding", key="ctrl+s", action="save")
def setup_dynamic_bindings(self):
    # Dynamic binding code
    pass
```

---

### Generated tests fail immediately. Why?

**Debug steps:**

1. **Check index accuracy:**
   ```bash
   cat .orchestro/index.json | jq '.screens'
   # Verify screens are correct
   ```

2. **Run with verbose mode:**
   ```bash
   orchestro tests/generated/test.yaml --verbose
   # See exact failure point
   ```

3. **Verify command:**
   ```yaml
   # In generated test
   command: python -m my_app
   # Is this correct? Try manually:
   python -m my_app
   ```

4. **Check timeouts:**
   ```yaml
   # Generated timeout might be too short
   timeout: 5
   # Try increasing:
   timeout: 30
   ```

5. **Validate screenshots:**
   ```bash
   # Ensure app has screenshot support
   export VYB_AUTO_SCREENSHOT=1
   python -m my_app
   # Create trigger manually to test
   ```

6. **Re-index with correct framework:**
   ```bash
   orchestro index ./app --framework textual --verbose
   ```

---

### How do I handle dynamic UI?

**For runtime-generated UI, use annotations:**

```python
from orchestro_cli import orchestro_hint

class DynamicScreen(Screen):
    def compose(self):
        # Dynamic widget creation
        for i in range(self.num_widgets):
            yield Widget(id=f"widget-{i}")

    @orchestro_hint("widgets", count="variable", pattern="widget-*")
    def on_mount(self):
        self.num_widgets = self.app.config.widget_count
```

**Or use custom templates:**
```jinja2
{# Handle dynamic widgets #}
{% for i in range(max_widgets) %}
- send: "{{ i }}"
  note: "Test dynamic widget {{ i }}"
{% endfor %}
```

---

### Can I generate tests for CLI apps (non-TUI)?

**Yes!** Click and Argparse support:

```bash
# Click CLI
orchestro index ./cli.py --framework click
orchestro generate .orchestro/index.json --type coverage
```

**Generated tests:**
```yaml
# tests/generated/command_help.yaml
name: Test 'help' Command
command: ./cli.py help
timeout: 10
steps:
  - expect: "Usage:"
    timeout: 5
  - expect: "Options:"
```

---

## Workflow Questions

### Should I commit generated tests?

**Two approaches:**

**Approach 1: Commit tests (recommended)**
```bash
# Benefits: Reproducible, reviewable, version controlled
orchestro generate index.json --output tests/generated/
git add tests/generated/
git commit -m "Update generated tests"
```

**Approach 2: Generate in CI**
```yaml
# .github/workflows/test.yml
- name: Generate tests
  run: |
    orchestro index ./app
    orchestro generate .orchestro/index.json --type smoke
- name: Run tests
  run: orchestro tests/generated/*.yaml
```

**Recommendation:** Commit high-confidence tests, generate low-confidence in CI.

---

### How often should I re-index?

**Re-index when:**
- ✅ Adding new screens
- ✅ Changing keybindings
- ✅ Modifying navigation
- ✅ Major refactors

**Don't re-index for:**
- ❌ Bug fixes (no structure change)
- ❌ CSS/styling changes
- ❌ Documentation updates

**Automate it:**
```bash
# Makefile
.PHONY: update-tests
update-tests:
	orchestro index ./app --framework textual
	orchestro generate .orchestro/index.json --type coverage
	@echo "Tests updated. Review with: git diff tests/"
```

---

### Can I use this in CI/CD?

**Absolutely!** Example GitHub Actions:

```yaml
name: Intelligent Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install
        run: pip install orchestro-cli textual

      - name: Analyze app
        run: orchestro index ./app --framework textual

      - name: Generate tests
        run: orchestro generate .orchestro/index.json --type smoke

      - name: Run tests
        run: orchestro tests/generated/*.yaml --junit-xml=results.xml

      - name: Publish results
        uses: EnricoMi/publish-unit-test-result-action@v2
        with:
          files: results.xml
```

---

## Performance Questions

### How fast is indexing?

**Typical performance:**
- Small app (5 files, 3 screens): ~0.5s
- Medium app (20 files, 10 screens): ~2s
- Large app (100 files, 30 screens): ~8s

**Optimize with:**
```bash
# Exclude unnecessary files
orchestro index ./app --exclude "tests/*,venv/*,docs/*"

# Limit depth
orchestro index ./app --max-depth 5

# Don't follow imports (faster but less complete)
orchestro index ./app --no-follow-imports
```

---

### How fast is scenario generation?

**Very fast:**
- Smoke tests (4-5 scenarios): ~100ms
- Coverage tests (10-20 scenarios): ~300ms
- Custom template (per scenario): ~10ms

**Bottleneck is usually I/O (writing YAML files), not generation.**

---

## Integration Questions

### Works with pytest?

**Yes!** Generated scenarios are standard YAML:

```python
# tests/test_generated.py
import pytest
from orchestro_cli import ScenarioRunner
from pathlib import Path

@pytest.mark.parametrize("scenario", [
    "tests/generated/smoke/01_startup.yaml",
    "tests/generated/smoke/02_navigation.yaml",
])
def test_generated_scenario(scenario):
    runner = ScenarioRunner(Path(scenario), verbose=True)
    runner.run()  # Raises on failure
```

---

### Works with other testing frameworks?

**Yes!** Orchestro is test-framework agnostic:

```bash
# Run with unittest
python -m unittest tests.test_orchestro

# Run with nose
nosetests tests/

# Run with tox
tox -e orchestro

# Run standalone
orchestro tests/*.yaml
```

---

## Troubleshooting

### "Low confidence scores (<0.5)"

**Reasons:**
- Inferred behavior (not explicit in code)
- Dynamic/runtime patterns
- Complex navigation logic

**Solutions:**

1. **Add annotations:**
   ```python
   @orchestro_hint("critical-path")
   def important_flow(self):
       pass
   ```

2. **Use custom templates:**
   ```bash
   orchestro generate index.json --template my_template.jinja2
   ```

3. **Filter low-confidence:**
   ```bash
   orchestro generate index.json --quality-threshold 0.7
   ```

4. **Manual review and enhance:**
   ```bash
   orchestro generate index.json --output review/
   # Edit low-confidence tests manually
   ```

---

### "ModuleNotFoundError during indexing"

**Cause:** Missing dependencies or imports

**Solution:**

1. **Install all dependencies:**
   ```bash
   pip install -e .[dev]
   ```

2. **Use virtual environment:**
   ```bash
   source venv/bin/activate
   orchestro index ./app
   ```

3. **Skip problematic imports:**
   ```bash
   orchestro index ./app --no-follow-imports
   ```

---

### "Generated tests timeout"

**Solutions:**

1. **Increase timeouts:**
   ```bash
   # Re-generate with higher timeouts
   orchestro generate index.json --timeout-multiplier 2
   ```

2. **Learn from failures:**
   ```bash
   orchestro tests/*.yaml --junit-xml=results.xml
   orchestro learn .orchestro/index.json results.xml --update
   orchestro generate .orchestro/index.json --type coverage
   ```

3. **Check app startup time:**
   ```bash
   time python -m my_app
   # If > 5s, adjust default timeout
   ```

---

## Best Practices

### What's the recommended workflow?

**Daily development:**
```bash
# 1. Make changes to app
git commit -m "Add new SettingsScreen"

# 2. Re-index (if structure changed)
orchestro index ./app

# 3. Re-generate tests
orchestro generate .orchestro/index.json --type coverage

# 4. Review changes
git diff tests/generated/

# 5. Run tests
orchestro tests/**/*.yaml

# 6. Commit if passing
git add .orchestro/index.json tests/generated/
git commit -m "Update tests for SettingsScreen"
```

**Weekly optimization:**
```bash
# 1. Collect results from week
cat ci-results/*.xml > weekly-results.xml

# 2. Learn from results
orchestro learn .orchestro/index.json weekly-results.xml --update

# 3. Re-generate with improvements
orchestro generate .orchestro/index.json --type coverage

# 4. Review confidence improvements
git diff tests/generated/
```

---

### How do I share templates with my team?

**Store in repo:**
```bash
.orchestro/
├── index.json                  # App knowledge
└── templates/                  # Team templates
    ├── smoke.jinja2
    ├── coverage.jinja2
    └── custom_integration.jinja2
```

**Use in generation:**
```bash
# Everyone uses same template
orchestro generate .orchestro/index.json \
  --template .orchestro/templates/smoke.jinja2 \
  --output tests/smoke/
```

**Document in README:**
```markdown
## Test Generation

```bash
# Generate smoke tests
make gen-smoke

# Generate coverage tests
make gen-coverage
```

See `.orchestro/templates/` for available templates.
```

---

## More Questions?

- [Intelligence Guide](INTELLIGENCE.md) - Complete documentation
- [Tutorial](tutorials/INTELLIGENT_TESTING.md) - Hands-on walkthrough
- [GitHub Issues](https://github.com/vyb/orchestro-cli/issues) - Bug reports
- [Discussions](https://github.com/vyb/orchestro-cli/discussions) - Ask community

---

**Version:** 0.3.0
**Last Updated:** 2025-11-17
