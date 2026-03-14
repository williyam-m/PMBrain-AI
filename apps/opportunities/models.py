from django.db import models
from apps.core.models import ProjectScopedModel

STATUS_CHOICES = [
    ('discovered', 'Discovered'),
    ('evaluating', 'Evaluating'),
    ('approved', 'Approved'),
    ('in_progress', 'In Progress'),
    ('shipped', 'Shipped'),
    ('rejected', 'Rejected'),
]


class Opportunity(ProjectScopedModel):
    """A product opportunity identified from insights."""
    title = models.CharField(max_length=500)
    problem_statement = models.TextField()
    affected_segments = models.JSONField(default=list, blank=True)
    proposed_solution = models.TextField(blank=True)
    assumptions = models.JSONField(default=list, blank=True)
    risks = models.JSONField(default=list, blank=True)
    alternatives = models.JSONField(default=list, blank=True)
    implementation_outline = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='discovered')

    # Relations
    supporting_insights = models.ManyToManyField(
        'insights.InsightCluster', blank=True, related_name='opportunities'
    )
    evidence_refs = models.ManyToManyField(
        'evidence.RawEvidence', blank=True, related_name='opportunities'
    )

    class Meta:
        db_table = 'opportunities'
        verbose_name_plural = 'Opportunities'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def total_score(self):
        score = self.scores.first()
        if score:
            return score.total_score
        return 0


class OpportunityScore(ProjectScopedModel):
    """Scoring for an opportunity with customizable weights."""
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='scores')
    frequency_score = models.FloatField(default=0, help_text="0-10")
    revenue_impact = models.FloatField(default=0, help_text="0-10")
    retention_impact = models.FloatField(default=0, help_text="0-10")
    strategic_alignment = models.FloatField(default=0, help_text="0-10")
    effort_estimate = models.FloatField(default=0, help_text="0-10, higher = more effort")
    confidence_score = models.FloatField(default=0, help_text="0-1")

    # Computed
    total_score = models.FloatField(default=0)

    # Custom weights used
    weights_used = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'opportunity_scores'
        ordering = ['-total_score']

    def calculate_score(self, weights=None):
        if not weights:
            weights = self.opportunity.project.get_scoring_weights()

        self.weights_used = weights
        self.total_score = (
            weights.get('frequency', 0.25) * self.frequency_score +
            weights.get('revenue', 0.25) * self.revenue_impact +
            weights.get('retention', 0.20) * self.retention_impact +
            weights.get('alignment', 0.15) * self.strategic_alignment -
            weights.get('effort', 0.15) * self.effort_estimate
        )
        self.save()
        return self.total_score

    def __str__(self):
        return f"Score for {self.opportunity.title}: {self.total_score:.2f}"


class OutcomeMetric(ProjectScopedModel):
    """Post-launch tracking for shipped opportunities."""
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='outcomes')
    metric_type = models.CharField(max_length=50, choices=[
        ('adoption', 'Adoption'),
        ('retention', 'Retention'),
        ('revenue', 'Revenue'),
        ('engagement', 'Engagement'),
        ('support_tickets', 'Support Tickets'),
    ])
    predicted_value = models.FloatField(default=0)
    actual_value = models.FloatField(null=True, blank=True)
    measured_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'outcome_metrics'
        ordering = ['-created_at']
