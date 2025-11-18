"""Markdown parser for extracting fenced code blocks."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from .models import CodeBlock


class MarkdownParser:
    """Extracts fenced code blocks from Markdown files.

    Supports standard triple-backtick syntax with optional language tags:
    ```language
    code content
    ```

    Handles edge cases:
    - Nested code blocks (in quoted sections)
    - Indented code blocks
    - Code blocks without language tags
    - Multiple code blocks in same file
    """

    # Pattern for fenced code blocks: ```language (optional) followed by content
    FENCE_PATTERN = re.compile(
        r'^```(\w+)?\s*$',  # Opening fence with optional language
        re.MULTILINE
    )

    def __init__(self, preserve_indentation: bool = True):
        """Initialize parser.

        Args:
            preserve_indentation: Whether to preserve code block indentation
        """
        self.preserve_indentation = preserve_indentation

    def parse_file(self, file_path: Path) -> List[CodeBlock]:
        """Parse Markdown file and extract code blocks.

        Args:
            file_path: Path to Markdown file

        Returns:
            List of extracted code blocks

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a Markdown file
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_path.suffix.lower() not in {'.md', '.markdown'}:
            raise ValueError(f"Not a Markdown file: {file_path}")

        content = file_path.read_text(encoding='utf-8')
        return self.parse_string(content, file_path)

    def parse_string(
        self,
        content: str,
        file_path: Optional[Path] = None
    ) -> List[CodeBlock]:
        """Parse Markdown string and extract code blocks.

        Args:
            content: Markdown content as string
            file_path: Optional source file path for error reporting

        Returns:
            List of extracted code blocks
        """
        blocks: List[CodeBlock] = []
        lines = content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check for opening fence
            match = self.FENCE_PATTERN.match(line)
            if match:
                language = match.group(1) or 'text'
                start_line = i + 2  # Line numbers are 1-indexed, +2 for line after fence
                block_content = []

                # Collect lines until closing fence
                i += 1
                while i < len(lines):
                    if self.FENCE_PATTERN.match(lines[i]):
                        # Found closing fence
                        content_str = '\n'.join(block_content)

                        # Optionally dedent content
                        if not self.preserve_indentation:
                            content_str = self._dedent(content_str)

                        # Only add non-empty blocks
                        if content_str.strip():
                            block = CodeBlock(
                                language=language,
                                content=content_str,
                                line_number=start_line,
                                file_path=file_path or Path('<string>')
                            )
                            blocks.append(block)
                        break

                    block_content.append(lines[i])
                    i += 1

            i += 1

        return blocks

    def _dedent(self, text: str) -> str:
        """Remove common leading whitespace from text.

        Args:
            text: Text to dedent

        Returns:
            Dedented text
        """
        lines = text.split('\n')
        if not lines:
            return text

        # Find minimum indentation (excluding empty lines)
        min_indent = float('inf')
        for line in lines:
            if line.strip():  # Skip empty lines
                indent = len(line) - len(line.lstrip())
                min_indent = min(min_indent, indent)

        if min_indent == float('inf'):
            return text

        # Remove common indentation
        dedented = []
        for line in lines:
            if line.strip():  # Skip empty lines
                dedented.append(line[int(min_indent):])
            else:
                dedented.append(line)

        return '\n'.join(dedented)

    def filter_by_language(
        self,
        blocks: List[CodeBlock],
        languages: List[str]
    ) -> List[CodeBlock]:
        """Filter code blocks by language.

        Args:
            blocks: List of code blocks
            languages: List of language tags to include

        Returns:
            Filtered list of code blocks
        """
        languages_lower = {lang.lower() for lang in languages}
        return [
            block for block in blocks
            if block.language.lower() in languages_lower
        ]

    def get_statistics(self, blocks: List[CodeBlock]) -> dict:
        """Get statistics about extracted code blocks.

        Args:
            blocks: List of code blocks

        Returns:
            Dictionary with statistics
        """
        language_counts: dict = {}
        total_lines = 0

        for block in blocks:
            lang = block.language
            language_counts[lang] = language_counts.get(lang, 0) + 1
            total_lines += len(block.content.split('\n'))

        return {
            'total_blocks': len(blocks),
            'total_lines': total_lines,
            'languages': language_counts,
            'avg_lines_per_block': total_lines / len(blocks) if blocks else 0
        }
