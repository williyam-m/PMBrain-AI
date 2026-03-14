from django.db import models
from apps.core.models import ProjectScopedModel

ARTIFACT_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('review', 'Review'),
    ('approved', 'Approved'),
    ('implementation', 'Implementation'),
    ('shipped', 'Shipped'),
]

ARTIFACT_TYPE_CHOICES = [
    ('prd', 'PRD'),
    ('user_stories', 'User Stories'),
    ('technical_spec', 'Technical Spec'),
    ('api_design', 'API Design'),
    ('qa_plan', 'QA Plan'),
]


class GeneratedArtifact(ProjectScopedModel):
    """A generated specification artifact."""
    opportunity = models.ForeignKey(
        'opportunities.Opportunity', on_delete=models.CASCADE,
        related_name='artifacts', null=True, blank=True
    )
    artifact_type = models.CharField(max_length=50, choices=ARTIFACT_TYPE_CHOICES)
    title = models.CharField(max_length=500)
    current_version = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=ARTIFACT_STATUS_CHOICES, default='draft')
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'generated_artifacts'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} (v{self.current_version})"

    @property
    def latest_version(self):
        return self.versions.first()

    @property
    def readiness_score(self):
        v = self.latest_version
        return v.readiness_score if v else 0


class ArtifactVersion(ProjectScopedModel):
    """Versioned content for artifacts."""
    artifact = models.ForeignKey(GeneratedArtifact, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField(default=1)
    content = models.JSONField(default=dict)
    change_summary = models.TextField(blank=True)
    readiness_score = models.FloatField(default=0)

    class Meta:
        db_table = 'artifact_versions'
        ordering = ['-version_number']
        unique_together = ('artifact', 'version_number')

    def __str__(self):
        return f"{self.artifact.title} v{self.version_number}"
