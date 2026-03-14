"""
GitHub Integration Views.
Handles OAuth flow, repository listing, linking, cloning, and analysis.
"""
import logging
import uuid

from django.conf import settings
from django.shortcuts import redirect
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditEvent
from apps.organizations.models import OrgMembership
from apps.projects.models import Project
from .models import GitHubIntegration, GitHubRepository
from .serializers import (
    GitHubIntegrationSerializer,
    GitHubRepositorySerializer,
    LinkRepoSerializer,
    GitHubRepoListItemSerializer,
)
from .services.github_api import GitHubAPIClient, GitHubAPIError, parse_github_url
from .services.github_repo_service import GitHubRepoService, RepoCloneError

logger = logging.getLogger('pmbrain')


def _get_user_org(user, org_id=None):
    """Resolve user's organization. Returns (org, membership) or raises."""
    if org_id:
        membership = OrgMembership.objects.filter(
            user=user, organization_id=org_id
        ).select_related('organization').first()
    else:
        membership = OrgMembership.objects.filter(
            user=user
        ).select_related('organization').first()

    if not membership:
        return None, None
    return membership.organization, membership


# ============================================================
# OAuth Flow
# ============================================================

class GitHubConnectView(APIView):
    """
    POST /api/integrations/github/connect/
    Initiates the GitHub OAuth flow.
    Returns the OAuth authorization URL for the frontend to redirect to.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        org_id = request.data.get('organization_id')
        org, membership = _get_user_org(request.user, org_id)
        if not org:
            return Response(
                {'error': 'No organization found. Please create or join one first.'},
                status=403
            )

        # Check if already connected
        existing = GitHubIntegration.objects.filter(
            organization=org, user=request.user, is_active=True
        ).first()
        if existing:
            return Response({
                'already_connected': True,
                'integration': GitHubIntegrationSerializer(existing).data,
            })

        # Generate state token (stored in session or token for CSRF protection)
        state = str(uuid.uuid4())
        request.session['github_oauth_state'] = state
        request.session['github_oauth_org_id'] = str(org.id)

        try:
            auth_url = GitHubAPIClient.get_oauth_url(state=state)
            return Response({'auth_url': auth_url, 'state': state})
        except GitHubAPIError as e:
            return Response({'error': str(e)}, status=400)


class GitHubCallbackView(APIView):
    """
    GET /api/integrations/github/callback/
    GitHub redirects here after OAuth authorization.
    Exchanges the code for an access token and stores the integration.
    """
    permission_classes = [AllowAny]  # GitHub redirects here without auth header

    def get(self, request):
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        error = request.query_params.get('error')

        if error:
            logger.warning(f"GitHub OAuth error: {error}")
            return redirect(f'/?github_error={error}')

        if not code:
            return redirect('/?github_error=no_code')

        # State validation (if session available)
        expected_state = request.session.get('github_oauth_state')
        if expected_state and state != expected_state:
            return redirect('/?github_error=invalid_state')

        try:
            # Exchange code for token
            token_data = GitHubAPIClient.exchange_code_for_token(code)
            access_token = token_data['access_token']

            # Fetch GitHub user info
            client = GitHubAPIClient(access_token)
            gh_user = client.get_user()

            # Determine org from session
            org_id = request.session.get('github_oauth_org_id')
            if not org_id:
                # Fallback: find the user from any means available
                return redirect('/?github_error=missing_org_context')

            from apps.organizations.models import Organization
            try:
                org = Organization.objects.get(id=org_id)
            except Organization.DoesNotExist:
                return redirect('/?github_error=org_not_found')

            # Find the user associated with this session
            # Since this is a redirect, the user may not be in request.user
            # We use session to find them
            from django.contrib.sessions.models import Session
            from apps.accounts.models import User

            user_id = request.session.get('_auth_user_id')
            if user_id:
                user = User.objects.get(pk=user_id)
            else:
                # Try to find user by org membership
                membership = OrgMembership.objects.filter(organization=org).first()
                if membership:
                    user = membership.user
                else:
                    return redirect('/?github_error=no_user')

            # Create or update integration
            integration, created = GitHubIntegration.objects.update_or_create(
                organization=org,
                user=user,
                defaults={
                    'github_user_id': gh_user['id'],
                    'github_username': gh_user['login'],
                    'avatar_url': gh_user.get('avatar_url', ''),
                    'scopes': token_data.get('scope', ''),
                    'is_active': True,
                    'created_by': user,
                }
            )
            integration.access_token = access_token  # Encrypted via property
            integration.save()

            # Audit
            AuditEvent.objects.create(
                actor=user,
                action='github_connected',
                entity='GitHubIntegration',
                entity_id=str(integration.id),
                organization=org,
                metadata={
                    'github_username': gh_user['login'],
                    'scopes': token_data.get('scope', ''),
                },
            )

            logger.info(f"GitHub connected: {gh_user['login']} → org {org.name}")

            # Clean up session
            request.session.pop('github_oauth_state', None)
            request.session.pop('github_oauth_org_id', None)

            return redirect('/?github_connected=true')

        except GitHubAPIError as e:
            logger.error(f"GitHub OAuth callback error: {e}")
            return redirect(f'/?github_error={str(e)[:100]}')
        except Exception as e:
            logger.error(f"GitHub callback unexpected error: {e}")
            return redirect('/?github_error=unexpected_error')


class GitHubConnectTokenView(APIView):
    """
    POST /api/integrations/github/connect-token/
    Alternative connection method: user directly provides a GitHub Personal Access Token.
    This is simpler than OAuth for development/demos (no OAuth app needed).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        access_token = request.data.get('access_token')
        org_id = request.data.get('organization_id')

        if not access_token:
            return Response({'error': 'access_token is required'}, status=400)

        org, membership = _get_user_org(request.user, org_id)
        if not org:
            return Response({'error': 'No organization found.'}, status=403)

        # Validate the token by fetching user info
        try:
            client = GitHubAPIClient(access_token)
            gh_user = client.get_user()
        except GitHubAPIError as e:
            return Response({'error': f'Invalid GitHub token: {str(e)}'}, status=400)

        # Create or update integration
        integration, created = GitHubIntegration.objects.update_or_create(
            organization=org,
            user=request.user,
            defaults={
                'github_user_id': gh_user['id'],
                'github_username': gh_user['login'],
                'avatar_url': gh_user.get('avatar_url', ''),
                'scopes': 'repo,read:user,user:email',
                'is_active': True,
                'created_by': request.user,
            }
        )
        integration.access_token = access_token
        integration.save()

        # Audit
        AuditEvent.objects.create(
            actor=request.user,
            action='github_connected',
            entity='GitHubIntegration',
            entity_id=str(integration.id),
            organization=org,
            metadata={'github_username': gh_user['login'], 'method': 'personal_token'},
        )

        return Response({
            'message': 'GitHub connected successfully!',
            'integration': GitHubIntegrationSerializer(integration).data,
        }, status=201 if created else 200)


