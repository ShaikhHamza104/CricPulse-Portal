import dj_database_url


def test_database_url_parsing_for_postgresql():
    dummy_pg_url = "postgresql://user:pass@ep-cool-db.us-east-1.render.com:5432/cricpulse_portal"
    config = dj_database_url.config(default=dummy_pg_url, conn_max_age=600)

    assert "django.db.backends.postgresql" in config["ENGINE"]
    assert config["NAME"] == "cricpulse_portal"
    assert config["USER"] == "user"
    assert config["PASSWORD"] == "pass"
    assert config["HOST"] == "ep-cool-db.us-east-1.render.com"
    assert config["PORT"] == 5432
    assert config["CONN_MAX_AGE"] == 600
