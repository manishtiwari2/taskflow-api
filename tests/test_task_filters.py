import pytest

from projects.models import Project
from tasks.models import Task

LIST_URL = "/api/v1/tasks/"


@pytest.fixture
def tasks(project, owner, member):
    def make(**fields):
        return Task.objects.create(project=project, created_by=owner, **fields)

    return {
        "bug": make(title="Fix login bug", status="todo", priority="high"),
        "docs": make(
            title="Write docs",
            status="done",
            priority="low",
            assignee=member,
            due_date="2030-01-01",
        ),
        "deploy": make(title="Deploy app", status="in_progress", due_date="2030-06-01"),
    }


def get_titles(client, query=""):
    response = client.get(f"{LIST_URL}{query}")
    assert response.status_code == 200
    return [t["title"] for t in response.json()["results"]]


def test_list_is_paginated(as_user, project, owner):
    Task.objects.bulk_create(
        Task(project=project, title=f"T{i}", created_by=owner) for i in range(21)
    )

    body = as_user(owner).get(LIST_URL).json()

    assert body["count"] == 21
    assert len(body["results"]) == 20
    assert body["next"] is not None


def test_filter_by_status(as_user, owner, tasks):
    assert get_titles(as_user(owner), "?status=done") == ["Write docs"]


def test_filter_by_priority(as_user, owner, tasks):
    assert get_titles(as_user(owner), "?priority=high") == ["Fix login bug"]


def test_filter_by_assignee(as_user, owner, member, tasks):
    assert get_titles(as_user(owner), f"?assignee={member.id}") == ["Write docs"]


def test_filter_by_project(as_user, owner, project, tasks):
    other = Project.objects.create(name="Other", owner=owner)
    Task.objects.create(project=other, title="Elsewhere", created_by=owner)

    assert get_titles(as_user(owner), f"?project={other.id}") == ["Elsewhere"]
    assert len(get_titles(as_user(owner), f"?project={project.id}")) == 3


def test_filter_by_someone_elses_project_is_rejected(as_user, project, outsider):
    response = as_user(outsider).get(f"{LIST_URL}?project={project.id}")

    assert response.status_code == 400


def test_search_matches_title(as_user, owner, tasks):
    assert get_titles(as_user(owner), "?search=deploy") == ["Deploy app"]


def test_ordering_by_due_date(as_user, owner, tasks):
    # Postgres puts tasks without a due date last when ordering ascending
    titles = get_titles(as_user(owner), "?ordering=due_date")

    assert titles == ["Write docs", "Deploy app", "Fix login bug"]
