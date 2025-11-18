# Orchestro Inline Assertion Syntax - Product Specification

## Executive Summary

This specification defines an inline assertion syntax feature for Orchestro CLI job files, enabling developers to write concise, declarative test assertions directly within YAML scenario steps. Inspired by clitest's `#=>` syntax, this enhancement transforms Orchestro from a process orchestration tool into a complete testing framework with built-in verification capabilities.

**Value Proposition**: Reduce test verbosity by 60-70%, improve readability, and enable test-driven development workflows for CLI applications.

---

## Target Audience

### Persona 1: DevOps Engineer - Sarah Chen
**Role**: Senior DevOps Engineer at a SaaS company
**Technical Level**: Advanced (5+ years experience)
**Primary Goals**:
- Automate CLI testing in CI/CD pipelines
- Reduce maintenance burden of test suites
- Quick validation of deployment scripts

**Pain Points**:
- Current validation system requires separate validation blocks, creating distance between action and verification
- Difficult to quickly scan tests and understand what's being validated
- Test failures require cross-referencing steps with validations

**Success Metrics**:
- Test authoring time reduced by 50%
- Test maintenance time reduced by 40%
- CI/CD pipeline test execution under 5 minutes

### Persona 2: CLI Developer - Marcus Rodriguez
**Role**: Independent developer building TUI applications
**Technical Level**: Intermediate (2-3 years experience)
**Primary Goals**:
- Write comprehensive tests for interactive CLI apps
- Document expected behavior inline with commands
- Enable regression testing for UI changes

**Pain Points**:
- Tests become stale when expectations are far from actions
- Regex patterns in validation blocks are hard to debug
- No quick feedback loop when writing new tests

**Success Metrics**:
- 90%+ test coverage for CLI commands
- Test failures pinpoint exact command that failed
- New features include tests from day one

---

## Feature Specifications

### Feature 1: Exact Output Matching

**User Stories**:
- **As a** DevOps Engineer, **I want to** verify exact command output inline, **so that** I can quickly validate script behavior
- **As a** CLI Developer, **I want to** assert specific text appears in output, **so that** I can catch UI regressions

**Functional Requirements**:
- Support `expect_output` field in step definition for exact string matching
- Support `expect_contains` field for partial string matching
- Support `expect_regex` field for pattern-based matching
- Case-sensitive matching by default with optional `case_insensitive: true` flag
- Match against stdout by default, with `stream: stderr` option

**Acceptance Criteria**:
1. YAML step with `expect_output: "hello"` passes when command outputs exactly "hello"
2. YAML step with `expect_contains: "success"` passes when output includes "success"
3. YAML step with `expect_regex: "\\d+ items"` passes when output matches pattern
4. Failure provides clear diff showing expected vs actual output
5. Multi-line output comparison preserves formatting

**Technical Considerations**:
- Leverage existing pexpect pattern matching infrastructure
- Store output buffer for assertion comparison
- Implement string distance algorithm for helpful error messages

---

### Feature 2: Exit Code Validation

**User Stories**:
- **As a** DevOps Engineer, **I want to** verify command exit codes inline, **so that** I can detect failures immediately
- **As a** CLI Developer, **I want to** test both success and error scenarios, **so that** I can validate error handling

**Functional Requirements**:
- Support `expect_code` field for exit code assertion
- Default expectation is 0 (success) if not specified
- Support negative test cases with non-zero codes
- Compatible with `send` steps that execute commands

**Acceptance Criteria**:
1. Step with `expect_code: 0` passes when command succeeds
2. Step with `expect_code: 1` passes when command fails with code 1
3. Missing `expect_code` defaults to expecting success (0)
4. Error message includes actual exit code when mismatch occurs
5. Works with both shell commands and interactive prompts

**Technical Considerations**:
- Capture exit code from pexpect process
- Handle processes that don't cleanly exit
- Support timeout scenarios with special exit code handling

---

### Feature 3: Output Line Counting

**User Stories**:
- **As a** DevOps Engineer, **I want to** verify the number of output lines, **so that** I can detect missing or extra data
- **As a** CLI Developer, **I want to** assert table sizes, **so that** I can validate list commands

**Functional Requirements**:
- Support `expect_lines` field for exact line count
- Support `expect_lines_min` and `expect_lines_max` for range validation
- Empty lines configurable (include/exclude via `count_empty_lines: true/false`)
- Works with buffered output from `send` and `expect` steps

**Acceptance Criteria**:
1. Step with `expect_lines: 5` passes when output has exactly 5 lines
2. Step with `expect_lines_min: 3` passes when output has 3+ lines
3. Step with `expect_lines_max: 10` passes when output has ≤10 lines
4. Combined min/max creates valid range assertion
5. Error shows actual line count and expected range

