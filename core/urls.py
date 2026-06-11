"""
Core API routes — scan, results, quota, billing.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('v1/scan/', views.ScanCreateView.as_view(), name='scan-create'),
    path('v1/results/<int:pk>/', views.ScanResultView.as_view(), name='scan-result'),
    path('v1/quota/', views.QuotaView.as_view(), name='quota'),
    path('v1/me/', views.CurrentUserView.as_view(), name='current-user'),
    path('v1/health/', views.HealthView.as_view(), name='health'),
]
