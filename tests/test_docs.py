from rest_framework.test import APIClient

EXPECTED_PATHS = [
    "/api/health/",
    "/api/v1/auth/register/",
    "/api/v1/auth/token/",
    "/api/v1/auth/token/refresh/",
    "/api/v1/auth/me/",
    "/api/v1/projects/",
    "/api/v1/projects/{id}/",
    "/api/v1/projects/{id}/members/",
    "/api/v1/tasks/",
    "/api/v1/tasks/{id}/",
]


def test_schema_lists_every_endpoint_for_anonymous_users(db):
    response = APIClient().get("/api/schema/?format=json")

    assert response.status_code == 200
    assert set(EXPECTED_PATHS) <= set(response.json()["paths"])


def test_swagger_ui_is_public(db):
    response = APIClient().get("/api/docs/")

    assert response.status_code == 200
