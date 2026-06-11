"""
Live website security & deployment audit.

Checks transport security, response headers, cookie flags, and information
leakage on a live site, then maps the results into the same score/gate/report
shape the ViabilityScan repo engine produces so one dashboard renders both.
"""

import ssl
import time
import socket
import urllib.request
import urllib.parse
from datetime import datetime, timezone

TIMEOUT = 15
UA = "sdv1-scanner/1.0 (+https://app4.nextaura.fit)"


def _fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
        body = resp.read(262144)  # first 256KB is plenty
        return resp.status, dict(resp.headers), body, resp.geturl()


def _tls_info(host, port=443):
    ctx = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=TIMEOUT) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as tls:
            cert = tls.getpeercert()
            not_after = cert.get("notAfter")
            expires = None
            if not_after:
                expires = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
            return {
                "version": tls.version(),
                "cipher": tls.cipher()[0] if tls.cipher() else None,
                "cert_expires": expires.isoformat() if expires else None,
                "days_to_expiry": (expires - datetime.utcnow()).days if expires else None,
            }


def scan_website(url):
    t0 = time.time()
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname or url

    sec_findings, dep_findings, rel_findings = [], [], []

    def f(sev, message, location=""):
        return {"severity": sev, "message": message, "file": location}

    # ── Transport ─────────────────────────────────────────────────────────
    if parsed.scheme != "https":
        sec_findings.append(f("CRITICAL", "Site is served over plain HTTP — no TLS"))
        tls = None
    else:
        try:
            tls = _tls_info(host)
            if tls["version"] in ("TLSv1", "TLSv1.1"):
                sec_findings.append(f("HIGH", f"Obsolete TLS version negotiated: {tls['version']}"))
            if tls["days_to_expiry"] is not None:
                if tls["days_to_expiry"] < 0:
                    sec_findings.append(f("CRITICAL", "TLS certificate is EXPIRED"))
                elif tls["days_to_expiry"] < 14:
                    rel_findings.append(f("HIGH", f"TLS certificate expires in {tls['days_to_expiry']} days"))
        except Exception as e:
            sec_findings.append(f("HIGH", f"TLS inspection failed: {e}"))
            tls = None

    # ── Fetch ─────────────────────────────────────────────────────────────
    try:
        status, headers, body, final_url = _fetch(url)
    except Exception as e:
        raise RuntimeError(f"Could not fetch {url}: {e}")

    hl = {k.lower(): v for k, v in headers.items()}

    # HTTP→HTTPS redirect check
    if parsed.scheme == "https" and final_url.startswith("http://"):
        sec_findings.append(f("HIGH", "HTTPS request was redirected back to plain HTTP"))

    # ── Security headers ─────────────────────────────────────────────────
    header_checks = [
        ("strict-transport-security", "HIGH",   "Missing Strict-Transport-Security (HSTS) header"),
        ("content-security-policy",   "HIGH",   "Missing Content-Security-Policy header"),
        ("x-content-type-options",    "MEDIUM", "Missing X-Content-Type-Options: nosniff"),
        ("x-frame-options",           "MEDIUM", "Missing X-Frame-Options (clickjacking protection) — acceptable if CSP frame-ancestors is set"),
        ("referrer-policy",           "LOW",    "Missing Referrer-Policy header"),
        ("permissions-policy",        "LOW",    "Missing Permissions-Policy header"),
    ]
    for header, sev, msg in header_checks:
        if header not in hl:
            if header == "x-frame-options" and "content-security-policy" in hl \
                    and "frame-ancestors" in hl["content-security-policy"]:
                continue
            sec_findings.append(f(sev, msg))

    if "content-security-policy" in hl:
        csp = hl["content-security-policy"]
        if "unsafe-inline" in csp:
            sec_findings.append(f("MEDIUM", "CSP allows 'unsafe-inline'"))
        if "unsafe-eval" in csp:
            sec_findings.append(f("MEDIUM", "CSP allows 'unsafe-eval'"))

    # ── Information leakage ──────────────────────────────────────────────
    for leak in ("server", "x-powered-by", "x-aspnet-version"):
        if leak in hl and len(hl[leak]) > 0 and hl[leak].lower() not in ("cloudflare",):
            dep_findings.append(f("LOW", f"Header leaks stack info: {leak}: {hl[leak]}"))

    # ── Cookies ──────────────────────────────────────────────────────────
    cookies = headers.get("Set-Cookie", "")
    if cookies:
        cl = cookies.lower()
        if "secure" not in cl:
            sec_findings.append(f("MEDIUM", "Set-Cookie without Secure flag"))
        if "httponly" not in cl:
            sec_findings.append(f("MEDIUM", "Set-Cookie without HttpOnly flag"))
        if "samesite" not in cl:
            sec_findings.append(f("LOW", "Set-Cookie without SameSite attribute"))

    # ── Mixed content (basic) ────────────────────────────────────────────
    if parsed.scheme == "https" and body:
        text = body.decode("utf-8", errors="ignore")
        if 'src="http://' in text or "src='http://" in text:
            sec_findings.append(f("MEDIUM", "Mixed content: page loads sub-resources over plain HTTP"))

    # ── Availability/deploy signals ──────────────────────────────────────
    if status >= 500:
        rel_findings.append(f("CRITICAL", f"Server error on fetch: HTTP {status}"))
    elif status >= 400:
        rel_findings.append(f("MEDIUM", f"Non-success response: HTTP {status}"))
    if "cache-control" not in hl:
        dep_findings.append(f("INFO", "No Cache-Control header on main document"))
    if "content-encoding" not in hl:
        dep_findings.append(f("INFO", "Response not compressed (no Content-Encoding)"))

    # ── Scoring (same shape as repo engine) ──────────────────────────────
    PENALTY = {"CRITICAL": 30, "HIGH": 15, "MEDIUM": 7, "LOW": 3, "INFO": 0}

    def layer_score(findings):
        return max(0, 100 - sum(PENALTY.get(x["severity"], 0) for x in findings))

    scores = {
        "security": layer_score(sec_findings),
        "deployment": layer_score(dep_findings),
        "reliability": layer_score(rel_findings),
    }
    scores["viability"] = round(
        0.4 * scores["security"] + 0.3 * scores["deployment"] + 0.3 * scores["reliability"], 1
    )

    gate = "PASS" if (
        scores["viability"] >= 75 and scores["security"] >= 70
        and scores["deployment"] >= 60 and scores["reliability"] >= 60
    ) else "FAIL"

    reasons = []
    if scores["security"] < 70:
        reasons.append(f"security {scores['security']} < 70")
    if scores["deployment"] < 60:
        reasons.append(f"deployment {scores['deployment']} < 60")
    if scores["reliability"] < 60:
        reasons.append(f"reliability {scores['reliability']} < 60")
    if scores["viability"] < 75:
        reasons.append(f"viability {scores['viability']} < 75")
    if not reasons:
        reasons.append("all thresholds met")

    elapsed = round(time.time() - t0, 2)

    def layer(findings):
        return {"findings": findings, "finding_count": len(findings)}

    return {
        "scan_id": 1,
        "status": "COMPLETE",
        "repo": url,
        "mode": "website",
        "gate": gate,
        "scores": scores,
        "elapsed_seconds": elapsed,
        "findings_count": len(sec_findings) + len(dep_findings) + len(rel_findings),
        "report": {
            "tool": "sdv1-website",
            "version": "1.0.0",
            "target": url,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "http_status": status,
            "tls": tls,
            "gate_reasons": reasons,
            "layers": {
                "security_mvp": layer(sec_findings),
                "deployment": layer(dep_findings),
                "reliability": layer(rel_findings),
            },
        },
    }
