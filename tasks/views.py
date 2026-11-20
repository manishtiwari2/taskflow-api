from rest_framework import viewsets

from projects.models import Project

from .filters import TaskFilter
from .models import Task
from .serializers import TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    # Placeholder so the API docs can find the model; see get_queryset
    queryset = Task.objects.none()
    serializer_class = TaskSerializer
    filterset_class = TaskFilter
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "due_date", "status"]

    def get_queryset(self):
        # Non-members get 404 because the task is not in their queryset
        return Task.objects.filter(
            project__in=Project.objects.for_user(self.request.user)
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
