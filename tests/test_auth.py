import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
class TestAuthenticationFlows:
    def test_signup_creates_user_and_auto_provisions_api_key(self, client):
        signup_url = reverse("accounts:signup")
        payload = {
            "username": "cricketer10",
            "email": "cricketer10@ipl.com",
            "first_name": "Hamza",
            "password1": "SuperSecretPass123!",
            "password2": "SuperSecretPass123!",
        }
        response = client.post(signup_url, payload, follow=True)
        assert response.status_code == 200

        # Verify user created in DB
        user = User.objects.filter(username="cricketer10").first()
        assert user is not None
        assert user.email == "cricketer10@ipl.com"

        # Verify automatic API Key provisioned by signal
        api_key = user.api_keys.first()
        assert api_key is not None
        assert api_key.masked_key.startswith("cric_live_")
        assert len(api_key.hashed_key) == 64
        assert api_key.is_active is True
        assert api_key.tier == "free"

    def test_signup_rejects_duplicate_email(self, client):
        User.objects.create_user(
            username="user1", email="duplicate@ipl.com", password="Pass123!Valid"
        )

        signup_url = reverse("accounts:signup")
        payload = {
            "username": "user2",
            "email": "duplicate@ipl.com",
            "password1": "Pass123!Valid2",
            "password2": "Pass123!Valid2",
        }
        response = client.post(signup_url, payload)
        assert response.status_code == 200
        assert "An account with this email address already exists." in response.content.decode()

    def test_login_and_logout_flow(self, client):
        user = User.objects.create_user(
            username="hamza_dev", email="hamza@ipl.com", password="MySecurePassword123"
        )

        # Login
        login_url = reverse("accounts:login")
        login_resp = client.post(
            login_url,
            {"username": "hamza_dev", "password": "MySecurePassword123"},
            follow=True,
        )
        assert login_resp.status_code == 200
        assert "_auth_user_id" in client.session

        # Logout: GET is rejected with 405 Method Not Allowed and user stays logged in
        logout_url = reverse("accounts:logout")
        get_logout_resp = client.get(logout_url)
        assert get_logout_resp.status_code == 405
        assert "_auth_user_id" in client.session

        # Logout: POST succeeds and logs out
        post_logout_resp = client.post(logout_url, follow=True)
        assert post_logout_resp.status_code == 200
        assert "_auth_user_id" not in client.session

    def test_profile_update(self, client):
        user = User.objects.create_user(
            username="dev_profile", email="old@ipl.com", password="Password123!"
        )
        client.force_login(user)

        profile_url = reverse("accounts:profile")
        response = client.post(
            profile_url,
            {"first_name": "UpdatedName", "last_name": "Shaikh", "email": "new@ipl.com"},
            follow=True,
        )
        assert response.status_code == 200

        user.refresh_from_db()
        assert user.first_name == "UpdatedName"
        assert user.email == "new@ipl.com"
