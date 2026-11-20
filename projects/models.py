from django.conf import settings
from django.db import models
from django.db.models import Q


class ProjectQuerySet(models.QuerySet):
    def for_user(self, user):
        # The owner is always treated as a member
        return self.filter(Q(owner=user) | Q(members=user)).distinct()


class Project(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="projects", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProjectQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def is_member(self, user):
        return self.owner_id == user.id or self.members.filter(pk=user.pk).exists()
