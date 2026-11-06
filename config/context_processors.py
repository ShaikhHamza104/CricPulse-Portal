"""
Context processors for CricPulse Portal.
Makes site-wide configuration available in all Django templates.
"""

from django.conf import settings


def portal_context(request):
    return {
        "CRICPULSE_ENGINE_URL": getattr(
            settings, "CRICPULSE_ENGINE_URL", "https://cricpulse-engine.onrender.com"
        ),
        "SITE_NAME": "CricPulse Developer Portal",
        "SITE_VERSION": "1.0.0",
        "API_VERSION": "v1",
    }
