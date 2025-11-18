"""
Orchestro CLI — Playwright for Terminal Applications

A scenario-driven CLI testing harness that supports:
- Interactive CLI automation via pexpect
- Automated screenshot capture for TUI apps
- File-based trigger mechanism for event injection
- Sentinel monitoring for async event detection
- YAML-based scenario definitions
"""

from .runner import ScenarioRunner, ScenarioStep, Validation
from .sentinel_monitor import SentinelMonitor

__version__ = "0.2.1"
__all__ = ["ScenarioRunner", "ScenarioStep", "Validation", "SentinelMonitor"]
