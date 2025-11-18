# AST Analyzer Usage Guide

## Overview

The AST Analyzer is a production-ready module for extracting structural information from Textual TUI applications. It uses Python's built-in `ast` module to statically analyze source code and extract:

- Screen classes and their hierarchies
- Keybindings (from `BINDINGS` class variables)
- Widgets (from `compose()` methods)
- Action methods (`action_*` methods)
- Navigation flows (screen transitions)

## Installation

The AST Analyzer is part of the `orchestro_cli.intelligence` package:

```python
from orchestro_cli.intelligence import ASTAnalyzer
```

## Basic Usage

### Analyzing a Single File

```python
import asyncio
from pathlib import Path
from orchestro_cli.intelligence import ASTAnalyzer

async def analyze_file_example():
    analyzer = ASTAnalyzer()
    result = await analyzer.analyze_file(Path("my_app/screens.py"))

    print(f"Framework: {result['framework']}")
    print(f"Screens found: {len(result['screens'])}")

    for screen in result['screens']:
        print(f"  - {screen['name']} at line {screen['line_number']}")

asyncio.run(analyze_file_example())
```

### Analyzing an Entire Project

```python
import asyncio
from pathlib import Path
from orchestro_cli.intelligence import ASTAnalyzer

async def analyze_project_example():
    analyzer = ASTAnalyzer()
    knowledge = await analyzer.analyze_project(Path("./my_tui_app"))

    print(f"Project: {knowledge.project_path.name}")
    print(f"Screens: {len(knowledge.screens)}")
    print(f"Entry screen: {knowledge.entry_screen}")

    for screen_name, screen in knowledge.screens.items():
        print(f"\nScreen: {screen_name}")
        print(f"  Keybindings: {len(screen.keybindings)}")
        print(f"  Widgets: {len(screen.widgets)}")
        print(f"  Methods: {len(screen.methods)}")

asyncio.run(analyze_project_example())
```

## Advanced Usage

### Extracting Keybindings

```python
async def extract_keybindings_example():
    analyzer = ASTAnalyzer()
    knowledge = await analyzer.analyze_project(Path("./my_app"))

    for screen_name, screen in knowledge.screens.items():
        print(f"\n{screen_name} keybindings:")
        for kb in screen.keybindings:
            print(f"  {kb.key:15} -> {kb.action:20} ({kb.description})")
```

Output:
```
MainMenuScreen keybindings:
  q               -> quit                 (Quit Application)
  s               -> show_settings        (Settings)
  h               -> show_help            (Help)
```

### Analyzing Widget Structure

```python
async def analyze_widgets_example():
    analyzer = ASTAnalyzer()
    knowledge = await analyzer.analyze_project(Path("./my_app"))

    for screen_name, screen in knowledge.screens.items():
        print(f"\n{screen_name} widgets:")
        for widget in screen.widgets:
            widget_id = widget.widget_id or "no-id"
            print(f"  {widget.widget_type:15} (id={widget_id})")
            if widget.attributes:
                for key, value in widget.attributes.items():
                    print(f"    {key}: {value}")
```

### Navigation Flow Analysis

```python
async def analyze_navigation_example():
    analyzer = ASTAnalyzer()
    knowledge = await analyzer.analyze_project(Path("./my_app"))

    print("Navigation flows:")
    for screen_name, screen in knowledge.screens.items():
        if screen.navigation_targets:
            print(f"\n{screen_name} can navigate to:")
            for target in screen.navigation_targets:
                print(f"  -> {target}")

    print("\n\nNavigation paths:")
    for path in knowledge.navigation_paths:
        print(f"{path.start_screen} -> {path.end_screen} ({path.cost} steps)")
        for step in path.steps:
            print(f"  {step['type']}: {step['action']} -> {step['target']}")
```

### Serialization and Persistence

```python
import json

async def serialization_example():
    analyzer = ASTAnalyzer()
    knowledge = await analyzer.analyze_project(Path("./my_app"))

    # Save to JSON
    data = knowledge.to_dict()
    with open("app_knowledge.json", "w") as f:
        json.dump(data, f, indent=2)

    # Load from JSON
    from orchestro_cli.intelligence.models import AppKnowledge

    with open("app_knowledge.json", "r") as f:
        loaded_data = json.load(f)

    restored_knowledge = AppKnowledge.from_dict(loaded_data)
    print(f"Restored {len(restored_knowledge.screens)} screens")
```

