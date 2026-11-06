import pytest
from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from apps.portal.admin import APIKeyAdmin
from apps.portal.models import APIKey

User = get_user_model()


@pytest.mark.django_db
class TestAdminInterface:
    def test_apikey_model_registered_in_admin(self):
        assert APIKey in site._registry
        admin_instance = site._registry[APIKey]
        assert isinstance(admin_instance, APIKeyAdmin)

    def test_admin_custom_badges_and_previews(self, rf):
        user = User.objects.create_user(
            username="admin_test_user", email="admintest@ipl.com", password="Pass123!Admin"
        )
        key = APIKey.objects.create(user=user, name="Admin Key", tier="pro")
        admin_instance = APIKeyAdmin(APIKey, site)

        # Previews and badges
        assert key.masked_key == admin_instance.key_preview(key)
        assert "admin_test_user" in admin_instance.user_link(key)
        assert "Active" in admin_instance.status_badge(key)
        assert "Pro Tier" in admin_instance.tier_badge(key)

    def test_admin_revoke_and_activate_actions(self, rf):
        admin_user = User.objects.create_superuser(
            username="superadmin", email="super@ipl.com", password="SuperPassword123!"
        )
        user = User.objects.create_user(
            username="regular_user", email="regular@ipl.com", password="RegularPassword123!"
        )
        key1 = APIKey.objects.create(user=user, name="Key 1")
        key2 = APIKey.objects.create(user=user, name="Key 2")

        admin_instance = APIKeyAdmin(APIKey, site)
        request = rf.get("/admin/portal/apikey/")
        request.user = admin_user
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(request, "session", {})
        setattr(request, "_messages", FallbackStorage(request))

        # Revoke action
        admin_instance.revoke_keys(request, APIKey.objects.filter(id__in=[key1.id, key2.id]))
        key1.refresh_from_db()
        key2.refresh_from_db()
        assert key1.is_active is False
        assert key2.is_active is False

        # Activate action
        admin_instance.activate_keys(request, APIKey.objects.filter(id__in=[key1.id, key2.id]))
        key1.refresh_from_db()
        key2.refresh_from_db()
        assert key1.is_active is True
        assert key2.is_active is True
