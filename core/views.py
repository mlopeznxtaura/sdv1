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
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from viabilityscan.engine import ViabilityEngine


class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin for employee-only internal views."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff


@method_decorator(csrf_exempt, name='dispatch')
class ScanCreateView(View):
    """POST /api/v1/scan/ — trigger a new scan. Open source: no auth, no quota."""

    def post(self, request, *args, **kwargs):
        user = request.user
        profile = getattr(user, 'profile', None)

        # Get repo URL or path from request
        data = json.loads(request.body or '{}')
        repo_url = data.get('repo_url', '')
        full_mode = data.get('full', False)

        if not repo_url:
            return JsonResponse({
                "error": "MISSING_REPO_URL",
                "message": "Provide repo_url in JSON body. Can be a GitHub URL, website URL, or local path.",
            }, status=400)

        # Website URLs (non-GitHub http/https) → live security-header audit
        if repo_url.startswith(('http://', 'https://')) and not repo_url.startswith('https://github.com/'):
            from .website_scan import scan_website
            try:
                result = scan_website(repo_url)
            except Exception as e:
                return JsonResponse({
                    "error": "WEBSITE_SCAN_FAILED",
                    "message": str(e),
                }, status=500)
            if profile:
                profile.scans_used += 1
                profile.save()
            return JsonResponse(result)

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


class ScanResultView(View):
    """GET /api/v1/results/<id>/ — fetch scan result."""

    def get(self, request, pk, *args, **kwargs):
        # TODO: fetch from DB when persistence is wired
        return JsonResponse({
            "scan_id": pk,
            "status": "COMPLETE",
            "scores": {},
            "findings": [],
        })


class QuotaView(View):
    """GET /api/v1/quota/ — open source: unlimited scans."""

    def get(self, request, *args, **kwargs):
        return JsonResponse({
            "scans_used": 0,
            "scans_limit": None,
            "scans_remaining": None,
            "paid": False,
            "open_source": True,
        })


class HealthView(View):
    """GET /api/v1/health/ — Envoy health check target."""

    def get(self, request, *args, **kwargs):
        return JsonResponse({"status": "ok"})


class CurrentUserView(View):
    """GET /api/v1/me/ — open source: anonymous access allowed."""

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            return JsonResponse({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_staff": user.is_staff,
                "provider": None,
            })
        return JsonResponse({
            "id": None,
            "username": "open-source",
            "email": "",
            "is_staff": False,
            "provider": None,
        })


class InternalDashboardView(StaffRequiredMixin, TemplateView):
    """Employee-only internal dashboard."""
    template_name = 'internal_dashboard.html'
