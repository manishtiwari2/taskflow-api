import pytest
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle


@pytest.fixture
def low_rate(monkeypatch):
    def _set(scope):
        monkeypatch.setitem(SimpleRateThrottle.THROTTLE_RATES, scope, "2/min")

    return _set


def test_anonymous_requests_are_throttled(db, low_rate):
    low_rate("anon")
    client = APIClient()

    codes = [client.get("/api/health/").status_code for _ in range(3)]

    assert codes == [200, 200, 429]


def test_logged_in_requests_are_throttled(as_user, owner, low_rate):
    low_rate("user")
    client = as_user(owner)

    codes = [client.get("/api/v1/auth/me/").status_code for _ in range(3)]

    assert codes == [200, 200, 429]
