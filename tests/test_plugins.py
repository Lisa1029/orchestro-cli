"""Tests for plugin system."""

import pytest
from pathlib import Path
from unittest.mock import Mock

from orchestro_cli.plugins import PluginManager, PluginRegistry
from orchestro_cli.interfaces import (
    ProcessDriver,
    StepPlugin,
    ValidatorPlugin,
    ReporterPlugin
)


class TestPluginRegistry:
    """Test plugin registry functionality."""

    def test_init(self):
        """Test registry initialization."""
        registry = PluginRegistry()
        assert len(registry.get_step_plugins()) == 0
        assert len(registry.get_validator_plugins()) == 0
        assert len(registry.get_reporter_plugins()) == 0
        assert len(registry.list_process_drivers()) == 0

    def test_register_step_plugin(self):
        """Test step plugin registration."""
        registry = PluginRegistry()
        plugin = Mock(spec=StepPlugin)
        plugin.step_type = "test_step"

        registry.register_step_plugin(plugin)
        assert len(registry.get_step_plugins()) == 1
        assert registry.get_step_plugins()[0] == plugin

    def test_register_validator_plugin(self):
        """Test validator plugin registration."""
        registry = PluginRegistry()
        plugin = Mock(spec=ValidatorPlugin)
        plugin.validator_type = "test_validator"

        registry.register_validator_plugin(plugin)
        assert len(registry.get_validator_plugins()) == 1

    def test_register_reporter_plugin(self):
        """Test reporter plugin registration."""
        registry = PluginRegistry()
        plugin = Mock(spec=ReporterPlugin)
        plugin.reporter_name = "test_reporter"

        registry.register_reporter_plugin(plugin)
        assert len(registry.get_reporter_plugins()) == 1

    def test_find_step_plugin(self):
        """Test finding step plugin by step."""
        registry = PluginRegistry()
        plugin1 = Mock(spec=StepPlugin)
        plugin1.can_handle.return_value = False
        plugin2 = Mock(spec=StepPlugin)
        plugin2.can_handle.return_value = True

        registry.register_step_plugin(plugin1)
        registry.register_step_plugin(plugin2)

        step = Mock()
        found = registry.find_step_plugin(step)
        assert found == plugin2
        plugin1.can_handle.assert_called_once_with(step)
        plugin2.can_handle.assert_called_once_with(step)

    def test_find_validator_plugin(self):
        """Test finding validator plugin by type."""
        registry = PluginRegistry()
        plugin1 = Mock(spec=ValidatorPlugin)
        plugin1.can_handle.return_value = False
        plugin2 = Mock(spec=ValidatorPlugin)
        plugin2.can_handle.return_value = True

        registry.register_validator_plugin(plugin1)
        registry.register_validator_plugin(plugin2)

        found = registry.find_validator_plugin("test_type")
        assert found == plugin2

    def test_find_reporter_plugin(self):
        """Test finding reporter plugin by name."""
        registry = PluginRegistry()
        plugin1 = Mock(spec=ReporterPlugin)
        plugin1.reporter_name = "json"
        plugin2 = Mock(spec=ReporterPlugin)
        plugin2.reporter_name = "html"

        registry.register_reporter_plugin(plugin1)
        registry.register_reporter_plugin(plugin2)

        found = registry.find_reporter_plugin("html")
        assert found == plugin2

    def test_register_process_driver(self):
        """Test process driver registration."""
        registry = PluginRegistry()
        driver_class = Mock(spec=ProcessDriver)

        registry.register_process_driver("test_driver", driver_class)
        assert "test_driver" in registry.list_process_drivers()
        assert registry.get_process_driver("test_driver") == driver_class

    def test_clear(self):
        """Test clearing all plugins."""
        registry = PluginRegistry()
        registry.register_step_plugin(Mock(spec=StepPlugin))
        registry.register_validator_plugin(Mock(spec=ValidatorPlugin))
        registry.register_reporter_plugin(Mock(spec=ReporterPlugin))

        registry.clear()
        assert len(registry.get_step_plugins()) == 0
        assert len(registry.get_validator_plugins()) == 0
        assert len(registry.get_reporter_plugins()) == 0

    def test_get_stats(self):
        """Test plugin statistics."""
        registry = PluginRegistry()
        registry.register_step_plugin(Mock(spec=StepPlugin))
        registry.register_step_plugin(Mock(spec=StepPlugin))
        registry.register_validator_plugin(Mock(spec=ValidatorPlugin))

        stats = registry.get_stats()
        assert stats["step_plugins"] == 2
        assert stats["validator_plugins"] == 1
        assert stats["reporter_plugins"] == 0


