"""
NextAura custom allauth adapter.
- Auto-promotes @nextaura.fit logins to staff
- Blocks non-staff from /internal/ (enforced in views)
"""

from django.core.exceptions import MultipleObjectsReturned
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialApp

EMPLOYEE_DOMAIN = 'nextaura.fit'


class NextAuraAccountAdapter(DefaultAccountAdapter):
    """Custom local account adapter."""

    def is_open_for_signup(self, request, **kwargs):
        # Always allow signup via social auth
        return True


class NextAuraSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter.
    Auto-promotes employees to staff.
    Handles duplicate SocialApp records gracefully.
    """

    def get_app(self, request, provider, client_id=None):
        """Override to handle duplicate SocialApp records."""
        try:
            return super().get_app(request, provider, client_id=client_id)
        except MultipleObjectsReturned:
            # If duplicates exist, use the first one and clean up
            apps = SocialApp.objects.filter(provider=provider)
            if client_id:
                apps = apps.filter(client_id=client_id)
            app = apps.first()
            if app:
                # Delete extras
                apps.exclude(pk=app.pk).delete()
                return app
            raise

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        email = user.email.lower()

        # Auto-promote employees
        if email.endswith(f'@{EMPLOYEE_DOMAIN}'):
            user.is_staff = True
            user.is_superuser = False  # manual only
            user.save()

        return user

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        # Ensure email is set from social provider
        if not user.email and data.get('email'):
            user.email = data['email']
        return user
