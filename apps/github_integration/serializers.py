"""
Serializers for GitHub Integration.
SECURITY: Never expose access tokens in any API response.
"""
from rest_framework import serializers
from .models import GitHubIntegration, GitHubRepository


class GitHubIntegrationSerializer(serializers.ModelSerializer):
    """Public serializer — never exposes the access token."""

    class Meta:
        model = GitHubIntegration
        fields = [
            'id', 'github_user_id', 'github_username', 'avatar_url',
            'scopes', 'connected_at', 'is_active',
            'organization', 'created_at',
        ]
        read_only_fields = [
            'id', 'github_user_id', 'github_username', 'avatar_url',
            'scopes', 'connected_at', 'is_active', 'organization', 'created_at',
        ]


class GitHubRepositorySerializer(serializers.ModelSerializer):
    analysis_status = serializers.SerializerMethodField()
    codebase_id = serializers.SerializerMethodField()

    class Meta:
        model = GitHubRepository
        fields = [
            'id', 'repo_name', 'repo_full_name', 'repo_url', 'default_branch',
            'description', 'language', 'stars', 'is_private',
            'clone_status', 'last_cloned_at', 'clone_error',
            'analysis_status', 'codebase_id',
            'organization', 'project', 'connected_by',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'repo_name', 'repo_full_name', 'clone_status',
            'last_cloned_at', 'clone_error',
            'analysis_status', 'codebase_id',
            'organization', 'connected_by', 'created_at', 'updated_at',
        ]

    def get_analysis_status(self, obj):
        if obj.codebase:
            analysis = obj.codebase.analyses.first()
            if analysis:
                return analysis.status
        return None

    def get_codebase_id(self, obj):
        return str(obj.codebase_id) if obj.codebase_id else None


class LinkRepoSerializer(serializers.Serializer):
    """Validates repo link request."""
    project_id = serializers.UUIDField()
    repo_url = serializers.URLField()

    def validate_repo_url(self, value):
        """Validate it looks like a GitHub URL."""
        import re
        pattern = r'^https?://github\.com/([a-zA-Z0-9._-]+)/([a-zA-Z0-9._-]+)/?$'
        if not re.match(pattern, value.rstrip('.git')):
            raise serializers.ValidationError(
                "Invalid GitHub repository URL. Expected format: https://github.com/owner/repo"
            )
        return value.rstrip('/')


class GitHubRepoListItemSerializer(serializers.Serializer):
    """Serializes repo data from GitHub API (not a model serializer)."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    full_name = serializers.CharField()
    html_url = serializers.URLField()
    description = serializers.CharField(allow_null=True, allow_blank=True, default='')
    language = serializers.CharField(allow_null=True, allow_blank=True, default='')
    stargazers_count = serializers.IntegerField(default=0)
    default_branch = serializers.CharField(default='main')
    private = serializers.BooleanField(default=False)
    clone_url = serializers.URLField()
    already_linked = serializers.BooleanField(default=False, required=False)
