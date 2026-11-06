import pytest
from unittest.mock import MagicMock, patch
from django.urls import reverse


def test_ssrf_protection_rejects_external_schemes(client):
    proxy_url = reverse("analytics:proxy")
    # Test rejection of external schemes
    resp = client.get(proxy_url, {"endpoint": "https://malicious-external-site.com/steal"})
    assert resp.status_code == 400
    assert "Invalid endpoint target" in resp.json()["error"]


def test_ssrf_protection_rejects_protocol_relative_urls(client):
    proxy_url = reverse("analytics:proxy")
    # Test rejection of protocol-relative authority redirects
    resp = client.get(proxy_url, {"endpoint": "//attacker.com/leak"})
    assert resp.status_code == 400
    assert "Invalid endpoint target" in resp.json()["error"]


def test_ssrf_protection_rejects_path_traversal(client):
    proxy_url = reverse("analytics:proxy")
    # Test rejection of directory traversal
    resp = client.get(proxy_url, {"endpoint": "/api/v1/../../etc/passwd"})
    assert resp.status_code == 400
    assert "Invalid endpoint target" in resp.json()["error"]


def test_ssrf_protection_rejects_non_whitelisted_routes(client):
    proxy_url = reverse("analytics:proxy")
    # Test rejection of unwhitelisted internal routes
    resp = client.get(proxy_url, {"endpoint": "/admin/auth/user/"})
    assert resp.status_code == 403
    assert "Access denied" in resp.json()["error"]


@patch("httpx.Client.get")
def test_ssrf_protection_allows_valid_api_routes(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"X-Process-Time": "0.015s"}
    mock_resp.json.return_value = {"status": "ok"}
    mock_resp.content = b'{"status": "ok"}'
    mock_get.return_value = mock_resp

    proxy_url = reverse("analytics:proxy")
    resp = client.get(proxy_url, {"endpoint": "/api/v1/analytics/head-to-head?team1=CSK&team2=RCB"})
    assert resp.status_code == 200


def test_open_redirect_protection_in_login(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="dev_redirect_test", password="Password123!"
    )
    login_url = reverse("accounts:login")

    # Attempt malicious external open redirect
    malicious_next = "https://malicious-phishing-attacker.com/steal"
    resp = client.post(
        f"{login_url}?next={malicious_next}",
        {"username": "dev_redirect_test", "password": "Password123!"},
    )
    # Must reject the malicious host and redirect safely to portal:dashboard
    assert resp.status_code == 302
    assert resp["Location"] == reverse("portal:dashboard")


def test_safe_internal_redirect_allowed_in_login(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="dev_safe_redirect", password="Password123!"
    )
    login_url = reverse("accounts:login")

    # Safe internal relative path
    safe_next = reverse("portal:docs")
    resp = client.post(
        f"{login_url}?next={safe_next}",
        {"username": "dev_safe_redirect", "password": "Password123!"},
    )
    assert resp.status_code == 302
    assert resp["Location"] == safe_next


def test_api_key_creation_quota_limit(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="quota_user", password="Password123!"
    )
    client.force_login(user)

    create_key_url = reverse("portal:create_key")

    # Create keys up to the limit (5 active keys)
    for i in range(5):
        client.post(create_key_url, {"name": f"Key #{i+1}"})

    assert user.api_keys.filter(is_active=True).count() == 5

    # Attempt to create the 6th key (exceeding quota)
    resp = client.post(create_key_url, {"name": "Exceeded Key #6"}, follow=True)
    assert resp.status_code == 200
    assert user.api_keys.filter(is_active=True).count() == 5  # Still capped at 5
    messages = [m.message for m in resp.context["messages"]]
    assert any("Key quota exceeded" in m for m in messages)


