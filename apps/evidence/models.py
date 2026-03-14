from django.db import models
from apps.core.models import ProjectScopedModel

EVIDENCE_TYPE_CHOICES = [
    ('support_ticket', 'Support Ticket'),
    ('interview_transcript', 'Interview Transcript'),
    ('feature_request', 'Feature Request'),
    ('nps_survey', 'NPS Survey'),
    ('churn_feedback', 'Churn Feedback'),
    ('slack_thread', 'Slack Thread'),
    ('analytics_event', 'Analytics Event'),
    ('session_replay', 'Session Replay'),
    ('custom', 'Custom'),
]

SEGMENT_CHOICES = [
    ('enterprise', 'Enterprise'),
    ('mid_market', 'Mid-Market'),
    ('smb', 'SMB'),
    ('startup', 'Startup'),
    ('individual', 'Individual'),
    ('unknown', 'Unknown'),
]

SENTIMENT_CHOICES = [
    ('positive', 'Positive'),
    ('negative', 'Negative'),
    ('neutral', 'Neutral'),
    ('mixed', 'Mixed'),
]


class RawEvidence(ProjectScopedModel):
    """Raw unprocessed evidence from any data source."""
    data_source = models.ForeignKey(
        'datasources.DataSource', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='evidence'
    )
    evidence_type = models.CharField(max_length=50, choices=EVIDENCE_TYPE_CHOICES)
    title = models.CharField(max_length=500, blank=True)
    text = models.TextField()
    customer_segment = models.CharField(max_length=50, choices=SEGMENT_CHOICES, default='unknown')
    source_name = models.CharField(max_length=100, blank=True, help_text="e.g., zendesk, intercom")
    sentiment = models.CharField(max_length=20, choices=SENTIMENT_CHOICES, default='neutral')
    urgency = models.IntegerField(default=5, help_text="1-10 scale")
    metadata = models.JSONField(default=dict, blank=True)

    # AI-extracted fields
    summary = models.TextField(blank=True)
    pain_points = models.JSONField(default=list, blank=True)
    key_quotes = models.JSONField(default=list, blank=True)
    topics = models.JSONField(default=list, blank=True)

    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'raw_evidence'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.evidence_type}] {self.title or self.text[:60]}"


class EvidenceAttachment(ProjectScopedModel):
    """File attachments for evidence."""
    evidence = models.ForeignKey(RawEvidence, on_delete=models.CASCADE, related_name='attachments')
    file_name = models.CharField(max_length=255)
    file_url = models.URLField(blank=True)
    file_type = models.CharField(max_length=50, blank=True)
    content_text = models.TextField(blank=True, help_text="Extracted text content")

    class Meta:
        db_table = 'evidence_attachments'
