from rest_framework.test import APIClient

from projects.models import Project

LIST_URL = "/api/v1/projects/"


def detail_url(project):
    return f"{LIST_URL}{project.pk}/"


def members_url(project):
    return f"{detail_url(project)}members/"


def test_anonymous_gets_401(db):
    assert APIClient().get(LIST_URL).status_code == 401


def test_create_sets_owner_from_request(as_user, owner):
    response = as_user(owner).post(LIST_URL, {"name": "New", "owner": 999})

    assert response.status_code == 201
    assert response.json()["owner"] == owner.id


def test_list_shows_only_my_projects(as_user, project, owner, member, outsider):
    Project.objects.create(name="Secret", owner=outsider)

    for user in (owner, member):
        names = [p["name"] for p in as_user(user).get(LIST_URL).json()]
        assert names == ["Website"]


def test_non_member_gets_404(as_user, project, outsider):
    client = as_user(outsider)

    assert client.get(detail_url(project)).status_code == 404
    assert client.patch(detail_url(project), {"name": "x"}).status_code == 404
    assert client.delete(detail_url(project)).status_code == 404


def test_owner_can_update(as_user, project, owner):
    response = as_user(owner).patch(detail_url(project), {"name": "Renamed"})

    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"


def test_member_can_read_but_not_update(as_user, project, member):
    client = as_user(member)

    assert client.get(detail_url(project)).status_code == 200
    assert client.patch(detail_url(project), {"name": "x"}).status_code == 403


def test_non_owner_cannot_delete_project(as_user, project, member):
    response = as_user(member).delete(detail_url(project))

    assert response.status_code == 403
    assert Project.objects.filter(pk=project.pk).exists()


def test_owner_can_delete_project(as_user, project, owner):
    response = as_user(owner).delete(detail_url(project))

    assert response.status_code == 204
    assert not Project.objects.filter(pk=project.pk).exists()


def test_owner_can_add_member(as_user, project, owner, outsider):
    response = as_user(owner).post(members_url(project), {"user_id": outsider.id})

    assert response.status_code == 200
    assert outsider.id in response.json()["members"]
    assert project.is_member(outsider)


def test_add_member_rejects_unknown_user(as_user, project, owner):
    response = as_user(owner).post(members_url(project), {"user_id": 99999})

    assert response.status_code == 400


def test_member_cannot_manage_members(as_user, project, member, outsider):
    response = as_user(member).post(members_url(project), {"user_id": outsider.id})

    assert response.status_code == 403
    assert not project.is_member(outsider)


def test_non_member_gets_404_on_members(as_user, project, outsider):
    response = as_user(outsider).post(members_url(project), {"user_id": outsider.id})

    assert response.status_code == 404


def test_owner_can_remove_member_and_tasks_are_unassigned(
    as_user, project, task, owner, member
):
    task.assignee = member
    task.save()

    response = as_user(owner).delete(members_url(project), {"user_id": member.id})

    assert response.status_code == 204
    assert not project.is_member(member)
    task.refresh_from_db()
    assert task.assignee is None
