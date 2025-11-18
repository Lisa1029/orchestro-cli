"""Integration tests for complete doctest workflow."""

from pathlib import Path

import pytest

from orchestro_cli.doctest import (
    MarkdownParser,
    TestExtractor,
    DocTestExecutor,
    MatchMode
)


class TestIntegration:
    """Integration tests showing complete workflow."""

    def test_full_workflow_readme_example(self, tmp_path: Path):
        """Test complete workflow from README to execution."""
        # Create sample README
        readme_content = """# My CLI Tool

## Installation

```bash
$ pip install my-tool
```

## Usage

Basic usage:

```bash
$ my-tool --version  #=> my-tool 1.0.0
$ echo "Hello, World!"
Hello, World!
```

Advanced features:

```bash
$ echo "test"
test
$ printf "line1\\nline2"
line1
line2
```

## API

```python
import my_tool
my_tool.run()
```
"""
        readme = tmp_path / "README.md"
        readme.write_text(readme_content)

        # Step 1: Parse Markdown
        parser = MarkdownParser()
        blocks = parser.parse_file(readme)

        assert len(blocks) == 4  # bash (install), bash (usage), bash (advanced), python
        bash_blocks = parser.filter_by_language(blocks, ['bash'])
        assert len(bash_blocks) == 3

        # Step 2: Extract tests
        extractor = TestExtractor()
        tests = extractor.extract_from_blocks(bash_blocks)

        assert len(tests) == 5  # pip install, --version, echo, echo, printf
        stats = extractor.get_statistics(tests)
        assert stats['inline_expectations'] == 1  # --version command
        assert stats['multiline_expectations'] == 3  # echo commands and printf
        assert stats['no_expectations'] == 1  # pip install

        # Step 3: Execute tests (only commands that will pass)
        executor = DocTestExecutor(match_mode=MatchMode.CONTAINS)

        # Execute only the commands that should work
        executable_tests = [
            t for t in tests
            if 'my-tool' not in t.command  # Skip non-existent tool
        ]

        results = executor.execute_tests(executable_tests)

        # Step 4: Verify results
        assert len(results) == 3  # echo, echo, printf (skipped pip and my-tool)
        passed = [r for r in results if r.passed]
        assert len(passed) >= 2  # At least echo commands should pass

        # Step 5: Get summary
        summary = executor.get_summary(results)
        assert summary['total_tests'] == 3
        assert summary['passed'] >= 2

    def test_workflow_with_statistics(self, sample_markdown: Path):
        """Test workflow with statistics gathering."""
        # Parse
        parser = MarkdownParser()
        blocks = parser.parse_file(sample_markdown)

        parse_stats = parser.get_statistics(blocks)
        assert parse_stats['total_blocks'] > 0

        # Extract
        extractor = TestExtractor()
        tests = extractor.extract_from_blocks(blocks)

        extract_stats = extractor.get_statistics(tests)
        assert extract_stats['total_tests'] > 0

        # Execute
        executor = DocTestExecutor(match_mode=MatchMode.CONTAINS)
        results = executor.execute_tests(tests)

        exec_stats = executor.get_summary(results)
        assert exec_stats['total_tests'] == len(results)

    def test_workflow_with_custom_config(self, tmp_path: Path):
        """Test workflow with custom configuration."""
        # Create Markdown with custom prompt
        content = """# Custom Shell

```console
> echo "custom prompt"
custom prompt
> pwd  #=> /tmp
```
"""
        md_file = tmp_path / "custom.md"
        md_file.write_text(content)

        # Parse with default settings
        parser = MarkdownParser()
        blocks = parser.parse_file(md_file)

        # Extract with custom prompt and language
        extractor = TestExtractor(prompt_prefix='>')
        tests = extractor.extract_from_blocks(
            blocks,
            shell_languages=['console', 'bash', 'shell']
        )

        assert len(tests) == 2

        # Execute with custom match mode
        executor = DocTestExecutor(
            match_mode=MatchMode.CONTAINS,
            strip_whitespace=True,
            timeout=10.0
        )
        results = executor.execute_tests(tests)

        # First test (echo) should pass
        assert results[0].passed is True

    def test_workflow_error_handling(self, tmp_path: Path):
        """Test workflow with error conditions."""
        # Create Markdown with failing commands
        content = """# Error Cases

```bash
$ ls /nonexistent
$ invalid_command_xyz
```
"""
        md_file = tmp_path / "errors.md"
        md_file.write_text(content)

        # Parse and extract
        parser = MarkdownParser()
        blocks = parser.parse_file(md_file)

        extractor = TestExtractor()
        tests = extractor.extract_from_blocks(blocks)

        # Execute - should handle errors gracefully
        executor = DocTestExecutor()
        results = executor.execute_tests(tests, stop_on_failure=False)

        # All should fail but not crash
        assert len(results) == 2
        assert all(not r.passed for r in results)
        assert all(r.error_message for r in results)

    def test_workflow_with_expectations(self, tmp_path: Path):
        """Test workflow focusing on expectation matching."""
        content = """# Expectation Testing

## Inline Expectations

```bash
$ echo hello  #=> hello
$ echo world  #=> world
```

## Multi-line Expectations

```bash
$ printf "a\\nb\\nc"
a
b
c
```

## No Expectations

```bash
$ echo "no check"
$ ls
```
"""
        md_file = tmp_path / "expectations.md"
        md_file.write_text(content)

        parser = MarkdownParser()
        blocks = parser.parse_file(md_file)

        extractor = TestExtractor()
        tests = extractor.extract_from_blocks(blocks)

        # Verify expectation types
        inline_tests = [t for t in tests if t.expectation_type == "inline"]
        multiline_tests = [t for t in tests if t.expectation_type == "multi-line"]
        no_expect_tests = [t for t in tests if t.expectation_type == "none"]

        assert len(inline_tests) == 2
        assert len(multiline_tests) == 1
        assert len(no_expect_tests) == 2

        # Execute
        executor = DocTestExecutor(match_mode=MatchMode.CONTAINS)
        results = executor.execute_tests(tests)

        # Tests with expectations should validate
        inline_results = results[:2]
        assert all(r.passed for r in inline_results)

    def test_workflow_different_match_modes(self, tmp_path: Path):
        """Test workflow with different matching strategies."""
        content = """# Match Modes

```bash
$ echo "hello world"
```
"""
        md_file = tmp_path / "match.md"
        md_file.write_text(content)

        parser = MarkdownParser()
        blocks = parser.parse_file(md_file)

        extractor = TestExtractor()
        tests = extractor.extract_from_blocks(blocks)

        # Add inline expectation manually for testing
        tests[0].inline_expectation = "hello"

        # Test different match modes
        for mode in [MatchMode.CONTAINS, MatchMode.STARTSWITH, MatchMode.REGEX]:
            executor = DocTestExecutor(match_mode=mode)
            result = executor.execute_test(tests[0])
            assert result.passed, f"Failed with mode {mode}"

    def test_workflow_preserves_location_info(self, tmp_path: Path):
        """Test that location information is preserved through workflow."""
        content = """# Test

Line 3

```bash
$ echo one
one
$ echo two
two
```
"""
        md_file = tmp_path / "location.md"
        md_file.write_text(content)

        parser = MarkdownParser()
        blocks = parser.parse_file(md_file)

        extractor = TestExtractor()
        tests = extractor.extract_from_blocks(blocks)

        executor = DocTestExecutor(match_mode=MatchMode.CONTAINS)
        results = executor.execute_tests(tests)

        # Verify location information
        for result in results:
            assert result.test.source_file == md_file
            assert result.test.line_number > 0
            assert str(md_file) in result.location

            summary = result.get_summary()
            assert str(md_file) in summary

    def test_workflow_empty_file(self, tmp_path: Path):
        """Test workflow with empty/minimal file."""
        content = "# Empty\n\nNo code blocks."
        md_file = tmp_path / "empty.md"
        md_file.write_text(content)

        parser = MarkdownParser()
        blocks = parser.parse_file(md_file)
        assert len(blocks) == 0

        extractor = TestExtractor()
        tests = extractor.extract_from_blocks(blocks)
        assert len(tests) == 0

        executor = DocTestExecutor()
        results = executor.execute_tests(tests)
        assert len(results) == 0

        summary = executor.get_summary(results)
        assert summary['total_tests'] == 0
        assert summary['success_rate'] == 0.0
