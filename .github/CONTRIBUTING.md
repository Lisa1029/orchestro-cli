# Contributing to Orchestro CLI

Thank you for your interest in contributing to Orchestro CLI! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- pip

### Local Development Environment

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/orchestro-cli.git
   cd orchestro-cli
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in development mode**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Verify installation**
   ```bash
   orchestro --help
   pytest tests/
   ```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Your Changes

- Write clean, readable code
- Follow existing code style (black formatting)
- Add docstrings to functions and classes
- Update documentation if needed

### 3. Run Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=orchestro_cli --cov-report=html

# Run specific test file
pytest tests/test_runner.py -v
```

### 4. Code Quality Checks

```bash
# Format code with black
black orchestro_cli/ tests/

# Type checking (if applicable)
mypy orchestro_cli/ --ignore-missing-imports

# Check test coverage
pytest tests/ --cov=orchestro_cli --cov-report=term-missing
```

### 5. Commit Your Changes

Follow conventional commit format:

```bash
# Feature
git commit -m "feat: add support for custom timeout handlers"

# Bug fix
git commit -m "fix: resolve race condition in sentinel monitor"

# Documentation
git commit -m "docs: update installation instructions"

# Tests
git commit -m "test: add integration tests for screenshot capture"

# Refactoring
git commit -m "refactor: simplify runner state management"
```

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear description of changes
- Reference to any related issues
- Screenshots/examples if applicable

## Code Style Guidelines

### Python Code Style

- Follow PEP 8
- Use black for automatic formatting
- Maximum line length: 88 characters (black default)
- Use type hints where appropriate
- Write docstrings for all public functions/classes

Example:
```python
def process_scenario(scenario_file: str, timeout: int = 30) -> dict:
    """
    Process a scenario file and execute the test steps.

    Args:
        scenario_file: Path to the YAML scenario file
        timeout: Maximum execution time in seconds

    Returns:
        Dictionary containing execution results and metrics

    Raises:
        FileNotFoundError: If scenario file doesn't exist
        ValidationError: If scenario format is invalid
    """
    pass
```

### Testing Guidelines

- Write tests for all new features
- Aim for >80% code coverage
- Use descriptive test names
- Organize tests with clear arrange-act-assert structure

Example:
```python
def test_runner_handles_timeout_correctly():
    """Test that runner properly handles command timeouts."""
    # Arrange
    scenario = create_test_scenario(timeout=5)
    runner = Runner(scenario)

    # Act
    result = runner.execute()

    # Assert
    assert result.status == "timeout"
    assert result.duration >= 5
```

### Documentation

- Update README.md for user-facing changes
- Update docstrings for API changes
- Add examples for new features
- Keep CHANGELOG.md updated

## Pull Request Process

1. **Ensure all tests pass**
   - All CI checks must be green
   - Code coverage should not decrease

2. **Update documentation**
   - README.md for user-visible changes
   - Docstrings for API changes
   - Add examples if appropriate

3. **Address review feedback**
   - Respond to all comments
   - Make requested changes
   - Re-request review when ready

4. **Squash commits** (if needed)
   - Maintainers may ask you to squash commits
   - Keep commit history clean and meaningful

## Reporting Issues

### Bug Reports

Include:
- Python version and OS
- Minimal reproducible example
- Expected vs actual behavior
- Error messages and stack traces
- Orchestro CLI version

### Feature Requests

Include:
- Clear use case description
- Proposed API/interface
- Examples of usage
- Why existing features don't meet the need

## CI/CD Pipeline

All pull requests run through our CI/CD pipeline:

### Automated Checks

1. **Linting**: Black formatting and mypy type checking
2. **Testing**: Full test suite on multiple Python versions (3.8-3.11)
3. **Platform Testing**: Ubuntu, macOS, and Windows
4. **Coverage**: Code coverage analysis
5. **Security**: CodeQL security scanning
6. **Build**: Package build verification

### Required Status Checks

- All tests must pass
- Code coverage must not decrease significantly
- No linting errors
- Successful package build

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Assume good intentions

## Getting Help

- Check existing issues and documentation
- Ask questions in GitHub Discussions
- Join our community chat (if available)
- Tag maintainers for urgent issues

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Acknowledged in commit history

Thank you for contributing to Orchestro CLI!
