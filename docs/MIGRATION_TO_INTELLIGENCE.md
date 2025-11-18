# Migrating to Intelligent Test Generation

**Version:** 0.3.0
**Audience:** Existing Orchestro CLI users

This guide helps you adopt Orchestro's intelligent test generation features alongside your existing manual test scenarios.

---

## Table of Contents

- [Overview](#overview)
- [When to Use Intelligence Features](#when-to-use-intelligence-features)
- [Gradual Adoption Path](#gradual-adoption-path)
- [Combining Manual and Generated Tests](#combining-manual-and-generated-tests)
- [Best Practices](#best-practices)
- [Common Pitfalls](#common-pitfalls)
- [Migration Checklist](#migration-checklist)

---

## Overview

### What's Changing?

**Nothing breaks.** Intelligence features are completely opt-in. Your existing scenarios continue to work exactly as before.

**What's new:**
- `orchestro index` - Analyze your app (NEW)
- `orchestro generate` - Generate scenarios (NEW)
- `orchestro coverage` - Analyze coverage (NEW)
- `orchestro learn` - Improve from results (NEW)

**What stays the same:**
- `orchestro <scenario>.yaml` - Run scenarios (UNCHANGED)
- All existing YAML syntax (UNCHANGED)
- Screenshot mechanisms (UNCHANGED)
- Validation system (UNCHANGED)

### Migration Philosophy

> "Enhance, don't replace. Manual expertise + automated coverage = comprehensive testing."

Intelligence features **complement** manual test writing:
- **Manual**: Critical business flows, edge cases, domain expertise
- **Generated**: Broad coverage, regression testing, repetitive scenarios

---

## When to Use Intelligence Features

### Use Generated Tests For:

✅ **Smoke testing** - Quick sanity checks
```bash
orchestro generate index.json --type smoke
# 4-5 scenarios covering basic functionality
```

✅ **Coverage expansion** - Fill testing gaps
```bash
orchestro coverage index.json tests/manual/
# Shows: "Missing: 12 screens, 18 keybindings"
orchestro generate index.json --type coverage
# Generates tests for missing areas
```

✅ **Regression testing** - Catch unintended changes
```bash
# After every commit, re-generate and compare
orchestro generate index.json --type smoke
git diff tests/generated/
```

✅ **Visual regression** - Screenshot galleries
```bash
orchestro generate index.json --type coverage --include-screenshots
# Auto-captures all screens for visual comparison
```

✅ **New features** - Bootstrap tests quickly
```bash
# Just added a new screen? Generate tests instantly
orchestro index ./app
orchestro generate index.json --type coverage
# Review and refine
```

### Keep Manual Tests For:

✋ **Business-critical flows** - Domain expertise required
```yaml
# tests/manual/checkout_flow.yaml
name: E-commerce Checkout Flow
description: |
  Critical revenue path requiring specific validation order,
  payment gateway integration, and business rule verification.
# ... complex multi-step scenario
```

✋ **Edge cases** - Boundary conditions
```yaml
# tests/manual/edge_cases.yaml
name: Edge Case - Empty Cart Checkout
description: |
  Verify graceful handling when user attempts checkout with
  empty cart, expired session, or invalid payment method.
```

✋ **Integration tests** - External dependencies
```yaml
# tests/manual/api_integration.yaml
name: Third-Party API Integration
description: |
  Test interaction with external payment API, including
  retry logic, timeout handling, and error recovery.
```

✋ **Performance tests** - Timing-sensitive scenarios
```yaml
# tests/manual/performance.yaml
name: Large Dataset Performance
description: |
  Verify app handles 10,000+ items without degradation,
  includes specific performance assertions and metrics.
```

---

## Gradual Adoption Path

### Week 1: Explore (No Commitment)

**Goal**: Understand what intelligence can do for your project.

```bash
# 1. Analyze your app (read-only, safe)
orchestro index ./my_app --framework textual

# 2. Check the index
cat .orchestro/index.json | jq '.'

# 3. Generate smoke tests (don't commit yet)
orchestro generate .orchestro/index.json --type smoke --output /tmp/generated/

# 4. Review generated scenarios
ls -lah /tmp/generated/
cat /tmp/generated/01_app_startup.yaml

# 5. Try running them
orchestro /tmp/generated/*.yaml --verbose
```

**Decision point**: Do generated tests work? Are they useful?

### Week 2: Adopt Smoke Tests

**Goal**: Use generated smoke tests in CI/CD.

```bash
# 1. Generate into your repo
orchestro generate .orchestro/index.json --type smoke --output tests/smoke/

# 2. Review and adjust
git diff tests/smoke/
# Edit if needed

# 3. Add to CI
# .github/workflows/test.yml
- name: Run smoke tests
  run: orchestro tests/smoke/*.yaml --junit-xml=results/smoke.xml

# 4. Commit
git add .orchestro/index.json tests/smoke/
git commit -m "Add auto-generated smoke tests"
```

**Benefit**: Instant smoke test coverage without manual effort.

### Week 3: Expand Coverage

**Goal**: Generate tests for gaps in manual coverage.

```bash
# 1. Analyze current coverage
orchestro coverage .orchestro/index.json tests/manual/

# Output shows:
# Screen coverage: 45% (5/11 screens tested)
# Keybinding coverage: 60% (12/20 keys tested)
# Missing screens: SettingsScreen, HelpScreen, ...

# 2. Generate tests for gaps
orchestro generate .orchestro/index.json --type coverage --output tests/coverage/

# 3. Review high-confidence tests first
grep "confidence: 0.[89]" tests/coverage/*.yaml

# 4. Add high-confidence tests to CI
git add tests/coverage/screen_*_high_confidence.yaml
```

**Benefit**: Achieve 80%+ coverage without doubling manual work.

### Week 4: Enable Learning

**Goal**: Improve generated tests based on execution results.

```bash
# 1. Run all tests with reporting
orchestro tests/**/*.yaml --junit-xml=results/all.xml

# 2. Learn from results
orchestro learn .orchestro/index.json results/all.xml --update

# Output:
# Learned: SettingsScreen loads in 0.5s (was 3s)
# Learned: Screenshot timing improved
# Updated index with 8 improvements

# 3. Re-generate with learned parameters
orchestro generate .orchestro/index.json --type coverage --output tests/coverage/

# 4. Compare improvements
git diff tests/coverage/
```

**Benefit**: Tests get smarter over time, reducing flakiness.

### Month 2+: Full Integration

**Goal**: Seamless workflow combining manual and generated tests.

```bash
# Project structure
tests/
├── manual/                  # Your handwritten tests
│   ├── critical/           # Business-critical flows
│   ├── edge_cases/         # Boundary conditions
│   └── integration/        # External dependencies
├── generated/              # Auto-generated tests
│   ├── smoke/             # Fast sanity checks
│   └── coverage/          # Comprehensive coverage
└── .orchestro/              # Intelligence files
    ├── index.json         # App knowledge base
    └── templates/         # Custom templates (optional)

# Workflow
make test-manual          # Run critical paths first
make test-smoke          # Run generated smoke tests
make test-coverage       # Run full coverage if smoke passes
make update-intelligence # Re-index, re-generate, learn
```

---

## Combining Manual and Generated Tests

### Strategy 1: Layer Testing

Use different test types for different purposes:

```bash
# tests/run_all.sh
#!/bin/bash

# Layer 1: Manual critical paths (MUST PASS)
echo "Running critical business flows..."
orchestro tests/manual/critical/*.yaml --junit-xml=results/critical.xml
if [ $? -ne 0 ]; then
    echo "CRITICAL TESTS FAILED - Stopping"
    exit 1
fi

# Layer 2: Generated smoke tests (SHOULD PASS)
echo "Running smoke tests..."
orchestro tests/generated/smoke/*.yaml --junit-xml=results/smoke.xml

# Layer 3: Full coverage (NICE TO PASS)
echo "Running coverage tests..."
orchestro tests/generated/coverage/*.yaml --junit-xml=results/coverage.xml
orchestro tests/manual/edge_cases/*.yaml --junit-xml=results/edge.xml
```

### Strategy 2: Hybrid Scenarios

Enhance generated tests with manual assertions:

```yaml
# tests/hybrid/main_screen.yaml
# Base: Generated by Orchestro
# Enhanced: Manual validations added

name: Main Screen - Enhanced
description: |
  Auto-generated test for MainScreen with additional
  business logic validations.

_orchestro_metadata:
  generated_by: orchestro_cli v0.3.0
  enhanced_by: human
  confidence: 0.95

command: python -m my_app
timeout: 30

steps:
  # Generated: Basic navigation
  - screenshot: "main-screen-startup"
    timeout: 10

  # Manual: Business-specific validation
  - send: "get_balance"
    note: "Check account balance"

  - expect: "Balance: \\$[0-9,]+\\.[0-9]{2}"
    timeout: 5
    note: "Verify balance format (manual addition)"

validations:
  # Generated validations
  - type: path_exists
    path: artifacts/screenshots/main-screen-startup.svg

  # Manual validations
  - type: file_contains
    path: balance.log
    text: "Balance retrieved successfully"
    description: "Business rule: Balance must be logged"
```

### Strategy 3: Complementary Coverage

Use `orchestro coverage` to identify manual test gaps:

```bash
# Generate coverage report
orchestro coverage .orchestro/index.json tests/manual/ --report text

# Output:
# Coverage Report
# ===============
# Overall: 65%
#
# Tested manually:
#   ✓ MainScreen (100%)
#   ✓ CheckoutFlow (100%)
#
# Gaps (auto-generate recommended):
#   ⚠ SettingsScreen (0%)    <-- Generate test
#   ⚠ HelpScreen (0%)        <-- Generate test
#   ⚠ ProfileScreen (30%)    <-- Generate test
#
# Recommendations:
#   1. Generate tests for SettingsScreen, HelpScreen
#   2. Expand ProfileScreen coverage (missing 70%)

# Generate tests for gaps only
orchestro generate .orchestro/index.json \
  --type coverage \
  --screens "SettingsScreen,HelpScreen" \
  --output tests/generated/gaps/
```

---

## Best Practices

### 1. Version Control Intelligence Files

```bash
# .gitignore - DO commit these
# .orchestro/index.json         <-- Commit
# tests/generated/             <-- Commit (or generate in CI)

# .gitignore - DON'T commit these
artifacts/screenshots/        # Test artifacts
test-results/                 # Test results
.orchestro/cache/              # Analysis cache
```

**Recommendation**: Commit `.orchestro/index.json` and generated tests for reproducibility.

### 2. Review Before Committing

```bash
# Always review generated tests before committing
orchestro generate .orchestro/index.json --type smoke --output tests/smoke/

# Review changes
git diff tests/smoke/

# Look for:
# - Correct timeouts
# - Sensible step order
# - Valid expect patterns
# - Appropriate validations

# Edit if needed, then commit
git add tests/smoke/
git commit -m "Update generated smoke tests"
```

### 3. Customize Templates

Create project-specific templates:

```bash
# .orchestro/templates/my_template.jinja2
name: {{ screen.name }} - Custom Test
description: Custom template for {{ project.name }}
command: {{ app.command }}
timeout: 60

env:
  PROJECT_MODE: test
  API_KEY: {{ env.TEST_API_KEY }}

steps:
  # Your custom step pattern
  - screenshot: "{{ screen.name|slugify }}-start"

  {% for key in screen.keybindings %}
  - send: "{{ key.key }}"
    note: "{{ project.name }}: {{ key.description }}"
  - expect: "{{ project.success_pattern }}"
    timeout: 5
  {% endfor %}
```

```bash
# Use custom template
orchestro generate .orchestro/index.json \
  --template .orchestro/templates/my_template.jinja2 \
  --output tests/custom/
```

### 4. Incremental Updates

Re-index after major changes:

```bash
# After adding new screen or feature
git commit -m "Add new DashboardScreen"

# Re-analyze
orchestro index ./my_app --framework textual

# Compare changes
git diff .orchestro/index.json

# Re-generate affected tests
orchestro generate .orchestro/index.json --type coverage
```

### 5. Quality Filtering

Filter by confidence score:

```bash
# Only commit high-confidence tests
orchestro generate .orchestro/index.json \
  --type coverage \
  --quality-threshold 0.8 \
  --output tests/generated/

# Low-confidence tests to separate directory for review
orchestro generate .orchestro/index.json \
  --type coverage \
  --quality-threshold 0.5 \
  --max-quality 0.8 \
  --output tests/review/
```

---

## Common Pitfalls

### Pitfall 1: Over-reliance on Generated Tests

❌ **Wrong**:
```bash
# Delete all manual tests, use only generated
rm -rf tests/manual/
orchestro generate index.json --type coverage
```

✅ **Right**:
```bash
# Keep critical manual tests, supplement with generated
tests/
├── manual/critical/        # Keep these
├── manual/edge_cases/      # Keep these
└── generated/coverage/     # Add these
```

### Pitfall 2: Ignoring Low Confidence

❌ **Wrong**:
```bash
# Commit all generated tests without review
orchestro generate index.json --type coverage
git add tests/generated/
git commit -m "Add tests"  # Some may be flaky!
```

✅ **Right**:
```bash
# Review low-confidence tests
orchestro generate index.json --type coverage
grep -r "confidence: 0.[0-5]" tests/generated/
# Review and fix before committing
```

### Pitfall 3: Stale Index

❌ **Wrong**:
```bash
# Index created 6 months ago, app changed significantly
orchestro generate old-index.json --type coverage
# Tests don't match current app!
```

✅ **Right**:
```bash
# Re-index regularly
orchestro index ./my_app --framework textual
orchestro generate .orchestro/index.json --type coverage
```

### Pitfall 4: Forgetting to Learn

❌ **Wrong**:
```bash
# Run tests, see timeouts, manually increase timeouts
# Repeat every release...
```

✅ **Right**:
```bash
# Let Orchestro learn optimal timeouts
orchestro tests/*.yaml --junit-xml=results.xml
orchestro learn .orchestro/index.json results.xml --update
orchestro generate .orchestro/index.json --type coverage
# Timeouts auto-optimized
```

### Pitfall 5: Not Customizing Templates

❌ **Wrong**:
```bash
# Use default templates even though your app has unique patterns
orchestro generate index.json --type coverage
# Generated tests miss project-specific conventions
```

✅ **Right**:
```bash
# Create custom template matching your patterns
cat > .orchestro/templates/custom.jinja2 << 'EOF'
# Your project-specific template
EOF

orchestro generate index.json \
  --template .orchestro/templates/custom.jinja2
```

---

## Migration Checklist

### Phase 1: Exploration (Week 1)
- [ ] Install Orchestro CLI 0.3.0+
- [ ] Run `orchestro index` on your app
- [ ] Review `.orchestro/index.json`
- [ ] Generate smoke tests to `/tmp` (don't commit)
- [ ] Run generated tests
- [ ] Evaluate if intelligence fits your project

### Phase 2: Adoption (Week 2-3)
- [ ] Generate smoke tests to repo
- [ ] Review and refine generated scenarios
- [ ] Add smoke tests to CI/CD
- [ ] Run `orchestro coverage` on manual tests
- [ ] Generate coverage tests for gaps
- [ ] Commit `.orchestro/index.json` and generated tests

### Phase 3: Integration (Week 4+)
- [ ] Enable learning from test results
- [ ] Create custom templates (if needed)
- [ ] Establish re-indexing workflow
- [ ] Document team workflow
- [ ] Train team on intelligence features
- [ ] Monitor and optimize

### Phase 4: Optimization (Month 2+)
- [ ] Review confidence scores regularly
- [ ] Refine quality thresholds
- [ ] Customize templates based on learnings
- [ ] Automate re-indexing in CI/CD
- [ ] Share patterns with community

---

## Example: Before and After

### Before Intelligence

```bash
# Manual effort required for every screen
# tests/manual/main_screen.yaml
name: Test Main Screen
command: python -m my_app
steps:
  - screenshot: "main-screen"
  - send: "a"  # Add task
  - screenshot: "task-added"
  # ... manually written

# tests/manual/settings_screen.yaml
name: Test Settings Screen
# ... manually written (30 minutes)

# tests/manual/help_screen.yaml
# ... manually written (30 minutes)

# Total: 90+ minutes for 3 screens
```

### After Intelligence

```bash
# One-time index (2 seconds)
orchestro index ./my_app --framework textual

# Generate all tests (1 second)
orchestro generate .orchestro/index.json --type coverage --output tests/generated/

# Generated:
# - tests/generated/main_screen.yaml
# - tests/generated/settings_screen.yaml
# - tests/generated/help_screen.yaml
# - tests/generated/profile_screen.yaml
# - tests/generated/dashboard_screen.yaml
# ... (all 11 screens)

# Total: 3 seconds for 11 screens
# Coverage: 85% vs 27% before
# Time saved: 270+ minutes
```

---

## Getting Help

### Resources

- [Intelligence Guide](INTELLIGENCE.md) - Complete documentation
- [Tutorial](tutorials/INTELLIGENT_TESTING.md) - Hands-on walkthrough
- [FAQ](FAQ_INTELLIGENCE.md) - Common questions
- [Examples](../examples/intelligence/) - Real-world usage

### Community

- [GitHub Issues](https://github.com/vyb/orchestro-cli/issues) - Bug reports
- [Discussions](https://github.com/vyb/orchestro-cli/discussions) - Questions
- [Discord](https://discord.gg/orchestro-cli) - Live chat

---

## Summary

Intelligence features **enhance**, not replace, manual testing:

**Manual** → Critical paths, edge cases, domain expertise
**Generated** → Broad coverage, regression testing, repetitive scenarios
**Combined** → Comprehensive testing with minimal effort

Start small, adopt gradually, and customize to your needs.

**Next Steps**:
1. Read the [Intelligence Guide](INTELLIGENCE.md)
2. Try the [Tutorial](tutorials/INTELLIGENT_TESTING.md)
3. Experiment in a test project
4. Adopt in production

---

**Version:** 0.3.0
**Last Updated:** 2025-11-17
