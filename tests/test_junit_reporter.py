"""Tests for JUnit XML report generation."""

import time
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from orchestro_cli.junit_reporter import (
    JUnitReporter,
    ScenarioTestResult,
    TestCase,
    TestSuite,
)


class TestTestCase:
    """Tests for TestCase dataclass."""

    def test_test_case_success(self):
        """Test creating a successful test case."""
        test_case = TestCase(
            name="test_example",
            classname="orchestro",
            time=1.5,
            system_out="Test output",
        )

        assert test_case.name == "test_example"
        assert test_case.classname == "orchestro"
        assert test_case.time == 1.5
        assert test_case.system_out == "Test output"
        assert test_case.failure_message is None
        assert test_case.error_message is None
        assert not test_case.skipped

    def test_test_case_failure(self):
        """Test creating a failed test case."""
        test_case = TestCase(
            name="test_example",
            classname="orchestro",
            time=1.5,
            failure_message="Assertion failed",
            failure_type="AssertionError",
            failure_traceback="Traceback...",
        )

        assert test_case.failure_message == "Assertion failed"
        assert test_case.failure_type == "AssertionError"
        assert test_case.failure_traceback == "Traceback..."

    def test_test_case_error(self):
        """Test creating a test case with error."""
        test_case = TestCase(
            name="test_example",
            classname="orchestro",
            time=1.5,
            error_message="Runtime error",
            error_type="RuntimeError",
            error_traceback="Traceback...",
        )

        assert test_case.error_message == "Runtime error"
        assert test_case.error_type == "RuntimeError"
        assert test_case.error_traceback == "Traceback..."

    def test_test_case_skipped(self):
        """Test creating a skipped test case."""
        test_case = TestCase(
            name="test_example",
            classname="orchestro",
            time=0.0,
            skipped=True,
            skipped_message="Test skipped",
        )

        assert test_case.skipped
        assert test_case.skipped_message == "Test skipped"


class TestTestSuite:
    """Tests for TestSuite dataclass."""

    def test_test_suite_properties(self):
        """Test test suite computed properties."""
        test_cases = [
            TestCase(name="test1", time=1.0),
            TestCase(name="test2", time=2.0, failure_message="Failed"),
            TestCase(name="test3", time=0.5, error_message="Error"),
            TestCase(name="test4", time=0.0, skipped=True),
        ]

        suite = TestSuite(name="My Suite", test_cases=test_cases)

        assert suite.tests == 4
        assert suite.failures == 1
        assert suite.errors == 1
        assert suite.skipped == 1
        assert suite.time == 3.5

    def test_empty_test_suite(self):
        """Test empty test suite."""
        suite = TestSuite(name="Empty Suite")

        assert suite.tests == 0
        assert suite.failures == 0
        assert suite.errors == 0
        assert suite.skipped == 0
        assert suite.time == 0.0


