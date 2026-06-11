"""
Supply Chain Layer — DepGuard integration (ported from sdv1integration1).

npm/yarn/pnpm supply-chain hardening checks:
  1. Lockfile presence       — missing lockfile = non-reproducible installs
  2. Exotic refs             — git:/github:/file:/http refs bypass registry integrity
  3. Lifecycle scripts       — preinstall/postinstall etc. run arbitrary code at install
  4. packageManager pin      — unpinned tooling = inconsistent resolution
  5. Min release age         — versions published <72h ago are a known attack window
  6. Deprecated patterns     — strict-ssl=false, rogue registries, wildcard versions
"""

import json
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from viabilityscan.layers.base import BaseLayer

LOCKFILE_NAMES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml"}
DANGEROUS_SCRIPTS = ("preinstall", "install", "postinstall", "prepack", "prepare")
EXOTIC_REF_RE = re.compile(r"(git\+|git://|github:|file:|link:|https?://(?!registry\.npmjs\.org|registry\.yarnpkg\.com))")
MIN_AGE_HOURS = 72
MAX_REGISTRY_LOOKUPS = 50
REVIEW_PACKAGES = ("node-pre-gyp", "request", "lodash")
SKIP_DIRS = {".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build"}


class SupplyChainLayer(BaseLayer):
    name = "supply_chain"
    description = "npm/yarn/pnpm supply-chain hardening (DepGuard checks)"

    def run(self) -> dict:
        findings = []
        remediations = []

        package_jsons = self._collect("package.json")
        if not package_jsons:
            return {
                "layer": self.name,
                "score": 100,
                "findings": [],
                "finding_count": 0,
                "severity_counts": self._count_severities([]),
                "remediations": ["No package.json found — supply-chain checks not applicable."],
                "checks_run": [],
                "skipped": True,
            }

        lockfiles = []
        for name in LOCKFILE_NAMES:
            lockfiles.extend(self._collect(name))
        npmrcs = self._collect(".npmrc")

        penalty = 0
        penalty += self._check_lockfile_presence(package_jsons, lockfiles, findings)
        penalty += self._check_exotic_refs(package_jsons, lockfiles, findings)
        penalty += self._check_lifecycle_scripts(package_jsons, findings)
        penalty += self._check_package_manager_pin(package_jsons, findings)
        penalty += self._check_min_release_age(package_jsons, findings)
        penalty += self._check_deprecated_patterns(package_jsons, npmrcs, findings)

        score = max(0, 100 - min(100, penalty))

        for f in [x for x in findings if x.get("severity") in ("CRITICAL", "HIGH")][:5]:
            remediations.append(f"Fix {f['severity']}: {f['title']} ({f.get('file', '?')})")
        if not remediations:
            remediations.append("Supply chain looks clean. Keep lockfiles committed and versions pinned.")

        return {
            "layer": self.name,
            "score": score,
            "findings": findings,
            "finding_count": len(findings),
            "severity_counts": self._count_severities(findings),
            "remediations": remediations,
            "checks_run": [
                "lockfile_presence", "exotic_refs", "lifecycle_scripts",
                "package_manager_pin", "min_release_age", "deprecated_patterns",
            ],
            "sources": [
                "https://docs.npmjs.com/cli/v10/configuring-npm/package-lock-json",
                "https://github.blog/security/supply-chain-security/",
            ],
        }

    # ── helpers ──────────────────────────────────────────────────────────

    def _collect(self, basename: str) -> list[Path]:
        out = []
        for p in self.repo.rglob(basename):
            if p.is_file() and not any(d in p.parts for d in SKIP_DIRS):
                out.append(p)
        return out

    def _rel(self, p: Path) -> str:
        try:
            return str(p.relative_to(self.repo))
        except ValueError:
            return str(p)

    @staticmethod
    def _load_json(p: Path):
        try:
            return json.loads(p.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            return None

    def _finding(self, findings, severity, title, file="", message=""):
        findings.append({
            "severity": severity,
            "title": title,
            "rule": "supply_chain",
            "file": file,
            "message": message or title,
        })

    # ── 1. lockfile presence ─────────────────────────────────────────────

    def _check_lockfile_presence(self, pkgs, lockfiles, findings) -> int:
        if lockfiles:
            return 0
        self._finding(
            findings, "CRITICAL",
            "No lockfile found — installs are non-reproducible",
            self._rel(pkgs[0]),
            "Add package-lock.json (npm), yarn.lock, or pnpm-lock.yaml and commit it.",
        )
        return 30

    # ── 2. exotic refs ───────────────────────────────────────────────────

    def _check_exotic_refs(self, pkgs, lockfiles, findings) -> int:
        hits = 0
        for p in pkgs:
            data = self._load_json(p)
            if not data:
                continue
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            for name, ref in deps.items():
                if isinstance(ref, str) and EXOTIC_REF_RE.match(ref):
                    hits += 1
                    self._finding(
                        findings, "HIGH",
                        f"Exotic dependency ref: {name} → {ref}",
                        self._rel(p),
                        "Non-registry sources bypass integrity verification. Pin an npm registry version.",
                    )
        for lf in lockfiles:
            try:
                text = lf.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for m in set(re.findall(r'"resolved":\s*"(git\+[^"]+|file:[^"]+)"', text))                :
                hits += 1
                self._finding(
                    findings, "HIGH",
                    f"Exotic resolved source in lockfile: {m[:120]}",
                    self._rel(lf),
                )
        return min(40, hits * 15)

    # ── 3. lifecycle scripts ─────────────────────────────────────────────

    def _check_lifecycle_scripts(self, pkgs, findings) -> int:
        hits = 0
        for p in pkgs:
            data = self._load_json(p)
            if not data:
                continue
            for script in DANGEROUS_SCRIPTS:
                cmd = (data.get("scripts") or {}).get(script)
                if cmd:
                    hits += 1
                    self._finding(
                        findings, "MEDIUM",
                        f"Lifecycle script '{script}' runs at install time",
                        self._rel(p),
                        f"`{script}: {str(cmd)[:120]}` — review that it is intentional, not injected.",
                    )
        return min(20, hits * 5)

    # ── 4. packageManager pin ────────────────────────────────────────────

    def _check_package_manager_pin(self, pkgs, findings) -> int:
        hits = 0
        for p in pkgs:
            data = self._load_json(p)
            if not data:
                continue
            pm = data.get("packageManager")
            if not pm:
                hits += 1
                self._finding(
                    findings, "LOW",
                    "Missing packageManager field",
                    self._rel(p),
                    'Add `"packageManager": "npm@10.x.x"` for reproducible installs via Corepack.',
                )
            elif not re.match(r"^(npm|yarn|pnpm|bun)@\d+\.\d+\.\d+", pm):
                hits += 1
                self._finding(
                    findings, "LOW",
                    f"packageManager '{pm}' is not pinned to a precise version",
                    self._rel(p),
                )
        return min(5, hits * 2)

    # ── 5. min release age ───────────────────────────────────────────────

    def _check_min_release_age(self, pkgs, findings) -> int:
        pinned = {}
        for p in pkgs:
            data = self._load_json(p)
            if not data:
                continue
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            for name, ver in deps.items():
                if isinstance(ver, str) and re.match(r"^\d+\.\d+\.\d+$", ver):
                    pinned[(name, ver)] = self._rel(p)

        if not pinned:
            return 0

        now = datetime.now(timezone.utc)
        too_new = []

        def probe(item):
            (name, ver), src = item
            url = f"https://registry.npmjs.org/{urllib.parse.quote(name, safe='')}/{ver}"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "sdv1-depguard/1.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read())
                created = (data.get("time") or {}).get("created")
                if created:
                    age_h = (now - datetime.fromisoformat(created.replace("Z", "+00:00"))).total_seconds() / 3600
                    if age_h < MIN_AGE_HOURS:
                        return (name, ver, round(age_h), src)
            except Exception:
                pass
            return None

        items = list(pinned.items())[:MAX_REGISTRY_LOOKUPS]
        with ThreadPoolExecutor(max_workers=10) as ex:
            for r in ex.map(probe, items):
                if r:
                    too_new.append(r)

        for name, ver, age_h, src in too_new:
            self._finding(
                findings, "HIGH",
                f"{name}@{ver} published only {age_h}h ago (<{MIN_AGE_HOURS}h supply-chain window)",
                src,
                "Very fresh versions are a common attack vector. Wait 72h+ or pin a known-good version.",
            )
        return min(40, len(too_new) * 20)

    # ── 6. deprecated patterns ───────────────────────────────────────────

    def _check_deprecated_patterns(self, pkgs, npmrcs, findings) -> int:
        penalty = 0
        for p in npmrcs:
            try:
                raw = dict(
                    line.split("=", 1)
                    for line in p.read_text(encoding="utf-8", errors="replace").splitlines()
                    if "=" in line and not line.strip().startswith("#")
                )
                raw = {k.strip(): v.strip() for k, v in raw.items()}
            except Exception:
                continue
            if raw.get("strict-ssl") == "false":
                penalty += 30
                self._finding(findings, "CRITICAL", "strict-ssl=false disables TLS verification", self._rel(p))
            reg = raw.get("registry", "")
            if reg and "registry.npmjs.org" not in reg and "registry.yarnpkg.com" not in reg:
                penalty += 10
                self._finding(findings, "MEDIUM", f"Non-standard global npm registry: {reg}", self._rel(p))

        for p in pkgs:
            data = self._load_json(p)
            if not data:
                continue
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            for name, ver in deps.items():
                if ver in ("*", "latest", "x"):
                    penalty += 15
                    self._finding(
                        findings, "HIGH",
                        f"{name} uses wildcard version '{ver}' — resolves unpredictably",
                        self._rel(p),
                    )
            for pkg in REVIEW_PACKAGES:
                if pkg in deps:
                    self._finding(
                        findings, "INFO",
                        f"Dependency '{pkg}' has supply-chain/vuln history — review",
                        self._rel(p),
                    )
        return min(45, penalty)