class TestPluginManager:
    """Test plugin manager functionality."""

    def test_init(self):
        """Test manager initialization."""
        manager = PluginManager()
        assert manager.registry is not None
        assert len(manager.get_loaded_modules()) == 0

    def test_init_with_custom_registry(self):
        """Test manager with custom registry."""
        registry = PluginRegistry()
        manager = PluginManager(registry=registry)
        assert manager.registry is registry

    def test_load_from_file_not_found(self):
        """Test loading from non-existent file."""
        manager = PluginManager()
        with pytest.raises(FileNotFoundError):
            manager.load_from_file(Path("/nonexistent/plugin.py"))

    def test_load_from_file_wrong_extension(self, tmp_path):
        """Test loading from non-Python file."""
        manager = PluginManager()
        file_path = tmp_path / "plugin.txt"
        file_path.write_text("test")
        with pytest.raises(ValueError, match="must be .py"):
            manager.load_from_file(file_path)

    def test_load_from_directory_not_found(self):
        """Test loading from non-existent directory."""
        manager = PluginManager()
        with pytest.raises(FileNotFoundError):
            manager.load_from_directory(Path("/nonexistent"))

    def test_load_from_directory_not_dir(self, tmp_path):
        """Test loading from file instead of directory."""
        manager = PluginManager()
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")

        with pytest.raises(ValueError, match="Not a directory"):
            manager.load_from_directory(file_path)

    def test_discover_plugins_no_paths(self):
        """Test plugin discovery with no paths."""
        manager = PluginManager()
        # Should not raise, just return 0
        count = manager.discover_plugins()
        assert count >= 0

    def test_get_loaded_modules(self):
        """Test getting loaded modules."""
        manager = PluginManager()
        assert manager.get_loaded_modules() == []


class TestPluginInterfaces:
    """Test plugin interface protocols."""

    def test_step_plugin_protocol(self):
        """Test step plugin protocol structure."""
        plugin = Mock(spec=StepPlugin)
        plugin.step_type = "custom"

        # Verify protocol methods exist
        assert hasattr(plugin, "step_type")
        assert hasattr(plugin, "can_handle")
        assert hasattr(plugin, "execute")
        assert hasattr(plugin, "validate_step")

    def test_validator_plugin_protocol(self):
        """Test validator plugin protocol structure."""
        plugin = Mock(spec=ValidatorPlugin)
        plugin.validator_type = "custom"

        # Verify protocol methods exist
        assert hasattr(plugin, "validator_type")
        assert hasattr(plugin, "can_handle")
        assert hasattr(plugin, "validate")
        assert hasattr(plugin, "validate_spec")

    def test_reporter_plugin_protocol(self):
        """Test reporter plugin protocol structure."""
        plugin = Mock(spec=ReporterPlugin)
        plugin.reporter_name = "custom"
        plugin.file_extension = ".ext"

        # Verify protocol methods exist
        assert hasattr(plugin, "reporter_name")
        assert hasattr(plugin, "file_extension")
        assert hasattr(plugin, "start_scenario")
        assert hasattr(plugin, "finish_scenario")
        assert hasattr(plugin, "generate_report")
        assert hasattr(plugin, "add_metadata")

    def test_process_driver_protocol(self):
        """Test process driver protocol structure."""
        driver = Mock(spec=ProcessDriver)

        # Verify protocol methods exist
        assert hasattr(driver, "spawn")
        assert hasattr(driver, "send")
        assert hasattr(driver, "sendline")
        assert hasattr(driver, "sendcontrol")
        assert hasattr(driver, "expect")
        assert hasattr(driver, "is_alive")
        assert hasattr(driver, "terminate")
        assert hasattr(driver, "kill")
        assert hasattr(driver, "exit_status")
        assert hasattr(driver, "before")
        assert hasattr(driver, "after")