# ============================================================
# Integration Status & Disconnect
# ============================================================

class GitHubStatusView(APIView):
    """
    GET /api/integrations/github/status/
    Returns the current GitHub connection status for the user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org_id = request.query_params.get('organization_id')
        org, membership = _get_user_org(request.user, org_id)
        if not org:
            return Response({'connected': False, 'error': 'No organization'})

        integration = GitHubIntegration.objects.filter(
            organization=org, user=request.user, is_active=True
        ).first()

        if not integration:
            return Response({'connected': False})

        return Response({
            'connected': True,
            'integration': GitHubIntegrationSerializer(integration).data,
        })


class GitHubDisconnectView(APIView):
    """
    POST /api/integrations/github/disconnect/
    Disconnects GitHub by deactivating the integration.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        org_id = request.data.get('organization_id')
        org, membership = _get_user_org(request.user, org_id)
        if not org:
            return Response({'error': 'No organization found.'}, status=403)

        integration = GitHubIntegration.objects.filter(
            organization=org, user=request.user, is_active=True
        ).first()

        if not integration:
            return Response({'error': 'No active GitHub connection found.'}, status=404)

        integration.is_active = False
        integration.save(update_fields=['is_active'])

        # Audit
        AuditEvent.objects.create(
            actor=request.user,
            action='github_disconnected',
            entity='GitHubIntegration',
            entity_id=str(integration.id),
            organization=org,
            metadata={'github_username': integration.github_username},
        )

        return Response({'message': 'GitHub disconnected successfully.'})


