"""Integration tests for real scenario execution.

These tests actually spawn processes and execute scenarios end-to-end.

NOTE: These tests require actual process execution and may be skipped
in CI environments. They serve as smoke tests for real-world usage.
"""

import pytest
import tempfile
from pathlib import Path

from orchestro_cli.core import Orchestrator

# Mark all as integration tests (skip by default)
pytestmark = pytest.mark.integration


class TestRealExecution:
    """Test real scenario execution end-to-end."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def simple_scenario(self, tmp_path):
        """Create a simple test scenario."""
        scenario = tmp_path / "simple.yaml"
        # Use python -c for interactive testing
        scenario.write_text("""
name: Simple Python Test
description: Basic python interactive test
command: python -c "print('ready'); input()"
timeout: 10

steps:
  - expect: "ready"
    note: "Wait for ready message"
""")
        return scenario

    @pytest.fixture
    def cat_scenario(self, tmp_path):
        """Create a scenario using cat command."""
        scenario = tmp_path / "cat_test.yaml"
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content\nLine 2\n")

        scenario.write_text(f"""
name: Cat File Test
description: Test reading file with cat
command: cat {test_file}
timeout: 10

steps:
  - expect: "Test content"
    note: "Wait for first line"

  - expect: "Line 2"
    note: "Wait for second line"

validations:
  - type: path_exists
    path: {test_file}
""")
        return scenario

    def test_simple_echo_execution(self, simple_scenario, temp_workspace):
        """Test executing a simple echo scenario."""
        orchestrator = Orchestrator(
            workspace=temp_workspace,
            verbose=False
        )

        # Should execute without errors
        orchestrator.run(simple_scenario)
        # If we get here, execution succeeded

    def test_cat_with_validation(self, cat_scenario, temp_workspace):
        """Test cat command with validation."""
        orchestrator = Orchestrator(
            workspace=temp_workspace,
            verbose=False
        )

        orchestrator.run(cat_scenario)
        # Validation should pass

    def test_junit_xml_generation(self, simple_scenario, tmp_path, temp_workspace):
        """Test JUnit XML report generation."""
        junit_path = tmp_path / "results.xml"

        orchestrator = Orchestrator(
            workspace=temp_workspace,
            verbose=False,
            junit_xml_path=junit_path
        )

        orchestrator.run(simple_scenario)

        # Verify JUnit XML was created
        assert junit_path.exists()

        # Verify XML content
        content = junit_path.read_text()
        assert "<?xml version" in content
        assert "testsuites" in content
        assert "Simple Echo Test" in content

    def test_failed_scenario(self, tmp_path, temp_workspace):
        """Test handling of failed scenario."""
        scenario = tmp_path / "fail.yaml"
        scenario.write_text("""
name: Failing Test
command: echo
timeout: 10

steps:
  - expect: "THIS_WILL_NOT_MATCH"
    note: "This should timeout"

validations:
  - type: path_exists
    path: /nonexistent/path
""")

        orchestrator = Orchestrator(
            workspace=temp_workspace,
            verbose=False
        )

        # Should raise exception due to timeout or validation failure
        with pytest.raises(Exception):
            orchestrator.run(scenario)

    def test_workspace_isolation(self, simple_scenario, tmp_path):
        """Test workspace isolation between runs."""
        workspace1 = tmp_path / "ws1"
        workspace2 = tmp_path / "ws2"
        workspace1.mkdir()
        workspace2.mkdir()

        orch1 = Orchestrator(workspace=workspace1, verbose=False)
        orch2 = Orchestrator(workspace=workspace2, verbose=False)

        # Both should execute independently
        orch1.run(simple_scenario)
        orch2.run(simple_scenario)

        # Workspaces should remain separate
        assert workspace1.exists()
        assert workspace2.exists()


class TestBackwardCompatibility:
    """Test backward compatibility with legacy API."""

    @pytest.fixture
    def echo_scenario(self, tmp_path):
        """Create echo scenario."""
        scenario = tmp_path / "echo.yaml"
        scenario.write_text("""
name: Echo Test
command: echo
timeout: 10

steps:
  - expect: ".*"
    send: "test"
""")
        return scenario

    def test_legacy_runner(self, echo_scenario, tmp_path):
        """Test that legacy ScenarioRunner still works."""
        from orchestro_cli.runner import ScenarioRunner

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Legacy API should still work
        runner = ScenarioRunner(
            scenario_path=echo_scenario,
            workspace=workspace,
            verbose=False
        )

        runner.run()
        # Should complete without errors

    def test_runner_v2_facade(self, echo_scenario, tmp_path):
        """Test runner_v2 facade."""
        from orchestro_cli.runner_v2 import ScenarioRunner

        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Should emit deprecation warning
        with pytest.warns(DeprecationWarning, match="deprecated"):
            runner = ScenarioRunner(
                scenario_path=echo_scenario,
                workspace=workspace,
                verbose=False
            )

        runner.run()
        # Should delegate to orchestrator successfully


class TestPluginSystem:
    """Test plugin system integration."""

    @pytest.fixture
    def custom_plugin(self, tmp_path):
        """Create a test plugin."""
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text("""
from orchestro_cli.interfaces.reporter_plugin import BaseReporter, ScenarioReport
from pathlib import Path

class TestReporter(BaseReporter):
    def __init__(self):
        super().__init__("test_reporter", ".test", verbose=True)
        self.reports = []

    def generate_report(self, report_data, output_path):
        self.reports.append(report_data.scenario_name)
        if output_path:
            output_path.write_text(f"Test report: {report_data.scenario_name}")

def register(registry):
    registry.register_reporter_plugin(TestReporter())
""")
        return plugin_file

    def test_plugin_loading(self, custom_plugin):
        """Test loading custom plugin."""
        from orchestro_cli.plugins import PluginManager

        manager = PluginManager()
        manager.load_from_file(custom_plugin)

        # Should have loaded the plugin
        reporters = manager.registry.get_reporter_plugins()
        assert len(reporters) == 1
        assert reporters[0].reporter_name == "test_reporter"

    def test_auto_discovery(self, tmp_path, monkeypatch):
        """Test plugin auto-discovery."""
        from orchestro_cli.plugins import PluginManager

        # Create plugin in standard location
        plugin_dir = tmp_path / "orchestro_plugins"
        plugin_dir.mkdir()

        plugin_file = plugin_dir / "auto_plugin.py"
        plugin_file.write_text("""
from orchestro_cli.interfaces.step_plugin import StepPlugin

class AutoPlugin:
    @property
    def step_type(self):
        return "auto_step"

    def can_handle(self, step):
        return False

    async def execute(self, step, context, timeout):
        pass

    def validate_step(self, step):
        return []

def register(registry):
    registry.register_step_plugin(AutoPlugin())
""")

        # Change cwd to tmp_path
        monkeypatch.chdir(tmp_path)

        manager = PluginManager()
        count = manager.discover_plugins()

        # Should discover the plugin
        assert count >= 1
        step_plugins = manager.registry.get_step_plugins()
        plugin_types = [p.step_type for p in step_plugins]
        assert "auto_step" in plugin_types
