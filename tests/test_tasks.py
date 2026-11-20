from projects.models import Project
from tasks.models import Task

LIST_URL = "/api/v1/tasks/"


def detail_url(task):
    return f"{LIST_URL}{task.pk}/"


def test_member_creates_task(as_user, project, member):
    response = as_user(member).post(
        LIST_URL, {"project": project.id, "title": "Fix bug", "priority": "high"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["created_by"] == member.id
    assert body["status"] == "todo"
    assert body["priority"] == "high"


def test_cannot_create_task_in_someone_elses_project(as_user, project, outsider):
    response = as_user(outsider).post(
        LIST_URL, {"project": project.id, "title": "Sneaky"}
    )

    assert response.status_code == 400
    assert not Task.objects.filter(title="Sneaky").exists()


def test_list_shows_only_tasks_from_my_projects(as_user, task, outsider):
    other = Project.objects.create(name="Other", owner=outsider)
    Task.objects.create(project=other, title="Hidden", created_by=outsider)

    results = as_user(task.created_by).get(LIST_URL).json()["results"]
    titles = [t["title"] for t in results]

    assert titles == ["Write docs"]


def test_non_member_gets_404(as_user, task, outsider):
    client = as_user(outsider)

    assert client.get(detail_url(task)).status_code == 404
    assert client.patch(detail_url(task), {"title": "x"}).status_code == 404
    assert client.delete(detail_url(task)).status_code == 404


def test_member_can_update_and_delete(as_user, task, member):
    client = as_user(member)

    updated = client.patch(detail_url(task), {"status": "done"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "done"

    assert client.delete(detail_url(task)).status_code == 204
    assert not Task.objects.filter(pk=task.pk).exists()


def test_assignee_must_be_project_member(as_user, task, owner, outsider):
    response = as_user(owner).patch(detail_url(task), {"assignee": outsider.id})

    assert response.status_code == 400
    assert "assignee" in response.json()


def test_assignee_can_be_project_member(as_user, task, owner, member):
    response = as_user(owner).patch(detail_url(task), {"assignee": member.id})

    assert response.status_code == 200
    assert response.json()["assignee"] == member.id


def test_owner_counts_as_member_for_assignment(as_user, project, owner, member):
    response = as_user(member).post(
        LIST_URL, {"project": project.id, "title": "Review", "assignee": owner.id}
    )

    assert response.status_code == 201


def test_task_cannot_move_to_another_project(as_user, task, owner):
    other = Project.objects.create(name="Other", owner=owner)

    response = as_user(owner).patch(detail_url(task), {"project": other.id})

    assert response.status_code == 400
    assert "project" in response.json()


def test_invalid_status_is_rejected(as_user, project, owner):
    response = as_user(owner).post(
        LIST_URL, {"project": project.id, "title": "Bad", "status": "waiting"}
    )

    assert response.status_code == 400
    assert "status" in response.json()
