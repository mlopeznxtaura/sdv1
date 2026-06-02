"""
Auto-create SocialApp records from environment variables.
Run on startup to wire OAuth without manual admin clicks.
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


PROVIDERS = {
    'github': 'GitHub',
    'google': 'Google',
    'apple': 'Apple',
    'microsoft': 'Microsoft',
    'yahoo': 'Yahoo',
}


class Command(BaseCommand):
    help = 'Create SocialApp records from env vars'

    def handle(self, *args, **options):
        site = Site.objects.get_or_create(pk=1, defaults={'domain': 'app4.nextaura.fit', 'name': 'NextAura'})[0]

        for provider_key, provider_name in PROVIDERS.items():
            client_id = os.environ.get(f'{provider_key.upper()}_CLIENT_ID', '')
            secret = os.environ.get(f'{provider_key.upper()}_CLIENT_SECRET', '')

            if not client_id:
                continue

            # Delete duplicates if they exist
            SocialApp.objects.filter(provider=provider_key).delete()

            app = SocialApp.objects.create(
                provider=provider_key,
                name=provider_name,
                client_id=client_id,
                secret=secret or '',
            )
            app.sites.add(site)

            self.stdout.write(self.style.SUCCESS(f'Created {provider_name} OAuth app'))

        self.stdout.write(self.style.SUCCESS('OAuth setup complete'))
