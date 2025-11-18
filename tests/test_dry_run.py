"""Tests for dry-run mode functionality."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from orchestro_cli.cli import main
from orchestro_cli.runner import ScenarioRunner


class TestDryRunCLI:
    """Tests for dry-run CLI flag."""

    def test_dry_run_flag_valid_scenario(self, scenario_file: Path, capsys):
        """Test dry-run with valid scenario exits successfully."""
        scenario_file.write_text(yaml.dump({
            "name": "Test Scenario",
            "command": "echo test",
            "timeout": 30,
            "steps": [
                {"send": "hello"},
                {"expect": ".*"}
            ],
            "validations": [
                {"type": "path_exists", "path": "test.txt"}
            ]
        }))

        with patch.object(sys, 'argv', ['orchestro', str(scenario_file), '--dry-run']):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

            captured = capsys.readouterr()
            assert "[DRY RUN]" in captured.out
            assert "valid and ready to run" in captured.out

    def test_dry_run_flag_invalid_scenario(self, scenario_file: Path, capsys):
        """Test dry-run with invalid scenario exits with error."""
        scenario_file.write_text(yaml.dump({
            "name": "Invalid Scenario",
            # Missing required 'command' field
            "steps": []
        }))

        with patch.object(sys, 'argv', ['orchestro', str(scenario_file), '--dry-run']):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

            captured = capsys.readouterr()
            assert "[DRY RUN]" in captured.out
            assert "validation failed" in captured.err

    def test_dry_run_does_not_execute(self, scenario_file: Path, temp_workspace: Path):
        """Test that dry-run doesn't actually execute the command."""
        # Create a scenario that would create a file if executed
        test_file = temp_workspace / "executed.txt"
        scenario_file.write_text(yaml.dump({
            "name": "Test",
            "command": f"touch {test_file}",
            "steps": []
        }))

        with patch.object(sys, 'argv', ['orchestro', str(scenario_file), '--dry-run']):
            with pytest.raises(SystemExit):
                main()

        # File should not exist because command was not executed
        assert not test_file.exists()


