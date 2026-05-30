# Security Policy

## Supported Versions

| Version | Supported          |
|---------|-------------------|
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Do not open a public issue.** Instead, contact the maintainer directly:

- Email: security@nextaura.fit

We aim to respond within 48 hours and will keep you updated on the status of the fix.

## Disclosure Policy

We follow a coordinated disclosure model:

1. Report received → Acknowledged within 48 hours
2. Vulnerability assessed and validated
3. Fix developed and tested
4. Patch released and vulnerability disclosed publicly (with credit to reporter if desired)

## Security Features

This repository is configured with:

- **Secret scanning** — GitHub scans for leaked credentials on every push
- **Push protection** — Commits containing secrets are blocked before they enter history
- **Dependabot alerts** — Automated notifications for vulnerable dependencies
- **CodeQL analysis** — Static analysis for security vulnerabilities in Python code
- **Dependency review** — PR-level checks for newly introduced vulnerabilities
- **Signed commits required** — All commits to `main` must be cryptographically signed
