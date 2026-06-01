"""
Custom Supabase OAuth provider for django-allauth.
Supabase uses its own OAuth flow, not standard OAuth2.

To activate, add to settings.py INSTALLED_APPS:
    'core.supabase_provider'  # Custom provider module

Then register the app in Django admin with:
    Provider: supabase
    Client id: your Supabase project URL
    Secret: your Supabase service role key
"""

from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider


class SupabaseAccount(ProviderAccount):
    pass


class SupabaseProvider(OAuth2Provider):
    id = 'supabase'
    name = 'Supabase'
    account_class = SupabaseAccount

    def extract_uid(self, data):
        return str(data.get('id', ''))

    def extract_common_fields(self, data):
        return dict(
            email=data.get('email'),
            username=data.get('user_metadata', {}).get('username'),
        )


provider_classes = [SupabaseProvider]
