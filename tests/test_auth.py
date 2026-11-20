from rest_framework.test import APIClient

from accounts.models import User

from .conftest import PASSWORD

REGISTER_URL = "/api/v1/auth/register/"
TOKEN_URL = "/api/v1/auth/token/"
REFRESH_URL = "/api/v1/auth/token/refresh/"
ME_URL = "/api/v1/auth/me/"


def register_payload(**overrides):
    payload = {"username": "ann", "email": "ann@example.com", "password": PASSWORD}
    return payload | overrides


def test_register_creates_user_with_hashed_password(db):
    response = APIClient().post(REGISTER_URL, register_payload())

    assert response.status_code == 201
    assert "password" not in response.json()
    user = User.objects.get(username="ann")
    assert user.password != PASSWORD
    assert user.check_password(PASSWORD)


def test_register_rejects_weak_password(db):
    response = APIClient().post(REGISTER_URL, register_payload(password="123"))

    assert response.status_code == 400
    assert "password" in response.json()


def test_register_rejects_duplicate_email(db, owner):
    response = APIClient().post(
        REGISTER_URL, register_payload(email=owner.email, username="other")
    )

    assert response.status_code == 400
    assert "email" in response.json()


def test_token_and_me_flow(owner):
    client = APIClient()
    token = client.post(TOKEN_URL, {"username": "owner", "password": PASSWORD})
    assert token.status_code == 200

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.json()['access']}")
    me = client.get(ME_URL)

    assert me.status_code == 200
    assert me.json()["username"] == "owner"


def test_token_rejects_wrong_password(owner):
    response = APIClient().post(TOKEN_URL, {"username": "owner", "password": "bad"})

    assert response.status_code == 401


def test_refresh_returns_new_access_token(owner):
    client = APIClient()
    tokens = client.post(TOKEN_URL, {"username": "owner", "password": PASSWORD}).json()

    response = client.post(REFRESH_URL, {"refresh": tokens["refresh"]})

    assert response.status_code == 200
    assert "access" in response.json()


def test_me_requires_login(db):
    assert APIClient().get(ME_URL).status_code == 401
