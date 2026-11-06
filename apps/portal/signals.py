from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import APIKey

User = get_user_model()


@receiver(post_save, sender=User)
def create_default_api_key_for_new_user(sender, instance, created, **kwargs):
    """
    Automatically issue an initial active API key whenever a new user registers.
    Ensures zero friction for developer onboarding.
    """
    if created and not instance.api_keys.exists():
        APIKey.objects.create(
            user=instance,
            name="Default Production Key",
            tier="free",
            rate_limit_per_minute=60,
        )
