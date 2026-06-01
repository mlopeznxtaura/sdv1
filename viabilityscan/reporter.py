"""
Reporter — formats ViabilityScan results for terminal and JSON output.
Vault Standard edition — ASCII-safe for all terminals.
"""

import json
import sys
from pathlib import Path
from datetime import datetime


SEVERITY_ICONS = {
    "CRITICAL": "[!]",
    "HIGH":     "[X]",
    "MEDIUM":   "[~]",
    "LOW":      "[-]",
    "INFO":     "[i]",
}

SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]


def _safe_print(s: str):
    """Print safely on Windows terminals that lack Unicode support."""
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode('ascii', 'replace').decode('ascii'))


class Reporter:
    def __init__(self, result: dict):
        self.r = result

    def print_summary(self):
        r = self.r
        scores = r["scores"]
        gate = r["gate"]
        gate_icon = "PASS" if gate == "PASS" else "FAIL"

        _safe_print(f"\n{'='*60}")
        _safe_print(f"  PHASE GATE:  {gate_icon}")
        _safe_print(f"{'='*60}")
        _safe_print(f"  Viability Score : {scores['viability']:>6.1f}  (threshold >=75)")
        _safe_print(f"  Security        : {scores['security']:>6.1f}  (threshold >=70)")
        _safe_print(f"  Deployment      : {scores['deployment']:>6.1f}  (threshold >=60)")
        _safe_print(f"  Reliability     : {scores['reliability']:>6.1f}  (threshold >=60)")
        _safe_print(f"{'='*60}")

        if r["gate_reasons"]:
            _safe_print("\n  Gate failures:")
            for reason in r["gate_reasons"]:
                _safe_print(f"     - {reason}")

        _safe_print(f"\n  Repository : {r['repo_name']}")
        _safe_print(f"  Scanned at : {r['scanned_at'][:19].replace('T', ' ')} UTC")
        _safe_print(f"  Elapsed    : {r['elapsed_seconds']}s")
        _safe_print(f"  Mode       : {r['mode'].upper()}")

        # Findings summary per layer
        _safe_print(f"\n{'='*60}")
        _safe_print("  FINDINGS SUMMARY")
        _safe_print(f"{'='*60}")
        for layer_name, layer_data in r.get("layers", {}).items():
            counts = layer_data.get("severity_counts", {})
            total = layer_data.get("finding_count", 0)
            if total == 0:
                _safe_print(f"  {layer_name:<22}  OK  No findings")
                continue
            parts = []
            for sev in SEVERITY_ORDER:
                n = counts.get(sev, 0)
                if n:
                    parts.append(f"{SEVERITY_ICONS[sev]} {sev}:{n}")
            _safe_print(f"  {layer_name:<22}  {' '.join(parts)}")

        # Top findings
        all_findings = []
        for layer_data in r.get("layers", {}).values():
            all_findings.extend(layer_data.get("findings", []))

        critical_high = [f for f in all_findings if f.get("severity") in ("CRITICAL", "HIGH")]
        if critical_high:
            _safe_print(f"\n{'='*60}")
            _safe_print("  TOP FINDINGS (CRITICAL / HIGH)")
            _safe_print(f"{'='*60}")
            for f in critical_high[:10]:
                icon = SEVERITY_ICONS.get(f.get("severity", "INFO"), "[i]")
                loc = f.get("file", "?")
                if f.get("line"):
                    loc += f":{f['line']}"
                _safe_print(f"  {icon} {f['title']}")
                _safe_print(f"       File: {loc}")
                _safe_print(f"       Fix:  {f.get('remediation','')[:100]}")
                _safe_print("")

        # Next frame prediction
        _safe_print(f"{'='*60}")
        _safe_print(f"  NEXT: {r.get('next_frame_prediction', '')}")
        _safe_print(f"{'='*60}\n")

    def save_json(self, output_path: str):
        path = Path(output_path)
        path.write_text(json.dumps(self.r, indent=2, default=str))
        _safe_print(f"  Full report saved: {path.resolve()}")
