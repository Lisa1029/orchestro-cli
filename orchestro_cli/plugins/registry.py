"""Plugin registry for managing plugin instances."""

from __future__ import annotations

from typing import Dict, List, Optional, Type

from ..interfaces import (
    ProcessDriver,
    ReporterPlugin,
    StepPlugin,
    ValidatorPlugin,
)


class PluginRegistry:
    """Central registry for all plugin types.

    Manages registration and lookup of plugins for different extension points.
    """

    def __init__(self):
        """Initialize empty registry."""
        self._step_plugins: List[StepPlugin] = []
        self._validator_plugins: List[ValidatorPlugin] = []
        self._reporter_plugins: List[ReporterPlugin] = []
        self._process_drivers: Dict[str, Type[ProcessDriver]] = {}

    # Step Plugins
    def register_step_plugin(self, plugin: StepPlugin) -> None:
        """Register a step plugin.

        Args:
            plugin: Step plugin instance
        """
        self._step_plugins.append(plugin)

    def get_step_plugins(self) -> List[StepPlugin]:
        """Get all registered step plugins.

        Returns:
            List of step plugins
        """
        return self._step_plugins.copy()

    def find_step_plugin(self, step: any) -> Optional[StepPlugin]:
        """Find a plugin that can handle the given step.

        Args:
            step: Step to handle

        Returns:
            First plugin that can handle the step, or None
        """
        for plugin in self._step_plugins:
            if plugin.can_handle(step):
                return plugin
        return None

    # Validator Plugins
    def register_validator_plugin(self, plugin: ValidatorPlugin) -> None:
        """Register a validator plugin.

        Args:
            plugin: Validator plugin instance
        """
        self._validator_plugins.append(plugin)

    def get_validator_plugins(self) -> List[ValidatorPlugin]:
        """Get all registered validator plugins.

        Returns:
            List of validator plugins
        """
        return self._validator_plugins.copy()

    def find_validator_plugin(
        self,
        validation_type: str
    ) -> Optional[ValidatorPlugin]:
        """Find a plugin that can handle the given validation type.

        Args:
            validation_type: Type of validation

        Returns:
            First plugin that can handle the type, or None
        """
        for plugin in self._validator_plugins:
            if plugin.can_handle(validation_type):
                return plugin
        return None

    # Reporter Plugins
    def register_reporter_plugin(self, plugin: ReporterPlugin) -> None:
        """Register a reporter plugin.

        Args:
            plugin: Reporter plugin instance
        """
        self._reporter_plugins.append(plugin)

    def get_reporter_plugins(self) -> List[ReporterPlugin]:
        """Get all registered reporter plugins.

        Returns:
            List of reporter plugins
        """
        return self._reporter_plugins.copy()

    def find_reporter_plugin(self, name: str) -> Optional[ReporterPlugin]:
        """Find a reporter plugin by name.

        Args:
            name: Reporter name

        Returns:
            Reporter plugin or None if not found
        """
        for plugin in self._reporter_plugins:
            if plugin.reporter_name == name:
                return plugin
        return None

    # Process Drivers
    def register_process_driver(
        self,
        name: str,
        driver_class: Type[ProcessDriver]
    ) -> None:
        """Register a process driver.

        Args:
            name: Driver name (e.g., 'pexpect', 'subprocess', 'ssh')
            driver_class: Driver class (not instance)
        """
        self._process_drivers[name] = driver_class

    def get_process_driver(self, name: str) -> Optional[Type[ProcessDriver]]:
        """Get process driver by name.

        Args:
            name: Driver name

        Returns:
            Driver class or None if not found
        """
        return self._process_drivers.get(name)

    def list_process_drivers(self) -> List[str]:
        """List all registered process driver names.

        Returns:
            List of driver names
        """
        return list(self._process_drivers.keys())

    # Utility
    def clear(self) -> None:
        """Clear all registered plugins."""
        self._step_plugins.clear()
        self._validator_plugins.clear()
        self._reporter_plugins.clear()
        self._process_drivers.clear()

    def get_stats(self) -> Dict[str, int]:
        """Get plugin registration statistics.

        Returns:
            Dict with counts for each plugin type
        """
        return {
            "step_plugins": len(self._step_plugins),
            "validator_plugins": len(self._validator_plugins),
            "reporter_plugins": len(self._reporter_plugins),
            "process_drivers": len(self._process_drivers),
        }
