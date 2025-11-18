# GitHub Configuration

This directory contains all GitHub-specific configuration for the Orchestro CLI project.

## 📁 Directory Structure

```
.github/
├── workflows/               # GitHub Actions workflows
│   ├── ci.yml              # Main CI/CD pipeline (testing, linting, coverage)
│   ├── release.yml         # Automated releases and PyPI publishing
│   ├── codeql.yml          # Security analysis with CodeQL
│   └── status-check.yml    # Quick status validation
├── ISSUE_TEMPLATE/         # Issue templates
│   ├── bug_report.yml      # Bug report form
│   └── feature_request.yml # Feature request form
├── BADGES.md               # Badge templates for README
├── CI_CD_SETUP.md          # Comprehensive CI/CD documentation
├── CONTRIBUTING.md         # Contribution guidelines
├── PULL_REQUEST_TEMPLATE.md # PR template
├── QUICKSTART_CI.md        # Quick setup guide
├── dependabot.yml          # Automated dependency updates
└── README.md               # This file
```

## 🚀 Quick Links

- **[Quick Start Guide](QUICKSTART_CI.md)** - Get CI/CD running in 5 minutes
- **[Full Documentation](CI_CD_SETUP.md)** - Comprehensive setup and configuration
- **[Contributing](CONTRIBUTING.md)** - How to contribute to the project
- **[Badges](BADGES.md)** - Add status badges to README

## 🔄 Workflows

### CI/CD Pipeline (`ci.yml`)

The main pipeline runs on every push and pull request:

- **Linting**: Black formatting, MyPy type checking
- **Testing**: Multi-platform (Ubuntu, macOS, Windows) × Multi-version (Python 3.8-3.11)
- **Coverage**: pytest with coverage reporting, Codecov integration
- **Building**: Package build and installation verification
- **Integration**: End-to-end testing with examples
- **Security**: Dependency vulnerability scanning

**Status**: [![CI/CD Pipeline](../../actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

### Release Pipeline (`release.yml`)

Automated releases triggered by version tags:

- Creates GitHub releases with auto-generated notes
- Builds distribution packages (wheel and sdist)
- Publishes to PyPI using trusted publishing
- Attaches build artifacts to releases

**Trigger**: `git tag v1.0.0 && git push origin v1.0.0`

### CodeQL Analysis (`codeql.yml`)

Security and code quality scanning:

- Static analysis for Python code
- Security vulnerability detection
- Runs on push, PR, and weekly schedule
- Results visible in Security tab

**Status**: [![CodeQL](../../actions/workflows/codeql.yml/badge.svg)](../../actions/workflows/codeql.yml)

### Status Check (`status-check.yml`)

Quick validation for rapid feedback:

- Fast smoke tests
- Critical file verification
- Installation validation
- Runs in under 5 minutes

## 🤖 Dependabot

Automated dependency management configured in `dependabot.yml`:

- **GitHub Actions**: Weekly updates on Mondays
- **Python Dependencies**: Weekly updates with grouped PRs
- **Auto-labeling**: `dependencies`, `github-actions`, `python`

## 📝 Templates

### Issue Templates

Two structured forms for better issue reporting:

1. **Bug Report** (`bug_report.yml`)
   - Detailed reproduction steps
   - Environment information
   - Scenario file attachment

2. **Feature Request** (`feature_request.yml`)
   - Problem statement
   - Proposed solution
   - Example usage
   - Priority indication

### Pull Request Template

Comprehensive PR template with:

- Change description and type
- Testing checklist
- Documentation requirements
- Code quality verification
- Breaking change documentation

## 🎯 Getting Started

### For Contributors

1. Read [CONTRIBUTING.md](CONTRIBUTING.md)
2. Set up development environment
3. Run tests locally before pushing
4. Use PR template when submitting changes

### For Maintainers

1. Follow [QUICKSTART_CI.md](QUICKSTART_CI.md) to enable workflows
2. Configure branch protection rules
3. Set up Codecov integration (optional)
4. Configure PyPI trusted publishing (for releases)

## 📊 Monitoring

### Metrics to Track

- **Build Success Rate**: Target >95%
- **Test Coverage**: Target >80%
- **Security Issues**: Address within 7 days
- **Dependency Updates**: Review weekly

### Where to Look

- **Actions Tab**: Workflow runs and logs
- **Security Tab**: CodeQL alerts and Dependabot
- **Insights Tab**: Contributor activity and metrics
- **Pull Requests**: Automated checks and reviews

## 🔧 Configuration Files

### Repository Root

- `pytest.ini`: pytest configuration with coverage settings
- `.coveragerc`: Coverage reporting configuration
- `pyproject.toml`: Package metadata and dependencies

### Workflow Variables

All workflows use:

```yaml
env:
  FORCE_COLOR: 1  # Colored output in CI logs
```

### Required Secrets (Optional)

- `CODECOV_TOKEN`: For coverage reporting (recommended)
- `GITHUB_TOKEN`: Automatically provided by GitHub

### Environments

- `pypi`: For release publishing (requires setup)

## 🛡️ Security

### Automated Security

- CodeQL scanning on all PRs
- Weekly scheduled security scans
- Dependabot security updates
- No long-lived credentials required

### Best Practices

- OIDC/Trusted publishing for PyPI
- Minimal secret usage
- Scoped GitHub tokens
- Environment protection rules

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Black Documentation](https://black.readthedocs.io/)

## 🤝 Support

Need help with CI/CD setup?

1. Check [CI_CD_SETUP.md](CI_CD_SETUP.md) for detailed docs
2. Review workflow logs in Actions tab
3. Open an issue using bug report template
4. Tag with `ci-cd` label

## 📈 Version History

- **v1.0.0** (2025-11-13): Initial comprehensive CI/CD setup
  - Multi-platform testing matrix
  - Coverage reporting and badges
  - Security scanning integration
  - Automated release pipeline
  - Community templates

---

**Maintained by**: Orchestro CLI Contributors
**Last Updated**: 2025-11-13
