from django.apps import AppConfig


class PortalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.portal"
    verbose_name = "Developer Portal & API Keys"

    def ready(self):
        import apps.portal.signals  # noqa: F401
