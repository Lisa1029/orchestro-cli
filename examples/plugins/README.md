# Orchestro CLI Plugin Examples

This directory contains example plugins demonstrating the plugin system.

## Available Examples

### 1. Delay Step Plugin (`delay_step_plugin.py`)

Adds a `delay` step type for waiting during scenario execution.

**Usage:**
```yaml
steps:
  - note: "delay: 2.5"
    # Waits 2.5 seconds before continuing
```

**Features:**
- Configurable delay duration
- Validation of delay values
- Timeout protection

### 2. JSON Reporter Plugin (`json_reporter_plugin.py`)

Generates JSON format test reports.

**Features:**
- Machine-readable JSON output
- Multiple scenario aggregation
- ISO 8601 timestamps
- Metadata support

## Creating Your Own Plugins

### Step Plugin Template

```python
from orchestro_cli.interfaces.step_plugin import StepPlugin, ExecutionContext
from orchestro_cli.parsing.models import Step

class MyStepPlugin:
    @property
    def step_type(self) -> str:
        return "my_custom_step"

    def can_handle(self, step: Step) -> bool:
        # Return True if this plugin handles the step
        return hasattr(step, 'custom_field')

    async def execute(self, step: Step, context: ExecutionContext, timeout: float):
        # Implement step logic
        context.log("Executing custom step")
        return {"result": "success"}

    def validate_step(self, step: Step) -> list[str]:
        # Return list of validation errors (empty if valid)
        return []

def register(registry):
    registry.register_step_plugin(MyStepPlugin())
```

### Reporter Plugin Template

```python
from orchestro_cli.interfaces.reporter_plugin import BaseReporter, ScenarioReport
from pathlib import Path

class MyReporter(BaseReporter):
    def __init__(self):
        super().__init__(
            reporter_name="my_format",
            file_extension=".ext",
            verbose=True
        )

    def generate_report(self, report_data: ScenarioReport, output_path: Path):
        # Generate report in your format
        with open(output_path, 'w') as f:
            f.write("Custom report content")

def register(registry):
    registry.register_reporter_plugin(MyReporter())
```

### Validator Plugin Template

```python
from orchestro_cli.interfaces.validator_plugin import (
    BaseValidator,
    ValidationContext,
    ValidationResult
)

class MyValidator(BaseValidator):
    def __init__(self):
        super().__init__("my_validation_type")

    def validate(self, validation_spec: dict, context: ValidationContext):
        # Perform validation
        passed = True  # Your validation logic
        return ValidationResult(
            passed=passed,
            validator_type=self.validator_type,
            message="Validation result"
        )

    def validate_spec(self, validation_spec: dict) -> list[str]:
        # Validate the spec itself
        return []

def register(registry):
    registry.register_validator_plugin(MyValidator())
```

## Loading Plugins

### Method 1: Auto-Discovery

Place plugins in standard locations:
- `~/.orchestro/plugins/`
- `./orchestro_plugins/`

```python
from orchestro_cli.plugins import PluginManager

manager = PluginManager()
count = manager.discover_plugins()
print(f"Loaded {count} plugins")
```

### Method 2: Explicit Loading

```python
from pathlib import Path
from orchestro_cli.plugins import PluginManager

manager = PluginManager()
manager.load_from_file(Path("my_plugin.py"))
manager.load_from_directory(Path("plugins/"))
manager.load_from_module("myapp.orchestro_plugins")
```

### Method 3: Direct Registration

```python
from orchestro_cli.plugins import PluginRegistry

registry = PluginRegistry()
registry.register_step_plugin(MyStepPlugin())
registry.register_reporter_plugin(MyReporter())
```

## Plugin Development Tips

1. **Single Responsibility**: Each plugin should do one thing well
2. **Error Handling**: Provide clear error messages in validation
3. **Documentation**: Include docstrings and usage examples
4. **Testing**: Write unit tests for your plugins
5. **Performance**: Avoid blocking operations in step execution
6. **Compatibility**: Test with different Python versions

## Testing Plugins

```python
import pytest
from orchestro_cli.plugins import PluginRegistry

def test_my_plugin():
    registry = PluginRegistry()

    # Register plugin
    from my_plugin import register
    register(registry)

    # Verify registration
    assert len(registry.get_step_plugins()) == 1

    # Test functionality
    plugin = registry.get_step_plugins()[0]
    assert plugin.step_type == "my_custom_step"
```

## Plugin Distribution

### PyPI Package

```python
# setup.py
from setuptools import setup

setup(
    name="orchestro-my-plugin",
    entry_points={
        "orchestro.plugins": [
            "my_plugin = my_plugin:register"
        ]
    }
)
```

### Local Installation

```bash
pip install -e /path/to/my-plugin
```

## Community Plugins

Submit your plugins to the [Orchestro Plugin Registry](https://github.com/orchestro-cli/plugins)!

## Support

- Issues: https://github.com/orchestro-cli/orchestro/issues
- Docs: https://orchestro-cli.readthedocs.io/plugins
- Discord: https://discord.gg/orchestro-cli
