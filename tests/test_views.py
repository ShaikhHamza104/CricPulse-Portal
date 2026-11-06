from unittest.mock import MagicMock, patch
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
class TestPublicAndShowcaseViews:
    def test_home_page_renders_successfully(self, client):
        home_url = reverse("portal:home")
        response = client.get(home_url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "CricPulse" in content
        assert "IPL Analytics" in content

    def test_docs_page_renders_successfully(self, client):
        docs_url = reverse("portal:docs")
        response = client.get(docs_url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Developer Documentation" in content
        assert "/api/v1/analytics/head-to-head" in content

    def test_pricing_page_renders_successfully(self, client):
        pricing_url = reverse("portal:pricing")
        response = client.get(pricing_url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Predictable plans" in content
        assert "Developer Free" in content
        assert "Pro Tier" in content
        assert "Enterprise Scale" in content
        assert "Full Plan Comparison Matrix" in content

    @patch("apps.analytics.views.get_engine_client")
    def test_analytics_showcase_tabs_render_without_crash(self, mock_get_client, client):
        mock_client = MagicMock()

        def mock_get(url, params=None):
            resp = MagicMock()
            resp.status_code = 200
            if "orange-cap" in url:
                resp.json.return_value = [
                    {"player_name": "Virat Kohli", "runs": 741, "balls": 480, "strike_rate": 154.37}
                ]
            elif "purple-cap" in url:
                resp.json.return_value = [
                    {"player_name": "Harshal Patel", "wickets": 24, "overs": "49.0", "economy": 9.15}
                ]
            elif "players/" in url:
                resp.json.return_value = {
                    "id": 1,
                    "name": "Virat Kohli",
                    "total_runs": 8004,
                    "strike_rate": 131.97,
                    "wickets": 4,
                    "economy": 8.8,
                }
            elif "players" in url:
                resp.json.return_value = {
                    "items": [
                        {"id": 1, "name": "Virat Kohli", "total_runs": 8004, "strike_rate": 131.97}
                    ]
                }
            else:
                resp.json.return_value = {
                    "team1": "CSK",
                    "team2": "MI",
                    "total_matches": 36,
                    "team1_wins": 16,
                    "team2_wins": 20,
                    "team1_win_pct": 44.4,
                    "team2_win_pct": 55.6,
                }
            return resp

        mock_client.get.side_effect = mock_get
        mock_client.__enter__.return_value = mock_client
        mock_get_client.return_value = mock_client

        showcase_url = reverse("analytics:showcase")

        # Rivalry tab
        resp_rivalry = client.get(showcase_url, {"tab": "rivalry", "team1": "CSK", "team2": "MI"})
        assert resp_rivalry.status_code == 200
        assert "CSK" in resp_rivalry.content.decode()

        # Caps tab
        resp_caps = client.get(showcase_url, {"tab": "caps", "season": "2024"})
        assert resp_caps.status_code == 200

        # Player tab
        resp_player = client.get(showcase_url, {"tab": "player", "player": "Kohli"})
        assert resp_player.status_code == 200

    @patch("httpx.Client.get")
    def test_live_query_proxy_handles_requests(self, mock_get, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"X-Process-Time": "0.0120s"}
        mock_resp.json.return_value = {"status": "ok", "version": "1.0.0"}
        mock_get.return_value = mock_resp

        proxy_url = reverse("analytics:proxy")
        response = client.get(proxy_url, {"endpoint": "/health"})
        assert response.status_code == 200
        data = response.json()
        assert data["status_code"] == 200
        assert data["process_time"] == "0.0120s"
        assert data["data"]["status"] == "ok"

    def test_dashboard_displays_enterprise_rate_limit_for_admin(self, client):
        admin_user = User.objects.create_superuser(
            username="test_admin_rate@cricpulse.io",
            email="admin_rate@cricpulse.io",
            password="pass",
        )
        from apps.portal.models import APIKey
        APIKey.objects.create(
            user=admin_user,
            name="Admin Key",
            tier="enterprise",
            rate_limit_per_minute=1200,
        )

        client.force_login(admin_user)
        dashboard_url = reverse("portal:dashboard")
        resp = client.get(dashboard_url)
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "1200 req/min" in content
        assert "Enterprise" in content
