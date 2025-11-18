"""Tests for documentation testing JUnit reporter."""

import pytest
from pathlib import Path
import tempfile
from xml.etree import ElementTree as ET

from orchestro_cli.doctest.junit_reporter import DocTestJUnitReporter
from orchestro_cli.doctest.models import CommandTest, DocTestResult


@pytest.fixture
def temp_output_dir():
    """Create temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_results():
    """Create sample test results."""
    file_path = Path("test.md")

    # Passing test
    test1 = CommandTest(
        command="echo 'test'",
        inline_expectation="test",
        line_number=10,
        source_file=file_path
    )
    result1 = DocTestResult(
        test=test1,
        passed=True,
        actual_output="test",
        execution_time=0.123
    )

    # Failing test with inline expectation
    test2 = CommandTest(
        command="echo 'wrong'",
        inline_expectation="expected",
        line_number=15,
        source_file=file_path
    )
    result2 = DocTestResult(
        test=test2,
        passed=False,
        actual_output="wrong",
        error_message="Output validation failed (mode: contains)\nExpected: expected\nActual: wrong",
        execution_time=0.234
    )

    # Failing test with multi-line expectation
    test3 = CommandTest(
        command="echo 'multi'",
        expected_output="line1\nline2",
        line_number=20,
        source_file=file_path
    )
    result3 = DocTestResult(
        test=test3,
        passed=False,
        actual_output="multi",
        error_message="Output validation failed",
        execution_time=0.345
    )

    return [result1, result2, result3]


class TestDocTestJUnitReporter:
    """Test JUnit reporter for documentation tests."""

    def test_generate_report_creates_file(self, sample_results, temp_output_dir):
        """Test that report file is created."""
        output_path = temp_output_dir / "results.xml"

        reporter = DocTestJUnitReporter()
        reporter.generate_report(sample_results, output_path)

        assert output_path.exists()

    def test_report_is_valid_xml(self, sample_results, temp_output_dir):
        """Test that generated report is valid XML."""
        output_path = temp_output_dir / "results.xml"

        reporter = DocTestJUnitReporter()
        reporter.generate_report(sample_results, output_path)

        # Parse XML to verify it's valid
        tree = ET.parse(output_path)
        root = tree.getroot()

        assert root.tag == "testsuites"

    def test_report_contains_test_suite(self, sample_results, temp_output_dir):
        """Test that report contains test suite."""
        output_path = temp_output_dir / "results.xml"

        reporter = DocTestJUnitReporter()
        reporter.generate_report(sample_results, output_path)

        tree = ET.parse(output_path)
        root = tree.getroot()

        # Find test suite
        suites = root.findall("testsuite")
        assert len(suites) == 1

        suite = suites[0]
        assert suite.get("name") == "doctest.test"
        assert suite.get("tests") == "3"
        assert suite.get("failures") == "2"
        assert suite.get("errors") == "0"

    def test_report_contains_test_cases(self, sample_results, temp_output_dir):
        """Test that report contains test cases."""
        output_path = temp_output_dir / "results.xml"

        reporter = DocTestJUnitReporter()
        reporter.generate_report(sample_results, output_path)

        tree = ET.parse(output_path)
        suite = tree.find(".//testsuite")
        test_cases = suite.findall("testcase")

        assert len(test_cases) == 3

    def test_passing_test_case_format(self, sample_results, temp_output_dir):
        """Test format of passing test case."""
        output_path = temp_output_dir / "results.xml"

        reporter = DocTestJUnitReporter()
        reporter.generate_report(sample_results, output_path)

        tree = ET.parse(output_path)
        test_cases = tree.findall(".//testcase")

        # First test case is passing
        passing = test_cases[0]
        assert passing.get("name").startswith("line_10_")
        assert passing.get("classname") == "doctest.test"
        assert float(passing.get("time")) > 0

        # Should not have failure element
        failures = passing.findall("failure")
        assert len(failures) == 0

    def test_failing_test_case_format(self, sample_results, temp_output_dir):
        """Test format of failing test case."""
        output_path = temp_output_dir / "results.xml"

        reporter = DocTestJUnitReporter()
        reporter.generate_report(sample_results, output_path)

        tree = ET.parse(output_path)
        test_cases = tree.findall(".//testcase")

        # Second test case is failing
        failing = test_cases[1]
        assert failing.get("name").startswith("line_15_")

        # Should have failure element
        failures = failing.findall("failure")
        assert len(failures) == 1

        failure = failures[0]
        assert failure.get("type") == "OutputMismatch"
        assert failure.get("message") is not None
        assert failure.text is not None
        assert "Command:" in failure.text
        assert "echo 'wrong'" in failure.text

    def test_failure_with_expected_output(self, sample_results, temp_output_dir):
        """Test failure includes expected output."""
        output_path = temp_output_dir / "results.xml"

        reporter = DocTestJUnitReporter()
        reporter.generate_report(sample_results, output_path)

        tree = ET.parse(output_path)
        test_cases = tree.findall(".//testcase")

        # Second test has inline expectation
        failing = test_cases[1]
        failure = failing.find("failure")
        assert "Expected: expected" in failure.text

        # Third test has multi-line expectation
        failing = test_cases[2]
        failure = failing.find("failure")
        assert "Expected output:" in failure.text
        assert "line1" in failure.text

    def test_system_out_included(self, sample_results, temp_output_dir):
        """Test that actual output is included in system-out."""
        output_path = temp_output_dir / "results.xml"

        reporter = DocTestJUnitReporter()
        reporter.generate_report(sample_results, output_path)

        tree = ET.parse(output_path)
        test_cases = tree.findall(".//testcase")

        # Check first test has system-out
        system_out = test_cases[0].find("system-out")
        assert system_out is not None
        assert system_out.text == "test"

    def test_group_by_file(self, temp_output_dir):
        """Test grouping results by source file."""
        file1 = Path("test1.md")
        file2 = Path("test2.md")

        # Create results from different files
        test1 = CommandTest(command="cmd1", line_number=1, source_file=file1)
        result1 = DocTestResult(test=test1, passed=True, execution_time=0.1)

        test2 = CommandTest(command="cmd2", line_number=1, source_file=file2)
        result2 = DocTestResult(test=test2, passed=True, execution_time=0.1)

        test3 = CommandTest(command="cmd3", line_number=2, source_file=file1)
        result3 = DocTestResult(test=test3, passed=True, execution_time=0.1)

        results = [result1, result2, result3]

        reporter = DocTestJUnitReporter()
        grouped = reporter._group_by_file(results)

        assert len(grouped) == 2
        assert file1 in grouped
        assert file2 in grouped
        assert len(grouped[file1]) == 2
        assert len(grouped[file2]) == 1

    def test_multiple_files_create_multiple_suites(self, temp_output_dir):
        """Test that multiple files create multiple test suites."""
        file1 = Path("test1.md")
        file2 = Path("test2.md")

        test1 = CommandTest(command="cmd1", line_number=1, source_file=file1)
        result1 = DocTestResult(test=test1, passed=True, execution_time=0.1)

        test2 = CommandTest(command="cmd2", line_number=1, source_file=file2)
        result2 = DocTestResult(test=test2, passed=True, execution_time=0.1)

        results = [result1, result2]
        output_path = temp_output_dir / "results.xml"

        reporter = DocTestJUnitReporter()
        reporter.generate_report(results, output_path)

        tree = ET.parse(output_path)
        suites = tree.findall(".//testsuite")

        assert len(suites) == 2

        suite_names = {suite.get("name") for suite in suites}
        assert "doctest.test1" in suite_names
        assert "doctest.test2" in suite_names

    def test_sanitize_name(self):
        """Test name sanitization for XML."""
        reporter = DocTestJUnitReporter()

        # Test basic sanitization
        assert reporter._sanitize_name("echo test") == "echo_test"
        assert reporter._sanitize_name("test-command") == "test-command"
        assert reporter._sanitize_name("test.sh") == "test.sh"

        # Test special characters removed
        assert reporter._sanitize_name("test@#$%") == "test"

        # Test truncation
        long_name = "a" * 100
        sanitized = reporter._sanitize_name(long_name)
        assert len(sanitized) <= 50

    def test_timeout_failure_type(self, temp_output_dir):
        """Test that timeout failures are properly typed."""
        test = CommandTest(
            command="sleep 100",
            line_number=1,
            source_file=Path("test.md")
        )
        result = DocTestResult(
            test=test,
            passed=False,
            error_message="Command timed out after 30s",
            execution_time=30.0
        )

        output_path = temp_output_dir / "results.xml"

        reporter = DocTestJUnitReporter()
        reporter.generate_report([result], output_path)

        tree = ET.parse(output_path)
        failure = tree.find(".//failure")

        assert failure.get("type") == "TimeoutError"

    def test_command_error_failure_type(self, temp_output_dir):
        """Test that command errors are properly typed."""
        test = CommandTest(
            command="false",
            line_number=1,
            source_file=Path("test.md")
        )
        result = DocTestResult(
            test=test,
            passed=False,
            error_message="Command failed with exit code 1",
            execution_time=0.1
        )

        output_path = temp_output_dir / "results.xml"

        reporter = DocTestJUnitReporter()
        reporter.generate_report([result], output_path)

        tree = ET.parse(output_path)
        failure = tree.find(".//failure")

        assert failure.get("type") == "CommandError"

    def test_output_mismatch_failure_type(self, temp_output_dir):
        """Test that output mismatches are properly typed."""
        test = CommandTest(
            command="echo wrong",
            inline_expectation="expected",
            line_number=1,
            source_file=Path("test.md")
        )
        result = DocTestResult(
            test=test,
            passed=False,
            actual_output="wrong",
            error_message="Output validation failed",
            execution_time=0.1
        )

        output_path = temp_output_dir / "results.xml"

        reporter = DocTestJUnitReporter()
        reporter.generate_report([result], output_path)

        tree = ET.parse(output_path)
        failure = tree.find(".//failure")

        assert failure.get("type") == "OutputMismatch"

    def test_empty_results_list(self, temp_output_dir):
        """Test handling of empty results list."""
        output_path = temp_output_dir / "results.xml"

        reporter = DocTestJUnitReporter()
        reporter.generate_report([], output_path)

        assert output_path.exists()

        tree = ET.parse(output_path)
        root = tree.getroot()
        assert root.tag == "testsuites"

    def test_suite_metadata(self, sample_results, temp_output_dir):
        """Test that suite metadata is included."""
        output_path = temp_output_dir / "results.xml"

        reporter = DocTestJUnitReporter()
        reporter.generate_report(sample_results, output_path)

        tree = ET.parse(output_path)
        suite = tree.find(".//testsuite")

        assert suite.get("timestamp") is not None
        assert suite.get("hostname") is not None
        assert float(suite.get("time")) > 0
