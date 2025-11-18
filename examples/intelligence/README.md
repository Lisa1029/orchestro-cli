# Intelligent Test Generation Examples

This directory contains examples demonstrating Orchestro CLI's intelligent test generation features.

---

## Examples

### 1. basic_textual_analysis.py

**What it demonstrates:**
- Analyzing a simple Textual TUI app
- Extracting screens and keybindings
- Generating basic test scenarios

**Usage:**
```bash
python examples/intelligence/basic_textual_analysis.py
```

**Output:**
- `.orchestro/index.json` - Application knowledge base
- `tests/generated/smoke.yaml` - Generated smoke test
- Analysis summary printed to console

---

### 2. custom_framework_extractor.py

**What it demonstrates:**
- Creating a custom framework extractor
- Registering with Orchestro's intelligence system
- Analyzing apps built with custom frameworks

**Usage:**
```python
from examples.intelligence.custom_framework_extractor import MyFrameworkExtractor
from orchestro_cli.intelligence import register_extractor, ASTAnalyzer

# Register your custom extractor
register_extractor(MyFrameworkExtractor)

# Now analyze apps using your framework
analyzer = ASTAnalyzer()
knowledge = await analyzer.analyze_project("./my_app", framework="myframework")
```

---

### 3. template_customization.py

**What it demonstrates:**
- Creating custom Jinja2 templates
- Using templates for scenario generation
- Customizing generation for project-specific needs

**Files:**
- `custom_template.jinja2` - Example template
- `template_customization.py` - Usage example

**Usage:**
```bash
python examples/intelligence/template_customization.py
```

**Output:**
- `tests/custom/screen_test.yaml` - Test generated from custom template

---

### 4. learning_from_execution.py

**What it demonstrates:**
- Running tests and collecting results
- Using the learning engine to improve tests
- Re-generating with learned parameters

**Usage:**
```bash
# 1. Generate initial tests
python examples/intelligence/learning_from_execution.py --generate

# 2. Run tests (creates test-results/junit.xml)
orchestro tests/generated/*.yaml --junit-xml=test-results/junit.xml

# 3. Learn from results and re-generate
python examples/intelligence/learning_from_execution.py --learn
```

**Output:**
- Initial tests with default parameters
- Learned improvements printed to console
- Updated tests with optimized timeouts

---

### 5. ci_cd_integration/

**What it demonstrates:**
- Integrating intelligence features in CI/CD
- Automated test generation pipeline
- Coverage analysis and reporting

**Files:**
- `.github/workflows/orchestro-intelligent.yml` - GitHub Actions workflow
- `.gitlab-ci.yml` - GitLab CI configuration
- `Jenkinsfile` - Jenkins pipeline

**Key features:**
- Automatic re-indexing on code changes
- Quality-gated test generation
- Coverage reports
- Learning from failed tests

---

## Quick Start

### Prerequisites

```bash
pip install orchestro-cli textual
```

### Run All Examples

```bash
# Run basic analysis example
python examples/intelligence/basic_textual_analysis.py

# Try custom template
python examples/intelligence/template_customization.py

# Full learning cycle (requires running tests)
python examples/intelligence/learning_from_execution.py --all
```

---

## File Descriptions

### basic_textual_analysis.py

```python
"""
Basic example of analyzing a Textual app and generating tests.

This example:
1. Creates a simple Textual app
2. Analyzes it with ASTAnalyzer
3. Generates smoke and coverage tests
4. Prints analysis results
"""

from orchestro_cli.intelligence import ASTAnalyzer, ScenarioGenerator
from pathlib import Path

# See file for full implementation
```

### custom_framework_extractor.py

```python
"""
Example of creating a custom framework extractor.

Demonstrates:
- Implementing FrameworkExtractor protocol
- Detecting framework-specific patterns
- Extracting screens and keybindings
- Registering with Orchestro
"""

from orchestro_cli.intelligence import FrameworkExtractor, AppKnowledge
import ast

class MyFrameworkExtractor(FrameworkExtractor):
    # Implementation
    pass
```

### template_customization.py

```python
"""
Example of using custom Jinja2 templates for generation.

Shows:
- Creating project-specific templates
- Using custom variables
- Advanced template features (filters, loops, conditions)
"""

from orchestro_cli.intelligence import ScenarioGenerator
from jinja2 import Template
```

### learning_from_execution.py

```python
"""
Example of learning from test execution results.

Workflow:
1. Generate initial tests
2. Run tests and collect JUnit XML
3. Analyze results with LearningEngine
4. Apply improvements to knowledge base
5. Re-generate improved tests
"""

from orchestro_cli.intelligence import LearningEngine
```

---

## Creating Your Own Examples

### Example Template

