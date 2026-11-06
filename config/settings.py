"""
Django settings for CricPulse Developer Portal.
Production-ready configuration with environment-driven secrets,
modular app architecture, and responsive styling integration.
"""

import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

from django.core.exceptions import ImproperlyConfigured

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

# Security & Debug mode
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() in ("true", "1", "yes")

if not DEBUG:
    SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
    if not SECRET_KEY:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY environment variable must be set when DEBUG is False.")
    INTERNAL_SERVICE_SECRET = os.getenv("INTERNAL_SERVICE_SECRET")
    if not INTERNAL_SERVICE_SECRET:
        raise ImproperlyConfigured("INTERNAL_SERVICE_SECRET environment variable must be set when DEBUG is False.")
else:
    SECRET_KEY = os.getenv(
        "DJANGO_SECRET_KEY",
        "django-insecure-cricpulse-portal-super-secret-key-change-in-production-2026",
    )
    INTERNAL_SERVICE_SECRET = os.getenv(
        "INTERNAL_SERVICE_SECRET",
        "cricpulse-internal-secret-2026",
    )

allowed_hosts_str = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0,.onrender.com")
ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_str.split(",") if h.strip()]

# Number of trusted reverse proxies in front of Django (Render uses 1)
NUM_PROXIES = int(os.getenv("NUM_PROXIES", "1"))

# CricPulse Backend Engine URL
CRICPULSE_ENGINE_URL = os.getenv(
    "CRICPULSE_ENGINE_URL", "https://cricpulse-engine.onrender.com"
).rstrip("/")

# Application definition
INSTALLED_APPS = [
    # Core Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Local CricPulse apps
    "apps.accounts.apps.AccountsConfig",
    "apps.portal.apps.PortalConfig",
    "apps.analytics.apps.AnalyticsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Storage Configuration (Django 5.1+)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "config.context_processors.portal_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database Configuration
# Automatically switches to Managed PostgreSQL when DATABASE_URL is present (Render, Railway, Supabase)
# Seamlessly falls back to local SQLite for instant, zero-config local development
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Cache Configuration
# Defaults to LocMemCache; allows configuring a shared cache (Redis/Memcached) via REDIS_URL or CACHE_URL
REDIS_URL = os.getenv("REDIS_URL") or os.getenv("CACHE_URL")
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "cricpulse-portal-cache",
            "OPTIONS": {
                "MAX_ENTRIES": 10000,
            },
        }
    }

# Observability & Error Tracking with Sentry
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()],
            traces_sample_rate=0.2,
            send_default_pii=False,
            environment=os.getenv(
                "DJANGO_ENV", "production" if not DEBUG else "development"
            ),
        )
    except Exception:
        pass

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Authentication redirection
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "portal:dashboard"
LOGOUT_REDIRECT_URL = "portal:home"

# Production Security Hardening
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Map Django message tags to Tailwind alert classes
from django.contrib.messages import constants as messages_constants  # noqa: E402

MESSAGE_TAGS = {
    messages_constants.DEBUG: "bg-slate-50 text-slate-700 border-slate-200",
    messages_constants.INFO: "bg-sky-50 text-sky-800 border-sky-200",
    messages_constants.SUCCESS: "bg-emerald-50 text-emerald-800 border-emerald-200",
    messages_constants.WARNING: "bg-amber-50 text-amber-800 border-amber-200",
    messages_constants.ERROR: "bg-rose-50 text-rose-800 border-rose-200",
}
