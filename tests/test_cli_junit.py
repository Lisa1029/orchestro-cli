"""Integration tests for CLI JUnit XML functionality."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from xml.etree import ElementTree as ET

import pytest

from orchestro_cli.cli import main


class TestCLIJUnitIntegration:
    """Integration tests for CLI with JUnit XML reporting."""

    def test_junit_xml_flag_accepted(self, scenario_file: Path, tmp_path: Path):
        """Test that --junit-xml flag is accepted by CLI."""
        scenario_file.write_text("""
name: Test Scenario
command: echo test
timeout: 10
steps: []
""")

        junit_path = tmp_path / "junit.xml"

        with patch.object(sys, 'argv', [
            'orchestro',
            str(scenario_file),
            '--junit-xml',
            str(junit_path)
        ]):
            with patch('orchestro_cli.cli.ScenarioRunner') as mock_runner:
                mock_instance = Mock()
                mock_runner.return_value = mock_instance

                main()

                # Verify ScenarioRunner was called with junit_xml_path
                mock_runner.assert_called_once()
                call_kwargs = mock_runner.call_args[1]
                assert 'junit_xml_path' in call_kwargs
                assert call_kwargs['junit_xml_path'] == junit_path

    def test_junit_xml_not_provided(self, scenario_file: Path):
        """Test that CLI works without --junit-xml flag."""
        scenario_file.write_text("""
name: Test Scenario
command: echo test
timeout: 10
steps: []
""")

        with patch.object(sys, 'argv', ['orchestro', str(scenario_file)]):
            with patch('orchestro_cli.cli.ScenarioRunner') as mock_runner:
                mock_instance = Mock()
                mock_runner.return_value = mock_instance

                main()

                # Verify ScenarioRunner was called without junit_xml_path (None)
                mock_runner.assert_called_once()
                call_kwargs = mock_runner.call_args[1]
                assert 'junit_xml_path' in call_kwargs
                assert call_kwargs['junit_xml_path'] is None

    def test_junit_xml_message_on_success(self, scenario_file: Path, tmp_path: Path, capsys):
        """Test that success message includes JUnit XML path."""
        scenario_file.write_text("""
name: Test Scenario
command: echo test
timeout: 10
steps: []
""")

        junit_path = tmp_path / "junit.xml"

        with patch.object(sys, 'argv', [
            'orchestro',
            str(scenario_file),
            '--junit-xml',
            str(junit_path)
        ]):
            with patch('orchestro_cli.cli.ScenarioRunner') as mock_runner:
                mock_instance = Mock()
                mock_runner.return_value = mock_instance

                main()

                captured = capsys.readouterr()
                assert "JUnit XML report generated" in captured.out
                assert str(junit_path) in captured.out

    def test_junit_xml_with_verbose(self, scenario_file: Path, tmp_path: Path):
        """Test JUnit XML with verbose flag."""
        scenario_file.write_text("""
name: Test Scenario
command: echo test
timeout: 10
steps: []
""")

        junit_path = tmp_path / "junit.xml"

        with patch.object(sys, 'argv', [
            'orchestro',
            str(scenario_file),
            '--verbose',
            '--junit-xml',
            str(junit_path)
        ]):
            with patch('orchestro_cli.cli.ScenarioRunner') as mock_runner:
                mock_instance = Mock()
                mock_runner.return_value = mock_instance

                main()

                mock_runner.assert_called_once()
                call_kwargs = mock_runner.call_args[1]
                assert call_kwargs['verbose'] is True
                assert call_kwargs['junit_xml_path'] == junit_path

    def test_junit_xml_with_workspace(self, scenario_file: Path, tmp_path: Path, temp_workspace: Path):
        """Test JUnit XML with workspace flag."""
        scenario_file.write_text("""
name: Test Scenario
command: echo test
timeout: 10
steps: []
""")

        junit_path = tmp_path / "junit.xml"

        with patch.object(sys, 'argv', [
            'orchestro',
            str(scenario_file),
            '--workspace',
            str(temp_workspace),
            '--junit-xml',
            str(junit_path)
        ]):
            with patch('orchestro_cli.cli.ScenarioRunner') as mock_runner:
                mock_instance = Mock()
                mock_runner.return_value = mock_instance

                main()

                mock_runner.assert_called_once()
                call_kwargs = mock_runner.call_args[1]
                assert call_kwargs['workspace'] == temp_workspace
                assert call_kwargs['junit_xml_path'] == junit_path


class TestRunnerJUnitIntegration:
    """Integration tests for ScenarioRunner with JUnit XML."""

    def test_runner_generates_junit_xml_on_success(self, scenario_file: Path, tmp_path: Path):
        """Test that runner generates JUnit XML on successful execution."""
        scenario_file.write_text("""
name: Success Test
description: Test successful scenario
command: echo "Hello World"
timeout: 5
steps:
  - expect: "Hello"