class TestScenarioValidation:
    """Tests for ScenarioRunner.validate() method."""

    def test_validate_missing_command(self, scenario_file: Path, capsys):
        """Test validation fails when command is missing."""
        scenario_file.write_text(yaml.dump({
            "name": "Test",
            "steps": []
        }))

        runner = ScenarioRunner(scenario_path=scenario_file)
        result = runner.validate()

        assert result["valid"] is False
        assert any("command" in err.lower() for err in result["errors"])

        captured = capsys.readouterr()
        assert "No command specified" in captured.out

    def test_validate_invalid_timeout(self, scenario_file: Path, capsys):
        """Test validation fails with invalid timeout."""
        scenario_file.write_text(yaml.dump({
            "name": "Test",
            "command": "echo test",
            "timeout": -5
        }))

        runner = ScenarioRunner(scenario_path=scenario_file)
        result = runner.validate()

        assert result["valid"] is False
        assert any("timeout" in err.lower() for err in result["errors"])

    def test_validate_invalid_timeout_type(self, scenario_file: Path, capsys):
        """Test validation fails with non-numeric timeout."""
        scenario_file.write_text(yaml.dump({
            "name": "Test",
            "command": "echo test",
            "timeout": "invalid"
        }))

        runner = ScenarioRunner(scenario_path=scenario_file)
        result = runner.validate()

        assert result["valid"] is False
        assert any("timeout" in err.lower() for err in result["errors"])

    def test_validate_command_in_path(self, scenario_file: Path, capsys):
        """Test validation succeeds for command in PATH."""
        scenario_file.write_text(yaml.dump({
            "name": "Test",
            "command": "echo test",
            "steps": []
        }))

        runner = ScenarioRunner(scenario_path=scenario_file)
        result = runner.validate()

        assert result["valid"] is True
        captured = capsys.readouterr()
        assert "Command found in PATH" in captured.out

    def test_validate_command_not_found(self, scenario_file: Path, capsys):
        """Test validation warns when command not found."""
        scenario_file.write_text(yaml.dump({
            "name": "Test",
            "command": "nonexistent_command_xyz",
            "steps": []
        }))

        runner = ScenarioRunner(scenario_path=scenario_file)
        result = runner.validate()

        # Should still be valid (just a warning)
        assert result["valid"] is True
        assert len(result["warnings"]) > 0
        assert any("not found" in warn.lower() for warn in result["warnings"])

    def test_validate_relative_path_command(self, scenario_file: Path, temp_workspace: Path, capsys):
        """Test validation of command with relative path."""
        # Create an executable file
        cmd_file = temp_workspace / "test_cmd"
        cmd_file.write_text("#!/bin/bash\necho test")
        cmd_file.chmod(0o755)

        scenario_file.write_text(yaml.dump({
            "name": "Test",
            "command": str(cmd_file),
            "steps": []
        }))

        runner = ScenarioRunner(scenario_path=scenario_file)
        result = runner.validate()

        assert result["valid"] is True
        captured = capsys.readouterr()
        assert "exists and is executable" in captured.out

    def test_validate_invalid_regex_pattern(self, scenario_file: Path, capsys):
        """Test validation fails with invalid regex in expect."""
        scenario_file.write_text(yaml.dump({
            "name": "Test",
            "command": "echo test",
            "steps": [
                {"expect": "[invalid(regex"}
            ]
        }))

        runner = ScenarioRunner(scenario_path=scenario_file)
        result = runner.validate()

        assert result["valid"] is False
        assert any("regex" in err.lower() for err in result["errors"])

    def test_validate_steps_with_send(self, scenario_file: Path, capsys):
        """Test validation of steps with send command."""
        scenario_file.write_text(yaml.dump({
            "name": "Test",
            "command": "echo test",
            "steps": [
                {"send": "hello world"},
                {"send": "test", "raw": True}
            ]
        }))

        runner = ScenarioRunner(scenario_path=scenario_file)
        result = runner.validate()

        assert result["valid"] is True
        captured = capsys.readouterr()
        assert "Send: 'hello world'" in captured.out
        assert "(raw)" in captured.out

    def test_validate_steps_with_screenshot(self, scenario_file: Path, capsys):
        """Test validation of screenshot steps."""
        scenario_file.write_text(yaml.dump({
            "name": "Test",
            "command": "echo test",
            "steps": [
                {"screenshot": "test-screen", "timeout": 15}
            ]
        }))

        runner = ScenarioRunner(scenario_path=scenario_file)
        result = runner.validate()

        assert result["valid"] is True
        captured = capsys.readouterr()
        assert "Screenshot: test-screen.svg" in captured.out
        assert "timeout: 15" in captured.out

    def test_validate_steps_with_control(self, scenario_file: Path, capsys):
        """Test validation of control character steps."""
        scenario_file.write_text(yaml.dump({
            "name": "Test",
            "command": "echo test",
            "steps": [
                {"control": "c"}
            ]
        }))

        runner = ScenarioRunner(scenario_path=scenario_file)
        result = runner.validate()

        assert result["valid"] is True
        captured = capsys.readouterr()
        assert "Control: c" in captured.out

    def test_validate_invalid_step_timeout(self, scenario_file: Path, capsys):
        """Test validation fails with invalid step timeout."""
        scenario_file.write_text(yaml.dump({
            "name": "Test",
            "command": "echo test",
            "steps": [
                {"send": "test", "timeout": -1}
            ]
        }))

        runner = ScenarioRunner(scenario_path=scenario_file)
        result = runner.validate()

        assert result["valid"] is False
        assert any("timeout" in err.lower() for err in result["errors"])

    def test_validate_path_exists_validation(self, scenario_file: Path, capsys):
        """Test validation of path_exists validation rule."""
        scenario_file.write_text(yaml.dump({
            "name": "Test",
            "command": "echo test",
            "steps": [],
            "validations": [
                {"type": "path_exists", "path": "test.txt"}
            ]
        }))

        runner = ScenarioRunner(scenario_path=scenario_file)
        result = runner.validate()

        assert result["valid"] is True
        captured = capsys.readouterr()
        assert "path_exists: test.txt" in captured.out

    def test_validate_path_exists_missing_path(self, scenario_file: Path, capsys):
        """Test validation fails when path_exists missing path field."""
        scenario_file.write_text(yaml.dump({
            "name": "Test",
            "command": "echo test",
            "steps": [],
            "validations": [
                {"type": "path_exists"}
            ]
        }))

        runner = ScenarioRunner(scenario_path=scenario_file)
        result = runner.validate()

        assert result["valid"] is False
        assert any("path_exists" in err and "path" in err for err in result["errors"])

    def test_validate_file_contains_validation(self, scenario_file: Path, capsys):
        """Test validation of file_contains validation rule."""
        scenario_file.write_text(yaml.dump({
            "name": "Test",
            "command": "echo test",
            "steps": [],
            "validations": [
                {"type": "file_contains", "path": "test.txt", "text": "Success"}
            ]
        }))

        runner = ScenarioRunner(scenario_path=scenario_file)
        result = runner.validate()

        assert result["valid"] is True
        captured = capsys.readouterr()
        assert "file_contains" in captured.out

    def test_validate_file_contains_missing_fields(self, scenario_file: Path, capsys):
        """Test validation fails when file_contains missing required fields."""
        scenario_file.write_text(yaml.dump({
            "name": "Test",
            "command": "echo test",
            "steps": [],
            "validations": [
                {"type": "file_contains", "path": "test.txt"}
            ]
        }))

        runner = ScenarioRunner(scenario_path=scenario_file)
        result = runner.validate()

        assert result["valid"] is False
        assert any("file_contains" in err and "text" in err for err in result["errors"])

    def test_validate_file_contains_invalid_regex(self, scenario_file: Path, capsys):
        """Test validation fails with invalid regex in file_contains."""
        scenario_file.write_text(yaml.dump({
            "name": "Test",
            "command": "echo test",
            "steps": [],
            "validations": [
                {"type": "file_contains", "path": "test.txt", "text": "[invalid("}
            ]
        }))

        runner = ScenarioRunner(scenario_path=scenario_file)
        result = runner.validate()

        assert result["valid"] is False
        assert any("regex" in err.lower() for err in result["errors"])

    def test_validate_unknown_validation_type(self, scenario_file: Path, capsys):
        """Test validation fails with unknown validation type."""
        scenario_file.write_text(yaml.dump({
            "name": "Test",
            "command": "echo test",
            "steps": [],
            "validations": [
                {"type": "unknown_type"}
            ]
        }))

        runner = ScenarioRunner(scenario_path=scenario_file)
        result = runner.validate()

        assert result["valid"] is False
        assert any("unknown" in err.lower() for err in result["errors"])

    def test_validate_environment_variables(self, scenario_file: Path, capsys):
        """Test validation of environment variables."""
        scenario_file.write_text(yaml.dump({
            "name": "Test",
            "command": "echo test",
            "env": {
                "TEST_VAR": "value1",
                "ANOTHER_VAR": "value2"
            },
            "steps": []
        }))

        runner = ScenarioRunner(scenario_path=scenario_file)
        result = runner.validate()

        assert result["valid"] is True
        captured = capsys.readouterr()
        assert "Environment variables: 2 defined" in captured.out

    def test_validate_complete_scenario(self, scenario_file: Path, capsys):
        """Test validation of a complete, complex scenario."""
        scenario_file.write_text(yaml.dump({
            "name": "Complete Test Scenario",
            "description": "A comprehensive test with all features",
            "command": "echo test",
            "timeout": 30,
            "env": {
                "TEST_MODE": "true"
            },
            "steps": [
                {"note": "Starting test..."},
                {"send": "start"},
                {"expect": "Ready"},
                {"screenshot": "initial", "timeout": 10},
                {"send": "help"},
                {"expect": "Commands:"},
                {"control": "c"}
            ],
            "validations": [
                {"type": "path_exists", "path": "artifacts/screenshots/initial.svg"},
                {"type": "file_contains", "path": "output.log", "text": "Success"}
            ]
        }))

        runner = ScenarioRunner(scenario_path=scenario_file)
        result = runner.validate()

        assert result["valid"] is True
        captured = capsys.readouterr()

        # Verify all components are validated
        assert "Complete Test Scenario" in captured.out
        assert "A comprehensive test" in captured.out
        assert "echo test" in captured.out
        assert "Timeout: 30" in captured.out
        assert "Environment variables: 1 defined" in captured.out
        assert "Steps: 7 step(s)" in captured.out
        assert "Validations: 2 rule(s)" in captured.out
        assert "Note: Starting test..." in captured.out

    def test_validate_with_warnings(self, scenario_file: Path, capsys):
        """Test validation with warnings but no errors."""
        scenario_file.write_text(yaml.dump({
            "name": "Test",
            "command": "nonexistent_cmd",
            "steps": [
                {"screenshot": "test@screen!"}  # Special characters in name
            ]
        }))

        runner = ScenarioRunner(scenario_path=scenario_file)
        result = runner.validate()

        assert result["valid"] is True
        assert len(result["warnings"]) > 0
        captured = capsys.readouterr()
        assert "warning" in captured.out.lower()

    def test_validate_step_with_note(self, scenario_file: Path, capsys):
        """Test validation displays step notes."""
        scenario_file.write_text(yaml.dump({
            "name": "Test",
            "command": "echo test",
            "steps": [
                {"note": "This is a test step", "send": "hello"}
            ]
        }))

        runner = ScenarioRunner(scenario_path=scenario_file)
        result = runner.validate()

        assert result["valid"] is True
        captured = capsys.readouterr()
        assert "Note: This is a test step" in captured.out
