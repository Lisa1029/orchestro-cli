"""Tests for ScenarioRunner."""

import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from orchestro_cli.runner import ScenarioRunner, ScenarioStep, Validation


class TestScenarioStep:
    """Tests for ScenarioStep dataclass."""

    def test_step_creation_with_expect(self):
        """Test creating step with expect pattern."""
        step = ScenarioStep(expect="Ready", timeout=10.0)
        assert step.expect == "Ready"
        assert step.timeout == 10.0
        assert step.send is None

    def test_step_creation_with_send(self):
        """Test creating step with send command."""
        step = ScenarioStep(send="ls -la", note="List files")
        assert step.send == "ls -la"
        assert step.note == "List files"

    def test_step_creation_with_screenshot(self):
        """Test creating step with screenshot."""
        step = ScenarioStep(screenshot="test-screen", timeout=15.0)
        assert step.screenshot == "test-screen"
        assert step.timeout == 15.0


class TestValidation:
    """Tests for Validation dataclass."""

    def test_path_exists_validation(self):
        """Test path_exists validation creation."""
        validation = Validation(type="path_exists", path="/tmp/test.txt")
        assert validation.type == "path_exists"
        assert validation.path == "/tmp/test.txt"

    def test_file_contains_validation(self):
        """Test file_contains validation creation."""
        validation = Validation(
            type="file_contains",
            path="output.log",
            text="Success"
        )
        assert validation.type == "file_contains"
        assert validation.text == "Success"


