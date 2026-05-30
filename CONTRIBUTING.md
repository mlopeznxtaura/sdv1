# Contributing to ViabilityScan

Thank you for your interest in contributing!

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -e ".[dev,dashboard]"
   ```

## Development Workflow

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and add tests

3. Run the test suite:
   ```bash
   pytest tests/ -v
   ```

4. Run the linter:
   ```bash
   ruff check viabilityscan/
   ```

5. Run a viability scan to ensure the repo itself passes:
   ```bash
   viabilityscan scan . --output viability_report.json
   ```

6. Commit your changes (commits must be signed)
7. Push to your fork and open a Pull Request

## Pull Request Requirements

- All commits must be cryptographically signed
- All status checks must pass (tests, lint, viability scan)
- At least one approving review is required
- Stale reviews are dismissed on new pushes
- CODEOWNERS review is required for all changes

## Code of Conduct

Be respectful and constructive. We aim to maintain a welcoming environment for all contributors.
