"""
Core views — API endpoints for scan, results, quota.
Actually runs ViabilityScan engine.
"""

import json
import tempfile
import subprocess
from pathlib import Path

from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from viabilityscan.engine import ViabilityEngine


class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin for employee-only internal views."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff


class ScanCreateView(LoginRequiredMixin, View):
    """POST /api/v1/scan/ — trigger a new scan."""

    def post(self, request, *args, **kwargs):
        user = request.user
        profile = getattr(user, 'profile', None)

        # Check quota
        scans_used = profile.scans_used if profile else 0
        scans_limit = 50 if not profile or not profile.paid else 9999
        if scans_used >= scans_limit and not (profile and profile.paid):
            return JsonResponse({
                "error": "QUOTA_EXCEEDED",
                "message": "You've used all free scans. Upgrade to continue.",
                "scans_used": scans_used,
                "scans_limit": scans_limit,
            }, status=402)

        # Get repo URL or path from request
        data = json.loads(request.body or '{}')
        repo_url = data.get('repo_url', '')
        full_mode = data.get('full', False)

        if not repo_url:
            return JsonResponse({
                "error": "MISSING_REPO_URL",
                "message": "Provide repo_url in JSON body. Can be a GitHub URL or local path.",
            }, status=400)

        # Handle GitHub URLs
        if repo_url.startswith('https://github.com/'):
            # Clone to temp directory
            repo_name = repo_url.rstrip('/').split('/')[-1]
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]

            tmp_dir = Path(tempfile.mkdtemp(prefix='nextaura_'))
            clone_path = tmp_dir / repo_name

            try:
                result = subprocess.run(
                    ['git', 'clone', '--depth', '1', repo_url, str(clone_path)],
                    capture_output=True, text=True, timeout=120
                )
                if result.returncode != 0:
                    return JsonResponse({
                        "error": "CLONE_FAILED",
                        "message": result.stderr,
                    }, status=400)
                repo_path = clone_path
            except subprocess.TimeoutExpired:
                return JsonResponse({
                    "error": "CLONE_TIMEOUT",
                    "message": "Repository clone timed out after 120s.",
                }, status=408)
            except Exception as e:
                return JsonResponse({
                    "error": "CLONE_ERROR",
                    "message": str(e),
                }, status=500)
        else:
            # Local path
            repo_path = Path(repo_url).resolve()
            if not repo_path.exists():
                return JsonResponse({
                    "error": "PATH_NOT_FOUND",
                    "message": f"Path not found: {repo_path}",
                }, status=400)

        # Run the scan
        try:
            engine = ViabilityEngine(repo_path, full=full_mode)
            result = engine.run()
        except Exception as e:
            return JsonResponse({
                "error": "SCAN_FAILED",
                "message": str(e),
            }, status=500)
        finally:
            # Clean up temp clone
            if repo_url.startswith('https://github.com/'):
                import shutil
                shutil.rmtree(tmp_dir, ignore_errors=True)

        # Increment scan count
        if profile:
            profile.scans_used += 1
            profile.save()

        return JsonResponse({
            "scan_id": 1,
            "status": "COMPLETE",
            "repo": repo_url,
            "mode": "full" if full_mode else "mvp",
            "gate": result["gate"],
            "scores": result["scores"],
            "elapsed_seconds": result["elapsed_seconds"],
            "findings_count": sum(
                layer.get("finding_count", 0)
                for layer in result.get("layers", {}).values()
            ),
            "report": result,
        })


class ScanResultView(LoginRequiredMixin, View):
    """GET /api/v1/results/<id>/ — fetch scan result."""

    def get(self, request, pk, *args, **kwargs):
        # TODO: fetch from DB when persistence is wired
        return JsonResponse({
            "scan_id": pk,
            "status": "COMPLETE",
            "scores": {},
            "findings": [],
        })


class QuotaView(LoginRequiredMixin, View):
    """GET /api/v1/quota/ — how many scans left?"""

    def get(self, request, *args, **kwargs):
        user = request.user
        profile = getattr(user, 'profile', None)
        scans_used = profile.scans_used if profile else 0
        scans_limit = 50 if not profile or not profile.paid else 9999

        return JsonResponse({
            "scans_used": scans_used,
            "scans_limit": scans_limit,
            "scans_remaining": max(0, scans_limit - scans_used),
            "paid": profile.paid if profile else False,
        })


class CurrentUserView(LoginRequiredMixin, View):
    """GET /api/v1/me/ — current user info."""

    def get(self, request, *args, **kwargs):
        user = request.user
        return JsonResponse({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_staff": user.is_staff,
            "provider": None,
        })


class InternalDashboardView(StaffRequiredMixin, TemplateView):
    """Employee-only internal dashboard."""
    template_name = 'internal_dashboard.html'
