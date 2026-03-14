from django.db import models
from apps.core.models import ProjectScopedModel

SOURCE_TYPE_CHOICES = [
    ('interview_transcript', 'Interview Transcript'),
    ('support_ticket', 'Support Ticket'),
    ('slack_thread', 'Slack Thread'),
    ('feature_request', 'Feature Request'),
    ('analytics_event', 'Analytics Event'),
    ('nps_survey', 'NPS Survey'),
    ('churn_feedback', 'Churn Feedback'),
    ('session_replay', 'Session Replay Metadata'),
    ('custom', 'Custom'),
]


class DataSource(ProjectScopedModel):
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPE_CHOICES)
    description = models.TextField(blank=True)
    config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    evidence_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'data_sources'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.source_type})"
