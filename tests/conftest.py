import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from accounts.models import User
from projects.models import Project
from tasks.models import Task

PASSWORD = "StrongPass123!"


@pytest.fixture(autouse=True)
def fast_password_hasher(settings):
    # The default hasher is slow on purpose, which makes tests crawl
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture(autouse=True)
def clear_cache():
    # Throttle counters live in the cache and must not leak between tests
    cache.clear()


@pytest.fixture
def make_user(db):
    def _make(username):
        return User.objects.create_user(
            username=username, email=f"{username}@example.com", password=PASSWORD
        )

    return _make


@pytest.fixture
def as_user():
    """Return an API client logged in as the given user."""

    def _as_user(user):
        client = APIClient()
        client.force_authenticate(user)
        return client

    return _as_user


@pytest.fixture
def owner(make_user):
    return make_user("owner")


@pytest.fixture
def member(make_user):
    return make_user("member")


@pytest.fixture
def outsider(make_user):
    return make_user("outsider")


@pytest.fixture
def project(owner, member):
    project = Project.objects.create(name="Website", owner=owner)
    project.members.add(member)
    return project


@pytest.fixture
def task(project, owner):
    return Task.objects.create(project=project, title="Write docs", created_by=owner)
