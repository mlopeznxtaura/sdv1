"""One-off script to fix duplicate SocialApps in the deployed container."""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')

import django
django.setup()

from allauth.socialaccount.models import SocialApp

count = SocialApp.objects.count()
print(f"SocialApp count: {count}")

if count > 1:
    print("Deleting all SocialApps...")
    SocialApp.objects.all().delete()
    print("Cleared.")

# Recreate GitHub app
github_id = os.environ.get('GITHUB_CLIENT_ID', '')
github_secret = os.environ.get('GITHUB_CLIENT_SECRET', '')

if github_id:
    from django.contrib.sites.models import Site
    site = Site.objects.get_or_create(pk=1, defaults={'domain': 'app4.nextaura.fit', 'name': 'NextAura'})[0]
    app = SocialApp.objects.create(
        provider='github',
        name='GitHub',
        client_id=github_id,
        secret=github_secret,
    )
    app.sites.add(site)
    print(f"Created GitHub app with ID: {github_id[:10]}...")
else:
    print("No GITHUB_CLIENT_ID in env")