## Error Handling

The analyzer provides robust error handling:

```python
async def error_handling_example():
    analyzer = ASTAnalyzer()

    try:
        # Non-existent file
        await analyzer.analyze_file(Path("/nonexistent/file.py"))
    except FileNotFoundError as e:
        print(f"File not found: {e}")

    try:
        # Empty project
        await analyzer.analyze_project(Path("/empty/directory"))
    except ValueError as e:
        print(f"Invalid project: {e}")

    try:
        # Syntax error in Python file
        # The analyzer will skip files with syntax errors
        # and log a warning
        knowledge = await analyzer.analyze_project(Path("./buggy_app"))
    except Exception as e:
        print(f"Analysis failed: {e}")
```

## Working with the Sample App

A complete sample Textual application is provided for testing:

```bash
# View the sample app
cat tests/intelligence/sample_app.py

# Analyze it
python -c "
import asyncio
from pathlib import Path
from orchestro_cli.intelligence import ASTAnalyzer

async def main():
    analyzer = ASTAnalyzer()

    # Analyze the sample app file
    result = await analyzer.analyze_file(Path('tests/intelligence/sample_app.py'))

    print(f'Found {len(result[\"screens\"])} screens:')
    for screen in result['screens']:
        print(f'  - {screen[\"name\"]}')

asyncio.run(main())
"
```

## Integration with Test Generation

The AST Analyzer is designed to work seamlessly with test generators:

```python
from orchestro_cli.intelligence import ASTAnalyzer, ScenarioGenerator

async def generate_tests_example():
    # Analyze the application
    analyzer = ASTAnalyzer()
    knowledge = await analyzer.analyze_project(Path("./my_app"))

    # Generate test scenarios
    generator = ScenarioGenerator()
    scenarios = await generator.generate(knowledge)

    print(f"Generated {len(scenarios)} test scenarios")
```

## Performance Considerations

- **File Analysis**: ~5-10ms per file
- **Project Analysis**: Scales linearly with number of Python files
- **Memory**: Minimal - only keeps AST nodes during parsing
- **Caching**: Results can be serialized and cached for reuse

## Limitations

1. **Static Analysis Only**: Cannot detect runtime screen installations
2. **Textual-Specific**: Currently only supports Textual framework
3. **Pattern-Based**: Relies on common Textual patterns (may miss custom implementations)

## Future Enhancements

Planned improvements include:

- Runtime introspection support
- Support for other TUI frameworks (Click, Rich, etc.)
- Enhanced navigation flow inference
- Integration with Textual's devtools
- Machine learning-based pattern recognition

## API Reference

### ASTAnalyzer

#### Methods

- `supports_framework(framework_name: str) -> bool`
  - Check if analyzer supports a framework

- `async analyze_file(file_path: Path) -> dict`
  - Analyze a single Python file
  - Returns: Dictionary with screens, imports, framework info

- `async analyze_project(root_path: Path) -> AppKnowledge`
  - Analyze entire project directory
  - Returns: AppKnowledge object with complete structure

### AppKnowledge

#### Attributes

- `project_path: Path` - Project root directory
- `screens: Dict[str, ScreenInfo]` - All discovered screens
- `entry_screen: Optional[str]` - Detected entry screen name
- `navigation_paths: List[NavigationPath]` - Navigation flows

#### Methods

- `add_screen(screen: ScreenInfo)` - Add a screen
- `get_screen(name: str) -> Optional[ScreenInfo]` - Get screen by name
- `to_dict() -> dict` - Serialize to dictionary
- `from_dict(data: dict) -> AppKnowledge` - Deserialize from dictionary

### ScreenInfo

#### Attributes

- `name: str` - Screen name
- `class_name: str` - Python class name
- `file_path: Path` - Source file path
- `keybindings: List[KeybindingInfo]` - Keybindings
- `widgets: List[WidgetInfo]` - Widgets
- `methods: List[str]` - Method names
- `navigation_targets: Set[str]` - Navigation targets

## Support

For issues or questions, please refer to:
- Test suite: `tests/intelligence/test_ast_analyzer.py`
- Verification script: `tests/intelligence/verify_implementation.py`
- Sample app: `tests/intelligence/sample_app.py`