```python
"""
My Custom Example
-----------------
Brief description of what this demonstrates.
"""

from orchestro_cli.intelligence import ASTAnalyzer, ScenarioGenerator, AppKnowledge
from pathlib import Path

def main():
    # 1. Setup
    # ...

    # 2. Analyze
    analyzer = ASTAnalyzer()
    knowledge = await analyzer.analyze_project(Path("./app"))

    # 3. Generate
    generator = ScenarioGenerator(knowledge)
    tests = generator.generate_coverage_tests()

    # 4. Save
    for i, test in enumerate(tests):
        Path(f"tests/test_{i:02d}.yaml").write_text(test)

    # 5. Report
    print(f"Generated {len(tests)} tests")

if __name__ == "__main__":
    main()
```

---

## CI/CD Integration Examples

### GitHub Actions

See `.github/workflows/orchestro-intelligent.yml`:

```yaml
name: Intelligent Testing
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Analyze app
        run: orchestro index ./app --framework textual
      - name: Generate tests
        run: orchestro generate .orchestro/index.json --type smoke
      - name: Run tests
        run: orchestro tests/generated/*.yaml --junit-xml=results.xml
      - name: Learn from results
        if: always()
        run: orchestro learn .orchestro/index.json results.xml --update
```

### GitLab CI

See `.gitlab-ci.yml`:

```yaml
stages:
  - analyze
  - generate
  - test
  - learn

analyze:
  stage: analyze
  script:
    - orchestro index ./app --framework textual --output .orchestro/index.json
  artifacts:
    paths:
      - .orchestro/index.json

# ... (see file for full example)
```

---

## Best Practices

### 1. Start Simple

Begin with basic analysis and smoke tests:

```python
# Basic example
analyzer = ASTAnalyzer()
knowledge = await analyzer.analyze_project(Path("./app"))
generator = ScenarioGenerator(knowledge)
smoke_test = generator.generate_smoke_test()
```

### 2. Customize Gradually

Add custom templates as you understand your needs:

```python
# After understanding basic generation
template = Template(Path("custom_template.jinja2").read_text())
custom_test = generator.generate_from_template(template, screen=screen)
```

### 3. Iterate with Learning

Improve tests based on execution:

```python
# After running tests
engine = LearningEngine(knowledge)
improvements = engine.learn_from_results(results)
engine.apply_improvements(improvements)
```

---

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`:

```bash
# Ensure Orchestro is installed
pip install orchestro-cli

# Install from source for development
pip install -e .
```

### Framework Not Detected

If analyzer doesn't detect your framework:

```python
# Explicitly specify framework
knowledge = await analyzer.analyze_project(
    Path("./app"),
    framework="textual"  # Explicit
)
```

### Low Confidence Scores

If generated tests have low confidence:

```python
# Filter by quality threshold
generator = ScenarioGenerator(knowledge, quality_threshold=0.7)

# Or add hints to your code
from orchestro_cli import orchestro_hint

@orchestro_hint("critical-path")
def important_method(self):
    pass
```

---

## Contributing Examples

Want to contribute an example?

1. **Create example file**: `examples/intelligence/my_example.py`
2. **Add docstring**: Explain what it demonstrates
3. **Include comments**: Make it educational
4. **Test it**: Ensure it runs without errors
5. **Update this README**: Add entry in Examples section
6. **Submit PR**: With clear description

---

## Additional Resources

- [Intelligence Guide](../../docs/INTELLIGENCE.md) - Complete documentation
- [Tutorial](../../docs/tutorials/INTELLIGENT_TESTING.md) - Step-by-step walkthrough
- [API Reference](../../docs/API.md#intelligence-api) - API documentation
- [FAQ](../../docs/FAQ_INTELLIGENCE.md) - Common questions

---

## Example Execution Outputs

### Basic Analysis Output

```
Analyzing application...
  Framework: textual
  Screens found: 3
    - MainScreen (5 keybindings, 8 widgets)
    - SettingsScreen (3 keybindings, 5 widgets)
    - HelpScreen (2 keybindings, 3 widgets)
  Global keybindings: 2
  Navigation paths: 4

Generating smoke test...
  Confidence: 0.92
  Coverage: 45%
  Saved to: tests/generated/smoke.yaml

Success! Generated 1 test scenario.
```

### Learning Output

```
Learning from test results...
  Tests analyzed: 12
  Success rate: 100%

Improvements identified:
  1. Optimize MainScreen timeout (5s → 1.2s)
     Confidence: 0.95, Impact: high
  2. Optimize screenshot timing (15s → 3s)
     Confidence: 0.90, Impact: medium
  3. Recognize fast navigation pattern
     Confidence: 0.85, Impact: low

Applied 3 improvements to knowledge base.
Average confidence boost: +12%

Re-generating tests with improvements...
  Generated: 12 scenarios
  Avg confidence: 0.89 (was 0.77)
  Estimated time savings: 45%
```

---

**Happy intelligent testing!** 🧠✨
