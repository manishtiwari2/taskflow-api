from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Project
from .permissions import IsOwnerOrReadOnly
from .serializers import MemberSerializer, ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        # Non-members get 404 because the project is not in their queryset
        # prefetch members: one extra query instead of one per project (N+1)
        return Project.objects.for_user(self.request.user).prefetch_related("members")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post", "delete"])
    def members(self, request, pk=None):
        project = self.get_object()
        serializer = MemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        if request.method == "POST":
            project.members.add(user)
            return Response(ProjectSerializer(project).data)

        project.members.remove(user)
        # A task assignee must be a member, so unassign the removed user
        project.tasks.filter(assignee=user).update(assignee=None)
        return Response(status=status.HTTP_204_NO_CONTENT)
