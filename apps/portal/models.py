import secrets
from django.conf import settings
from django.db import models
from django.utils import timezone


import hashlib
import secrets
from django.conf import settings
from django.db import models
from django.utils import timezone


class APIKey(models.Model):
    """
    Cryptographically secure API Key issued to a registered developer.
    Enables access to CricPulse-Engine analytical endpoints.
    Keys are stored as SHA-256 hashes for zero-leak security.
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
    hashed_key = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="SHA-256 cryptographic hash of the API key.",
    )
    prefix = models.CharField(
        max_length=16,
        default="cric_live_",
        help_text="Display prefix (e.g. cric_live_).",
    )
    last4 = models.CharField(
        max_length=4,
        default="",
        help_text="Last 4 characters of the key for identification.",
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

    # Ephemeral storage for raw key immediately after generation (not persisted)
    _raw_key: str | None = None

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

    @staticmethod
    def hash_key(raw_token: str) -> str:
        """Calculate the SHA-256 hex digest of a raw token."""
        return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()

    @property
    def key(self) -> str | None:
        """
        Plaintext key is ephemeral and only available in memory immediately
        after generation in the current session.
        """
        return self._raw_key

    @key.setter
    def key(self, raw_val: str):
        if raw_val:
            self._raw_key = raw_val
            self.hashed_key = self.hash_key(raw_val)
            self.prefix = raw_val[:10] if len(raw_val) >= 10 else "cric_live_"
            self.last4 = raw_val[-4:] if len(raw_val) >= 4 else ""

    def save(self, *args, **kwargs):
        if not self.hashed_key:
            raw = self.generate_secret()
            self._raw_key = raw
            self.hashed_key = self.hash_key(raw)
            self.prefix = raw[:10]
            self.last4 = raw[-4:]
        super().save(*args, **kwargs)

    def refresh_from_db(self, *args, **kwargs):
        self._raw_key = None
        super().refresh_from_db(*args, **kwargs)

    @property
    def masked_key(self) -> str:
        """Returns masked version for secure display (e.g. cric_live_••••••••3a7b)."""
        pfx = self.prefix or "cric_live_"
        l4 = self.last4 or ""
        return f"{pfx}{'•' * 16}{l4}"

    def revoke(self):
        """Immediately revoke this API key."""
        self.is_active = False
        self.revoked_at = timezone.now()
        self.save(update_fields=["is_active", "revoked_at"])