@patch("httpx.Client.get")
def test_live_query_proxy_rate_limit(mock_get, client):
    from django.core.cache import cache
    cache.clear()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"X-Process-Time": "0.010s"}
    mock_resp.json.return_value = {"status": "ok"}
    mock_resp.content = b'{"status": "ok"}'
    mock_get.return_value = mock_resp

    proxy_url = reverse("analytics:proxy")

    # Send 60 requests (allowed)
    for _ in range(60):
        resp = client.get(proxy_url, {"endpoint": "/health"})
        assert resp.status_code == 200

    # 61st request must trigger HTTP 429
    resp_429 = client.get(proxy_url, {"endpoint": "/health"})
    assert resp_429.status_code == 429
    assert "rate limit exceeded" in resp_429.json()["error"].lower()
    assert "Retry-After" in resp_429.headers


@patch("httpx.Client.get")
def test_rotating_x_forwarded_for_cannot_bypass_rate_limit(mock_get, client):
    from django.core.cache import cache
    cache.clear()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"X-Process-Time": "0.010s"}
    mock_resp.json.return_value = {"status": "ok"}
    mock_resp.content = b'{"status": "ok"}'
    mock_get.return_value = mock_resp

    proxy_url = reverse("analytics:proxy")
    real_client_ip = "198.51.100.42"

    # Attacker rotates the client-controlled first IP in X-Forwarded-For
    for i in range(60):
        fake_ip = f"10.0.{i // 256}.{i % 256}"
        resp = client.get(
            proxy_url,
            {"endpoint": "/health"},
            HTTP_X_FORWARDED_FOR=f"{fake_ip}, {real_client_ip}",
        )
        assert resp.status_code == 200

    # 61st request with yet another fake IP must be blocked because the real client IP is tracked
    resp_429 = client.get(
        proxy_url,
        {"endpoint": "/health"},
        HTTP_X_FORWARDED_FOR=f"10.99.99.99, {real_client_ip}",
    )
    assert resp_429.status_code == 429
    assert "rate limit exceeded" in resp_429.json()["error"].lower()
    assert "Retry-After" in resp_429.headers


def test_get_client_ip_fallback():
    from django.test import RequestFactory
    from apps.analytics.views import _get_client_ip
    rf = RequestFactory()

    # Valid IP extracted from last entry appended by proxy
    req1 = rf.get("/", HTTP_X_FORWARDED_FOR="1.1.1.1, 198.51.100.5")
    assert _get_client_ip(req1) == "198.51.100.5"

    # Malicious invalid IP in X-Forwarded-For falls back to REMOTE_ADDR
    req2 = rf.get("/", HTTP_X_FORWARDED_FOR="not-an-ip", REMOTE_ADDR="192.168.1.10")
    assert _get_client_ip(req2) == "192.168.1.10"

    # Missing X-Forwarded-For falls back to REMOTE_ADDR
    req3 = rf.get("/", REMOTE_ADDR="192.168.1.20")
    assert _get_client_ip(req3) == "192.168.1.20"


def test_internal_verify_key_unauthorized_without_secret(client):
    verify_url = reverse("portal:internal_verify_key")
    resp = client.get(verify_url, {"key": "some_key"})
    assert resp.status_code == 403


def test_internal_verify_key_wrong_secret_gives_403(client):
    verify_url = reverse("portal:internal_verify_key")
    resp = client.get(
        verify_url,
        {"key": "some_key"},
        HTTP_X_INTERNAL_SECRET="invalid-wrong-secret",
    )
    assert resp.status_code == 403
    assert resp.json()["valid"] is False


def test_internal_verify_key_rejects_query_string_secret(client, django_user_model):
    from apps.portal.models import APIKey
    user = django_user_model.objects.create_user(username="qs_secret_user", password="Password123!")
    key_obj = APIKey.objects.create(user=user, name="QS Key")

    verify_url = reverse("portal:internal_verify_key")
    # Secret sent via query parameter must be rejected
    resp = client.get(
        f"{verify_url}?key={key_obj.key}&secret=cricpulse-internal-secret-2026"
    )
    assert resp.status_code == 403
    assert resp.json()["valid"] is False


