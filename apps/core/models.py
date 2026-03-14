"""
Core base models for PMBrain AI.
Every model inherits from these to ensure tenant isolation and auditability.
"""
import uuid
from django.db import models
from django.conf import settings


class TimeStampedModel(models.Model):
    """Abstract base with timestamps."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']


class TenantModel(TimeStampedModel):
    """Abstract base with multi-tenant fields."""
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        db_index=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='%(class)ss_created'
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']


class ProjectScopedModel(TenantModel):
    """Abstract base scoped to a project within an organization."""
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        db_index=True
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']
