# Inline Assertions for Orchestro

## Overview

Inline assertions enable concise test validation directly in YAML scenario definitions. Instead of separate validation blocks, you can now specify assertions inline with each step.

## Quick Start

```yaml
name: Simple Test
command: bash
steps:
  - send: "echo hello"
  - expect_output: "hello"
  - expect_code: 0
```

## Supported Assertion Types

### 1. `expect_output` - Exact Output Match

Validates that command output exactly matches the expected value (whitespace is trimmed).

```yaml
steps:
  - send: "echo 'Hello, World!'"
  - expect_output: "Hello, World!"
```

### 2. `expect_code` - Exit Code Validation

Validates command exit code.

```yaml
steps:
  - send: "true"
  - expect_code: 0

  - send: "false"
  - expect_code: 1
```

### 3. `expect_contains` - Substring Match

Validates that output contains specific text.

```yaml
steps:
  - send: "echo 'The quick brown fox'"
  - expect_contains: "quick"
```

### 4. `expect_regex` - Regular Expression Match

Validates output against a regex pattern.

```yaml
steps:
  - send: "echo '12345'"
  - expect_regex: "^\\d+$"

  - send: "date '+%Y-%m-%d'"
  - expect_regex: "^\\d{4}-\\d{2}-\\d{2}$"
```

### 5. `expect_lines` - Line Count

Validates the number of lines in output.

```yaml
steps:
  - send: "printf 'line1\\nline2\\nline3'"
  - expect_lines: 3
```

### 6. `expect_not_contains` - Negative Match

Validates that output does NOT contain specific text.

```yaml
steps:
  - send: "echo 'Success!'"
  - expect_not_contains: "error"
  - expect_not_contains: "failed"
```

### 7. `expect_json` - JSON Structure Validation

Validates JSON output structure and content.

```yaml
steps:
  - send: "cat config.json"
  - expect_json:
      name: "test"
      version: "1.0.0"
      enabled: true
```

## Multiple Assertions Per Step

You can combine multiple assertions on a single step:

```yaml
steps:
  - send: "echo 'test output'"
  - expect_output: "test output"
    expect_contains: "test"
    expect_regex: "^test"
    expect_lines: 1
    expect_not_contains: "error"
```

## Backward Compatibility

Inline assertions work alongside legacy validations:

```yaml
name: Mixed Validations
command: ./my-app
steps:
  - send: "create file.txt"
  - expect_output: "File created"

# Legacy validations still work
validations:
  - type: path_exists
    path: file.txt
  - type: file_contains
    path: file.txt
    text: "content"
```

## Error Messages

Assertions provide clear, actionable error messages:

```
❌ Assertion failed: output
  Error: Output does not match expected value
  Expected: hello world
  Actual:   goodbye world
  Diff:
--- expected
+++ actual
@@ -1 +1 @@
-hello world
+goodbye world
  Location: line 42
```

## Advanced Examples

### Testing Command Success

```yaml
steps:
  - send: "make build"
  - expect_code: 0
    expect_contains: "Build successful"
    expect_not_contains: "error"
```

### Validating API Responses

```yaml
steps:
  - send: "curl -s http://api/status"
  - expect_json:
      status: "ok"
      code: 200
    expect_contains: "healthy"
```

### Testing Error Handling

```yaml
steps:
  - send: "rm /nonexistent 2>&1 || echo 'Expected failure'"
  - expect_contains: "Expected failure"
    expect_not_contains: "panic"
```

### Verifying Multi-line Output

```yaml
steps:
  - send: "ls -1 /etc"
  - expect_lines: 10
    expect_contains: "hosts"
    expect_regex: ".*\\.conf$"
```

## Performance

- Assertions run in parallel when possible
- Fail-fast mode stops on first failure
- Non-blocking mode collects all failures

## Configuration

Control assertion behavior in code:

```python
from orchestro_cli.assertions import AssertionEngine

# Fail-fast mode (default)
engine = AssertionEngine(fail_fast=True)

# Collect all failures
engine = AssertionEngine(fail_fast=False)

# Verbose mode for debugging
engine = AssertionEngine(verbose=True)
```

## Integration with Plugins

Create custom assertion validators:

```python
from orchestro_cli.plugins.assertion_validator import AssertionValidator

class CustomValidator(AssertionValidator):
    def validate(self, validation_spec, context):
        # Custom validation logic
        pass

# Register with plugin system
def register(registry):
    registry.register_validator_plugin(CustomValidator())
```

## Best Practices

1. **Use descriptive assertions**: Combine multiple assertion types for comprehensive validation
2. **Test both success and failure**: Validate expected behavior and error handling
3. **Keep assertions simple**: Each assertion should test one specific condition
4. **Use regex for patterns**: When exact match is too strict, use regex patterns
5. **Verify absence of errors**: Use `expect_not_contains` to ensure clean output

## Comparison with Legacy Validations

### Before (Legacy)
```yaml
steps:
  - send: "echo hello"

validations:
  - type: output
    pattern: "hello"
  - type: exit_code
    value: 0
```

### After (Inline)
```yaml
steps:
  - send: "echo hello"
  - expect_output: "hello"
    expect_code: 0
```

Benefits:
- Less verbose
- Easier to read
- Assertions are close to the steps they validate
- Better error messages with line numbers
- More assertion types available

## Testing

Run assertion tests:
```bash
pytest tests/test_assertions.py -v
pytest tests/test_assertion_parser.py -v
```

## API Reference

### AssertionEngine

Main engine for validating assertions.

```python
engine = AssertionEngine(fail_fast=True, verbose=False)
result = engine.validate(assertion)
results = engine.validate_all(assertions)
summary = engine.get_summary()
```

### Assertion

Represents a single assertion.

```python
from orchestro_cli.assertions import Assertion, AssertionType

assertion = Assertion(
    assertion_type=AssertionType.OUTPUT,
    expected="hello",
    actual="hello",
    description="Verify greeting",
    line_number=42
)
```

### AssertionResult

Result of an assertion validation.

```python
result.passed  # True/False
result.error_message  # Error description
result.format_failure()  # Formatted error message
```

## Contributing

To add new assertion types:

1. Add to `AssertionType` enum in `models.py`
2. Implement validator in `engine.py`
3. Add parser support in `scenario_parser.py`
4. Add to `Step` model in `parsing/models.py`
5. Write tests
6. Update documentation

## See Also

- [Validation Engine](../orchestro_cli/validation/validation_engine.py)
- [Plugin System](../orchestro_cli/plugins/README.md)
- [Example Scenarios](../examples/inline_assertions_demo.yaml)