class TestJUnitReporter:
    """Tests for JUnitReporter."""

    def test_add_test_suite(self):
        """Test adding test suites to reporter."""
        reporter = JUnitReporter()
        suite1 = TestSuite(name="Suite1")
        suite2 = TestSuite(name="Suite2")

        reporter.add_test_suite(suite1)
        reporter.add_test_suite(suite2)

        assert len(reporter.test_suites) == 2
        assert reporter.test_suites[0] == suite1
        assert reporter.test_suites[1] == suite2

    def test_generate_xml_success(self, tmp_path: Path):
        """Test generating XML for successful test."""
        reporter = JUnitReporter()
        test_case = TestCase(
            name="My Test",
            classname="orchestro",
            time=2.5,
            system_out="Test output here",
        )
        suite = TestSuite(name="My Suite", test_cases=[test_case])
        reporter.add_test_suite(suite)

        output_path = tmp_path / "junit.xml"
        reporter.generate_xml(output_path)

        # Verify file was created
        assert output_path.exists()

        # Parse and verify XML structure
        tree = ET.parse(output_path)
        root = tree.getroot()

        assert root.tag == "testsuites"
        testsuites = root.findall("testsuite")
        assert len(testsuites) == 1

        testsuite = testsuites[0]
        assert testsuite.get("name") == "My Suite"
        assert testsuite.get("tests") == "1"
        assert testsuite.get("failures") == "0"
        assert testsuite.get("errors") == "0"
        assert testsuite.get("skipped") == "0"
        assert testsuite.get("time") == "2.500"

        testcases = testsuite.findall("testcase")
        assert len(testcases) == 1

        testcase = testcases[0]
        assert testcase.get("name") == "My Test"
        assert testcase.get("classname") == "orchestro"
        assert testcase.get("time") == "2.500"

        system_out = testcase.find("system-out")
        assert system_out is not None
        assert system_out.text == "Test output here"

    def test_generate_xml_failure(self, tmp_path: Path):
        """Test generating XML for failed test."""
        reporter = JUnitReporter()
        test_case = TestCase(
            name="Failed Test",
            classname="orchestro",
            time=1.5,
            failure_message="Expected True but got False",
            failure_type="AssertionError",
            failure_traceback="Traceback (most recent call last):\n  ...",
        )
        suite = TestSuite(name="Failure Suite", test_cases=[test_case])
        reporter.add_test_suite(suite)

        output_path = tmp_path / "junit-failure.xml"
        reporter.generate_xml(output_path)

        # Parse and verify XML structure
        tree = ET.parse(output_path)
        root = tree.getroot()

        testsuite = root.find("testsuite")
        assert testsuite.get("failures") == "1"

        testcase = testsuite.find("testcase")
        failure = testcase.find("failure")
        assert failure is not None
        assert "Expected True but got False" in failure.get("message")
        assert failure.get("type") == "AssertionError"
        assert failure.text == "Traceback (most recent call last):\n  ..."

    def test_generate_xml_error(self, tmp_path: Path):
        """Test generating XML for test with error."""
        reporter = JUnitReporter()
        test_case = TestCase(
            name="Error Test",
            classname="orchestro",
            time=0.5,
            error_message="Connection refused",
            error_type="ConnectionError",
            error_traceback="Traceback...",
        )
        suite = TestSuite(name="Error Suite", test_cases=[test_case])
        reporter.add_test_suite(suite)

        output_path = tmp_path / "junit-error.xml"
        reporter.generate_xml(output_path)

        # Parse and verify XML structure
        tree = ET.parse(output_path)
        root = tree.getroot()

        testsuite = root.find("testsuite")
        assert testsuite.get("errors") == "1"

        testcase = testsuite.find("testcase")
        error = testcase.find("error")
        assert error is not None
        assert "Connection refused" in error.get("message")
        assert error.get("type") == "ConnectionError"

    def test_generate_xml_skipped(self, tmp_path: Path):
        """Test generating XML for skipped test."""
        reporter = JUnitReporter()
        test_case = TestCase(
            name="Skipped Test",
            classname="orchestro",
            time=0.0,
            skipped=True,
            skipped_message="Test not applicable",
        )
        suite = TestSuite(name="Skipped Suite", test_cases=[test_case])
        reporter.add_test_suite(suite)

        output_path = tmp_path / "junit-skipped.xml"
        reporter.generate_xml(output_path)

        # Parse and verify XML structure
        tree = ET.parse(output_path)
        root = tree.getroot()

        testsuite = root.find("testsuite")
        assert testsuite.get("skipped") == "1"

        testcase = testsuite.find("testcase")
        skipped = testcase.find("skipped")
        assert skipped is not None
        assert "Test not applicable" in skipped.get("message")

    def test_generate_xml_special_characters(self, tmp_path: Path):
        """Test XML generation with special characters."""
        reporter = JUnitReporter()
        test_case = TestCase(
            name="Test with <special> & 'characters'",
            classname="orchestro",
            time=1.0,
            failure_message="Error: <tag> & 'quote'",
            system_out="Output with <tags>",
        )
        suite = TestSuite(name="Special Suite", test_cases=[test_case])
        reporter.add_test_suite(suite)

        output_path = tmp_path / "junit-special.xml"
        reporter.generate_xml(output_path)

        # Verify file is valid XML
        tree = ET.parse(output_path)
        root = tree.getroot()

        # Verify special characters are escaped
        testcase = root.find(".//testcase")
        assert testcase.get("name") == "Test with <special> & 'characters'"

        failure = testcase.find("failure")
        assert "<tag>" not in failure.get("message")  # Should be escaped
        assert "&lt;tag&gt;" in failure.get("message")

    def test_generate_xml_creates_directory(self, tmp_path: Path):
        """Test that XML generation creates parent directories."""
        reporter = JUnitReporter()
        test_case = TestCase(name="Test", time=1.0)
        suite = TestSuite(name="Suite", test_cases=[test_case])
        reporter.add_test_suite(suite)

        output_path = tmp_path / "subdir" / "nested" / "junit.xml"
        reporter.generate_xml(output_path)

        # Verify file and directories were created
        assert output_path.exists()
        assert output_path.parent.exists()


