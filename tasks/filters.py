from django_filters import rest_framework as filters

from projects.models import Project

from .models import Task


def my_projects(request):
    return Project.objects.for_user(request.user)


class TaskFilter(filters.FilterSet):
    # Limited to my projects, so ids of other projects are not revealed
    project = filters.ModelChoiceFilter(queryset=my_projects)

    class Meta:
        model = Task
        fields = ["status", "priority", "assignee"]
