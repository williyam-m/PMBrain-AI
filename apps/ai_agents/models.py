from django.db import models
from apps.core.models import ProjectScopedModel

AGENT_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('running', 'Running'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
]

AGENT_TYPE_CHOICES = [
    ('evidence_summarizer', 'Evidence Summarizer'),
    ('insight_clustering', 'Insight Clustering'),
    ('opportunity_discovery', 'Opportunity Discovery'),
    ('opportunity_scoring', 'Opportunity Scoring'),
    ('spec_generator', 'Spec Generator'),
    ('impact_prediction', 'Impact Prediction'),
    ('what_to_build', 'What To Build Next'),
    ('spec_chat', 'Spec Conversational Edit'),
    ('code_understanding', 'Code Understanding'),
    ('market_trend', 'Market Trend Analysis'),
    ('feature_discovery', 'Feature Discovery'),
]


class AgentRun(ProjectScopedModel):
    """Track every AI agent execution for auditability."""
    agent_type = models.CharField(max_length=50, choices=AGENT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=AGENT_STATUS_CHOICES, default='pending')
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)
    tokens_used = models.IntegerField(default=0)

    class Meta:
        db_table = 'agent_runs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.agent_type} - {self.status}"


class ProductPrompt(ProjectScopedModel):
    """Versioned prompts for AI agents."""
    agent_type = models.CharField(max_length=50, choices=AGENT_TYPE_CHOICES)
    name = models.CharField(max_length=255)
    prompt_template = models.TextField()
    version = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'product_prompts'
        ordering = ['-version']
        unique_together = ('project', 'agent_type', 'version')

    def __str__(self):
        return f"{self.name} v{self.version}"