""")

        junit_path = tmp_path / "test-results" / "junit.xml"

        from orchestro_cli.runner import ScenarioRunner

        runner = ScenarioRunner(
            scenario_path=scenario_file,
            junit_xml_path=junit_path
        )

        # Mock the async run to avoid actual execution
        with patch.object(runner, '_run_async') as mock_run:
            mock_run.return_value = None
            runner.run()

        # Verify JUnit XML was generated
        assert junit_path.exists()

        # Parse and verify structure
        tree = ET.parse(junit_path)
        root = tree.getroot()

        assert root.tag == "testsuites"
        testsuite = root.find("testsuite")
        assert testsuite is not None
        assert testsuite.get("name") == "Success Test"
        assert testsuite.get("tests") == "1"
        assert testsuite.get("failures") == "0"
        assert testsuite.get("errors") == "0"

        testcase = testsuite.find("testcase")
        assert testcase is not None
        assert testcase.get("name") == "Success Test"
        assert testcase.get("classname") == "orchestro"
        assert float(testcase.get("time")) >= 0

        # Should not have failure element
        assert testcase.find("failure") is None

    def test_runner_generates_junit_xml_on_failure(self, scenario_file: Path, tmp_path: Path):
        """Test that runner generates JUnit XML on failed execution."""
        scenario_file.write_text("""
name: Failure Test
description: Test failed scenario
command: echo "test"
timeout: 5
steps:
  - expect: "this_will_not_match"
""")

        junit_path = tmp_path / "test-results" / "junit-failure.xml"

        from orchestro_cli.runner import ScenarioRunner

        runner = ScenarioRunner(
            scenario_path=scenario_file,
            junit_xml_path=junit_path
        )

        # Mock the async run to simulate failure
        test_error = TimeoutError("Pattern not found")
        with patch.object(runner, '_run_async') as mock_run:
            mock_run.side_effect = test_error
            with pytest.raises(TimeoutError):
                runner.run()

        # Verify JUnit XML was generated even on failure
        assert junit_path.exists()

        # Parse and verify structure
        tree = ET.parse(junit_path)
        root = tree.getroot()

        testsuite = root.find("testsuite")
        assert testsuite.get("name") == "Failure Test"
        assert testsuite.get("tests") == "1"
        # Should have either failure or error
        assert int(testsuite.get("failures")) + int(testsuite.get("errors")) >= 1

        testcase = testsuite.find("testcase")
        assert testcase is not None

        # Should have failure or error element
        has_failure_or_error = (
            testcase.find("failure") is not None or
            testcase.find("error") is not None
        )
        assert has_failure_or_error

    def test_runner_no_junit_xml_when_not_configured(self, scenario_file: Path, tmp_path: Path):
        """Test that runner doesn't generate JUnit XML when not configured."""
        scenario_file.write_text("""
name: No JUnit Test
command: echo "test"
timeout: 5
steps:
  - expect: "test"
""")

        from orchestro_cli.runner import ScenarioRunner

        # Create runner without junit_xml_path
        runner = ScenarioRunner(
            scenario_path=scenario_file,
            junit_xml_path=None
        )

        # Mock the async run to avoid actual execution
        with patch.object(runner, '_run_async') as mock_run:
            mock_run.return_value = None
            runner.run()

        # Verify no JUnit XML files were created in tmp_path
        junit_files = list(tmp_path.glob("**/*.xml"))
        assert len(junit_files) == 0

    def test_junit_xml_includes_scenario_metadata(self, scenario_file: Path, tmp_path: Path):
        """Test that JUnit XML includes scenario metadata."""
        scenario_file.write_text("""
name: Metadata Test Scenario
description: Testing metadata in JUnit XML
command: echo "test"
timeout: 5
steps:
  - expect: "test"
""")

        junit_path = tmp_path / "junit-metadata.xml"

        from orchestro_cli.runner import ScenarioRunner

        runner = ScenarioRunner(
            scenario_path=scenario_file,
            junit_xml_path=junit_path
        )

        # Mock the async run to avoid actual execution
        with patch.object(runner, '_run_async') as mock_run:
            mock_run.return_value = None
            runner.run()

        # Parse XML
        tree = ET.parse(junit_path)
        root = tree.getroot()

        testsuite = root.find("testsuite")
        assert testsuite.get("name") == "Metadata Test Scenario"

        # Verify timestamp is present
        assert testsuite.get("timestamp") is not None

        # Verify hostname is present
        assert testsuite.get("hostname") is not None

    def test_junit_xml_timing_accuracy(self, scenario_file: Path, tmp_path: Path):
        """Test that JUnit XML timing information is accurate."""
        scenario_file.write_text("""
name: Timing Test
command: sleep 0.5
timeout: 5
steps: []
""")

        junit_path = tmp_path / "junit-timing.xml"

        from orchestro_cli.runner import ScenarioRunner

        runner = ScenarioRunner(
            scenario_path=scenario_file,
            junit_xml_path=junit_path
        )

        import time

        # Mock the async run with a sleep to simulate execution time
        async def mock_run_with_delay():
            await asyncio.sleep(0.1)

        with patch.object(runner, '_run_async', new=mock_run_with_delay):
            start = time.time()
            runner.run()
            duration = time.time() - start

        # Parse XML
        tree = ET.parse(junit_path)
        root = tree.getroot()

        testcase = root.find(".//testcase")
        reported_time = float(testcase.get("time"))

        # Reported time should be close to actual duration
        assert abs(reported_time - duration) < 0.5
        # Should be at least 0.05 seconds
        assert reported_time >= 0.05
