# GitHub Badges for README

Add these badges to the top of your README.md file for a professional, informative header:

## Status Badges

```markdown
[![CI/CD Pipeline](https://github.com/vyb/orchestro-cli/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/vyb/orchestro-cli/actions/workflows/ci.yml)
[![CodeQL](https://github.com/vyb/orchestro-cli/workflows/CodeQL%20Security%20Analysis/badge.svg)](https://github.com/vyb/orchestro-cli/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/gh/vyb/orchestro-cli/branch/main/graph/badge.svg)](https://codecov.io/gh/vyb/orchestro-cli)
[![Python Version](https://img.shields.io/pypi/pyversions/orchestro-cli.svg)](https://pypi.org/project/orchestro-cli/)
[![PyPI version](https://badge.fury.io/py/orchestro-cli.svg)](https://badge.fury.io/py/orchestro-cli)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
```

## Suggested README Header

Replace the current header in README.md with this enhanced version:

```markdown
# Orchestro CLI 🎭

[![CI/CD Pipeline](https://github.com/vyb/orchestro-cli/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/vyb/orchestro-cli/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/vyb/orchestro-cli/branch/main/graph/badge.svg)](https://codecov.io/gh/vyb/orchestro-cli)
[![Python Version](https://img.shields.io/pypi/pyversions/orchestro-cli.svg)](https://pypi.org/project/orchestro-cli/)
[![PyPI version](https://badge.fury.io/py/orchestro-cli.svg)](https://badge.fury.io/py/orchestro-cli)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Automated CLI testing framework with screenshot support for TUI applications**

Orchestro CLI is a powerful, scenario-driven testing framework that automates interactive command-line applications, with special support for Terminal User Interface (TUI) apps built with frameworks like Textual, Rich, and curses.
```

## Notes

- Update the repository URLs from `vyb/orchestro-cli` to match your actual GitHub username/organization
- After first successful CI run, all badges will become active
- Codecov badge requires signing up at https://codecov.io and adding the repository
- PyPI badges will work once the package is published to PyPI
