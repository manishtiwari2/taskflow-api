from rest_framework import serializers

from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id",
            "project",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "due_date",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_by"]

    def validate_project(self, project):
        # Same message as an unknown id, so we do not reveal other users' projects
        if not project.is_member(self.context["request"].user):
            raise serializers.ValidationError(
                f'Invalid pk "{project.pk}" - object does not exist.'
            )
        return project

    def validate(self, attrs):
        project = attrs.get("project") or self.instance.project
        if self.instance and project != self.instance.project:
            raise serializers.ValidationError(
                {"project": "A task cannot be moved to another project."}
            )

        assignee = attrs.get("assignee")
        if assignee and not project.is_member(assignee):
            raise serializers.ValidationError(
                {"assignee": "Assignee must be a member of the project."}
            )
        return attrs
