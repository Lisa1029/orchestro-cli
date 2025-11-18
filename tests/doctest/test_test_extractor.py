"""Tests for test extractor."""

from pathlib import Path

import pytest

from orchestro_cli.doctest import CodeBlock, TestExtractor, CommandTest


class TestTestExtractor:
    """Tests for TestExtractor class."""

    def test_extract_inline_expectation(self):
        """Test extracting command with inline expectation."""
        block = CodeBlock(
            language="bash",
            content="$ echo hello  #=> hello",
            line_number=1,
            file_path=Path("test.md")
        )

        extractor = TestExtractor()
        tests = extractor.extract_tests(block)

        assert len(tests) == 1
        assert tests[0].command == "echo hello"
        assert tests[0].inline_expectation == "hello"
        assert tests[0].expectation_type == "inline"

    def test_extract_multiline_expectation(self):
        """Test extracting command with multi-line output."""
        block = CodeBlock(
            language="bash",
            content="""$ ls -la
file1.txt
file2.txt
total 2 files""",
            line_number=1,
            file_path=Path("test.md")
        )

        extractor = TestExtractor()
        tests = extractor.extract_tests(block)

        assert len(tests) == 1
        assert tests[0].command == "ls -la"
        assert "file1.txt" in tests[0].expected_output
        assert "file2.txt" in tests[0].expected_output
        assert tests[0].expectation_type == "multi-line"

    def test_extract_no_expectation(self):
        """Test extracting command without expectation."""
        block = CodeBlock(
            language="bash",
            content="$ echo test",
            line_number=1,
            file_path=Path("test.md")
        )

        extractor = TestExtractor()
        tests = extractor.extract_tests(block)

        assert len(tests) == 1
        assert tests[0].command == "echo test"
        assert not tests[0].has_expectation

    def test_extract_multiple_commands(self):
        """Test extracting multiple commands from one block."""
        block = CodeBlock(
            language="bash",
            content="""$ echo first
first
$ echo second
second
$ echo third  #=> third""",
            line_number=1,
            file_path=Path("test.md")
        )

        extractor = TestExtractor()
        tests = extractor.extract_tests(block)

        assert len(tests) == 3
        assert tests[0].command == "echo first"
        assert tests[1].command == "echo second"
        assert tests[2].command == "echo third"
        assert tests[2].inline_expectation == "third"

    def test_extract_skip_comments(self):
        """Test that comment lines are skipped."""
        block = CodeBlock(
            language="bash",
            content="""# This is a comment
$ echo hello
hello
# Another comment
$ echo world
world""",
            line_number=1,
            file_path=Path("test.md")
        )

        extractor = TestExtractor(skip_comments=True)
        tests = extractor.extract_tests(block)

        assert len(tests) == 2
        assert tests[0].command == "echo hello"
        assert tests[1].command == "echo world"

    def test_extract_line_continuation(self):
        """Test handling line continuation with backslash."""
        block = CodeBlock(
            language="bash",
            content="""$ echo "line one" \\
  "line two" \\
  "line three"
line one line two line three""",
            line_number=1,
            file_path=Path("test.md")
        )

        extractor = TestExtractor()
        tests = extractor.extract_tests(block)

        assert len(tests) == 1
        assert "line one" in tests[0].command
        assert "line two" in tests[0].command
        assert "line three" in tests[0].command

    def test_extract_custom_prompt(self):
        """Test using custom prompt prefix."""
        block = CodeBlock(
            language="bash",
            content="""> echo hello
hello""",
            line_number=1,
            file_path=Path("test.md")
        )

        extractor = TestExtractor(prompt_prefix='>')
        tests = extractor.extract_tests(block)

        assert len(tests) == 1
        assert tests[0].command == "echo hello"

    def test_extract_ignore_blank_lines(self):
        """Test ignoring blank lines in output."""
        block = CodeBlock(
            language="bash",
            content="""$ echo test

test

""",
            line_number=1,
            file_path=Path("test.md")
        )

        extractor = TestExtractor(ignore_blank_lines=True)
        tests = extractor.extract_tests(block)

        assert len(tests) == 1
        # Blank lines should not be in expected output
        assert tests[0].expected_output == "test"

    def test_extract_preserve_blank_lines(self):
        """Test preserving blank lines when configured."""
        block = CodeBlock(
            language="bash",
            content="""$ echo test

output with blank

line""",
            line_number=1,
            file_path=Path("test.md")
        )

        extractor = TestExtractor(ignore_blank_lines=False)
        tests = extractor.extract_tests(block)

        assert len(tests) == 1
        # Blank lines should be preserved
        assert "\n\n" in tests[0].expected_output

    def test_extract_non_shell_language_ignored(self):
        """Test that non-shell languages are ignored."""
        block = CodeBlock(
            language="python",
            content="""$ echo hello
hello""",
            line_number=1,
            file_path=Path("test.md")
        )

        extractor = TestExtractor()
        tests = extractor.extract_tests(block)

        # Python block should be ignored
        assert len(tests) == 0

    def test_extract_custom_shell_languages(self):
        """Test using custom shell language list."""
        block = CodeBlock(
            language="powershell",
            content="$ echo hello\nhello",
            line_number=1,
            file_path=Path("test.md")
        )

        extractor = TestExtractor()
        tests = extractor.extract_tests(
            block,
            shell_languages=['powershell', 'bash']
        )

        assert len(tests) == 1
        assert tests[0].command == "echo hello"

    def test_extract_from_blocks(self):
        """Test extracting from multiple blocks."""
        blocks = [
            CodeBlock(
                language="bash",
                content="$ echo one\none",
                line_number=1,
                file_path=Path("test.md")
            ),
            CodeBlock(
                language="python",
                content="print('skip')",
                line_number=5,
                file_path=Path("test.md")
            ),
            CodeBlock(
                language="bash",
                content="$ echo two\ntwo",
                line_number=10,
                file_path=Path("test.md")
            ),
        ]

        extractor = TestExtractor()
        tests = extractor.extract_from_blocks(blocks)

        # Should extract from bash blocks only
        assert len(tests) == 2
        assert tests[0].command == "echo one"
        assert tests[1].command == "echo two"

    def test_extract_line_numbers_accurate(self):
        """Test that line numbers are accurately tracked."""
        block = CodeBlock(
            language="bash",
            content="""$ echo first
first
$ echo second
second""",
            line_number=10,  # Block starts at line 10
            file_path=Path("test.md")
        )

        extractor = TestExtractor()
        tests = extractor.extract_tests(block)

        assert len(tests) == 2
        # Line numbers should be relative to block start
        assert tests[0].line_number == 10  # First command at block start
        assert tests[1].line_number > tests[0].line_number

    def test_extract_source_file_preserved(self):
        """Test that source file is preserved in tests."""
        block = CodeBlock(
            language="bash",
            content="$ echo test\ntest",
            line_number=1,
            file_path=Path("docs/README.md")
        )

        extractor = TestExtractor()
        tests = extractor.extract_tests(block)

        assert len(tests) == 1
        assert tests[0].source_file == Path("docs/README.md")

    def test_get_statistics(self):
        """Test getting statistics about extracted tests."""
        tests = [
            CommandTest(command="cmd1", inline_expectation="out1", line_number=1),
            CommandTest(command="cmd2", expected_output="out2", line_number=2),
            CommandTest(command="cmd3", line_number=3),  # No expectation
            CommandTest(command="cmd4", inline_expectation="out4", line_number=4),
        ]

        extractor = TestExtractor()
        stats = extractor.get_statistics(tests)

        assert stats['total_tests'] == 4
        assert stats['inline_expectations'] == 2
        assert stats['multiline_expectations'] == 1
        assert stats['no_expectations'] == 1
        assert stats['has_expectations'] == 3

    def test_get_statistics_empty(self):
        """Test statistics with no tests."""
        extractor = TestExtractor()
        stats = extractor.get_statistics([])

        assert stats['total_tests'] == 0
        assert stats['inline_expectations'] == 0
        assert stats['multiline_expectations'] == 0
        assert stats['no_expectations'] == 0

    def test_extract_inline_comment_preserved(self):
        """Test that inline comments (non-expectation) are handled."""
        block = CodeBlock(
            language="bash",
            content="$ echo hello  # this is a comment, not expectation",
            line_number=1,
            file_path=Path("test.md")
        )

        extractor = TestExtractor()
        tests = extractor.extract_tests(block)

        assert len(tests) == 1
        # Comment should be part of command (no #=> marker)
        assert "echo hello" in tests[0].command
        assert not tests[0].has_expectation

    def test_extract_whitespace_handling(self):
        """Test proper whitespace handling in commands."""
        block = CodeBlock(
            language="bash",
            content="$    echo   hello   #=>   world  ",
            line_number=1,
            file_path=Path("test.md")
        )

        extractor = TestExtractor()
        tests = extractor.extract_tests(block)

        assert len(tests) == 1
        # Leading/trailing whitespace should be stripped
        assert tests[0].command.strip() == "echo   hello"
        assert tests[0].inline_expectation.strip() == "world"
