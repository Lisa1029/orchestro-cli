"""Plugin manager for dynamic plugin loading."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import List, Optional

from .registry import PluginRegistry


class PluginManager:
    """Manages plugin discovery and loading.

    Supports loading plugins from:
    - Python modules (importable)
    - Python files (.py)
    - Plugin directories
    """

    def __init__(self, registry: Optional[PluginRegistry] = None):
        """Initialize plugin manager.

        Args:
            registry: Optional existing registry (creates new if None)
        """
        self.registry = registry or PluginRegistry()
        self._loaded_modules: List[str] = []

    def load_from_module(self, module_name: str) -> None:
        """Load plugins from an importable Python module.

        The module should have a `register(registry)` function that
        registers plugins with the provided registry.

        Args:
            module_name: Fully qualified module name (e.g., 'myapp.plugins')

        Raises:
            ImportError: If module cannot be imported
            AttributeError: If module lacks register() function
        """
        if module_name in self._loaded_modules:
            return  # Already loaded

        module = importlib.import_module(module_name)
        if not hasattr(module, "register"):
            raise AttributeError(
                f"Module '{module_name}' does not have a register() function"
            )

        module.register(self.registry)
        self._loaded_modules.append(module_name)

    def load_from_file(self, plugin_path: Path) -> None:
        """Load plugins from a Python file.

        The file should have a `register(registry)` function.

        Args:
            plugin_path: Path to .py file

        Raises:
            FileNotFoundError: If file does not exist
            AttributeError: If file lacks register() function
        """
        if not plugin_path.exists():
            raise FileNotFoundError(f"Plugin file not found: {plugin_path}")

        if not plugin_path.suffix == ".py":
            raise ValueError(f"Plugin file must be .py: {plugin_path}")

        # Load module from file
        spec = importlib.util.spec_from_file_location(
            plugin_path.stem,
            plugin_path
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load plugin from {plugin_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[plugin_path.stem] = module
        spec.loader.exec_module(module)

        if not hasattr(module, "register"):
            raise AttributeError(
                f"Plugin '{plugin_path}' does not have a register() function"
            )

        module.register(self.registry)
        self._loaded_modules.append(str(plugin_path))

    def load_from_directory(self, plugin_dir: Path) -> int:
        """Load all plugins from a directory.

        Searches for .py files with a register() function.

        Args:
            plugin_dir: Directory containing plugin files

        Returns:
            Number of plugins successfully loaded

        Raises:
            FileNotFoundError: If directory does not exist
        """
        if not plugin_dir.exists():
            raise FileNotFoundError(f"Plugin directory not found: {plugin_dir}")

        if not plugin_dir.is_dir():
            raise ValueError(f"Not a directory: {plugin_dir}")

        loaded_count = 0
        for plugin_file in plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue  # Skip private/internal files

            try:
                self.load_from_file(plugin_file)
                loaded_count += 1
            except Exception as e:
                # Log error but continue loading other plugins
                print(f"Warning: Failed to load plugin {plugin_file}: {e}")

        return loaded_count

    def discover_plugins(
        self,
        search_paths: Optional[List[Path]] = None
    ) -> int:
        """Auto-discover and load plugins from standard locations.

        Default search paths:
        - ~/.orchestro/plugins/
        - ./orchestro_plugins/
        - Custom paths from search_paths parameter

        Args:
            search_paths: Additional paths to search

        Returns:
            Total number of plugins loaded
        """
        default_paths = [
            Path.home() / ".orchestro" / "plugins",
            Path.cwd() / "orchestro_plugins",
        ]

        all_paths = default_paths + (search_paths or [])
        total_loaded = 0

        for path in all_paths:
            if path.exists() and path.is_dir():
                try:
                    count = self.load_from_directory(path)
                    total_loaded += count
                except Exception as e:
                    print(f"Warning: Failed to load from {path}: {e}")

        return total_loaded

    def get_loaded_modules(self) -> List[str]:
        """Get list of loaded plugin modules.

        Returns:
            List of module names/paths
        """
        return self._loaded_modules.copy()

    def reload_all(self) -> None:
        """Reload all previously loaded plugins.

        Useful for development/testing.
        """
        modules_to_reload = self._loaded_modules.copy()
        self.registry.clear()
        self._loaded_modules.clear()

        for module_name in modules_to_reload:
            if module_name.endswith(".py"):
                # File-based plugin
                self.load_from_file(Path(module_name))
            else:
                # Module-based plugin
                self.load_from_module(module_name)
