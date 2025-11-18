# Dry-Run Mode Guide

## Overview

The dry-run mode allows you to validate your scenario files without actually executing the commands. This is useful for:

- Checking scenario syntax before running tests
- Validating scenario structure in CI/CD pipelines
- Debugging scenario configuration issues
- Learning about scenario structure

## Usage

```bash
python -m orchestro_cli.cli <scenario-file> --dry-run
```

## What Dry-Run Validates

### 1. Command Validation
- Checks if the command field is present
- Verifies if command exists in PATH
- Validates if command file exists and is executable (for relative/absolute paths)

### 2. Timeout Validation
- Ensures timeout is a valid number
- Checks that timeout is positive

### 3. Step Validation
- Validates regex patterns in `expect` steps
- Checks step timeout values
- Validates screenshot name formats
- Verifies control character syntax

### 4. Validation Rules
- Checks `path_exists` has required `path` field
- Validates `file_contains` has both `path` and `text` fields
- Verifies regex patterns in `file_contains` rules
- Detects unknown validation types

### 5. Environment Variables
- Validates environment variable syntax
- Counts and reports defined variables

## Output Format

Dry-run provides detailed output with visual indicators:

- `✓` - Validation passed
- `❌` - Validation error (will cause failure)
- `⚠️` - Warning (won't cause failure)

### Example Output

```
[DRY RUN] Validating scenario: My Test Scenario
[DRY RUN] Description: Example scenario
[DRY RUN] Command: echo test
[DRY RUN] ✓ Command found in PATH
[DRY RUN] Timeout: 30.0s
[DRY RUN] Environment variables: 2 defined
[DRY RUN] Steps: 3 step(s)
[DRY RUN]   1. Send: 'hello'
[DRY RUN]   2. Expect pattern: 'Ready>', timeout: 10.0s
[DRY RUN]   3. Screenshot: initial.svg, timeout: 15.0s
[DRY RUN] Validations: 1 rule(s)
[DRY RUN]   1. ✓ path_exists: artifacts/screenshots/initial.svg

✅ Scenario is valid and ready to run
```

## Exit Codes

- `0` - Scenario is valid (may have warnings)
- `1` - Scenario has validation errors

## Examples

### Valid Scenario

```bash
python -m orchestro_cli.cli examples/dry_run_demo.yaml --dry-run
```

Expected: Exit code 0, success message

### Invalid Scenario

```bash
python -m orchestro_cli.cli examples/invalid_scenario.yaml --dry-run
```

Expected: Exit code 1, detailed error messages

## Common Validation Errors

### Missing Command
```yaml
name: Test
# Error: Missing 'command' field
steps: []
```

### Invalid Regex Pattern
```yaml
steps:
  - expect: "[invalid(regex"  # Error: Unterminated character set
```

### Invalid Timeout
```yaml
timeout: -10  # Error: Timeout must be positive
```

### Missing Validation Fields
```yaml
validations:
  - type: path_exists
    # Error: Missing 'path' field
```

## Warnings vs Errors

### Warnings (Won't Prevent Execution)
- Command not found in PATH (might be installed later)
- Screenshot names with special characters
- Missing optional fields

### Errors (Will Prevent Execution)
- Missing required fields (command, validation paths, etc.)
- Invalid regex patterns
- Invalid timeout values
- Unknown validation types

## Integration with CI/CD

Use dry-run in your CI pipeline to validate scenarios:

```yaml
# .github/workflows/test.yml
- name: Validate Scenarios
  run: |
    python -m orchestro_cli.cli scenarios/test1.yaml --dry-run
    python -m orchestro_cli.cli scenarios/test2.yaml --dry-run
```

## Tips

1. **Always dry-run first**: Validate your scenario before running it
2. **Check exit codes**: Use `$?` to check if validation passed
3. **Read all output**: Warnings might indicate potential runtime issues
4. **Fix errors before running**: Don't ignore validation errors
5. **Use verbose mode**: Combine with `-v` for more details (if needed)

## Limitations

Dry-run mode does NOT:
- Execute commands or spawn processes
- Check if expected patterns will actually match
- Verify that files exist (only validates path format)
- Test actual application behavior
- Create screenshots or artifacts

Dry-run only validates the scenario structure and syntax.
