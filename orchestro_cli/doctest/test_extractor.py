"""Test extractor for parsing command/output pairs from code blocks."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from .models import CodeBlock, CommandTest


class TestExtractor:
    """Extracts testable commands from code blocks.

    Supports two test patterns:

    1. Multi-line output:
       $ command arg1 arg2
       expected line 1
       expected line 2

    2. Inline expectation:
       $ command arg1 arg2  #=> expected output

    The prompt prefix is configurable (default: '$').
    """

    # Pattern for inline expectation: #=> followed by expected output
    INLINE_PATTERN = re.compile(r'#=>\s*(.+)$')

    # Pattern for continuation lines (backslash at end)
    CONTINUATION_PATTERN = re.compile(r'\\\s*$')

    def __init__(
        self,
        prompt_prefix: str = '$',
        skip_comments: bool = True,
        ignore_blank_lines: bool = True
    ):
        """Initialize test extractor.

        Args:
            prompt_prefix: Prefix that indicates a command line (e.g., '$', '>')
            skip_comments: Skip lines starting with '#' (except inline expectations)
            ignore_blank_lines: Ignore blank lines in output
        """
        self.prompt_prefix = prompt_prefix
        self.skip_comments = skip_comments
        self.ignore_blank_lines = ignore_blank_lines

    def extract_tests(
        self,
        code_block: CodeBlock,
        shell_languages: Optional[List[str]] = None
    ) -> List[CommandTest]:
        """Extract command tests from a code block.

        Args:
            code_block: Code block to parse
            shell_languages: Languages to treat as shell code (default: bash, sh, shell)

        Returns:
            List of extracted command tests
        """
        if shell_languages is None:
            shell_languages = ['bash', 'sh', 'shell', 'console', 'terminal']

        # Only process shell code blocks
        if code_block.language.lower() not in shell_languages:
            return []

        tests: List[CommandTest] = []
        lines = code_block.content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].rstrip()

            # Skip blank lines
            if not line and self.ignore_blank_lines:
                i += 1
                continue

            # Skip comment lines (but not inline expectations)
            if self.skip_comments and line.startswith('#') and '#=>' not in line:
                i += 1
                continue

            # Check if line is a command (starts with prompt)
            if line.startswith(self.prompt_prefix):
                # Remove prompt prefix
                command_line = line[len(self.prompt_prefix):].lstrip()

                # Check for inline expectation
                inline_match = self.INLINE_PATTERN.search(command_line)
                if inline_match:
                    # Extract command and expectation
                    command = self.INLINE_PATTERN.sub('', command_line).rstrip()
                    expectation = inline_match.group(1).strip()

                    test = CommandTest(
                        command=command,
                        inline_expectation=expectation,
                        line_number=code_block.line_number + i,
                        source_file=code_block.file_path
                    )
                    tests.append(test)
                    i += 1
                    continue

                # Check for line continuation
                full_command = command_line
                while self.CONTINUATION_PATTERN.search(full_command) and i + 1 < len(lines):
                    # Remove backslash and append next line
                    full_command = self.CONTINUATION_PATTERN.sub('', full_command)
                    i += 1
                    next_line = lines[i].lstrip()
                    if next_line.startswith(self.prompt_prefix):
                        # Next line is a new command, don't continue
                        i -= 1
                        break
                    full_command += ' ' + next_line

                # Collect output lines (multi-line expectation)
                output_lines = []
                i += 1
                while i < len(lines):
                    next_line = lines[i].rstrip()

                    # Stop at next command
                    if next_line.startswith(self.prompt_prefix):
                        break

                    # Skip blank lines if configured
                    if not next_line and self.ignore_blank_lines:
                        i += 1
                        continue

                    # Stop at comment lines (unless they're part of output)
                    if self.skip_comments and next_line.startswith('#'):
                        break

                    output_lines.append(next_line)
                    i += 1

                # Create test with or without expected output
                expected_output = '\n'.join(output_lines) if output_lines else None

                test = CommandTest(
                    command=full_command.strip(),
                    expected_output=expected_output,
                    line_number=code_block.line_number + i - len(output_lines) - 1,
                    source_file=code_block.file_path
                )
                tests.append(test)
                continue

            # Not a command line, skip it
            i += 1

        return tests

    def extract_from_blocks(
        self,
        code_blocks: List[CodeBlock],
        shell_languages: Optional[List[str]] = None
    ) -> List[CommandTest]:
        """Extract tests from multiple code blocks.

        Args:
            code_blocks: List of code blocks to process
            shell_languages: Languages to treat as shell code

        Returns:
            Combined list of all extracted tests
        """
        all_tests: List[CommandTest] = []

        for block in code_blocks:
            tests = self.extract_tests(block, shell_languages)
            all_tests.extend(tests)

        return all_tests

    def get_statistics(self, tests: List[CommandTest]) -> dict:
        """Get statistics about extracted tests.

        Args:
            tests: List of command tests

        Returns:
            Dictionary with statistics
        """
        inline_count = sum(1 for t in tests if t.inline_expectation)
        multiline_count = sum(1 for t in tests if t.expected_output)
        no_expectation_count = sum(1 for t in tests if not t.has_expectation)

        return {
            'total_tests': len(tests),
            'inline_expectations': inline_count,
            'multiline_expectations': multiline_count,
            'no_expectations': no_expectation_count,
            'has_expectations': inline_count + multiline_count
        }
