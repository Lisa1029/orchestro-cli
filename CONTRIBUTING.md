# Contributing to Orchestro CLI

Thank you for your interest in contributing to Orchestro CLI! We welcome contributions from the community and are grateful for any help you can provide.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment Setup](#development-environment-setup)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting Guidelines](#issue-reporting-guidelines)
- [Documentation](#documentation)
- [Questions and Support](#questions-and-support)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. By participating, you are expected to uphold this code. Please be respectful, inclusive, and considerate in all interactions.

Key principles:
- Be welcoming and inclusive
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- A GitHub account

### First-Time Contributors

If you're new to open source, we recommend:
1. Start with issues labeled `good first issue` or `help wanted`
2. Read through the codebase to understand the architecture
3. Ask questions if anything is unclear - we're here to help!

## Development Environment Setup

### 1. Fork and Clone

Fork the repository on GitHub, then clone your fork:

```bash
git clone https://github.com/YOUR-USERNAME/orchestro-cli.git
cd orchestro-cli
```

### 2. Set Up Remote

Add the upstream repository as a remote:

```bash
git remote add upstream https://github.com/vyb/orchestro-cli.git
```

### 3. Create Virtual Environment

Create and activate a Python virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate on Linux/macOS
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

### 4. Install Development Dependencies

Install the package in editable mode with development dependencies:

```bash
pip install -e ".[dev]"
```

This installs:
- `pytest` - Testing framework
- `pytest-asyncio` - Async testing support
- `black` - Code formatter
- `mypy` - Static type checker

### 5. Verify Installation

Run the test suite to ensure everything is set up correctly:

```bash
pytest
```

## Development Workflow

### 1. Sync with Upstream

Before starting work, sync your fork with the upstream repository:

```bash
git checkout main
git fetch upstream
git merge upstream/main
git push origin main
```

### 2. Create a Feature Branch

Create a new branch for your work:

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or improvements

### 3. Make Your Changes

Write your code, following the [Coding Standards](#coding-standards) below.

### 4. Write Tests

All new features and bug fixes must include tests. See [Testing Requirements](#testing-requirements).

### 5. Run Quality Checks

Before committing, run the quality checks:

```bash
# Format code with Black
black orchestro_cli tests

# Run type checker
mypy orchestro_cli

# Run tests
pytest

# Run tests with coverage
pytest --cov=orchestro_cli --cov-report=term-missing
```

### 6. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "Add feature: brief description

Detailed explanation of what this commit does and why.
References #issue-number if applicable."
```

Commit message guidelines:
- Use present tense ("Add feature" not "Added feature")
- First line should be 50 characters or less
- Include a blank line between subject and body
- Reference relevant issues/PRs

### 7. Push and Create Pull Request

Push your branch and create a pull request:

```bash
git push origin feature/your-feature-name
```

Then open a pull request on GitHub.

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line Length**: Maximum 100 characters (Black default is 88, we're flexible)
- **Formatter**: Use Black for automatic code formatting
- **Imports**: Organize imports alphabetically, group by standard library, third-party, local
- **Naming Conventions**:
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
  - Private members: `_leading_underscore`

### Type Hints

All new code must include type hints:

```python
from typing import List, Optional, Dict
from pathlib import Path

def process_scenario(
    scenario_path: Path,
    workspace: Optional[Path] = None,
    verbose: bool = False
) -> Dict[str, any]:
    """Process a scenario file.

    Args:
        scenario_path: Path to the scenario YAML file
        workspace: Optional workspace directory for isolation
        verbose: Enable verbose logging

    Returns:
        Dictionary containing execution results

    Raises:
        FileNotFoundError: If scenario file doesn't exist
        ValueError: If scenario is invalid
    """
    pass
```

### Docstrings

Use Google-style docstrings for all public functions, classes, and methods:

```python
def example_function(param1: str, param2: int) -> bool:
    """Brief description of function.

    Longer description if needed, explaining what the function does,
    any important details about its behavior, etc.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param2 is negative
    """
    pass
```

### Code Organization

- Keep functions focused and single-purpose
- Extract complex logic into helper functions
- Use meaningful variable and function names
- Avoid deep nesting (max 3-4 levels)
- Add comments for complex logic, not obvious code

### Error Handling

```python
# Good: Specific exceptions with helpful messages
try:
    result = process_data(input_file)
except FileNotFoundError as e:
    raise ScenarioError(f"Input file not found: {input_file}") from e
except ValueError as e:
    raise ScenarioError(f"Invalid data format: {e}") from e

# Bad: Bare except or generic exceptions
try:
    result = process_data(input_file)
except:  # Don't do this
    pass
```

## Testing Requirements

### Writing Tests

All contributions must include appropriate tests:

1. **Unit Tests**: Test individual functions and classes in isolation
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test complete workflows

### Test Structure

```python
import pytest
from pathlib import Path
from orchestro_cli import ScenarioRunner

def test_scenario_runner_initialization(temp_workspace: Path):
    """Test that ScenarioRunner initializes correctly."""
    runner = ScenarioRunner(
        scenario_path=temp_workspace / "test.yaml",
        workspace=temp_workspace
    )
    assert runner.workspace == temp_workspace
    assert runner.scenario_path.name == "test.yaml"

def test_validation_with_missing_file(temp_workspace: Path):
    """Test that validation fails when expected file is missing."""
    runner = ScenarioRunner(
        scenario_path=temp_workspace / "test.yaml",
        workspace=temp_workspace
    )

    # Test expects specific exception
    with pytest.raises(ValidationError):
        runner._validate_path_exists(Path("nonexistent.txt"))
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_runner.py

# Run specific test
pytest tests/test_runner.py::test_scenario_runner_initialization

# Run with coverage
pytest --cov=orchestro_cli --cov-report=html

# Run with verbose output
pytest -v

# Run with debug output
pytest -vv -s
```

### Test Coverage

- Aim for at least 80% code coverage
- All new features must have tests
- Bug fixes should include regression tests
- Critical paths should have 100% coverage

### Fixtures

Use pytest fixtures for common test setup:

```python
@pytest.fixture
def mock_scenario_file(tmp_path: Path) -> Path:
    """Create a mock scenario YAML file."""
    scenario = tmp_path / "test.yaml"
    scenario.write_text("""
name: Test Scenario
command: echo "test"
steps:
  - send: "test"
    """)
    return scenario
```

## Pull Request Process

### Before Submitting

Checklist before opening a PR:

- [ ] Code follows style guidelines (Black formatted)
- [ ] Type hints added to all functions
- [ ] Docstrings added to public APIs
- [ ] Tests written and passing
- [ ] Test coverage maintained or improved
- [ ] Documentation updated if needed
- [ ] CHANGELOG.md updated with changes
- [ ] No merge conflicts with main branch
- [ ] All commits are clean and well-described

### PR Description Template

```markdown
## Description
Brief description of what this PR does.

## Motivation and Context
Why is this change required? What problem does it solve?
Fixes #(issue number)

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Testing
Describe the tests you ran and how to reproduce them.

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Code commented where necessary
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] No new warnings generated
- [ ] CHANGELOG.md updated
```

### Review Process

1. Maintainers will review your PR within 1-2 weeks
2. Address any feedback or requested changes
3. Once approved, a maintainer will merge your PR
4. Your contribution will be included in the next release!

### After Merge

- Your PR will be included in the next release
- You'll be credited in the release notes
- Consider helping review other PRs!

## Issue Reporting Guidelines

### Before Creating an Issue

1. Search existing issues to avoid duplicates
2. Check if it's already fixed in the latest version
3. Verify it's a Orchestro CLI issue, not a dependency issue

### Bug Reports

Use this template for bug reports:

```markdown
## Bug Description
Clear description of the bug.

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- OS: [e.g., Ubuntu 22.04, macOS 13, Windows 11]
- Python version: [e.g., 3.10.5]
- Orchestro CLI version: [e.g., 1.0.0]
- Installation method: [pip, source]

## Additional Context
- Scenario file (if applicable)
- Error messages/stack traces
- Screenshots (if relevant)
```

### Feature Requests

Use this template for feature requests:

```markdown
## Feature Description
Clear description of the proposed feature.

## Motivation
Why is this feature needed? What problem does it solve?

## Proposed Solution
How should this feature work?

## Alternatives Considered
What other approaches did you consider?

## Additional Context
Any other relevant information, examples, or mockups.
```

## Extending Intelligence Features

### Adding Framework Extractors

To add support for a new framework:

1. **Create the Extractor Class**

```python
# orchestro_cli/intelligence/extractors/my_framework.py
from orchestro_cli.intelligence import FrameworkExtractor, AppKnowledge, Screen
import ast

class MyFrameworkExtractor(FrameworkExtractor):
    """Extract structure from MyFramework apps."""

    @classmethod
    def can_handle(cls, code: str) -> bool:
        """Detect if code uses this framework."""
        return "from myframework import" in code

    def extract(self, tree: ast.AST, source_file: Path) -> AppKnowledge:
        """Extract application structure."""
        knowledge = AppKnowledge(framework="myframework")
        # Implementation: Walk AST, extract screens, keybindings, etc.
        return knowledge
```

2. **Write Tests**

```python
# tests/intelligence/test_my_framework_extractor.py
def test_my_framework_screen_detection():
    code = """
    from myframework import Screen

    class MyScreen(Screen):
        pass
    """
    extractor = MyFrameworkExtractor()
    tree = ast.parse(code)
    knowledge = extractor.extract(tree, Path("test.py"))
    assert len(knowledge.screens) == 1
    assert knowledge.screens[0].name == "MyScreen"
```

3. **Register the Extractor**

```python
# orchestro_cli/intelligence/extractors/__init__.py
from .my_framework import MyFrameworkExtractor

__all__ = [..., "MyFrameworkExtractor"]
```

4. **Add Documentation**

Update `docs/INTELLIGENCE.md` with framework support details.

### Creating Scenario Templates

To create custom generation templates:

1. **Create Template File**

```jinja2
{# .orchestro/templates/my_template.jinja2 #}
name: {{ screen.name }} Custom Test
description: |
  Custom template for {{ screen.name }}
  Framework: {{ app.framework }}

command: {{ app.command }}
timeout: {{ screen.timeout or 30 }}

steps:
  # Custom step pattern
  - screenshot: "{{ screen.name|slugify }}-start"
    timeout: 15

  {% for key in screen.keybindings %}
  - send: "{{ key.key }}"
    note: "Test {{ key.description }}"
  {% if key.action in critical_actions %}
  - expect: "Success|Complete"
    timeout: 10
  {% endif %}
  {% endfor %}

validations:
  - type: path_exists
    path: artifacts/screenshots/{{ screen.name|slugify }}-start.svg
```

2. **Test Template**

```python
# tests/intelligence/test_templates.py
from orchestro_cli.intelligence import ScenarioGenerator
from jinja2 import Template

def test_custom_template():
    template = Template(Path("my_template.jinja2").read_text())
    generator = ScenarioGenerator(knowledge)
    result = generator.generate_from_template(template, screen=screen)
    assert "Custom Test" in result
```

3. **Document Template**

Add template to `examples/intelligence/` with usage example.

### Improving AST Analysis

To enhance code analysis:

1. **Identify Pattern**

Find code pattern that should be recognized:
```python
# Pattern to detect: Custom decorators
@my_custom_decorator("key", "action")
def my_method(self):
    pass
```

2. **Add Extraction Logic**

```python
# orchestro_cli/intelligence/ast_analyzer.py
def _extract_custom_decorators(self, node: ast.FunctionDef) -> List[Keybinding]:
    """Extract keybindings from custom decorators."""
    bindings = []
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call):
            if hasattr(decorator.func, 'id') and decorator.func.id == 'my_custom_decorator':
                key = self._get_arg_value(decorator, 0)
                action = self._get_arg_value(decorator, 1)
                bindings.append(Keybinding(key=key, action=action))
    return bindings
```

3. **Write Tests**

```python
def test_custom_decorator_extraction():
    code = """
    @my_custom_decorator("k", "action")
    def my_method(self):
        pass
    """
    analyzer = ASTAnalyzer()
    tree = ast.parse(code)
    bindings = analyzer._extract_custom_decorators(tree.body[0])
    assert len(bindings) == 1
```

### Adding Learning Algorithms

To improve the learning engine:

1. **Identify Pattern to Learn**

Example: Learn optimal screenshot timing from test results.

2. **Implement Learning Algorithm**

```python
# orchestro_cli/intelligence/learning_engine.py
class LearningEngine:
    def learn_screenshot_timing(self, results: JUnitResults) -> Improvement:
        """Learn optimal screenshot timing from test execution."""
        screenshot_times = []
        for test in results.tests:
            if "screenshot" in test.name:
                screenshot_times.append(test.time)

        avg_time = statistics.mean(screenshot_times)
        optimal_timeout = avg_time * 1.5  # 50% buffer

        return Improvement(
            description=f"Optimize screenshot timeout to {optimal_timeout:.1f}s",
            confidence=0.9,
            impact="high",
            apply_to=["screenshot_steps"]
        )
```

3. **Test Learning Algorithm**

```python
def test_screenshot_timing_learning():
    results = create_mock_results(screenshot_time=0.8)
    engine = LearningEngine(knowledge)
    improvement = engine.learn_screenshot_timing(results)
    assert improvement.confidence > 0.8
```

## Documentation

### When to Update Documentation

Update documentation when:
- Adding new features
- Changing existing behavior
- Fixing bugs that affect usage
- Adding new examples or use cases
- **Adding new framework extractors**
- **Creating new scenario templates**
- **Improving AST analysis**
- **Enhancing learning algorithms**

### Documentation Files

- `README.md` - Main documentation, quick start, examples
- `CHANGELOG.md` - All changes (update with every PR)
- `CONTRIBUTING.md` - This file
- `docs/INTELLIGENCE.md` - Intelligence feature guide
- `docs/tutorials/INTELLIGENT_TESTING.md` - Step-by-step tutorial
- `docs/MIGRATION_TO_INTELLIGENCE.md` - Migration guide
- `docs/FAQ_INTELLIGENCE.md` - Common questions
- Code docstrings - Inline API documentation

### Documentation Style

- Write in clear, simple English
- Use concrete examples
- Include code snippets for clarity
- Keep it up-to-date with code changes
- Use proper Markdown formatting
- **Include confidence scores and quality metrics for intelligence features**
- **Provide before/after examples for learning improvements**

## Questions and Support

### Getting Help

If you need help:

1. Check the README and documentation
2. Search existing issues and discussions
3. Ask in GitHub Discussions
4. Open an issue if you found a bug

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions, ideas, general discussion
- **Pull Requests**: Code contributions and reviews

### Response Time

We aim to:
- Acknowledge issues within 3 days
- Review PRs within 1-2 weeks
- Release new versions monthly (or as needed)

## Recognition

All contributors will be:
- Listed in release notes
- Credited in the project
- Given our sincere gratitude!

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Orchestro CLI! Your efforts help make automated CLI testing better for everyone.
