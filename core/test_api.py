"""
Quick test script to verify the scan API works locally.
Run: .venv\Scripts\python core\test_api.py
"""
import requests
import json

BASE = "http://localhost:8000"

# 1. Login
login_resp = requests.post(f"{BASE}/accounts/login/", data={
    "login": "admin",
    "password": "NextAura2026!",
    "csrfmiddlewaretoken": requests.get(f"{BASE}/accounts/login/").cookies.get("csrftoken", ""),
}, cookies=requests.get(f"{BASE}/accounts/login/").cookies, allow_redirects=False)

session_cookie = login_resp.cookies.get("sessionid")
if not session_cookie:
    print("Login failed")
    exit(1)

print("Logged in as admin")

# 2. Check quota
quota = requests.get(f"{BASE}/api/v1/quota/", cookies={"sessionid": session_cookie}).json()
print(f"Quota: {json.dumps(quota, indent=2)}")

# 3. Scan local repo
scan = requests.post(
    f"{BASE}/api/v1/scan/",
    json={"repo_url": ".", "full": False},
    cookies={"sessionid": session_cookie},
).json()

if "error" in scan:
    print(f"Scan error: {scan['error']} - {scan.get('message', '')}")
else:
    print(f"Scan complete!")
    print(f"  Gate: {scan['gate']}")
    print(f"  Scores: {json.dumps(scan['scores'], indent=2)}")
    print(f"  Elapsed: {scan['elapsed_seconds']}s")
    print(f"  Findings: {scan['findings_count']}")
