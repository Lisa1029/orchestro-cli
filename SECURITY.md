# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2.0 | :x:                |

## Reporting a Vulnerability

The Orchestro CLI team takes security bugs seriously. We appreciate your efforts to responsibly disclose your findings.

### How to Report a Security Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

1. **Preferred**: Open a [Security Advisory](https://github.com/jonthemediocre/orchestro-cli/security/advisories/new) on GitHub
2. **Alternative**: Email the maintainers directly (see GitHub profile for contact)

Please include the following information:

- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### What to Expect

- We will acknowledge receipt of your vulnerability report within 48 hours
- We will send you regular updates about our progress
- We will notify you when the vulnerability has been fixed
- We will publicly disclose the vulnerability after a fix is available (with credit to you, unless you prefer to remain anonymous)

### Security Update Process

1. The security report is received and assigned to a primary handler
2. The problem is confirmed and a list of all affected versions is determined
3. Code is audited to find any similar problems
4. Fixes are prepared for all still-supported releases
5. Fixes are released and security advisory is published

## Security Best Practices

When using Orchestro CLI:

### 1. Input Validation
- Always validate and sanitize test scenario files before execution
- Be cautious when running test scenarios from untrusted sources
- Use the `--dry-run` flag to preview what a scenario will do

### 2. Subprocess Security
- Orchestro CLI executes external commands as specified in test scenarios
- Ensure test scenarios only execute trusted commands
- Review scenarios before running them in CI/CD environments

### 3. File System Access
- Test scenarios can read and write files in the workspace
- Use isolated workspaces for untrusted scenarios
- Review file validation and path operations in scenarios

### 4. CI/CD Integration
- Use read-only tokens when possible
- Restrict scenario execution to trusted branches
- Review JUnit XML reports before publishing

### 5. API Security
- When using the REST/GraphQL API, use authentication
- Limit API access to trusted networks
- Use HTTPS in production environments

## Vulnerability Disclosure Policy

We follow the principle of Coordinated Vulnerability Disclosure:

1. Security researchers: Please allow us a reasonable time to fix the issue before public disclosure
2. We aim to patch critical vulnerabilities within 7 days
3. We will acknowledge security researchers in our release notes (unless they prefer anonymity)
4. We will not take legal action against researchers who:
   - Report vulnerabilities responsibly
   - Avoid privacy violations and data destruction
   - Do not exploit the vulnerability beyond the minimum necessary to prove it exists

## Security Updates

Subscribe to security updates:

- Watch this repository for security advisories
- Enable notifications for security updates
- Follow [@orchestro-cli](https://github.com/jonthemediocre/orchestro-cli) for announcements

## Bug Bounty

We currently do not offer a paid bug bounty program, but we deeply appreciate security researchers who help keep Orchestro CLI safe and will:

- Acknowledge you in our release notes and security advisories
- Provide a detailed write-up of the vulnerability (if desired)
- Send you Orchestro CLI swag (when available)

## Security Hall of Fame

We will recognize security researchers who responsibly disclose vulnerabilities:

<!-- This section will be updated as we receive security reports -->

*No vulnerabilities have been reported yet.*

---

Thank you for helping keep Orchestro CLI and its users safe!