def test_internal_verify_key_active_key_succeeds(client, django_user_model):
    from apps.portal.models import APIKey
    user = django_user_model.objects.create_user(username="verify_user", password="Password123!")
    key_obj = APIKey.objects.create(user=user, name="Live Key", tier="pro", rate_limit_per_minute=300)
    assert key_obj.total_requests == 0
    assert key_obj.last_used_at is None

    verify_url = reverse("portal:internal_verify_key")
    resp = client.get(
        verify_url,
        {"key": key_obj.key},
        HTTP_X_INTERNAL_SECRET="cricpulse-internal-secret-2026",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert data["is_active"] is True
    assert data["tier"] == "pro"
    assert data["rate_limit_per_minute"] == 300

    # Verify usage counters updated atomically
    key_obj.refresh_from_db()
    assert key_obj.total_requests == 1
    assert key_obj.last_used_at is not None


def test_internal_verify_key_revoked_key_rejected(client, django_user_model):
    from apps.portal.models import APIKey
    user = django_user_model.objects.create_user(username="revoked_verify_user", password="Password123!")
    key_obj = APIKey.objects.create(user=user, name="Revoked Key", is_active=False)

    verify_url = reverse("portal:internal_verify_key")
    resp = client.get(
        verify_url,
        {"key": key_obj.key},
        HTTP_X_INTERNAL_SECRET="cricpulse-internal-secret-2026",
    )
    assert resp.status_code == 403
    data = resp.json()
    assert data["valid"] is False
    assert data["is_active"] is False
    assert data["reason"] == "revoked"


def test_internal_verify_key_hashes_input_and_looks_up_by_hash(client, django_user_model):
    from apps.portal.models import APIKey
    user = django_user_model.objects.create_user(username="hash_test_user", password="Password123!")
    key_obj = APIKey.objects.create(user=user, name="Hashed Key Test")
    raw_key = key_obj.key
    assert raw_key is not None

    # Reload from DB: plaintext key must NOT be stored
    key_obj.refresh_from_db()
    assert key_obj.key is None
    assert len(key_obj.hashed_key) == 64

    verify_url = reverse("portal:internal_verify_key")

    # Correct raw key hashes to match stored hash
    resp = client.get(
        verify_url,
        {"key": raw_key},
        HTTP_X_INTERNAL_SECRET="cricpulse-internal-secret-2026",
    )
    assert resp.status_code == 200
    assert resp.json()["valid"] is True

    # Tampered raw key results in 404 key_not_found
    tampered_key = raw_key[:-4] + "ffff"
    tampered_resp = client.get(
        verify_url,
        {"key": tampered_key},
        HTTP_X_INTERNAL_SECRET="cricpulse-internal-secret-2026",
    )
    assert tampered_resp.status_code == 404
    assert tampered_resp.json()["reason"] == "key_not_found"


def test_production_missing_secrets_raises_improperly_configured(monkeypatch):
    import importlib
    from django.core.exceptions import ImproperlyConfigured
    import config.settings

    # Prevent load_dotenv from re-reading .env file during unit test reload
    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: None)

    # Verify missing DJANGO_SECRET_KEY in production raises ImproperlyConfigured
    monkeypatch.setenv("DJANGO_DEBUG", "False")
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)
    monkeypatch.setenv("INTERNAL_SERVICE_SECRET", "some-secret")
    with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY"):
        importlib.reload(config.settings)

    # Verify missing INTERNAL_SERVICE_SECRET in production raises ImproperlyConfigured
    monkeypatch.setenv("DJANGO_SECRET_KEY", "prod-secret-key-1234567890")
    monkeypatch.delenv("INTERNAL_SERVICE_SECRET", raising=False)
    with pytest.raises(ImproperlyConfigured, match="INTERNAL_SERVICE_SECRET"):
        importlib.reload(config.settings)

    # Clean reload in dev mode so subsequent tests run normally
    monkeypatch.setenv("DJANGO_DEBUG", "True")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "django-insecure-test")
    monkeypatch.setenv("INTERNAL_SERVICE_SECRET", "cricpulse-internal-secret-2026")
    importlib.reload(config.settings)
