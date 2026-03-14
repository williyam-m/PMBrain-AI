from django.db import models
from apps.core.models import ProjectScopedModel

TREND_CHOICES = [
    ('rising', 'Rising'),
    ('stable', 'Stable'),
    ('declining', 'Declining'),
]

SEVERITY_CHOICES = [
    ('critical', 'Critical'),
    ('high', 'High'),
    ('medium', 'Medium'),
    ('low', 'Low'),
]


class InsightCluster(ProjectScopedModel):
    """AI-generated insight cluster from evidence."""
    title = models.CharField(max_length=500)
    summary = models.TextField()
    frequency = models.IntegerField(default=1, help_text="How often this appears")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    segments_affected = models.JSONField(default=list, blank=True)
    representative_quotes = models.JSONField(default=list, blank=True)
    trend_direction = models.CharField(max_length=20, choices=TREND_CHOICES, default='stable')
    confidence = models.FloatField(default=0.0, help_text="0-1 confidence score")
    topics = models.JSONField(default=list, blank=True)

    # Evidence references
    evidence_refs = models.ManyToManyField(
        'evidence.RawEvidence', blank=True, related_name='insight_clusters'
    )

    is_validated = models.BooleanField(default=False)

    class Meta:
        db_table = 'insight_clusters'
        ordering = ['-frequency', '-created_at']

    def __str__(self):
        return self.title


class InsightTrend(ProjectScopedModel):
    """Tracks how insights evolve over time."""
    insight = models.ForeignKey(InsightCluster, on_delete=models.CASCADE, related_name='trends')
    period = models.CharField(max_length=50, help_text="e.g., 2024-W01")
    mention_count = models.IntegerField(default=0)
    severity_score = models.FloatField(default=0.0)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'insight_trends'
        ordering = ['-period']
