"""
NextAura custom allauth adapter.
- Auto-promotes @nextaura.fit logins to staff
- Blocks non-staff from /internal/ (enforced in views)
"""

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

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
    """

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
