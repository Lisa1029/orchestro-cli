# CI/CD Pipeline Setup Documentation

This document describes the comprehensive CI/CD pipeline setup for Orchestro CLI.

## Overview

The CI/CD infrastructure provides automated testing, quality checks, security scanning, and release automation for the Orchestro CLI project.

## Pipeline Components

### 1. Main CI/CD Pipeline (`ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

**Jobs:**

#### 1.1 Lint Job
- **Platform:** Ubuntu Latest
- **Python:** 3.11
- **Checks:**
  - Black code formatting
  - MyPy type checking (non-blocking)
- **Purpose:** Ensure code quality and consistency

#### 1.2 Test Job (Matrix)
- **Platforms:** Ubuntu, macOS, Windows
- **Python Versions:** 3.8, 3.9, 3.10, 3.11
- **Matrix Strategy:**
  - Full testing on Ubuntu (all Python versions)
  - Sampled testing on macOS and Windows (3.10, 3.11 only)
  - Fail-fast disabled for comprehensive results
- **Features:**
  - pytest with coverage reporting
  - Coverage upload to Codecov (Ubuntu + Python 3.11)
  - HTML coverage reports as artifacts
  - Branch coverage enabled

#### 1.3 Build Job
- **Platform:** Ubuntu Latest
- **Python:** 3.11
- **Tasks:**
  - Package building (wheel and sdist)
  - Twine validation
  - Installation testing
  - CLI smoke test
  - Distribution artifacts upload (30-day retention)

#### 1.4 Integration Job
- **Platform:** Ubuntu Latest
- **Python:** 3.11
- **Tasks:**
  - CLI installation verification
  - Example scenario testing (if available)
  - End-to-end workflow validation

#### 1.5 Security Job
- **Platform:** Ubuntu Latest
- **Python:** 3.11
- **Tools:**
  - Safety (dependency vulnerability scanning)
- **Mode:** Non-blocking (continue-on-error)

#### 1.6 CI Success Job
- **Purpose:** Aggregate status check
- **Function:** Verifies all required jobs passed
- **Usage:** Branch protection rule target

### 2. Release Pipeline (`release.yml`)

**Triggers:**
- Git tags matching `v*.*.*` pattern
- Manual workflow dispatch with version input

**Jobs:**

#### 2.1 Release Job
- Creates GitHub release with auto-generated notes
- Extracts commits since last tag
- Attaches distribution packages
- Configured for production releases (not drafts)

#### 2.2 PyPI Publishing Job
- Publishes to PyPI using trusted publishing (OIDC)
- Requires `pypi` environment configuration
- Uses official PyPI GitHub Action
- Skips existing versions automatically

### 3. CodeQL Security Analysis (`codeql.yml`)

**Triggers:**
- Push to `main` or `develop`
- Pull requests to `main`
- Weekly schedule (Mondays at 02:00 UTC)

**Features:**
- Python static analysis
- Security vulnerability detection
- Code quality assessment
- Security-and-quality query suite

### 4. Dependabot Configuration (`dependabot.yml`)

**Automated Updates:**

#### GitHub Actions Dependencies
- Weekly updates (Mondays)
- Up to 5 concurrent PRs
- Labeled: `dependencies`, `github-actions`
- Commit prefix: `ci`

#### Python Dependencies
- Weekly updates (Mondays)
- Up to 10 concurrent PRs
- Labeled: `dependencies`, `python`
- Commit prefix: `deps`
- Grouped updates:
  - Development dependencies (pytest, black, mypy, etc.)
  - Production dependencies (pexpect, pyyaml)

## Configuration Files

### pytest.ini
```ini
[pytest]
- Test discovery configuration
- Coverage settings
- Custom markers (unit, integration, slow)
- Warning filters
```

### .coveragerc
```ini
[run]
- Source tracking
- Branch coverage enabled
- Omit patterns for test files

[report]
- Precision settings
- Coverage exclusion patterns
- Missing line reporting

[html/xml]
- Output configuration
```

## Setup Instructions

