from rest_framework import viewsets

from projects.models import Project

from .models import Task
from .serializers import TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer

    def get_queryset(self):
        # Non-members get 404 because the task is not in their queryset
        return Task.objects.filter(
            project__in=Project.objects.for_user(self.request.user)
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
