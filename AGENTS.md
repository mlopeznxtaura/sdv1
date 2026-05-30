# Agent Environment Notes — sdv1 (E: drive)

## Python Environment
- **Python**: 3.13.7 (system)
- **Venv**: `.venv/` inside repo root
- **Activate**: `.venv\Scripts\Activate.ps1` (PowerShell) or `.venv\Scripts\activate.bat` (CMD)

## Key Commands (run from repo root)
```powershell
# Run tests
.venv\Scripts\python -m pytest tests/ -v

# Run with coverage
.venv\Scripts\python -m pytest tests/ --cov=viabilityscan --cov-report=term-missing

# Lint
.venv\Scripts\python -m ruff check viabilityscan/

# Scan current repo
.venv\Scripts\viabilityscan scan . --output viability_report.json

# Start dashboard
.venv\Scripts\python dashboard/app.py   # → http://localhost:8765
```

## Shell Access (MCP)
- **windows-mcp** → `PowerShell` works directly on any drive (including E:)
- **super-shell** → `cmd.exe` was whitelisted as `safe` to route built-in commands
  - Example: `cmd.exe` with args `[/c, dir E:\...]` executes any CMD builtin
- **chrome-browser** MCP works globally regardless of drive

## Project Notes
- Build backend in `pyproject.toml` was fixed from `setuptools.backends.legacy:build` → `setuptools.build_meta`
- `.env` file present with dashboard defaults
- 2 pre-existing test failures in `tests/test_viabilityscan.py` (not environment-related)
