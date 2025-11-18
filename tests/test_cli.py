"""Tests for CLI entry point."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from orchestro_cli.cli import main


class TestCLI:
    """Tests for CLI interface."""

    def test_main_missing_scenario(self, capsys):
        """Test CLI with missing scenario file."""
        with patch.object(sys, 'argv', ['orchestro', 'nonexistent.yaml']):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

            captured = capsys.readouterr()
            assert "not found" in captured.err

    def test_main_with_verbose_flag(self, scenario_file: Path):
        """Test CLI with verbose flag."""
        scenario_file.write_text("""
name: Test
command: echo test
timeout: 10
steps: []
""")

        with patch.object(sys, 'argv', ['orchestro', str(scenario_file), '--verbose']):
            with patch('orchestro_cli.cli.ScenarioRunner') as mock_runner:
                mock_instance = Mock()
                mock_runner.return_value = mock_instance

                main()

                mock_runner.assert_called_once()
                call_kwargs = mock_runner.call_args[1]
                assert call_kwargs['verbose'] is True

    def test_main_with_workspace(self, scenario_file: Path, temp_workspace: Path):
        """Test CLI with workspace flag."""
        scenario_file.write_text("""
name: Test
command: echo test
timeout: 10
steps: []
""")

        with patch.object(sys, 'argv', [
            'orchestro',
            str(scenario_file),
            '--workspace',
            str(temp_workspace)
        ]):
            with patch('orchestro_cli.cli.ScenarioRunner') as mock_runner:
                mock_instance = Mock()
                mock_runner.return_value = mock_instance

                main()

                mock_runner.assert_called_once()
                call_kwargs = mock_runner.call_args[1]
                assert call_kwargs['workspace'] == temp_workspace

    def test_main_success(self, scenario_file: Path, capsys):
        """Test successful scenario execution."""
        scenario_file.write_text("""
name: Test
command: echo test
timeout: 10
steps: []
""")

        with patch.object(sys, 'argv', ['orchestro', str(scenario_file)]):
            with patch('orchestro_cli.cli.ScenarioRunner') as mock_runner:
                mock_instance = Mock()
                mock_runner.return_value = mock_instance

                main()

                captured = capsys.readouterr()
                assert "completed successfully" in captured.out

    def test_main_scenario_failure(self, scenario_file: Path, capsys):
        """Test scenario execution failure."""
        scenario_file.write_text("""
name: Test
command: echo test
timeout: 10
steps: []
""")

        with patch.object(sys, 'argv', ['orchestro', str(scenario_file)]):
            with patch('orchestro_cli.cli.ScenarioRunner') as mock_runner:
                mock_instance = Mock()
                mock_instance.run.side_effect = Exception("Test error")
                mock_runner.return_value = mock_instance

                with pytest.raises(SystemExit) as exc_info:
                    main()

                assert exc_info.value.code == 1

                captured = capsys.readouterr()
                assert "failed" in captured.err

    def test_version_flag(self, capsys):
        """Test --version flag."""
        with patch.object(sys, 'argv', ['orchestro', '--version']):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # --version exits with 0
            assert exc_info.value.code == 0

            captured = capsys.readouterr()
            assert "0.2.1" in captured.out
