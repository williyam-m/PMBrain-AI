from django.db import models
from django.conf import settings
from apps.core.models import TenantModel


class Comment(TenantModel):
    """Comments on any entity."""
    entity_type = models.CharField(max_length=50, help_text="e.g., opportunity, spec, insight")
    entity_id = models.UUIDField()
    text = models.TextField()
    mentions = models.JSONField(default=list, blank=True, help_text="User IDs mentioned")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    class Meta:
        db_table = 'comments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment on {self.entity_type}:{self.entity_id}"


class Approval(TenantModel):
    """Approval workflow for specs and opportunities."""
    entity_type = models.CharField(max_length=50)
    entity_id = models.UUIDField()
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('changes_requested', 'Changes Requested'),
    ], default='pending')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='approvals_given')
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'approvals'
        ordering = ['-created_at']


class ReviewRequest(TenantModel):
    """Review requests for specs."""
    entity_type = models.CharField(max_length=50)
    entity_id = models.UUIDField()
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_requests_sent')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_requests_received')
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ], default='pending')

    class Meta:
        db_table = 'review_requests'
        ordering = ['-created_at']
