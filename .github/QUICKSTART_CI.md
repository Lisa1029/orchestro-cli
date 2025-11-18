# CI/CD Quick Start Guide

Get your Orchestro CLI CI/CD pipeline running in 5 minutes.

## Step 1: Push to GitHub (1 minute)

```bash
cd /home/jonbrookings/vibe_coding_projects/my-orchestro-copy

# Initialize git if needed
git init

# Add all files
git add .
git commit -m "feat: add comprehensive CI/CD pipeline

- Multi-platform testing (Ubuntu, macOS, Windows)
- Python 3.8-3.11 support
- Coverage reporting with Codecov integration
- Security scanning with CodeQL
- Automated releases
- Dependabot for dependency updates"

# Add remote and push
git remote add origin https://github.com/YOUR_USERNAME/orchestro-cli.git
git branch -M main
git push -u origin main
```

## Step 2: Enable GitHub Actions (30 seconds)

1. Go to your repository on GitHub
2. Click "Actions" tab
3. Click "I understand my workflows, go ahead and enable them"

The CI pipeline will automatically start running!

## Step 3: Watch Your First Build (2 minutes)

Navigate to the Actions tab to see:

- ✓ Lint and Format Check
- ✓ Test - Python 3.8-3.11 on Ubuntu/macOS/Windows
- ✓ Build and Install Package
- ✓ Integration Tests
- ✓ Security Scan
- ✓ CodeQL Analysis

## Step 4: Add Badges to README (1 minute)

Copy from `.github/BADGES.md` and paste at the top of your README.md:

```markdown
[![CI/CD Pipeline](https://github.com/YOUR_USERNAME/orchestro-cli/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/YOUR_USERNAME/orchestro-cli/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/pypi/pyversions/orchestro-cli.svg)](https://pypi.org/project/orchestro-cli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
```

Replace `YOUR_USERNAME` with your GitHub username.

## Step 5: Optional Setup (5 minutes)

### Add Codecov for Coverage Reporting

1. Go to https://codecov.io
2. Sign in with GitHub
3. Add your repository
4. Copy the token
5. In GitHub: Settings > Secrets and variables > Actions > New repository secret
6. Name: `CODECOV_TOKEN`, Value: (paste token)

### Set Up Branch Protection

1. Settings > Branches > Add rule
2. Branch name pattern: `main`
3. Enable:
   - ✓ Require status checks before merging
   - ✓ Require branches to be up to date
   - Select: `CI Pipeline Success`

### Configure PyPI Publishing (for releases)

1. Create PyPI account: https://pypi.org
2. Go to Account Settings > Publishing
3. Add GitHub publisher:
   - Owner: YOUR_USERNAME
   - Repository: orchestro-cli
   - Workflow: release.yml
4. In GitHub: Settings > Environments > New environment
   - Name: `pypi`

## What You Get

### Automated Testing

Every push and PR runs:
- ✓ 12 test jobs (3 OS × 4 Python versions)
- ✓ Code formatting check (black)
- ✓ Type checking (mypy)
- ✓ Coverage reporting
- ✓ Package build verification
- ✓ Security scanning

### Automated Maintenance

- ✓ Weekly dependency updates via Dependabot
- ✓ Security vulnerability scanning
- ✓ Code quality analysis

### Automated Releases

Tag a release and it automatically:
1. Creates GitHub release
2. Builds distribution packages
3. Publishes to PyPI
4. Generates release notes

```bash
# Create a release
git tag v1.0.0
git push origin v1.0.0
```

## Testing Locally

Before pushing, test locally:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ --cov=orchestro_cli

# Check formatting
black --check orchestro_cli/ tests/

# Type check
mypy orchestro_cli/ --ignore-missing-imports

# Build package
python -m build
```

## Workflow Files

| File | Purpose | Triggers |
|------|---------|----------|
| `ci.yml` | Main testing pipeline | Push, PR |
| `release.yml` | Package publishing | Tags |
| `codeql.yml` | Security analysis | Push, PR, Weekly |
| `status-check.yml` | Quick validation | Push, PR |

## Next Steps

1. **Review workflow results** in the Actions tab
2. **Add badges** to your README
3. **Set up branch protection** to enforce CI checks
4. **Configure Codecov** for coverage tracking
5. **Read** `.github/CONTRIBUTING.md` for contribution guidelines
6. **Share** with your contributors!

## Getting Help

- **Documentation**: See `.github/CI_CD_SETUP.md`
- **Issues**: Use issue templates in `.github/ISSUE_TEMPLATE/`
- **PRs**: Use template in `.github/PULL_REQUEST_TEMPLATE.md`

## Troubleshooting

### CI Failing?

1. Check the Actions tab for error messages
2. Review failed job logs
3. Test locally with same Python version
4. Check if dependencies need updating

### Badge Not Showing?

1. Wait for first successful workflow run
2. Verify repository URL in badge markdown
3. Check workflow name matches exactly

### Tests Pass Locally But Fail in CI?

1. Check for environment-specific code
2. Verify all dependencies in pyproject.toml
3. Review platform-specific behavior (especially pexpect)

## Success!

Your Orchestro CLI project now has:

- ✅ Professional CI/CD pipeline
- ✅ Multi-platform testing
- ✅ Automated quality checks
- ✅ Security scanning
- ✅ Release automation
- ✅ Community-ready templates

Contributors and users can now have confidence in the quality and reliability of your testing framework!

---

**Pro Tip:** Star or watch your repository to get notifications when workflows complete. You'll see a green checkmark on commits when all tests pass!
