"""
Django settings for django_project project.

Vault-grade infrastructure. All secrets via environment variables.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ──────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-secret-change-me-in-production')

DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Trust Cloudflare proxy and custom domain for CSRF
CSRF_TRUSTED_ORIGINS = [f'https://{host.strip()}' for host in ALLOWED_HOSTS if host.strip() not in ('localhost', '127.0.0.1', '')]

# ── Apps ──────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    # social providers — priority order: GitHub, Apple, Google, Supabase, Microsoft, Yahoo
    'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.apple',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.microsoft',
    'allauth.socialaccount.providers.yahoo',

    # custom
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'django_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'django_project.wsgi.application'

# ── Database ──────────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'data' / 'db.sqlite3',
    }
}

# ── Auth ──────────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

# allauth settings
ACCOUNT_LOGIN_METHODS = {'email', 'username'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*']
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_UNIQUE_EMAIL = True

# Magic link / passwordless login via email
ACCOUNT_EMAIL_NOTIFICATIONS = True

# Custom adapters
ACCOUNT_ADAPTER = 'core.adapter.NextAuraAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'core.adapter.NextAuraSocialAccountAdapter'

# Login redirects
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Social login settings
SOCIALACCOUNT_PROVIDERS = {
    'github': {
        'APP': {
            'client_id': os.environ.get('GITHUB_CLIENT_ID', ''),
            'secret': os.environ.get('GITHUB_CLIENT_SECRET', ''),
            'key': '',
        },
        'SCOPE': ['read:user', 'user:email'],
    },
    'apple': {
        'APP': {
            'client_id': os.environ.get('APPLE_CLIENT_ID', ''),
            'secret': os.environ.get('APPLE_SECRET', ''),
            'key': '',
        },
        'CERTIFICATE': os.environ.get('APPLE_CERTIFICATE_PATH', ''),
        'CERTIFICATE_KEY': os.environ.get('APPLE_CERTIFICATE_KEY_PATH', ''),
    },
    'google': {
        'APP': {
            'client_id': os.environ.get('GOOGLE_CLIENT_ID', ''),
            'secret': os.environ.get('GOOGLE_CLIENT_SECRET', ''),
            'key': '',
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    },
    'microsoft': {
        'APP': {
            'client_id': os.environ.get('MICROSOFT_CLIENT_ID', ''),
            'secret': os.environ.get('MICROSOFT_CLIENT_SECRET', ''),
            'key': '',
        },
        'SCOPE': ['openid', 'email', 'profile'],
        'TENANT': 'common',
    },
    'yahoo': {
        'APP': {
            'client_id': os.environ.get('YAHOO_CLIENT_ID', ''),
            'secret': os.environ.get('YAHOO_CLIENT_SECRET', ''),
            'key': '',
        },
        'SCOPE': ['openid', 'profile', 'email'],
    },
}

# Supabase uses its own OAuth flow — configured as a custom provider
# See core/supabase_provider.py

# ── Email ─────────────────────────────────────────────────────────────────
# Production: use SMTP (SendGrid, AWS SES, or Gmail for testing)
EMAIL_BACKEND = os.environ.get(
    'DJANGO_EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'  # default: prints to console
)

EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'vault@nextaura.fit')
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', 'vault@nextaura.fit')

# ── Internationalization ────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ── Static / Media ──────────────────────────────────────────────────────
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Security Headers ────────────────────────────────────────────────────
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