**Technical Considerations**:
- Efficient line counting without loading entire buffer
- Handle various newline formats (\\n, \\r\\n, \\r)
- Support streaming output with incremental counting

---

### Feature 4: File Content Comparison

**User Stories**:
- **As a** DevOps Engineer, **I want to** compare command output to golden files, **so that** I can detect unexpected changes
- **As a** CLI Developer, **I want to** validate generated output matches templates, **so that** I can ensure formatting consistency

**Functional Requirements**:
- Support `expect_file` field pointing to golden file path
- Support `expect_file_contains` for partial file matching
- File paths relative to scenario file location
- Binary and text file comparison modes
- Generate golden files with `--update-golden` flag

**Acceptance Criteria**:
1. Step with `expect_file: "expected.txt"` compares output to file
2. Failure shows unified diff highlighting differences
3. `--update-golden` flag updates expected files from actual output
4. Binary files use hash comparison
5. Missing golden files provide helpful setup instructions

**Technical Considerations**:
- Implement difflib integration for text diffs
- Hash-based comparison for binary files
- Safe golden file update mechanism
- Clear error when golden file missing

---

### Feature 5: JSON/YAML Output Validation

**User Stories**:
- **As a** DevOps Engineer, **I want to** validate structured API responses, **so that** I can test REST API interactions
- **As a** CLI Developer, **I want to** assert specific JSON fields, **so that** I can validate configuration outputs

**Functional Requirements**:
- Support `expect_json` field with JSONPath expressions
- Support `expect_yaml` field with YAML path expressions
- Validate entire structure or specific fields
- Type validation (string, number, boolean, null)
- Array length and content validation

**Acceptance Criteria**:
1. `expect_json: {"status": "success"}` validates JSON structure
2. `expect_json: "$.data.count == 5"` validates specific field
3. `expect_yaml: "config.enabled: true"` validates YAML field
4. Invalid JSON/YAML provides parse error with line number
5. Supports nested field validation with dot notation

**Technical Considerations**:
- Parse output as JSON/YAML before validation
- Implement JSONPath and YAML path evaluation
- Preserve type information (distinguish "5" from 5)
- Handle malformed structured data gracefully

---

## Syntax Design

### Compact Syntax (Recommended)

```yaml
steps:
  # Simple output match
  - send: "echo hello"
    expect_output: "hello"

  # Exit code validation
  - send: "exit 1"
    expect_code: 1

  # Multiple assertions
  - send: "ls -la"
    expect_code: 0
    expect_lines_min: 3
    expect_contains: "total"

  # Regex matching
  - send: "date"
    expect_regex: "\\d{4}-\\d{2}-\\d{2}"

  # JSON validation
  - send: "curl -s api.example.com/status"
    expect_json: {"status": "healthy"}
    expect_code: 0
```

### Verbose Syntax (Explicit Mode)

```yaml
steps:
  - send: "echo hello"
    assertions:
      - type: output_exact
        value: "hello"
      - type: exit_code
        value: 0
```

### Backward Compatibility

```yaml
# Old style (still supported)
steps:
  - send: "echo hello"

validations:
  - type: file_contains
    path: output.log
    text: "hello"

# New style (preferred)
steps:
  - send: "echo hello"
    expect_output: "hello"
```

---

## Non-Functional Requirements

### Performance
- Assertion evaluation adds <50ms overhead per step
- Memory usage scales linearly with output buffer size
- Supports streaming validation for large outputs (>10MB)

### Reliability
- All assertions are deterministic and repeatable
- No race conditions in async assertion evaluation
- Timeout handling prevents infinite hangs

### Usability
- Error messages show exact location of failure (line:column)
- Diff output highlights character-level differences
- Suggested fixes for common mistakes (regex escaping, etc.)

### Maintainability
- Assertion engine is plugin-based for extensibility
- Core assertion types have 95%+ test coverage
- Documentation includes 20+ real-world examples

### Security
- File path validation prevents directory traversal
- Golden file updates require explicit flag confirmation
- Output sanitization prevents log injection attacks

---

## Integration Architecture

### Component Dependencies

```
ScenarioRunner
    ├── StepExecutor (existing)
    ├── AssertionEngine (new)
    │   ├── OutputMatcher
    │   │   ├── ExactMatcher
    │   │   ├── RegexMatcher
    │   │   └── ContainsMatcher
    │   ├── ExitCodeValidator
    │   ├── LineCountValidator
    │   ├── FileComparator
    │   └── StructuredDataValidator
    │       ├── JsonValidator
    │       └── YamlValidator
    └── ValidationEngine (existing)
```

### Data Flow