### 1. GitHub Repository Setup

1. **Enable GitHub Actions:**
   - Go to repository Settings > Actions > General
   - Allow all actions and reusable workflows

2. **Configure Branch Protection:**
   - Settings > Branches > Add rule for `main`
   - Required status checks:
     - `CI Pipeline Success`
     - `Lint and Format Check`
     - `Test - Python 3.11 on ubuntu-latest`

3. **Set Up Secrets (Optional but Recommended):**
   - `CODECOV_TOKEN`: For Codecov integration
     - Sign up at https://codecov.io
     - Add repository and copy token
     - Add to repository secrets

4. **Create PyPI Environment (For Releases):**
   - Settings > Environments > New environment: `pypi`
   - Configure trusted publishing:
     - Go to PyPI account settings
     - Add GitHub OIDC publisher
     - Organization/Username: your-org
     - Repository: orchestro-cli
     - Workflow: release.yml

### 2. Local Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests locally
pytest tests/ --cov=orchestro_cli

# Format code
black orchestro_cli/ tests/

# Type check
mypy orchestro_cli/ --ignore-missing-imports
```

### 3. Badge Integration

Add badges to README.md using the provided templates in `.github/BADGES.md`.

Update repository URLs from `vyb/orchestro-cli` to your actual repository path.

## Workflow Optimization

### Performance Features

1. **Caching:**
   - pip dependencies cached automatically
   - Cache key based on OS and requirements

2. **Matrix Strategy:**
   - Parallel execution across platforms
   - Reduced matrix for faster feedback
   - Full coverage where it matters (Ubuntu)

3. **Artifact Management:**
   - Coverage reports: 7 days retention
   - Distribution packages: 30 days retention
   - Minimal artifact size

### Cost Optimization

- Windows/macOS testing limited to recent Python versions
- Fail-fast disabled only for test matrix
- Concurrent job limits prevent runaway costs

## Monitoring and Maintenance

### Key Metrics to Monitor

1. **Build Success Rate:** Target >95%
2. **Test Coverage:** Target >80%
3. **Build Duration:** Monitor for performance regression
4. **Dependency Updates:** Review weekly Dependabot PRs

### Regular Maintenance Tasks

- **Weekly:** Review and merge Dependabot PRs
- **Monthly:** Review CI/CD metrics and logs
- **Quarterly:** Update workflow versions (actions)
- **As Needed:** Adjust matrix based on usage patterns

## Troubleshooting

### Common Issues

1. **Tests Fail on Specific Platform:**
   - Check platform-specific code paths
   - Review pexpect behavior differences
   - Add platform-specific test markers

2. **Coverage Drops Unexpectedly:**
   - Review .coveragerc omit patterns
   - Check for untested code paths
   - Verify test discovery settings

3. **Build Artifacts Missing:**
   - Verify job dependencies (`needs:`)
   - Check artifact upload/download steps
   - Review retention settings

4. **PyPI Publishing Fails:**
   - Verify OIDC configuration
   - Check package version uniqueness
   - Review twine validation output

## Security Considerations

1. **No Secret Commits:**
   - All workflows use OIDC/trusted publishing
   - No long-lived tokens required
   - Secrets only for optional integrations

2. **Code Scanning:**
   - CodeQL runs on all PRs
   - Weekly scheduled scans
   - Security advisories enabled

3. **Dependency Management:**
   - Automated security updates via Dependabot
   - Safety checks in CI pipeline
   - Grouped updates for easier review

## Contributing

See `.github/CONTRIBUTING.md` for detailed contribution guidelines including:
- Development workflow
- Code style requirements
- Testing guidelines
- PR submission process

## Support

For issues with CI/CD:
1. Check workflow logs in Actions tab
2. Review this documentation
3. Open an issue using bug report template
4. Tag with `ci-cd` label

## Version History

- **v1.0.0** (2025-11-13): Initial comprehensive CI/CD setup
  - Multi-platform testing
  - Coverage reporting
  - Security scanning
  - Automated releases
  - Dependabot integration
