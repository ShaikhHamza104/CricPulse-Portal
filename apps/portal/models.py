import secrets
from django.conf import settings
from django.db import models
from django.utils import timezone


class APIKey(models.Model):
    """
    Cryptographically secure API Key issued to a registered developer.
    Enables access to CricPulse-Engine analytical endpoints.
    """

    TIER_CHOICES = [
        ("free", "Developer Free (60 req/min)"),
        ("pro", "Pro Tier (300 req/min)"),
        ("enterprise", "Enterprise Tier (1200 req/min)"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="api_keys",
    )
    name = models.CharField(
        max_length=64,
        default="Default Production Key",
        help_text="A friendly label to identify this key.",
    )
    key = models.CharField(
        max_length=80,
        unique=True,
        db_index=True,
        help_text="Unique secret key (cric_live_...)",
    )
    tier = models.CharField(
        max_length=20,
        choices=TIER_CHOICES,
        default="free",
    )
    rate_limit_per_minute = models.PositiveIntegerField(
        default=60,
        help_text="Max permitted requests per minute for this key.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Active keys can authenticate against the engine.",
    )
    total_requests = models.PositiveIntegerField(
        default=0,
        help_text="Total requests logged with this key.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.name} ({self.masked_key})"

    @classmethod
    def generate_secret(cls) -> str:
        """Generate a cryptographically secure 24-byte hex token with a domain prefix."""
        return f"cric_live_{secrets.token_hex(24)}"

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_secret()
        super().save(*args, **kwargs)

    @property
    def masked_key(self) -> str:
        """Returns masked version for secure display (e.g. cric_live_••••••••3a7b)."""
        if not self.key:
            return ""
        prefix = "cric_live_"
        raw = self.key.replace(prefix, "")
        if len(raw) <= 8:
            return self.key
        return f"{prefix}{'•' * 16}{raw[-4:]}"

    def revoke(self):
        """Immediately revoke this API key."""
        self.is_active = False
        self.revoked_at = timezone.now()
        self.save(update_fields=["is_active", "revoked_at"])
