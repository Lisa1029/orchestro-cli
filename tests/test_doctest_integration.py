"""Integration tests for orchestro doctest command."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cli(args, **kwargs):
    """Run the Orchestro CLI with the repository on PYTHONPATH."""
    env = kwargs.pop("env", None) or os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(PROJECT_ROOT), env.get("PYTHONPATH", "")]
    ).strip(os.pathsep)
    return subprocess.run(args, env=env, **kwargs)


@pytest.fixture
def temp_dir():
    """Create temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_markdown(temp_dir):
    """Create sample Markdown file with tests."""
    content = """# Sample Documentation

## Basic Commands

```bash
$ echo "hello world"
hello world

$ echo "inline test"  #=> inline test
```

## More Examples

```bash
$ true
```
"""
    md_file = temp_dir / "sample.md"
    md_file.write_text(content)
    return md_file


@pytest.fixture
def failing_markdown(temp_dir):
    """Create Markdown file with failing test."""
    content = """# Failing Tests

```bash
$ echo "wrong"
expected output
```
"""
    md_file = temp_dir / "failing.md"
    md_file.write_text(content)
    return md_file


class TestDoctestCLI:
    """Integration tests for orchestro doctest CLI."""

    def test_doctest_help(self):
        """Test that doctest help works."""
        result = run_cli(
            [sys.executable, "-m", "orchestro_cli.cli", "doctest", "--help"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Markdown file(s) to test" in result.stdout
        assert "--verbose" in result.stdout
        assert "--fail-fast" in result.stdout
        assert "--junit-xml" in result.stdout

    def test_doctest_success(self, sample_markdown):
        """Test successful doctest run."""
        result = run_cli(
            [sys.executable, "-m", "orchestro_cli.cli", "doctest", str(sample_markdown)],
            capture_output=True,
            text=True,
            cwd=sample_markdown.parent
        )

        assert result.returncode == 0
        assert "Testing documentation in:" in result.stdout
        assert "passed" in result.stdout

    def test_doctest_failure(self, failing_markdown):
        """Test failing doctest run."""
        result = run_cli(
            [sys.executable, "-m", "orchestro_cli.cli", "doctest", str(failing_markdown)],
            capture_output=True,
            text=True,
            cwd=failing_markdown.parent
        )

        assert result.returncode == 1
        assert "failed" in result.stdout

    def test_doctest_verbose(self, sample_markdown):
        """Test verbose output."""
        result = run_cli(
            [
                sys.executable, "-m", "orchestro_cli.cli",
                "doctest", str(sample_markdown),
                "--verbose"
            ],
            capture_output=True,
            text=True,
            cwd=sample_markdown.parent
        )

        assert result.returncode == 0
        assert "Found" in result.stdout

    def test_doctest_fail_fast(self, temp_dir):
        """Test fail-fast mode."""
        # Create file with multiple tests, first one fails
        md_file = temp_dir / "failfast.md"
        md_file.write_text("""
```bash
$ echo "first"
wrong

$ echo "second"
second
```
""")

        result = run_cli(
            [
                sys.executable, "-m", "orchestro_cli.cli",
                "doctest", str(md_file),
                "--fail-fast"
            ],
            capture_output=True,
            text=True,
            cwd=temp_dir
        )

        assert result.returncode == 1

    def test_doctest_junit_xml(self, sample_markdown, temp_dir):
        """Test JUnit XML report generation."""
        junit_file = temp_dir / "results.xml"

        result = run_cli(
            [
                sys.executable, "-m", "orchestro_cli.cli",
                "doctest", str(sample_markdown),
                "--junit-xml", str(junit_file)
            ],
            capture_output=True,
            text=True,
            cwd=temp_dir
        )

        assert result.returncode == 0
        assert junit_file.exists()

        # Verify XML content
        xml_content = junit_file.read_text()
        assert '<?xml version' in xml_content
        assert '<testsuites>' in xml_content

    def test_doctest_multiple_files(self, temp_dir):
        """Test processing multiple files."""
        file1 = temp_dir / "file1.md"
        file1.write_text("""
```bash
$ echo "test1"
test1
```
""")

        file2 = temp_dir / "file2.md"
        file2.write_text("""
```bash
$ echo "test2"
test2
```
""")

        result = run_cli(
            [
                sys.executable, "-m", "orchestro_cli.cli",
                "doctest", str(file1), str(file2)
            ],
            capture_output=True,
            text=True,
            cwd=temp_dir
        )

        assert result.returncode == 0
        assert "file1.md" in result.stdout
        assert "file2.md" in result.stdout

    def test_doctest_custom_prefix(self, temp_dir):
        """Test custom prompt prefix."""
        md_file = temp_dir / "custom.md"
        md_file.write_text("""
```bash
> echo "test"
test
```
""")

        result = run_cli(
            [
                sys.executable, "-m", "orchestro_cli.cli",
                "doctest", str(md_file),
                "--prefix", ">"
            ],
            capture_output=True,
            text=True,
            cwd=temp_dir
        )

        assert result.returncode == 0

    def test_doctest_match_mode_exact(self, temp_dir):
        """Test exact match mode."""
        md_file = temp_dir / "exact.md"
        md_file.write_text("""
```bash
$ echo "test"
test
```
""")

        result = run_cli(
            [
                sys.executable, "-m", "orchestro_cli.cli",
                "doctest", str(md_file),
                "--match-mode", "exact"
            ],
            capture_output=True,
            text=True,
            cwd=temp_dir
        )

        assert result.returncode == 0

    def test_doctest_nonexistent_file(self):
        """Test error handling for nonexistent file."""
        result = run_cli(
            [
                sys.executable, "-m", "orchestro_cli.cli",
                "doctest", "/nonexistent/file.md"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 1
        assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()

    def test_doctest_no_color(self, sample_markdown):
        """Test no-color option."""
        result = run_cli(
            [
                sys.executable, "-m", "orchestro_cli.cli",
                "doctest", str(sample_markdown),
                "--no-color"
            ],
            capture_output=True,
            text=True,
            cwd=sample_markdown.parent
        )

        assert result.returncode == 0
        # Should not contain ANSI color codes
        assert '\033[' not in result.stdout

    def test_doctest_timeout(self, temp_dir):
        """Test timeout configuration."""
        md_file = temp_dir / "timeout.md"
        md_file.write_text("""
```bash
$ echo "quick"
quick
```
""")

        result = run_cli(
            [
                sys.executable, "-m", "orchestro_cli.cli",
                "doctest", str(md_file),
                "--timeout", "1.0"
            ],
            capture_output=True,
            text=True,
            cwd=temp_dir
        )

        assert result.returncode == 0

    def test_doctest_working_dir(self, temp_dir, sample_markdown):
        """Test custom working directory."""
        result = run_cli(
            [
                sys.executable, "-m", "orchestro_cli.cli",
                "doctest", str(sample_markdown),
                "--working-dir", str(temp_dir)
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    def test_doctest_with_comments(self, temp_dir):
        """Test that comments are handled correctly."""
        md_file = temp_dir / "comments.md"
        md_file.write_text("""
```bash
# This is a comment
$ echo "test"
test
# Another comment
```
""")

        result = run_cli(
            [sys.executable, "-m", "orchestro_cli.cli", "doctest", str(md_file)],
            capture_output=True,
            text=True,
            cwd=temp_dir
        )

        assert result.returncode == 0

    def test_doctest_empty_markdown(self, temp_dir):
        """Test handling of Markdown with no code blocks."""
        md_file = temp_dir / "empty.md"
        md_file.write_text("""# Just Text

No code blocks here.
""")

        result = run_cli(
            [sys.executable, "-m", "orchestro_cli.cli", "doctest", str(md_file)],
            capture_output=True,
            text=True,
            cwd=temp_dir
        )

        assert result.returncode == 0
        assert "No tests found" in result.stdout

    def test_doctest_mixed_languages(self, temp_dir):
        """Test that only shell blocks are tested."""
        md_file = temp_dir / "mixed.md"
        md_file.write_text("""
```python
print("not tested")
```

```bash
$ echo "tested"
tested
```
""")

        result = run_cli(
            [sys.executable, "-m", "orchestro_cli.cli", "doctest", str(md_file)],
            capture_output=True,
            text=True,
            cwd=temp_dir
        )

        assert result.returncode == 0
        # Should only run bash test
        assert "1 total" in result.stdout or "1 passed" in result.stdout
