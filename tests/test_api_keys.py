import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.portal.models import APIKey

User = get_user_model()


@pytest.mark.django_db
class TestAPIKeyManagement:
    def test_key_generation_and_masking(self):
        user = User.objects.create_user(
            username="key_tester", email="tester@ipl.com", password="Pass123!Secure"
        )
        key = APIKey.objects.create(user=user, name="Mobile Key")

        assert key.key.startswith("cric_live_")
        assert len(key.key) > 30
        assert key.is_active is True
        assert "•" in key.masked_key
        assert key.masked_key.endswith(key.key[-4:])

    def test_create_additional_key_via_dashboard(self, client):
        user = User.objects.create_user(
            username="dev_multi", email="multi@ipl.com", password="Pass123!Multi"
        )
        client.force_login(user)

        create_url = reverse("portal:create_key")
        response = client.post(create_url, {"name": "Staging Backend Key"}, follow=True)
        assert response.status_code == 200

        user_keys = user.api_keys.filter(name="Staging Backend Key")
        assert user_keys.exists()
        assert user_keys.first().is_active is True

    def test_revoke_key_via_dashboard(self, client):
        user = User.objects.create_user(
            username="dev_revoke", email="revoke@ipl.com", password="Pass123!Revoke"
        )
        client.force_login(user)

        key = user.api_keys.first()
        assert key.is_active is True

        revoke_url = reverse("portal:revoke_key", kwargs={"key_id": key.id})
        response = client.post(revoke_url, follow=True)
        assert response.status_code == 200

        key.refresh_from_db()
        assert key.is_active is False
        assert key.revoked_at is not None

    def test_dashboard_requires_login(self, client):
        dashboard_url = reverse("portal:dashboard")
        response = client.get(dashboard_url)
        assert response.status_code == 302
        assert reverse("accounts:login") in response.url
