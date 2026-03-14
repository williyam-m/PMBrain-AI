import uuid
from django.db import models
from django.conf import settings


ROLE_CHOICES = [
    ('org-owner', 'Organization Owner'),
    ('product-manager', 'Product Manager'),
    ('engineer', 'Engineer'),
    ('reviewer', 'Reviewer'),
]


class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=100)
    description = models.TextField(blank=True)
    logo_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organizations'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class OrgMembership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='reviewer')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'org_memberships'
        unique_together = ('organization', 'user')

    def __str__(self):
        return f"{self.user.email} - {self.role} @ {self.organization.name}"
