"""
Codebase models for product code analysis.
Allows uploading and analyzing product codebases for AI-driven feature discovery.
"""
import uuid
from django.db import models
from django.conf import settings
from apps.core.models import ProjectScopedModel

SOURCE_TYPE_CHOICES = [
    ('zip', 'ZIP Upload'),
    ('tar', 'TAR.GZ Upload'),
    ('git', 'Git Repository'),
]

ANALYSIS_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('processing', 'Processing'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
]


class Codebase(ProjectScopedModel):
    """Uploaded product codebase for analysis."""
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES, default='zip')
    storage_path = models.CharField(max_length=500, blank=True)
    git_url = models.URLField(blank=True, null=True)
    file_size_bytes = models.BigIntegerField(default=0)
    file_count = models.IntegerField(default=0)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='uploaded_codebases'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'codebases'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.source_type})"


class CodebaseAnalysis(ProjectScopedModel):
    """AI-generated analysis of a codebase."""
    codebase = models.ForeignKey(Codebase, on_delete=models.CASCADE, related_name='analyses')
    status = models.CharField(max_length=20, choices=ANALYSIS_STATUS_CHOICES, default='pending')

    # AI-generated structured analysis
    system_summary = models.TextField(blank=True)
    major_modules = models.JSONField(default=list, blank=True)
    existing_features = models.JSONField(default=list, blank=True)
    api_endpoints = models.JSONField(default=list, blank=True)
    database_models = models.JSONField(default=list, blank=True)
    capability_map = models.JSONField(default=dict, blank=True)
    technology_stack = models.JSONField(default=list, blank=True)
    architecture_patterns = models.JSONField(default=list, blank=True)

    # Enhanced analysis fields (v2)
    missing_capabilities = models.JSONField(default=list, blank=True)
    improvement_areas = models.JSONField(default=list, blank=True)
    competitor_comparison = models.JSONField(default=dict, blank=True,
        help_text="Competitor feature comparison data")
    new_feature_opportunities = models.JSONField(default=list, blank=True,
        help_text="AI-suggested new features based on codebase analysis")

    # Raw file structure
    file_structure = models.JSONField(default=dict, blank=True)
    code_samples = models.JSONField(default=dict, blank=True,
        help_text="Key code snippets used for analysis")

    error_message = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'codebase_analyses'
        ordering = ['-created_at']

    def __str__(self):
        return f"Analysis of {self.codebase.name} - {self.status}"


class MarketTrend(ProjectScopedModel):
    """AI-generated market trend analysis."""
    trend_summary = models.TextField(blank=True)
    emerging_features = models.JSONField(default=list, blank=True)
    competitor_features = models.JSONField(default=list, blank=True)
    market_gap_opportunities = models.JSONField(default=list, blank=True)
    industry_trends = models.JSONField(default=list, blank=True)
    analysis_context = models.TextField(blank=True, help_text="Product context used for analysis")

    class Meta:
        db_table = 'market_trends'
        ordering = ['-created_at']

    def __str__(self):
        return f"Market Trend - {self.created_at}"


class FeatureDiscovery(ProjectScopedModel):
    """AI-discovered feature opportunities combining evidence, code, and trends."""
    feature_name = models.CharField(max_length=500)
    problem_statement = models.TextField()
    evidence_links = models.JSONField(default=list, blank=True)
    code_integration_points = models.JSONField(default=list, blank=True)
    implementation_complexity = models.CharField(max_length=20, choices=[
        ('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('very_high', 'Very High'),
    ], default='medium')
    execution_plan = models.TextField(blank=True)
    expected_impact = models.JSONField(default=dict, blank=True)
    trend_alignment = models.JSONField(default=dict, blank=True)
    source_type = models.CharField(max_length=50, choices=[
        ('evidence', 'Evidence-Driven'),
        ('code', 'Code-Aware'),
        ('trend', 'Trend-Driven'),
        ('combined', 'Combined Analysis'),
    ], default='combined')

    class Meta:
        db_table = 'feature_discoveries'
        ordering = ['-created_at']

    def __str__(self):
        return self.feature_name