# ============================================================
# Repository Listing & Linking
# ============================================================

class GitHubReposView(APIView):
    """
    GET /api/integrations/github/repos/
    Lists repositories the user has access to on GitHub.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org_id = request.query_params.get('organization_id')
        project_id = request.query_params.get('project_id')
        page = int(request.query_params.get('page', 1))

        org, membership = _get_user_org(request.user, org_id)
        if not org:
            return Response({'error': 'No organization found.'}, status=403)

        integration = GitHubIntegration.objects.filter(
            organization=org, user=request.user, is_active=True
        ).first()

        if not integration:
            return Response({'error': 'GitHub not connected. Please connect first.'}, status=400)

        try:
            client = GitHubAPIClient(integration.access_token)
            repos = client.list_repos(page=page, per_page=30)
        except GitHubAPIError as e:
            return Response({'error': f'GitHub API error: {str(e)}'}, status=502)

        # Check which repos are already linked to this project
        linked_full_names = set()
        if project_id:
            linked_full_names = set(
                GitHubRepository.objects.filter(
                    project_id=project_id, organization=org
                ).values_list('repo_full_name', flat=True)
            )

        # Annotate repos with linked status
        for repo in repos:
            repo['already_linked'] = repo.get('full_name', '') in linked_full_names

        serializer = GitHubRepoListItemSerializer(repos, many=True)
        return Response({
            'repos': serializer.data,
            'page': page,
            'count': len(repos),
        })


class GitHubLinkRepoView(APIView):
    """
    POST /api/integrations/github/link-repo/
    Links a GitHub repository to a project and triggers analysis.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LinkRepoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project_id = serializer.validated_data['project_id']
        repo_url = serializer.validated_data['repo_url']

        # Validate project access
        try:
            project = Project.objects.select_related('organization').get(id=project_id)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found.'}, status=404)

        org = project.organization
        if not OrgMembership.objects.filter(organization=org, user=request.user).exists():
            return Response({'error': 'Not a member of this organization.'}, status=403)

        # Get GitHub integration
        integration = GitHubIntegration.objects.filter(
            organization=org, user=request.user, is_active=True
        ).first()

        if not integration:
            return Response({
                'error': 'GitHub not connected. Please connect your GitHub account first.'
            }, status=400)

        # Parse the URL
        try:
            owner, repo_name = parse_github_url(repo_url)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

        # Verify repo exists and user has access
        try:
            client = GitHubAPIClient(integration.access_token)
            repo_data = client.check_repo_access(owner, repo_name)
        except GitHubAPIError as e:
            return Response({'error': f'Cannot access repository: {str(e)}'}, status=400)

        # Check if already linked
        full_name = repo_data['full_name']
        existing = GitHubRepository.objects.filter(
            project=project, repo_full_name=full_name
        ).first()

        if existing:
            return Response({
                'error': f'Repository {full_name} is already linked to this project.',
                'repo': GitHubRepositorySerializer(existing).data,
            }, status=400)

        # Create the repository record
        github_repo = GitHubRepository.objects.create(
            integration=integration,
            github_repo_id=repo_data['id'],
            repo_name=repo_data['name'],
            repo_full_name=repo_data['full_name'],
            repo_url=repo_data['html_url'],
            clone_url=repo_data.get('clone_url', ''),
            default_branch=repo_data.get('default_branch', 'main'),
            description=repo_data.get('description', '') or '',
            language=repo_data.get('language', '') or '',
            stars=repo_data.get('stargazers_count', 0),
            is_private=repo_data.get('private', False),
            connected_by=request.user,
            organization=org,
            project=project,
            created_by=request.user,
        )

        # Audit
        AuditEvent.objects.create(
            actor=request.user,
            action='github_repo_linked',
            entity='GitHubRepository',
            entity_id=str(github_repo.id),
            organization=org,
            metadata={
                'repo_full_name': full_name,
                'project_id': str(project.id),
            },
        )

        return Response({
            'message': f'Repository {full_name} linked successfully!',
            'repo': GitHubRepositorySerializer(github_repo).data,
        }, status=201)


