"""Tests for Markdown parser."""

from pathlib import Path

import pytest

from orchestro_cli.doctest import MarkdownParser, CodeBlock


class TestMarkdownParser:
    """Tests for MarkdownParser class."""

    def test_parse_file_basic(self, sample_markdown: Path):
        """Test parsing a basic Markdown file."""
        parser = MarkdownParser()
        blocks = parser.parse_file(sample_markdown)

        assert len(blocks) > 0
        assert all(isinstance(block, CodeBlock) for block in blocks)

    def test_parse_file_not_found(self):
        """Test parsing non-existent file raises error."""
        parser = MarkdownParser()

        with pytest.raises(FileNotFoundError):
            parser.parse_file(Path("nonexistent.md"))

    def test_parse_file_not_markdown(self, tmp_path: Path):
        """Test parsing non-Markdown file raises error."""
        parser = MarkdownParser()
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Not markdown")

        with pytest.raises(ValueError, match="Not a Markdown file"):
            parser.parse_file(txt_file)

    def test_parse_string_single_block(self):
        """Test parsing string with single code block."""
        content = """# Test

```bash
echo "hello"
```
"""
        parser = MarkdownParser()
        blocks = parser.parse_string(content)

        assert len(blocks) == 1
        assert blocks[0].language == "bash"
        assert "echo" in blocks[0].content
        assert blocks[0].line_number == 4  # Line after opening fence

    def test_parse_string_multiple_blocks(self):
        """Test parsing string with multiple code blocks."""
        content = """# Test

```bash
echo "one"
```

Some text

```python
print("two")
```
"""
        parser = MarkdownParser()
        blocks = parser.parse_string(content)

        assert len(blocks) == 2
        assert blocks[0].language == "bash"
        assert blocks[1].language == "python"

    def test_parse_string_no_language_tag(self):
        """Test parsing code block without language tag."""
        content = """```
generic code
```"""
        parser = MarkdownParser()
        blocks = parser.parse_string(content)

        assert len(blocks) == 1
        assert blocks[0].language == "text"

    def test_parse_string_empty_block_ignored(self):
        """Test that empty code blocks are ignored."""
        content = """```bash

```

```python
print("hello")
```
"""
        parser = MarkdownParser()
        blocks = parser.parse_string(content)

        # Empty bash block should be ignored
        assert len(blocks) == 1
        assert blocks[0].language == "python"

    def test_parse_string_preserves_indentation(self):
        """Test that indentation is preserved by default."""
        content = """```python
def hello():
    print("hello")
    if True:
        pass
```"""
        parser = MarkdownParser(preserve_indentation=True)
        blocks = parser.parse_string(content)

        assert len(blocks) == 1
        assert "    print" in blocks[0].content  # Indentation preserved

    def test_parse_string_dedent_mode(self):
        """Test dedenting code blocks."""
        content = """```python
    def hello():
        print("hello")
```"""
        parser = MarkdownParser(preserve_indentation=False)
        blocks = parser.parse_string(content)

        assert len(blocks) == 1
        # Common indentation should be removed
        assert blocks[0].content.startswith("def")

    def test_parse_string_unclosed_fence(self):
        """Test handling of unclosed code fence."""
        content = """```bash
echo "never closed
"""
        parser = MarkdownParser()
        blocks = parser.parse_string(content)

        # Unclosed fence should not create a block
        assert len(blocks) == 0

    def test_parse_string_nested_in_quote(self):
        """Test parsing code block in quote (edge case)."""
        content = """> Quote text
> ```bash
> echo "quoted"
> ```
"""
        parser = MarkdownParser()
        blocks = parser.parse_string(content)

        # Quoted code blocks are not extracted (lines don't start with ```)
        # This is expected behavior - quote markers break the fence pattern
        assert len(blocks) == 0

    def test_filter_by_language(self):
        """Test filtering blocks by language."""
        content = """```bash
echo "bash"
```

```python
print("python")
```

```bash
echo "more bash"
```
"""
        parser = MarkdownParser()
        blocks = parser.parse_string(content)

        bash_blocks = parser.filter_by_language(blocks, ["bash"])
        assert len(bash_blocks) == 2
        assert all(b.language == "bash" for b in bash_blocks)

        python_blocks = parser.filter_by_language(blocks, ["python"])
        assert len(python_blocks) == 1
        assert python_blocks[0].language == "python"

    def test_filter_by_language_case_insensitive(self):
        """Test that language filtering is case-insensitive."""
        content = """```BASH
echo "uppercase"
```"""
        parser = MarkdownParser()
        blocks = parser.parse_string(content)

        filtered = parser.filter_by_language(blocks, ["bash"])
        assert len(filtered) == 1

    def test_get_statistics(self):
        """Test getting statistics about blocks."""
        content = """```bash
echo "line 1"
echo "line 2"
```

```python
print("one")
```

```bash
echo "three"
```
"""
        parser = MarkdownParser()
        blocks = parser.parse_string(content)

        stats = parser.get_statistics(blocks)

        assert stats['total_blocks'] == 3
        assert stats['languages']['bash'] == 2
        assert stats['languages']['python'] == 1
        assert stats['total_lines'] > 0
        assert stats['avg_lines_per_block'] > 0

    def test_get_statistics_empty(self):
        """Test statistics with no blocks."""
        parser = MarkdownParser()
        stats = parser.get_statistics([])

        assert stats['total_blocks'] == 0
        assert stats['total_lines'] == 0
        assert stats['avg_lines_per_block'] == 0

    def test_line_numbers_accurate(self, sample_markdown: Path):
        """Test that line numbers are accurately tracked."""
        parser = MarkdownParser()
        blocks = parser.parse_file(sample_markdown)

        # All blocks should have valid line numbers
        assert all(b.line_number > 0 for b in blocks)

        # Line numbers should be increasing (blocks appear in order)
        line_numbers = [b.line_number for b in blocks]
        assert line_numbers == sorted(line_numbers)

    def test_file_path_preserved(self, sample_markdown: Path):
        """Test that file path is preserved in blocks."""
        parser = MarkdownParser()
        blocks = parser.parse_file(sample_markdown)

        assert all(b.file_path == sample_markdown for b in blocks)

    def test_empty_markdown_file(self, empty_markdown: Path):
        """Test parsing Markdown file with no code blocks."""
        parser = MarkdownParser()
        blocks = parser.parse_file(empty_markdown)

        assert len(blocks) == 0

    def test_complex_markdown_file(self, complex_markdown: Path):
        """Test parsing complex Markdown with edge cases."""
        parser = MarkdownParser()
        blocks = parser.parse_file(complex_markdown)

        # Should handle various edge cases without crashing
        assert len(blocks) >= 0
        assert all(isinstance(b, CodeBlock) for b in blocks)
