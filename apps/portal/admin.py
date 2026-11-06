from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import APIKey


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = (
        "key_preview",
        "user_link",
        "name",
        "tier_badge",
        "status_badge",
        "rate_limit_per_minute",
        "total_requests",
        "created_at",
    )
    list_filter = ("is_active", "tier", "created_at")
    search_fields = ("user__username", "user__email", "key", "name")
    readonly_fields = ("created_at", "last_used_at", "revoked_at", "total_requests")
    actions = ["revoke_keys", "activate_keys"]

    @admin.display(description="API Key")
    def key_preview(self, obj: APIKey) -> str:
        return obj.masked_key

    @admin.display(description="Developer")
    def user_link(self, obj: APIKey):
        return format_html("<strong>{}</strong> ({})", obj.user.username, obj.user.email)

    @admin.display(description="Tier")
    def tier_badge(self, obj: APIKey):
        colors = {
            "free": "background:#e0f2fe; color:#0369a1;",
            "pro": "background:#fef3c7; color:#b45309;",
            "enterprise": "background:#f3e8ff; color:#7e22ce;",
        }
        style = colors.get(obj.tier, "background:#f1f5f9; color:#475569;")
        return format_html(
            '<span style="padding:3px 8px; border-radius:9999px; font-weight:600; font-size:11px; {}">{}</span>',
            style,
            obj.get_tier_display(),
        )

    @admin.display(description="Status")
    def status_badge(self, obj: APIKey):
        if obj.is_active:
            return format_html(
                '<span style="padding:3px 8px; border-radius:9999px; background:#dcfce7; color:#15803d; font-weight:600; font-size:11px;">{}</span>',
                "Active",
            )
        return format_html(
            '<span style="padding:3px 8px; border-radius:9999px; background:#fee2e2; color:#b91c1c; font-weight:600; font-size:11px;">{}</span>',
            "Revoked",
        )

    @admin.action(description="Revoke selected API keys")
    def revoke_keys(self, request, queryset):
        count = queryset.update(is_active=False, revoked_at=timezone.now())
        self.message_user(request, f"Successfully revoked {count} API key(s).")

    @admin.action(description="Activate selected API keys")
    def activate_keys(self, request, queryset):
        count = queryset.update(is_active=True, revoked_at=None)
        self.message_user(request, f"Successfully activated {count} API key(s).")