# ============================================================
# Repository Operations
# ============================================================

class GitHubLinkedReposView(APIView):
    """
    GET /api/integrations/github/linked-repos/
    Lists repositories linked to a project.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response({'error': 'project_id required'}, status=400)

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=404)

        if not OrgMembership.objects.filter(
            organization=project.organization, user=request.user
        ).exists():
            return Response({'error': 'Not authorized'}, status=403)

        repos = GitHubRepository.objects.filter(
            project=project, is_active=True
        ).select_related('codebase')

        return Response({
            'repos': GitHubRepositorySerializer(repos, many=True).data,
        })


class GitHubAnalyzeRepoView(APIView):
    """
    POST /api/integrations/github/analyze-repo/
    Clones a linked repository and triggers AI codebase analysis.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        repo_id = request.data.get('repo_id')
        if not repo_id:
            return Response({'error': 'repo_id required'}, status=400)

        try:
            github_repo = GitHubRepository.objects.select_related(
                'integration', 'organization', 'project'
            ).get(id=repo_id)
        except GitHubRepository.DoesNotExist:
            return Response({'error': 'Repository not found'}, status=404)

        # Permission check
        if not OrgMembership.objects.filter(
            organization=github_repo.organization, user=request.user
        ).exists():
            return Response({'error': 'Not authorized'}, status=403)

        try:
            result = GitHubRepoService.trigger_analysis(github_repo, request.user)

            # Audit
            AuditEvent.objects.create(
                actor=request.user,
                action='github_repo_analyzed',
                entity='GitHubRepository',
                entity_id=str(github_repo.id),
                organization=github_repo.organization,
                metadata={
                    'repo_full_name': github_repo.repo_full_name,
                    'analysis_status': result['analysis'].status,
                },
            )

            from apps.codebase.serializers import CodebaseAnalysisSerializer
            return Response({
                'message': f'Analysis complete for {github_repo.repo_full_name}!',
                'repo': GitHubRepositorySerializer(github_repo).data,
                'analysis': CodebaseAnalysisSerializer(result['analysis']).data,
            })

        except RepoCloneError as e:
            return Response({
                'error': f'Clone failed: {str(e)}',
                'repo': GitHubRepositorySerializer(github_repo).data,
            }, status=400)
        except Exception as e:
            logger.error(f"Analyze repo error: {e}")
            return Response({
                'error': f'Analysis failed: {str(e)}',
                'repo': GitHubRepositorySerializer(github_repo).data,
            }, status=500)


class GitHubUnlinkRepoView(APIView):
    """
    POST /api/integrations/github/unlink-repo/
    Unlinks a repository from a project.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        repo_id = request.data.get('repo_id')
        if not repo_id:
            return Response({'error': 'repo_id required'}, status=400)

        try:
            github_repo = GitHubRepository.objects.select_related('organization').get(id=repo_id)
        except GitHubRepository.DoesNotExist:
            return Response({'error': 'Repository not found'}, status=404)

        if not OrgMembership.objects.filter(
            organization=github_repo.organization, user=request.user
        ).exists():
            return Response({'error': 'Not authorized'}, status=403)

        github_repo.is_active = False
        github_repo.save(update_fields=['is_active'])

        AuditEvent.objects.create(
            actor=request.user,
            action='github_repo_unlinked',
            entity='GitHubRepository',
            entity_id=str(github_repo.id),
            organization=github_repo.organization,
            metadata={'repo_full_name': github_repo.repo_full_name},
        )

        return Response({'message': 'Repository unlinked successfully.'})
