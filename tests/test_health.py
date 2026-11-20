from unittest.mock import patch

from django.db.utils import OperationalError


def test_health_ok(client, db):
    response = client.get("/api/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_returns_503_when_database_is_down(client):
    with patch("core.views.connection.ensure_connection", side_effect=OperationalError):
        response = client.get("/api/health/")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "down"}
