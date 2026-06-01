"""
Core views — API endpoints for scan, results, quota.
"""

import json
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
        # TODO: check quota, Stripe payment, then enqueue scan
        # For now, return a stub
        return JsonResponse({
            "scan_id": 1,
            "status": "QUEUED",
            "message": "Scan queued. This endpoint will trigger ViabilityEngine in a background worker.",
        })


class ScanResultView(LoginRequiredMixin, View):
    """GET /api/v1/results/<id>/ — fetch scan result."""

    def get(self, request, pk, *args, **kwargs):
        # TODO: fetch from DB
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
        # TODO: fetch from DB / Stripe subscription
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
            "provider": getattr(user, 'socialaccount_set', lambda: []).first().provider if hasattr(user, 'socialaccount_set') and user.socialaccount_set.exists() else None,
        })


class InternalDashboardView(StaffRequiredMixin, TemplateView):
    """Employee-only internal dashboard."""
    template_name = 'internal_dashboard.html'
