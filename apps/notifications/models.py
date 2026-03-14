import uuid
from django.db import models
from django.conf import settings


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    organization = models.ForeignKey(
        'organizations.Organization', on_delete=models.CASCADE,
        null=True, blank=True
    )
    notification_type = models.CharField(max_length=50, choices=[
        ('opportunity_discovered', 'Opportunity Discovered'),
        ('spec_ready', 'Spec Ready for Review'),
        ('approval_requested', 'Approval Requested'),
        ('impact_report', 'Impact Report Generated'),
        ('agent_completed', 'Agent Completed'),
        ('comment_added', 'Comment Added'),
        ('mention', 'Mentioned'),
    ])
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    entity_type = models.CharField(max_length=50, blank=True)
    entity_id = models.UUIDField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type}: {self.title}"
