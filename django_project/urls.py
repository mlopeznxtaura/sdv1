"""
URL configuration for django_project.

Vault-grade routing. Public auth and internal paths.
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('accounts/', include('allauth.urls')),
    path('', TemplateView.as_view(template_name='landing.html'), name='landing'),
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    path('internal/', views.InternalDashboardView.as_view(), name='internal'),
]
