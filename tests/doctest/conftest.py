"""Pytest fixtures for doctest tests."""

from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def sample_markdown(tmp_path: Path) -> Path:
    """Create a sample Markdown file with code blocks.

    Args:
        tmp_path: Pytest temporary directory fixture

    Returns:
        Path to created Markdown file
    """
    content = """# Sample Documentation

This is a test document.

## Basic Commands

```bash
$ echo "Hello, World!"
Hello, World!
```

## Inline Expectations

```shell
$ orchestro --version  #=> orchestro 0.2.1
$ pwd  #=> /home/user
```

## Multi-line Output

```bash
$ orchestro run scenario.yaml
Running scenario...
Executing 5 steps...
Success!
```

## Code Without Commands

```python
def hello():
    print("Hello")
```

## Multiple Languages

```javascript
console.log("JavaScript");
```

```bash
$ echo "Bash command"
Bash command
```
"""
    md_file = tmp_path / "test.md"
    md_file.write_text(content, encoding='utf-8')
    return md_file


@pytest.fixture
def empty_markdown(tmp_path: Path) -> Path:
    """Create an empty Markdown file.

    Args:
        tmp_path: Pytest temporary directory fixture

    Returns:
        Path to created Markdown file
    """
    md_file = tmp_path / "empty.md"
    md_file.write_text("# Empty\n\nNo code blocks here.", encoding='utf-8')
    return md_file


@pytest.fixture
def complex_markdown(tmp_path: Path) -> Path:
    """Create a complex Markdown file with edge cases.

    Args:
        tmp_path: Pytest temporary directory fixture

    Returns:
        Path to created Markdown file
    """
    content = """# Complex Cases

## Nested Blocks

> Quote with code:
> ```bash
> $ echo "quoted"
> quoted
> ```

## Line Continuations

```bash
$ echo "line one" \\
  "line two" \\
  "line three"
line one line two line three
```

## Comments

```bash
# This is a comment
$ echo "real command"  # inline comment
real command

# Another comment
```

## Empty Blocks

```bash

```

## No Language Tag

```
$ generic command
output
```
"""
    md_file = tmp_path / "complex.md"
    md_file.write_text(content, encoding='utf-8')
    return md_file
