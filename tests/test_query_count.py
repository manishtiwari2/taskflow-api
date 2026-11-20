from projects.models import Project
from tasks.models import Task


def test_project_list_query_count_does_not_grow(
    as_user, owner, member, outsider, django_assert_max_num_queries
):
    for i in range(10):
        project = Project.objects.create(name=f"P{i}", owner=owner)
        project.members.add(member, outsider)

    # count + projects + prefetched members, however many projects there are
    with django_assert_max_num_queries(3):
        response = as_user(owner).get("/api/v1/projects/")

    assert response.json()["count"] == 10


def test_task_list_query_count_does_not_grow(
    as_user, project, owner, django_assert_max_num_queries
):
    Task.objects.bulk_create(
        Task(project=project, title=f"T{i}", created_by=owner) for i in range(10)
    )

    with django_assert_max_num_queries(3):
        response = as_user(owner).get("/api/v1/tasks/")

    assert response.json()["count"] == 10