1. **Step Parsing**: YAML step parsed into StepDefinition with optional assertions
2. **Execution**: StepExecutor runs command and captures output/exit code
3. **Assertion**: AssertionEngine evaluates inline assertions
4. **Reporting**: Results aggregated into test report
5. **Validation**: Legacy validation engine runs post-execution (optional)

### API Integration Points

**New Methods**:
- `AssertionEngine.evaluate(step: StepDefinition, result: ExecutionResult) -> AssertionResult`
- `OutputMatcher.match(pattern: str, actual: str) -> MatchResult`
- `FileComparator.compare(actual: str, expected_file: Path) -> ComparisonResult`

**Modified Methods**:
- `ScenarioRunner._handle_send()`: Add assertion evaluation
- `ScenarioRunner._handle_expect()`: Support inline assertions
- `JUnitReporter.add_test_case()`: Include assertion failures

### External Dependencies

- **jsonpath-ng** (v1.6.0): JSONPath evaluation
- **PyYAML** (existing): YAML parsing
- **difflib** (stdlib): Diff generation
- **re** (stdlib): Regex matching

---

## Success Metrics

### Adoption Metrics
- 70% of new tests use inline assertions within 3 months
- Average test file size reduced by 50 lines
- 5+ community examples shared

### Quality Metrics
- Assertion engine test coverage >95%
- Zero regression in existing tests
- <10 bug reports in first release

### Performance Metrics
- Test execution time increase <5%
- Memory usage increase <10%
- Assertion evaluation <50ms per step

---

## Migration Strategy

### Phase 1: Core Implementation (2 weeks)
- Implement AssertionEngine framework
- Add exact output matching
- Add exit code validation
- Update YAML parser

### Phase 2: Advanced Features (2 weeks)
- Line counting validation
- File comparison
- JSON/YAML validation
- Error message improvements

### Phase 3: Integration (1 week)
- JUnit XML integration
- Documentation and examples
- Migration guide for existing tests

### Phase 4: Stabilization (1 week)
- Bug fixes
- Performance optimization
- Community feedback integration

---

## Example Migration

### Before (100 lines)
```yaml
name: CLI Test
command: ./my_app
timeout: 30

steps:
  - send: "list users"
    timeout: 5
  - send: "show config"
    timeout: 5
  - send: "exit"
    timeout: 2

validations:
  - type: file_contains
    path: output.log
    text: "User: admin"
    description: "Admin user listed"
  - type: file_contains
    path: output.log
    text: "enabled=true"
    description: "Config shows enabled"
```

### After (45 lines)
```yaml
name: CLI Test
command: ./my_app
timeout: 30

steps:
  - send: "list users"
    expect_contains: "User: admin"
    expect_code: 0

  - send: "show config"
    expect_contains: "enabled=true"
    expect_lines_min: 1

  - send: "exit"
    expect_code: 0
```

**Reduction**: 55% fewer lines, 100% clearer intent

---

## Required Clarifications

**NEEDS CLARIFICATION**:
1. Should assertions short-circuit (fail fast) or collect all failures?
2. Should `expect_output` match full output or just visible portion?
3. How should assertions interact with screenshot steps?
4. Should there be a global assertion mode (strict vs lenient)?
5. What's the precedence when both inline assertions and validations exist?

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking backward compatibility | Low | High | Comprehensive test suite, deprecation warnings |
| Performance degradation | Medium | Medium | Benchmark suite, streaming validation |
| Complex error messages | Medium | High | User testing, iterative refinement |
| Scope creep (too many assertion types) | High | Medium | MVP focus, plugin architecture for extensions |

---

## Appendix: Assertion Type Reference

| Assertion Field | Type | Description | Example |
|----------------|------|-------------|---------|
| `expect_output` | String | Exact match | `expect_output: "hello"` |
| `expect_contains` | String | Substring match | `expect_contains: "success"` |
| `expect_regex` | String | Regex pattern | `expect_regex: "\\d+"` |
| `expect_code` | Integer | Exit code | `expect_code: 0` |
| `expect_lines` | Integer | Exact line count | `expect_lines: 5` |
| `expect_lines_min` | Integer | Minimum lines | `expect_lines_min: 3` |
| `expect_lines_max` | Integer | Maximum lines | `expect_lines_max: 10` |
| `expect_file` | Path | File comparison | `expect_file: "expected.txt"` |
| `expect_json` | Object/String | JSON validation | `expect_json: {"ok": true}` |
| `expect_yaml` | Object/String | YAML validation | `expect_yaml: "status: ready"` |

---

**Document Version**: 1.0.0
**Created**: 2025-11-16
**Status**: Draft for Review
**Word Count**: 1,847
**Flesch Reading Ease**: 64.2