class TestScenarioRunner:
    """Tests for ScenarioRunner class."""

    def test_init(self, scenario_file: Path, temp_workspace: Path):
        """Test ScenarioRunner initialization."""
        scenario_file.write_text(yaml.dump({
            "name": "Test Scenario",
            "command": "echo test",
            "timeout": 30,
            "steps": []
        }))

        runner = ScenarioRunner(
            scenario_path=scenario_file,
            workspace=temp_workspace,
            verbose=True
        )

        assert runner.scenario_path == scenario_file.resolve()
        assert runner.workspace == temp_workspace.resolve()
        assert runner.verbose is True
        assert runner.spec["name"] == "Test Scenario"

    def test_load_spec(self, scenario_file: Path):
        """Test loading YAML scenario specification."""
        spec = {
            "name": "Test",
            "command": "ls",
            "timeout": 10,
            "steps": [{"send": "test"}]
        }
        scenario_file.write_text(yaml.dump(spec))

        runner = ScenarioRunner(scenario_path=scenario_file)
        assert runner.spec["name"] == "Test"
        assert runner.spec["command"] == "ls"

    def test_parse_steps_with_expect(self, scenario_file: Path):
        """Test parsing steps with expect patterns."""
        spec = {
            "name": "Test",
            "command": "ls",
            "steps": [
                {"expect": "Ready", "timeout": 10},
                {"send": "hello"}
            ]
        }
        scenario_file.write_text(yaml.dump(spec))

        runner = ScenarioRunner(scenario_path=scenario_file)
        steps = runner._parse_steps()

        assert len(steps) == 2
        assert steps[0].expect == "Ready"
        assert steps[0].timeout == 10
        assert steps[1].send == "hello"

    def test_parse_steps_with_pattern_alias(self, scenario_file: Path):
        """Test parsing steps with 'pattern' alias for 'expect'."""
        spec = {
            "name": "Test",
            "command": "ls",
            "steps": [{"pattern": "Ready", "timeout": 5}]
        }
        scenario_file.write_text(yaml.dump(spec))

        runner = ScenarioRunner(scenario_path=scenario_file)
        steps = runner._parse_steps()

        assert steps[0].expect == "Ready"

    def test_parse_steps_with_screenshot(self, scenario_file: Path):
        """Test parsing steps with screenshot."""
        spec = {
            "name": "Test",
            "command": "ls",
            "steps": [{"screenshot": "test-screen", "timeout": 15}]
        }
        scenario_file.write_text(yaml.dump(spec))

        runner = ScenarioRunner(scenario_path=scenario_file)
        steps = runner._parse_steps()

        assert steps[0].screenshot == "test-screen"
        assert steps[0].timeout == 15

    def test_parse_validations(self, scenario_file: Path):
        """Test parsing validation rules."""
        spec = {
            "name": "Test",
            "command": "ls",
            "steps": [],
            "validations": [
                {"type": "path_exists", "path": "test.txt"},
                {"type": "file_contains", "path": "log.txt", "text": "Success"}
            ]
        }
        scenario_file.write_text(yaml.dump(spec))

        runner = ScenarioRunner(scenario_path=scenario_file)
        validations = runner._parse_validations()

        assert len(validations) == 2
        assert validations[0].type == "path_exists"
        assert validations[1].type == "file_contains"

    def test_prepare_env_basic(self, scenario_file: Path):
        """Test environment preparation without workspace."""
        spec = {
            "name": "Test",
            "command": "ls",
            "env": {"TEST_VAR": "test_value"}
        }
        scenario_file.write_text(yaml.dump(spec))

        runner = ScenarioRunner(scenario_path=scenario_file)
        env = runner._prepare_env()

        assert env["TEST_VAR"] == "test_value"
        assert env["VYB_AUTO_SCREENSHOT"] == "1"

    def test_prepare_env_with_workspace(self, scenario_file: Path, temp_workspace: Path):
        """Test environment preparation with workspace isolation."""
        spec = {"name": "Test", "command": "ls"}
        scenario_file.write_text(yaml.dump(spec))

        runner = ScenarioRunner(
            scenario_path=scenario_file,
            workspace=temp_workspace
        )
        env = runner._prepare_env()

        assert "HOME" in env
        assert "VYB_DATA_ROOT" in env
        assert Path(env["HOME"]).exists()
        assert Path(env["VYB_DATA_ROOT"]).exists()

    def test_run_validations_path_exists(self, scenario_file: Path, temp_workspace: Path):
        """Test path_exists validation."""
        spec = {
            "name": "Test",
            "command": "ls",
            "steps": [],
            "validations": [{"type": "path_exists", "path": "test.txt"}]
        }
        scenario_file.write_text(yaml.dump(spec))

        runner = ScenarioRunner(
            scenario_path=scenario_file,
            workspace=temp_workspace
        )

        # Create the expected file
        (temp_workspace / "test.txt").touch()

        # Should not raise
        runner._run_validations({})

    def test_run_validations_path_missing(self, scenario_file: Path, temp_workspace: Path):
        """Test path_exists validation fails when file missing."""
        spec = {
            "name": "Test",
            "command": "ls",
            "steps": [],
            "validations": [{"type": "path_exists", "path": "missing.txt"}]
        }
        scenario_file.write_text(yaml.dump(spec))

        runner = ScenarioRunner(
            scenario_path=scenario_file,
            workspace=temp_workspace
        )

        with pytest.raises(AssertionError, match="Expected path to exist"):
            runner._run_validations({})

    def test_run_validations_file_contains(self, scenario_file: Path, temp_workspace: Path):
        """Test file_contains validation."""
        spec = {
            "name": "Test",
            "command": "ls",
            "steps": [],
            "validations": [
                {"type": "file_contains", "path": "test.txt", "text": "Success"}
            ]
        }
        scenario_file.write_text(yaml.dump(spec))

        runner = ScenarioRunner(
            scenario_path=scenario_file,
            workspace=temp_workspace
        )

        # Create file with expected content
        (temp_workspace / "test.txt").write_text("Test Success Message")

        # Should not raise
        runner._run_validations({})

    def test_run_validations_file_contains_regex(self, scenario_file: Path, temp_workspace: Path):
        """Test file_contains validation with regex."""
        spec = {
            "name": "Test",
            "command": "ls",
            "steps": [],
            "validations": [
                {"type": "file_contains", "path": "test.txt", "text": r"Success.*\d+"}
            ]
        }
        scenario_file.write_text(yaml.dump(spec))

        runner = ScenarioRunner(
            scenario_path=scenario_file,
            workspace=temp_workspace
        )

        (temp_workspace / "test.txt").write_text("Success: 42 records")

        # Should not raise
        runner._run_validations({})

    def test_run_validations_unknown_type(self, scenario_file: Path):
        """Test validation with unknown type."""
        spec = {
            "name": "Test",
            "command": "ls",
            "steps": [],
            "validations": [{"type": "unknown_type"}]
        }
        scenario_file.write_text(yaml.dump(spec))

        runner = ScenarioRunner(scenario_path=scenario_file)

        with pytest.raises(ValueError, match="Unknown validation type"):
            runner._run_validations({})

    def test_missing_command(self, scenario_file: Path):
        """Test scenario without command raises error."""
        spec = {
            "name": "Test",
            "steps": []
        }
        scenario_file.write_text(yaml.dump(spec))

        runner = ScenarioRunner(scenario_path=scenario_file)

        with pytest.raises(ValueError, match="Scenario missing 'command'"):
            runner.run()
