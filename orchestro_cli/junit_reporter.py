"""JUnit XML report generation for CI/CD integration.

This module generates JUnit XML test reports compatible with:
- Jenkins
- GitHub Actions
- GitLab CI
- Azure DevOps
- CircleCI
"""

from __future__ import annotations

import html
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
from xml.etree import ElementTree as ET


@dataclass
class TestCase:
    """Represents a single test case in JUnit XML format."""

    name: str
    classname: str = "orchestro"
    time: float = 0.0
    failure_message: Optional[str] = None
    failure_type: Optional[str] = None
    failure_traceback: Optional[str] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    error_traceback: Optional[str] = None
    system_out: Optional[str] = None
    system_err: Optional[str] = None
    skipped: bool = False
    skipped_message: Optional[str] = None


@dataclass
class TestSuite:
    """Represents a test suite containing test cases."""

    name: str
    test_cases: List[TestCase] = field(default_factory=list)
    timestamp: Optional[str] = None
    hostname: Optional[str] = None

    @property
    def tests(self) -> int:
        """Total number of tests."""
        return len(self.test_cases)

    @property
    def failures(self) -> int:
        """Number of failed tests."""
        return sum(1 for tc in self.test_cases if tc.failure_message is not None)

    @property
    def errors(self) -> int:
        """Number of errored tests."""
        return sum(1 for tc in self.test_cases if tc.error_message is not None)

    @property
    def skipped(self) -> int:
        """Number of skipped tests."""
        return sum(1 for tc in self.test_cases if tc.skipped)

    @property
    def time(self) -> float:
        """Total execution time."""
        return sum(tc.time for tc in self.test_cases)


class JUnitReporter:
    """Generate JUnit XML reports from test results."""

    def __init__(self):
        """Initialize the reporter."""
        self.test_suites: List[TestSuite] = []

    def add_test_suite(self, suite: TestSuite) -> None:
        """Add a test suite to the report.

        Args:
            suite: TestSuite to add
        """
        self.test_suites.append(suite)

    def generate_xml(self, output_path: Path) -> None:
        """Generate JUnit XML report and write to file.

        Args:
            output_path: Path where XML report should be written
        """
        # Create root element
        testsuites = ET.Element("testsuites")

        # Add each test suite
        for suite in self.test_suites:
            testsuite_elem = self._create_testsuite_element(suite)
            testsuites.append(testsuite_elem)

        # Create tree and write to file
        tree = ET.ElementTree(testsuites)
        ET.indent(tree, space="  ")  # Pretty print

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write with XML declaration
        with open(output_path, "wb") as f:
            tree.write(f, encoding="utf-8", xml_declaration=True)

    def _create_testsuite_element(self, suite: TestSuite) -> ET.Element:
        """Create XML element for a test suite.

        Args:
            suite: TestSuite to convert to XML

        Returns:
            XML Element representing the test suite
        """
        testsuite = ET.Element("testsuite")
        testsuite.set("name", suite.name)
        testsuite.set("tests", str(suite.tests))
        testsuite.set("failures", str(suite.failures))
        testsuite.set("errors", str(suite.errors))
        testsuite.set("skipped", str(suite.skipped))
        testsuite.set("time", f"{suite.time:.3f}")

        if suite.timestamp:
            testsuite.set("timestamp", suite.timestamp)

        if suite.hostname:
            testsuite.set("hostname", suite.hostname)

        # Add test cases
        for test_case in suite.test_cases:
            testcase_elem = self._create_testcase_element(test_case)
            testsuite.append(testcase_elem)

        return testsuite

    def _create_testcase_element(self, test_case: TestCase) -> ET.Element:
        """Create XML element for a test case.

        Args:
            test_case: TestCase to convert to XML

        Returns:
            XML Element representing the test case
        """
        testcase = ET.Element("testcase")
        testcase.set("name", test_case.name)
        testcase.set("classname", test_case.classname)
        testcase.set("time", f"{test_case.time:.3f}")

        # Add failure if present
        if test_case.failure_message is not None:
            failure = ET.SubElement(testcase, "failure")
            failure.set("message", html.escape(test_case.failure_message))

            if test_case.failure_type:
                failure.set("type", test_case.failure_type)

            if test_case.failure_traceback:
                failure.text = test_case.failure_traceback

        # Add error if present
        if test_case.error_message is not None:
            error = ET.SubElement(testcase, "error")
            error.set("message", html.escape(test_case.error_message))

            if test_case.error_type:
                error.set("type", test_case.error_type)

            if test_case.error_traceback:
                error.text = test_case.error_traceback

        # Add skipped if present
        if test_case.skipped:
            skipped = ET.SubElement(testcase, "skipped")
            if test_case.skipped_message:
                skipped.set("message", html.escape(test_case.skipped_message))

        # Add system-out if present
        if test_case.system_out:
            system_out = ET.SubElement(testcase, "system-out")
            system_out.text = test_case.system_out

        # Add system-err if present
        if test_case.system_err:
            system_err = ET.SubElement(testcase, "system-err")
            system_err.text = test_case.system_err

        return testcase


class ScenarioTestResult:
    """Container for scenario execution results to be converted to JUnit format."""

    def __init__(self, scenario_name: str):
        """Initialize test result.

        Args:
            scenario_name: Name of the scenario
        """
        self.scenario_name = scenario_name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.success: bool = False
        self.error: Optional[Exception] = None
        self.output_buffer: List[str] = []
        self.error_buffer: List[str] = []

    def start(self) -> None:
        """Mark scenario start time."""
        self.start_time = time.time()

    def finish(self, success: bool, error: Optional[Exception] = None) -> None:
        """Mark scenario completion.

        Args:
            success: Whether the scenario succeeded
            error: Exception if scenario failed
        """
        self.end_time = time.time()
        self.success = success
        self.error = error

    def add_output(self, text: str) -> None:
        """Add output text.

        Args:
            text: Output text to add
        """
        self.output_buffer.append(text)

    def add_error(self, text: str) -> None:
        """Add error text.

        Args:
            text: Error text to add
        """
        self.error_buffer.append(text)

    @property
    def duration(self) -> float:
        """Get execution duration in seconds."""
        if self.start_time is None or self.end_time is None:
            return 0.0
        return self.end_time - self.start_time

    def to_test_case(self) -> TestCase:
        """Convert scenario result to JUnit TestCase.

        Returns:
            TestCase representation of this result
        """
        test_case = TestCase(
            name=self.scenario_name,
            classname="orchestro",
            time=self.duration,
            system_out="\n".join(self.output_buffer) if self.output_buffer else None,
            system_err="\n".join(self.error_buffer) if self.error_buffer else None,
        )

        if not self.success and self.error:
            import traceback

            # Add failure information
            test_case.failure_message = str(self.error)
            test_case.failure_type = type(self.error).__name__
            test_case.failure_traceback = "".join(
                traceback.format_exception(type(self.error), self.error, self.error.__traceback__)
            )

        return test_case

    def to_test_suite(self) -> TestSuite:
        """Convert scenario result to JUnit TestSuite.

        Returns:
            TestSuite containing this result as a single test case
        """
        from datetime import datetime
        import socket

        suite = TestSuite(
            name=self.scenario_name,
            test_cases=[self.to_test_case()],
            timestamp=datetime.utcnow().isoformat(),
            hostname=socket.gethostname(),
        )

        return suite
