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

    def test_login_brute_force_throttling_by_ip(self, client):
        from django.core.cache import cache
        cache.clear()

        User.objects.create_user(username="brute_victim", password="CorrectPass123!")
        login_url = reverse("accounts:login")

        # 5 failed attempts from same IP
        for _ in range(5):
            resp = client.post(
                login_url,
                {"username": "brute_victim", "password": "WrongPassword!"},
                REMOTE_ADDR="198.51.100.99",
            )
            assert resp.status_code == 200
            assert "Invalid username or password" in resp.content.decode()

        # 6th attempt must be throttled with HTTP 429
        resp_429 = client.post(
            login_url,
            {"username": "brute_victim", "password": "CorrectPass123!"},
            REMOTE_ADDR="198.51.100.99",
        )
        assert resp_429.status_code == 429
        assert "Too many failed login attempts" in resp_429.content.decode()

    def test_login_brute_force_throttling_by_username(self, client):
        from django.core.cache import cache
        cache.clear()

        User.objects.create_user(username="target_user", password="CorrectPass123!")
        login_url = reverse("accounts:login")

        # Attacker rotates IP but attacks same username 5 times
        for i in range(5):
            resp = client.post(
                login_url,
                {"username": "target_user", "password": "WrongPassword!"},
                REMOTE_ADDR=f"10.10.10.{i+1}",
            )
            assert resp.status_code == 200

        # 6th attempt from a brand new IP for this username must be blocked
        resp_429 = client.post(
            login_url,
            {"username": "target_user", "password": "WrongPassword!"},
            REMOTE_ADDR="10.10.10.99",
        )
        assert resp_429.status_code == 429
        assert "Too many failed login attempts" in resp_429.content.decode()

    def test_login_success_clears_throttle_counter(self, client):
        from django.core.cache import cache
        cache.clear()

        User.objects.create_user(username="clean_user", password="ValidPassword123!")
        login_url = reverse("accounts:login")

        # 3 failed attempts
        for _ in range(3):
            client.post(
                login_url,
                {"username": "clean_user", "password": "WrongPassword!"},
                REMOTE_ADDR="192.168.50.1",
            )

        # Successful login clears the counter
        success_resp = client.post(
            login_url,
            {"username": "clean_user", "password": "ValidPassword123!"},
            REMOTE_ADDR="192.168.50.1",
            follow=True,
        )
        assert success_resp.status_code == 200
        assert "_auth_user_id" in client.session

        # Counter is cleared
        assert cache.get("throttle:login:ip:192.168.50.1") is None
        assert cache.get("throttle:login:user:clean_user") is None

    def test_signup_rate_limiting_per_ip(self, client):
        from django.core.cache import cache
        cache.clear()

        signup_url = reverse("accounts:signup")
        ip = "198.51.100.77"

        # 5 valid signup attempts from same IP
        for i in range(5):
            resp = client.post(
                signup_url,
                {
                    "username": f"bulk_user_{i}",
                    "email": f"bulk_{i}@ipl.com",
                    "password1": "SecurePass123!",
                    "password2": "SecurePass123!",
                },
                REMOTE_ADDR=ip,
            )
            assert resp.status_code == 302
            client.logout()  # Log out so subsequent request simulates a new visitor from the same IP

        # 6th signup attempt from same IP must be rejected with 429
        resp_429 = client.post(
            signup_url,
            {
                "username": "bulk_user_6",
                "email": "bulk_6@ipl.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            },
            REMOTE_ADDR=ip,
        )
        assert resp_429.status_code == 429
        assert "Too many account creation attempts" in resp_429.content.decode()
