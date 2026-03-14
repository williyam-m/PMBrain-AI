from django.db import models
from apps.core.models import TenantModel


class Project(TenantModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100)
    description = models.TextField(blank=True)
    product_context = models.TextField(blank=True, help_text="What is this product? Who are the users?")
    goals = models.JSONField(default=list, blank=True, help_text="Strategic goals")
    is_active = models.BooleanField(default=True)

    # Scoring weights (customizable per project)
    scoring_weights = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'projects'
        unique_together = ('organization', 'slug')
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_scoring_weights(self):
        defaults = {
            'frequency': 0.25,
            'revenue': 0.25,
            'retention': 0.20,
            'alignment': 0.15,
            'effort': 0.15,
        }
        defaults.update(self.scoring_weights or {})
        return defaults