class TestScenarioTestResult:
    """Tests for ScenarioTestResult."""

    def test_scenario_test_result_success(self):
        """Test successful scenario result."""
        result = ScenarioTestResult("My Scenario")
        result.start()
        time.sleep(0.1)
        result.finish(success=True)

        assert result.success
        assert result.error is None
        assert result.duration > 0

    def test_scenario_test_result_failure(self):
        """Test failed scenario result."""
        result = ScenarioTestResult("My Scenario")
        result.start()
        error = ValueError("Test error")
        result.finish(success=False, error=error)

        assert not result.success
        assert result.error == error

    def test_add_output(self):
        """Test adding output to result."""
        result = ScenarioTestResult("My Scenario")
        result.add_output("Line 1")
        result.add_output("Line 2")

        assert len(result.output_buffer) == 2
        assert result.output_buffer[0] == "Line 1"
        assert result.output_buffer[1] == "Line 2"

    def test_add_error(self):
        """Test adding error output to result."""
        result = ScenarioTestResult("My Scenario")
        result.add_error("Error 1")
        result.add_error("Error 2")

        assert len(result.error_buffer) == 2
        assert result.error_buffer[0] == "Error 1"
        assert result.error_buffer[1] == "Error 2"

    def test_to_test_case_success(self):
        """Test converting successful result to test case."""
        result = ScenarioTestResult("My Scenario")
        result.start()
        result.add_output("Test output")
        time.sleep(0.05)
        result.finish(success=True)

        test_case = result.to_test_case()

        assert test_case.name == "My Scenario"
        assert test_case.classname == "orchestro"
        assert test_case.time > 0
        assert test_case.system_out == "Test output"
        assert test_case.failure_message is None

    def test_to_test_case_failure(self):
        """Test converting failed result to test case."""
        result = ScenarioTestResult("My Scenario")
        result.start()
        result.add_error("Error output")
        error = AssertionError("Test failed")
        result.finish(success=False, error=error)

        test_case = result.to_test_case()

        assert test_case.name == "My Scenario"
        assert test_case.failure_message == "Test failed"
        assert test_case.failure_type == "AssertionError"
        assert "AssertionError: Test failed" in test_case.failure_traceback
        assert test_case.system_err == "Error output"

    def test_to_test_suite(self):
        """Test converting result to test suite."""
        result = ScenarioTestResult("My Scenario")
        result.start()
        result.finish(success=True)

        suite = result.to_test_suite()

        assert suite.name == "My Scenario"
        assert suite.tests == 1
        assert suite.failures == 0
        assert suite.errors == 0
        assert suite.timestamp is not None
        assert suite.hostname is not None

    def test_duration_before_finish(self):
        """Test duration before finish is called."""
        result = ScenarioTestResult("My Scenario")
        assert result.duration == 0.0

        result.start()
        assert result.duration == 0.0  # End time not set yet
