"""
GitHub Integration models for PMBrain AI.
Handles OAuth connections, repository linking, and clone tracking.
Tokens are encrypted at rest using Fernet symmetric encryption.
"""
import uuid
import os
import logging
from cryptography.fernet import Fernet
from django.db import models
from django.conf import settings
from apps.core.models import TenantModel, ProjectScopedModel

logger = logging.getLogger('pmbrain')


def _get_fernet():
    """Get Fernet cipher for encrypting/decrypting tokens."""
    key = getattr(settings, 'GITHUB_ENCRYPTION_KEY', None) or os.getenv('GITHUB_ENCRYPTION_KEY', '')
    if not key:
        # Generate a stable key from SECRET_KEY if not configured
        import hashlib
        import base64
        h = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key = base64.urlsafe_b64encode(h)
    else:
        if isinstance(key, str):
            key = key.encode()
    return Fernet(key)


CLONE_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('cloning', 'Cloning'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
]


class GitHubIntegration(TenantModel):
    """
    Stores a user's GitHub OAuth connection within an organization.
    Access tokens are encrypted at rest.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='github_integrations'
    )
    github_user_id = models.BigIntegerField()
    github_username = models.CharField(max_length=255)
    avatar_url = models.URLField(blank=True, null=True)
    _access_token = models.BinaryField(
        db_column='access_token_encrypted',
        help_text='Fernet-encrypted GitHub OAuth token'
    )
    scopes = models.CharField(max_length=500, blank=True, default='repo,read:user,user:email')
    connected_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'github_integrations'
        unique_together = ('organization', 'user')
        ordering = ['-connected_at']

    def __str__(self):
        return f"{self.github_username} @ {self.organization.name}"

    @property
    def access_token(self):
        """Decrypt and return the access token."""
        if not self._access_token:
            return None
        try:
            f = _get_fernet()
            raw = bytes(self._access_token) if not isinstance(self._access_token, bytes) else self._access_token
            return f.decrypt(raw).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to decrypt GitHub token for user {self.user_id}: {e}")
            return None

    @access_token.setter
    def access_token(self, value):
        """Encrypt and store the access token."""
        if value:
            f = _get_fernet()
            self._access_token = f.encrypt(value.encode('utf-8'))
        else:
            self._access_token = None


class GitHubRepository(ProjectScopedModel):
    """
    A GitHub repository linked to a PMBrain project for code analysis.
    """
    integration = models.ForeignKey(
        GitHubIntegration, on_delete=models.CASCADE,
        related_name='repositories'
    )
    github_repo_id = models.BigIntegerField()
    repo_name = models.CharField(max_length=255)
    repo_full_name = models.CharField(max_length=500)
    repo_url = models.URLField()
    clone_url = models.URLField(blank=True)
    default_branch = models.CharField(max_length=255, default='main')
    description = models.TextField(blank=True)
    language = models.CharField(max_length=100, blank=True)
    stars = models.IntegerField(default=0)
    is_private = models.BooleanField(default=False)
    connected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='linked_repos'
    )
    is_active = models.BooleanField(default=True)

    # Clone tracking
    clone_status = models.CharField(
        max_length=20, choices=CLONE_STATUS_CHOICES, default='pending'
    )
    clone_path = models.CharField(max_length=500, blank=True)
    last_cloned_at = models.DateTimeField(null=True, blank=True)
    clone_error = models.TextField(blank=True)

    # Link to Codebase model for AI analysis
    codebase = models.ForeignKey(
        'codebase.Codebase', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='github_repos'
    )

    class Meta:
        db_table = 'github_repositories'
        unique_together = ('project', 'repo_full_name')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.repo_full_name} → {self.project.name}"
