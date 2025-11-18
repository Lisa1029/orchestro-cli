"""CLI handler for documentation testing.

This module provides the command-line interface for running documentation tests
extracted from Markdown files. It supports multiple output formats, filtering,
and CI/CD integration via JUnit XML reports.

Example:
    $ orchestro doctest README.md
    $ orchestro doctest docs/*.md --verbose --fail-fast
    $ orchestro doctest README.md --junit-xml=test-results.xml
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

from .models import DocTestResult
from .markdown_parser import MarkdownParser
from .test_extractor import TestExtractor
from .executor import DocTestExecutor, MatchMode
from .junit_reporter import DocTestJUnitReporter


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    GRAY = '\033[90m'

    @classmethod
    def disable(cls) -> None:
        """Disable colors for non-TTY environments."""
        cls.GREEN = ''
        cls.RED = ''
        cls.YELLOW = ''
        cls.BLUE = ''
        cls.BOLD = ''
        cls.RESET = ''
        cls.GRAY = ''


class DocTestCLIHandler:
    """Handles CLI execution of documentation tests.

    Orchestrates parsing, test extraction, execution, and reporting of
    documentation tests from Markdown files.
    """

    def __init__(
        self,
        markdown_files: List[Path],
        prompt_prefix: str = '$',
        verbose: bool = False,
        fail_fast: bool = False,
        junit_xml: Optional[Path] = None,
        match_mode: MatchMode = MatchMode.CONTAINS,
        working_dir: Optional[Path] = None,
        timeout: float = 30.0,
        no_color: bool = False
    ):
        """Initialize CLI handler.

        Args:
            markdown_files: List of Markdown files to test
            prompt_prefix: Command prompt prefix (e.g., '$', '>')
            verbose: Enable verbose output
            fail_fast: Stop on first test failure
            junit_xml: Path for JUnit XML report output
            match_mode: Output matching strategy
            working_dir: Working directory for command execution
            timeout: Command timeout in seconds
            no_color: Disable colored output
        """
        self.markdown_files = markdown_files
        self.prompt_prefix = prompt_prefix
        self.verbose = verbose
        self.fail_fast = fail_fast
        self.junit_xml = junit_xml
        self.match_mode = match_mode
        self.working_dir = working_dir or Path.cwd()
        self.timeout = timeout

        # Disable colors if requested or not a TTY
        if no_color or not sys.stdout.isatty():
            Colors.disable()

        # Initialize components
        self.parser = MarkdownParser()
        self.extractor = TestExtractor(prompt_prefix=prompt_prefix)
        self.executor = DocTestExecutor(
            working_dir=working_dir,
            timeout=timeout,
            match_mode=match_mode
        )

    def run(self) -> int:
        """Run documentation tests.

        Returns:
            Exit code: 0 on success, 1 on failure
        """
        # Validate files
        for file_path in self.markdown_files:
            if not file_path.exists():
                self._print_error(f"File not found: {file_path}")
                return 1
            if file_path.suffix.lower() not in {'.md', '.markdown'}:
                self._print_error(f"Not a Markdown file: {file_path}")
                return 1

        # Parse and extract tests
        all_results: List[DocTestResult] = []
        total_tests = 0

        for file_path in self.markdown_files:
            # Print file header
            self._print_file_header(file_path)

            try:
                # Parse Markdown
                code_blocks = self.parser.parse_file(file_path)

                # Extract tests
                tests = self.extractor.extract_from_blocks(code_blocks)

                if not tests:
                    self._print_info(f"  No tests found in {file_path.name}")
                    continue

                total_tests += len(tests)

                if self.verbose:
                    self._print_info(f"  Found {len(tests)} test(s)")
                    print()

                # Execute tests
                for test in tests:
                    result = self.executor.execute_test(test)
                    all_results.append(result)

                    # Print result
                    self._print_result(result)

                    # Stop on failure if fail_fast enabled
                    if self.fail_fast and not result.passed:
                        break

                # Stop processing files if fail_fast and we have failures
                if self.fail_fast and any(not r.passed for r in all_results):
                    break

            except Exception as e:
                self._print_error(f"Error processing {file_path}: {e}")
                if self.verbose:
                    import traceback
                    traceback.print_exc()
                return 1

        # Print summary
        print()
        success = self._print_summary(all_results, total_tests)

        # Generate JUnit XML report if requested
        if self.junit_xml:
            try:
                self._generate_junit_report(all_results)
                self._print_info(f"JUnit XML report: {self.junit_xml}")
            except Exception as e:
                self._print_error(f"Failed to generate JUnit report: {e}")
                return 1

        return 0 if success else 1

    def _print_file_header(self, file_path: Path) -> None:
        """Print file header."""
        print(f"\n{Colors.BOLD}Testing documentation in: {Colors.BLUE}{file_path}{Colors.RESET}")
        print()

    def _print_result(self, result: DocTestResult) -> None:
        """Print test result.

        Args:
            result: Test result to print
        """
        # Get location info
        source_file = result.test.source_file
        line_num = result.test.line_number

        if result.passed:
            # Success
            status = f"{Colors.GREEN}✓{Colors.RESET}"
            command = result.test.command

            # Truncate long commands
            if len(command) > 70:
                command = command[:67] + "..."

            location = f"{Colors.GRAY}(line {line_num}){Colors.RESET}"
            print(f"{status} {command} {location}")

            if self.verbose and result.actual_output:
                print(f"{Colors.GRAY}  Output: {result.actual_output[:100]}{Colors.RESET}")
        else:
            # Failure
            status = f"{Colors.RED}✗{Colors.RESET}"
            command = result.test.command

            # Truncate long commands
            if len(command) > 70:
                command = command[:67] + "..."

            location = f"{Colors.GRAY}(line {line_num}){Colors.RESET}"
            print(f"{status} {command} {location}")

            # Print error details
            if result.error_message:
                print(f"{Colors.RED}  {result.error_message}{Colors.RESET}")

            # Print expected vs actual for verbose mode
            if self.verbose:
                if result.test.inline_expectation:
                    expected = result.test.inline_expectation
                    print(f"{Colors.GRAY}  Expected: {expected}{Colors.RESET}")
                elif result.test.expected_output:
                    expected = result.test.expected_output
                    # Truncate long output
                    if len(expected) > 100:
                        expected = expected[:97] + "..."
                    print(f"{Colors.GRAY}  Expected: {expected}{Colors.RESET}")

                if result.actual_output:
                    actual = result.actual_output
                    # Truncate long output
                    if len(actual) > 100:
                        actual = actual[:97] + "..."
                    print(f"{Colors.GRAY}  Got: {actual}{Colors.RESET}")

            print()

    def _print_summary(self, results: List[DocTestResult], total_tests: int) -> bool:
        """Print summary statistics.

        Args:
            results: List of test results
            total_tests: Total number of tests found

        Returns:
            True if all tests passed
        """
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        total_time = sum(r.execution_time for r in results)

        # Print separator
        print(f"{Colors.GRAY}{'━' * 50}{Colors.RESET}")

        # Print results
        if failed == 0:
            status_text = f"{Colors.GREEN}✓ All tests passed!{Colors.RESET}"
        else:
            status_text = f"{Colors.RED}✗ {failed} test(s) failed{Colors.RESET}"

        passed_text = f"{Colors.GREEN}{passed} passed{Colors.RESET}"
        failed_text = f"{Colors.RED}{failed} failed{Colors.RESET}" if failed > 0 else "0 failed"
        total_text = f"{len(results)} total"

        print(f"{status_text}")
        print(f"Results: {passed_text}, {failed_text}, {total_text}")
        print(f"Time: {total_time:.2f}s")

        return failed == 0

    def _generate_junit_report(self, results: List[DocTestResult]) -> None:
        """Generate JUnit XML report.

        Args:
            results: List of test results
        """
        reporter = DocTestJUnitReporter()
        reporter.generate_report(results, self.junit_xml)

    def _print_info(self, message: str) -> None:
        """Print info message.

        Args:
            message: Message to print
        """
        print(f"{Colors.BLUE}ℹ{Colors.RESET} {message}")

    def _print_error(self, message: str) -> None:
        """Print error message.

        Args:
            message: Error message to print
        """
        print(f"{Colors.RED}✗ Error:{Colors.RESET} {message}", file=sys.stderr)
