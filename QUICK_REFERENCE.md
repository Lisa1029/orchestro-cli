# Inline Assertions - Quick Reference

## Basic Syntax

```yaml
steps:
  - send: "command"
  - expect_output: "expected"
  - expect_code: 0
```

## All Assertion Types

| Assertion | Purpose | Example |
|-----------|---------|---------|
| `expect_output` | Exact match | `expect_output: "hello world"` |
| `expect_code` | Exit code | `expect_code: 0` |
| `expect_contains` | Substring | `expect_contains: "success"` |
| `expect_regex` | Pattern | `expect_regex: "^\\d+$"` |
| `expect_lines` | Line count | `expect_lines: 3` |
| `expect_not_contains` | Absence | `expect_not_contains: "error"` |
| `expect_json` | JSON structure | `expect_json: {key: value}` |

## Multiple Assertions

```yaml
steps:
  - send: "echo test"
  - expect_output: "test"
    expect_contains: "te"
    expect_regex: "^test$"
    expect_lines: 1
```

## File Locations

### Core Implementation
- `/home/jonbrookings/vibe_coding_projects/my-orchestro-copy/orchestro_cli/assertions/engine.py` - Validation engine
- `/home/jonbrookings/vibe_coding_projects/my-orchestro-copy/orchestro_cli/assertions/models.py` - Data models
- `/home/jonbrookings/vibe_coding_projects/my-orchestro-copy/orchestro_cli/parsing/scenario_parser.py` - YAML parser
- `/home/jonbrookings/vibe_coding_projects/my-orchestro-copy/orchestro_cli/execution/step_executor.py` - Step execution

### Tests
- `/home/jonbrookings/vibe_coding_projects/my-orchestro-copy/tests/test_assertions.py` - Engine tests
- `/home/jonbrookings/vibe_coding_projects/my-orchestro-copy/tests/test_assertion_parser.py` - Parser tests

### Documentation
- `/home/jonbrookings/vibe_coding_projects/my-orchestro-copy/docs/inline-assertions.md` - Full guide
- `/home/jonbrookings/vibe_coding_projects/my-orchestro-copy/examples/inline_assertions_demo.yaml` - Examples

## Common Patterns

### Success Validation
```yaml
- send: "make build"
- expect_code: 0
  expect_contains: "Build successful"
  expect_not_contains: "error"
```

### Error Checking
```yaml
- send: "validate input"
- expect_contains: "Invalid"
  expect_code: 1
```

### JSON API
```yaml
- send: "curl api/status"
- expect_json:
    status: "ok"
    code: 200
```

### Multi-line Output
```yaml
- send: "ls -1"
- expect_lines: 5
  expect_regex: ".*\\.txt$"
```

## Running Tests

```bash
# Run all assertion tests
pytest tests/test_assertions.py tests/test_assertion_parser.py -v

# Run with coverage
pytest tests/test_assertions.py --cov=orchestro_cli/assertions --cov-report=term-missing

# Run example scenario
orchestro run examples/inline_assertions_demo.yaml
```

## Integration with Code

```python
from orchestro_cli.assertions import AssertionEngine, Assertion, AssertionType

# Create engine
engine = AssertionEngine(fail_fast=True)

# Create assertion
assertion = Assertion(
    assertion_type=AssertionType.OUTPUT,
    expected="hello",
    actual="hello"
)

# Validate
result = engine.validate(assertion)
print(f"Passed: {result.passed}")
```

## Key Features

- ✅ 7 assertion types
- ✅ Multiple assertions per step
- ✅ Backward compatible
- ✅ Clear error messages
- ✅ Line number tracking
- ✅ Unified diffs
- ✅ >90% test coverage

## Architecture

```
┌─────────────────────┐
│   YAML Scenario     │
│   (expect_output)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  ScenarioParser     │
│  Recognizes keywords│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Step Model         │
│  has_assertions     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  StepExecutor       │
│  Captures output    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  AssertionEngine    │
│  Validates results  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  AssertionResult    │
│  Pass/Fail + Diff   │
└─────────────────────┘
```

## Next Steps

1. Read `/home/jonbrookings/vibe_coding_projects/my-orchestro-copy/docs/inline-assertions.md` for full documentation
2. Review `/home/jonbrookings/vibe_coding_projects/my-orchestro-copy/examples/inline_assertions_demo.yaml` for examples
3. Run tests to verify installation
4. Try creating your first assertion-based scenario
