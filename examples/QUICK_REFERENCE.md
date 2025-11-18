# Orchestro CLI Examples - Quick Reference Card

## Examples at a Glance

| Example | Difficulty | Runtime | Key Features |
|---------|-----------|---------|--------------|
| `basic_echo.yaml` | ⭐ Beginner | 5s | Expect patterns, basic timeouts |
| `python_repl.yaml` | ⭐ Beginner | 30s | Interactive sessions, expect/send cycles |
| `file_validation.yaml` | ⭐⭐ Intermediate | 10s | File operations, content validation |
| `environment_vars.yaml` | ⭐⭐ Intermediate | 30s | Environment configuration, variable usage |
| `timeout_handling.yaml` | ⭐⭐ Intermediate | 120s | Timeout configuration, best practices |
| `multi_step_workflow.yaml` | ⭐⭐⭐ Advanced | 60s | Complex pipelines, multi-phase workflows |
| `screenshot_gallery.yaml` | ⭐⭐⭐ Advanced | 90s | TUI testing, screenshot capture (template) |
| `screenshot_example.yaml` | ⭐⭐⭐ Advanced | 30s | VyB-specific TUI testing (original) |

## Run Any Example

```bash
orchestro examples/<example-name>.yaml --verbose
```

## Example Selection Guide

### "I want to learn..."

**Basic Orchestro usage** → `basic_echo.yaml`

**Interactive CLI testing** → `python_repl.yaml`

**File creation and validation** → `file_validation.yaml`

**Environment variables** → `environment_vars.yaml`

**Timeout configuration** → `timeout_handling.yaml`

**Complex workflows** → `multi_step_workflow.yaml`

**TUI screenshot testing** → `screenshot_gallery.yaml`

### "I need to test..."

**Simple command output** → `basic_echo.yaml`

**REPL or interactive shell** → `python_repl.yaml`

**Script that creates files** → `file_validation.yaml`

**App with configuration** → `environment_vars.yaml`

**Slow operations** → `timeout_handling.yaml`

**Data pipeline** → `multi_step_workflow.yaml`

**Terminal UI app** → `screenshot_gallery.yaml`

## Syntax Quick Reference

### Step Types

```yaml
# Wait for pattern (regex)
- expect: "Ready|Started"
  timeout: 10
  note: "Waiting for app..."

# Send input (with newline)
- send: "command"
  note: "Sending command..."

# Send raw input (no newline)
- send: "raw input"
  raw: true

# Send control character
- control: "c"  # Ctrl+C
  note: "Interrupting..."

# Capture screenshot
- screenshot: "screen-name"
  timeout: 15
  note: "Capturing screen..."
```

### Validation Types

```yaml
validations:
  # Check file exists
  - type: path_exists
    path: output/file.txt
    description: "File created"

  # Check file content
  - type: file_contains
    path: output/file.txt
    text: "expected.*pattern"  # Regex
    description: "Content matches"
```

### Environment Variables

```yaml
env:
  APP_NAME: "MyApp"
  ENABLE_DEBUG: "true"
  MAX_WORKERS: "4"
```

## Timeout Guidelines

| Operation Type | Recommended Timeout |
|----------------|---------------------|
| Quick commands | 1-5s |
| Normal operations | 5-15s |
| Slow operations | 15-30s |
| Very slow operations | 30-60s |
| Screenshot capture | 10-20s |
| File I/O | 3-10s |

**Rule of thumb**: Add 20-30% buffer to expected operation time

## Common Patterns

### Basic Test Flow
```yaml
name: My Test
command: ./app
timeout: 30

steps:
  - expect: "Ready"
  - send: "command"
  - expect: "Output"

validations:
  - type: path_exists
    path: output.txt
```

### Interactive Session
```yaml
steps:
  - expect: "prompt>"
    timeout: 5
  - send: "input"
  - expect: "response"
    timeout: 3
  - send: "exit"
```

### Screenshot Sequence
```yaml
steps:
  - screenshot: "01-start"
    timeout: 15
  - send: "navigate"
  - screenshot: "02-screen"
    timeout: 15
```

### File Validation
```yaml
validations:
  - type: path_exists
    path: output/data.csv
  - type: file_contains
    path: output/data.csv
    text: "Success.*complete"
```

## Debugging Tips

### Enable Verbose Mode
```bash
orchestro example.yaml --verbose
```

### Common Fixes

**"Timeout waiting for pattern"**
- Increase timeout value
- Check regex pattern syntax
- Use `.*` to match anything
- Enable verbose to see actual output

**"Screenshot not captured"**
- Ensure app has screenshot monitoring code
- Increase screenshot timeout
- Check trigger directory exists
- Verify `VYB_AUTO_SCREENSHOT=1` is set

**"Validation failed: path not found"**
- Check path is relative to correct directory
- Verify file created before validation
- Use absolute paths if needed

**"Validation failed: text not found"**
- Check regex pattern escaping
- Verify file has expected content
- Use simpler pattern for debugging

## Cleanup Commands

```bash
# Clean basic examples
rm -rf test_output/ pipeline/ timeout_test_results.txt

# Clean environment example
rm -f env_test_config.ini env_test_report.txt
rm -rf /tmp/orchestro-data/

# Clean screenshots
rm -rf artifacts/screenshots/

# Clean all
rm -rf test_output/ pipeline/ artifacts/ *.txt *.ini /tmp/orchestro-data/
```

## Next Steps

1. **Start with basics**: Run `basic_echo.yaml`
2. **Try interactive**: Run `python_repl.yaml`
3. **Learn validation**: Run `file_validation.yaml`
4. **Explore features**: Run other examples
5. **Create your own**: Copy and modify examples
6. **Read full docs**: See `README.md` for details

## Resources

- **Detailed Guide**: [examples/README.md](README.md)
- **Main Documentation**: [../README.md](../README.md)
- **API Reference**: [../docs/API.md](../docs/API.md)

---

*Quick Reference v1.0 - Orchestro CLI Testing Framework*
