"""Orchestro Intelligence System

Automatically discovers TUI application structure and generates test scenarios.

This package provides:
- Static code analysis (ASTAnalyzer)
- Application knowledge extraction (AppKnowledge models)
- Test scenario generation (ScenarioGenerator)
- Protocol definitions for extensibility

Example:
    ```python
    from orchestro_cli.intelligence import ASTAnalyzer
    from pathlib import Path

    analyzer = ASTAnalyzer()
    knowledge = await analyzer.analyze_project(Path("./my_app"))
    print(f"Found {len(knowledge.screens)} screens")
    ```
"""

from orchestro_cli.intelligence.models import (
    AppKnowledge,
    ScreenInfo,
    KeybindingInfo,
    WidgetInfo,
    NavigationPath,
)
from orchestro_cli.intelligence.indexing import ASTAnalyzer
from orchestro_cli.intelligence.generation import ScenarioGenerator
from orchestro_cli.intelligence import protocols

__all__ = [
    # Models
    "AppKnowledge",
    "ScreenInfo",
    "KeybindingInfo",
    "WidgetInfo",
    "NavigationPath",
    # Analyzers
    "ASTAnalyzer",
    # Generators
    "ScenarioGenerator",
    # Protocols module
    "protocols",
]

__version__ = "0.2.1"
