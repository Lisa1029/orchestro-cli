# JUnit XML Integration Guide

Orchestro CLI supports generating JUnit XML test reports for seamless CI/CD integration. This allows you to integrate your CLI testing workflows with popular continuous integration systems like Jenkins, GitHub Actions, GitLab CI, and Azure DevOps.

## Quick Start

Generate a JUnit XML report by adding the `--junit-xml` flag:

```bash
orchestro scenario.yaml --junit-xml=test-results/junit.xml
```

## CI/CD Platform Integration

### GitHub Actions

```yaml
name: CLI Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Orchestro CLI
        run: pip install orchestro-cli

      - name: Run CLI tests
        run: orchestro scenarios/test.yaml --junit-xml=test-results/junit.xml

      - name: Publish Test Results
        uses: EnricoMi/publish-unit-test-result-action@v2
        if: always()
        with:
          files: test-results/junit.xml
```

### GitLab CI

```yaml
test:
  stage: test
  script:
    - pip install orchestro-cli
    - orchestro scenarios/test.yaml --junit-xml=test-results/junit.xml
  artifacts:
    when: always
    reports:
      junit: test-results/junit.xml
```

### Jenkins

```groovy
pipeline {
    agent any

    stages {
        stage('Test') {
            steps {
                sh 'pip install orchestro-cli'
                sh 'orchestro scenarios/test.yaml --junit-xml=test-results/junit.xml'
            }
        }
    }

    post {
        always {
            junit 'test-results/junit.xml'
        }
    }
}
```

### Azure DevOps

```yaml
steps:
  - script: |
      pip install orchestro-cli
      orchestro scenarios/test.yaml --junit-xml=test-results/junit.xml
    displayName: 'Run CLI Tests'

  - task: PublishTestResults@2
    inputs:
      testResultsFormat: 'JUnit'
      testResultsFiles: 'test-results/junit.xml'
    condition: always()
```

### CircleCI

```yaml
version: 2.1

jobs:
  test:
    docker:
      - image: python:3.11
    steps:
      - checkout
      - run:
          name: Install dependencies
          command: pip install orchestro-cli
      - run:
          name: Run tests
          command: orchestro scenarios/test.yaml --junit-xml=test-results/junit.xml
      - store_test_results:
          path: test-results

workflows:
  test:
    jobs:
      - test
```

## JUnit XML Report Structure

The generated XML report follows the standard JUnit format:

```xml
<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="My Test Scenario" tests="1" failures="0" errors="0" skipped="0" time="3.5" timestamp="2025-11-13T12:00:00" hostname="test-machine">
    <testcase classname="orchestro" name="My Test Scenario" time="3.5">
      <system-out>Scenario execution output...</system-out>
    </testcase>
  </testsuite>
</testsuites>
```

### On Failure

When a scenario fails, the XML includes detailed failure information:

```xml
<testcase classname="orchestro" name="Failed Scenario" time="2.1">
  <failure message="Expected path to exist: /tmp/output.txt" type="AssertionError">
Traceback (most recent call last):
  File "/path/to/runner.py", line 123, in _run_validations
    raise AssertionError(f"Expected path to exist: {target}")
AssertionError: Expected path to exist: /tmp/output.txt
  </failure>
  <system-out>Scenario output...</system-out>
  <system-err>Error messages...</system-err>
</testcase>
```

## Report Contents

The JUnit XML report includes:

- **Test suite name**: Scenario name from YAML file
- **Timing information**: Accurate execution duration
- **Test status**: Pass/fail status
- **Failure details**: Error messages and stack traces on failure
- **System output**: Captured stdout and stderr
- **Metadata**: Timestamp and hostname

## Advanced Usage

### Multiple Scenarios

Run multiple scenarios and combine results:

```bash
# Run multiple scenarios, each generating its own report
orchestro scenarios/test1.yaml --junit-xml=results/test1.xml
orchestro scenarios/test2.yaml --junit-xml=results/test2.xml
orchestro scenarios/test3.yaml --junit-xml=results/test3.xml

# CI systems can merge multiple JUnit XML files
```

### Nested Directories

Reports automatically create parent directories:

```bash
# Creates nested/directory/structure/junit.xml
orchestro scenario.yaml --junit-xml=nested/directory/structure/junit.xml
```

### Combining with Other Flags

JUnit XML works with all other Orchestro CLI flags:

```bash
# With verbose output
orchestro scenario.yaml --verbose --junit-xml=results.xml

# With workspace isolation
orchestro scenario.yaml --workspace=/tmp/test --junit-xml=results.xml

# Dry run (no XML generated)
orchestro scenario.yaml --dry-run
```

## Best Practices

### 1. Use Consistent Paths

Always use the same report path structure in your CI configuration:

```bash
test-results/junit.xml
```

### 2. Always Archive Results

Configure your CI system to archive results even on failure:

```yaml
# GitHub Actions
- name: Upload test results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: test-results
    path: test-results/
```

### 3. Descriptive Scenario Names

Use clear, descriptive names in your YAML scenarios:

```yaml
name: User Authentication Flow Test
```

This makes CI reports more readable.

### 4. Directory Structure

Organize reports by test category:

```
test-results/
  ├── unit/junit.xml
  ├── integration/junit.xml
  └── e2e/junit.xml
```

### 5. Fail Fast

Set appropriate timeouts to prevent hanging CI jobs:

```yaml
name: Quick Test
command: ./app
timeout: 30  # 30 seconds max
```

## Troubleshooting

### Report Not Generated

If the JUnit XML report isn't created:

1. **Check parent directory exists** - Orchestro creates it automatically, but verify permissions
2. **Verify path is writable** - Ensure the CI user has write permissions
3. **Check for exceptions** - Look for errors in CI logs

### Invalid XML

If CI systems reject the XML:

1. **Validate XML syntax**:
   ```bash
   xmllint --noout test-results/junit.xml
   ```

2. **Check for special characters** - Orchestro automatically escapes them

3. **Verify file encoding** - Should be UTF-8

### Missing Test Results

If tests don't appear in CI:

1. **Check file path** - Ensure it matches CI configuration
2. **Verify timing** - Report is generated after scenario completes
3. **Check CI configuration** - Ensure results path is correct

## Example Scenario

See [`examples/ci_cd_example.yaml`](../examples/ci_cd_example.yaml) for a complete example.

Run it with:

```bash
orchestro examples/ci_cd_example.yaml --junit-xml=test-results/junit.xml
```

## API Reference

### Command Line Flag

```
--junit-xml PATH
```

Generate JUnit XML test report at specified path.

- **Type**: Path
- **Default**: None (no report generated)
- **Example**: `--junit-xml=test-results/junit.xml`

### Python API

```python
from pathlib import Path
from orchestro_cli.runner import ScenarioRunner

runner = ScenarioRunner(
    scenario_path=Path("test.yaml"),
    junit_xml_path=Path("results.xml")
)

runner.run()  # Generates JUnit XML on completion
```

## Standards Compliance

Orchestro's JUnit XML output is compatible with:

- JUnit 4/5 XML format
- Jenkins JUnit plugin
- GitHub Actions test reporting
- GitLab CI/CD test reports
- Azure DevOps test results
- CircleCI test summary
- Allure Framework
- ReportPortal

## Related Documentation

- [CLI Reference](../README.md#command-line-interface)
- [Scenario Format](../README.md#scenario-format)
- [CI/CD Examples](../examples/)
