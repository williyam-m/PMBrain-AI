"""
Tests for GitHub Integration.
Covers: OAuth, repo validation, linking, permissions, project isolation, analysis trigger.
"""
import json
import uuid
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import Organization, OrgMembership
from apps.projects.models import Project
from .models import GitHubIntegration, GitHubRepository
from .services.github_api import parse_github_url, GitHubAPIClient, GitHubAPIError


class GitHubURLParsingTest(TestCase):
    """Test GitHub URL parsing utility."""

    def test_standard_url(self):
        owner, repo = parse_github_url('https://github.com/owner/repo')
        self.assertEqual(owner, 'owner')
        self.assertEqual(repo, 'repo')

    def test_url_with_git_suffix(self):
        owner, repo = parse_github_url('https://github.com/owner/repo.git')
        self.assertEqual(owner, 'owner')
        self.assertEqual(repo, 'repo')

    def test_url_with_trailing_slash(self):
        owner, repo = parse_github_url('https://github.com/owner/repo/')
        self.assertEqual(owner, 'owner')
        self.assertEqual(repo, 'repo')

    def test_invalid_url(self):
        with self.assertRaises(ValueError):
            parse_github_url('https://gitlab.com/owner/repo')

    def test_missing_repo(self):
        with self.assertRaises(ValueError):
            parse_github_url('https://github.com/owner')


class GitHubIntegrationModelTest(TestCase):
    """Test GitHub Integration model with token encryption."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.org = Organization.objects.create(name='Test Org', slug='test-org')
        OrgMembership.objects.create(organization=self.org, user=self.user, role='org-owner')

    def test_token_encryption_roundtrip(self):
        """Ensure tokens are encrypted and can be decrypted."""
        integration = GitHubIntegration(
            organization=self.org,
            user=self.user,
            github_user_id=12345,
            github_username='testgh',
            created_by=self.user,
        )
        integration.access_token = 'ghp_test_token_abc123'
        integration.save()

        # Reload from DB
        loaded = GitHubIntegration.objects.get(id=integration.id)
        self.assertEqual(loaded.access_token, 'ghp_test_token_abc123')

    def test_token_not_in_plain_text(self):
        """Ensure raw DB field is encrypted (not plaintext)."""
        integration = GitHubIntegration(
            organization=self.org,
            user=self.user,
            github_user_id=12345,
            github_username='testgh',
            created_by=self.user,
        )
        integration.access_token = 'ghp_plain_text_token'
        integration.save()

        loaded = GitHubIntegration.objects.get(id=integration.id)
        raw = bytes(loaded._access_token)
        self.assertNotIn(b'ghp_plain_text_token', raw)


class GitHubAPIPermissionsTest(TestCase):
    """Test authorization on GitHub API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='user1', email='user1@test.com', password='testpass123'
        )
        self.org = Organization.objects.create(name='Org1', slug='org1')
        OrgMembership.objects.create(organization=self.org, user=self.user, role='org-owner')
        self.project = Project.objects.create(
            name='Proj1', slug='proj1', organization=self.org, created_by=self.user,
        )

        # Another user in different org
        self.user2 = User.objects.create_user(
            username='user2', email='user2@test.com', password='testpass123'
        )
        self.org2 = Organization.objects.create(name='Org2', slug='org2')
        OrgMembership.objects.create(organization=self.org2, user=self.user2, role='org-owner')

    def test_unauthenticated_status_returns_401(self):
        resp = self.client.get('/api/integrations/github/status/')
        self.assertEqual(resp.status_code, 401)

    def test_status_returns_not_connected(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(f'/api/integrations/github/status/?organization_id={self.org.id}')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['connected'])

    def test_link_repo_requires_auth(self):
        resp = self.client.post('/api/integrations/github/link-repo/', {})
        self.assertEqual(resp.status_code, 401)

    def test_cross_org_isolation(self):
        """User from org2 cannot access org1 resources."""
        self.client.force_authenticate(user=self.user2)
        resp = self.client.get(
            f'/api/integrations/github/linked-repos/?project_id={self.project.id}'
        )
        self.assertEqual(resp.status_code, 403)


class GitHubRepoLinkingTest(TestCase):
    """Test repository linking flow."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='linker', email='linker@test.com', password='testpass123'
        )
        self.org = Organization.objects.create(name='LinkOrg', slug='link-org')
        OrgMembership.objects.create(organization=self.org, user=self.user, role='org-owner')
        self.project = Project.objects.create(
            name='LinkProj', slug='link-proj', organization=self.org, created_by=self.user,
        )
        # Create integration
        self.integration = GitHubIntegration(
            organization=self.org, user=self.user,
            github_user_id=99, github_username='linkergh',
            created_by=self.user,
        )
        self.integration.access_token = 'ghp_test_token'
        self.integration.save()

        self.client.force_authenticate(user=self.user)

    def test_invalid_github_url(self):
        resp = self.client.post('/api/integrations/github/link-repo/', {
            'project_id': str(self.project.id),
            'repo_url': 'https://gitlab.com/owner/repo',
        })
        self.assertEqual(resp.status_code, 400)

    @patch.object(GitHubAPIClient, 'check_repo_access')
    def test_link_repo_success(self, mock_check):
        mock_check.return_value = {
            'id': 12345, 'name': 'test-repo', 'full_name': 'owner/test-repo',
            'html_url': 'https://github.com/owner/test-repo',
            'clone_url': 'https://github.com/owner/test-repo.git',
            'default_branch': 'main', 'description': 'A test repo',
            'language': 'Python', 'stargazers_count': 10, 'private': False,
        }

        resp = self.client.post('/api/integrations/github/link-repo/', {
            'project_id': str(self.project.id),
            'repo_url': 'https://github.com/owner/test-repo',
        })
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(GitHubRepository.objects.filter(
            project=self.project, repo_full_name='owner/test-repo'
        ).exists())

    @patch.object(GitHubAPIClient, 'check_repo_access')
    def test_duplicate_link_rejected(self, mock_check):
        mock_check.return_value = {
            'id': 12345, 'name': 'dupe-repo', 'full_name': 'owner/dupe-repo',
            'html_url': 'https://github.com/owner/dupe-repo',
            'clone_url': 'https://github.com/owner/dupe-repo.git',
            'default_branch': 'main', 'description': '', 'language': 'JS',
            'stargazers_count': 0, 'private': False,
        }

        # Link once
        self.client.post('/api/integrations/github/link-repo/', {
            'project_id': str(self.project.id),
            'repo_url': 'https://github.com/owner/dupe-repo',
        })

        # Link again — should fail
        resp = self.client.post('/api/integrations/github/link-repo/', {
            'project_id': str(self.project.id),
            'repo_url': 'https://github.com/owner/dupe-repo',
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn('already linked', resp.data['error'])
