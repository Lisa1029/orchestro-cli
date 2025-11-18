"""Testable documentation system for Orchestro CLI.

This module provides infrastructure for extracting and validating code examples
from Markdown documentation files. It supports:

- Parsing fenced code blocks from Markdown
- Extracting testable commands with expected outputs
- Executing commands and validating results
- Multiple validation strategies (exact, contains, regex)

Example usage:
    >>> from orchestro_cli.doctest import (
    ...     MarkdownParser,
    ...     TestExtractor,
    ...     DocTestExecutor
    ... )
    >>> from pathlib import Path
    >>>
    >>> # Parse Markdown file
    >>> parser = MarkdownParser()
    >>> blocks = parser.parse_file(Path('README.md'))
    >>>
    >>> # Extract testable commands
    >>> extractor = TestExtractor()
    >>> tests = extractor.extract_from_blocks(blocks)
    >>>
    >>> # Execute tests
    >>> executor = DocTestExecutor()
    >>> results = executor.execute_tests(tests)
    >>>
    >>> # Get summary
    >>> summary = executor.get_summary(results)
    >>> print(f"Passed: {summary['passed']}/{summary['total_tests']}")
"""

from .models import CodeBlock, CommandTest, DocTestResult
from .markdown_parser import MarkdownParser
from .test_extractor import TestExtractor
from .executor import DocTestExecutor, MatchMode
from .cli_handler import DocTestCLIHandler
from .junit_reporter import DocTestJUnitReporter

__all__ = [
    # Models
    "CodeBlock",
    "CommandTest",
    "DocTestResult",
    # Parsers
    "MarkdownParser",
    "TestExtractor",
    # Execution
    "DocTestExecutor",
    "MatchMode",
    # CLI
    "DocTestCLIHandler",
    # Reporting
    "DocTestJUnitReporter",
]
