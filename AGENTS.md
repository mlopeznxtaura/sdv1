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

## CLI Authentication (E: drive)
All CLIs installed globally and authenticated. Run from any drive:

```powershell
# GitHub CLI — authenticated as mlopeznxtaura
gh auth status

# IBM Cloud CLI — authenticated as mlopez@nextaura.fit, region us-south
ibmcloud account show

# Google Cloud SDK — authenticated as marco.a.lopez89@gmail.com, project nextaura-core
gcloud config list project

# Cloudflare Wrangler — authenticated via API token (CLOUDFLARE_API_TOKEN)
wrangler whoami
```

## GitHub Security Configuration
Repo: `https://github.com/mlopeznxtaura/sdv1`

| Feature | Status |
|---|---|
| **Branch protection** (main) | Enabled |
| Require PR before merging | 1 approving review required |
| Dismiss stale reviews | Enabled |
| Require CODEOWNERS review | Enabled |
| Require last push approval | Enabled |
| Require linear history | Enabled |
| Require signed commits | Enabled |
| Require conversation resolution | Enabled |
| Require status checks | `viabilityscan` (strict) |
| Enforce admins | Enabled |
| Allow force pushes | Disabled |
| Allow deletions | Disabled |
| **Secret scanning** | Enabled |
| **Secret scanning push protection** | Enabled |
| **Dependabot alerts** | Enabled |
| **Dependabot security updates** | Enabled |
| **CodeQL analysis** | Workflow `.github/workflows/codeql.yml` |
| **Dependency review** | Workflow `.github/workflows/dependency-review.yml` |
| **CODEOWNERS** | `@mlopeznxtaura` owns all files |

## Git
- `.gitignore` ignores: `.env`, `.venv/`, `__pycache__/`, `.playwright-mcp/`, `*.log`, `.coverage`
- Commit history was rewritten to a single clean root commit

## Project Notes
- Build backend in `pyproject.toml` was fixed from `setuptools.backends.legacy:build` → `setuptools.build_meta`
- `.env` file present with dashboard defaults (ignored by git)
- 2 pre-existing test failures in `tests/test_viabilityscan.py` (not environment-related)
