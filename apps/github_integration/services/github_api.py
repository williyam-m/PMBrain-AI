"""
GitHub API Client.
Handles all communication with the GitHub REST API:
  - OAuth token exchange
  - Fetching user info
  - Listing repositories
  - Validating repo access
  - Fetching repo metadata
"""
import logging
import requests as http_requests
from django.conf import settings

logger = logging.getLogger('pmbrain')

GITHUB_API_BASE = 'https://api.github.com'
GITHUB_OAUTH_AUTHORIZE = 'https://github.com/login/oauth/authorize'
GITHUB_OAUTH_TOKEN = 'https://github.com/login/oauth/access_token'


class GitHubAPIError(Exception):
    """Raised on GitHub API failures."""
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class GitHubAPIClient:
    """
    GitHub REST API client.
    All methods require a valid access_token.
    """

    def __init__(self, access_token=None):
        self.access_token = access_token
        self.timeout = 30

    def _headers(self):
        h = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'PMBrain-AI/1.0',
        }
        if self.access_token:
            h['Authorization'] = f'token {self.access_token}'
        return h

    def _get(self, url, params=None):
        """Make an authenticated GET request to GitHub API."""
        try:
            resp = http_requests.get(url, headers=self._headers(), params=params, timeout=self.timeout)
            if resp.status_code == 401:
                raise GitHubAPIError("GitHub token is invalid or expired.", 401)
            if resp.status_code == 403:
                raise GitHubAPIError("GitHub API rate limit or insufficient permissions.", 403)
            if resp.status_code == 404:
                raise GitHubAPIError("Repository not found or no access.", 404)
            if resp.status_code >= 400:
                raise GitHubAPIError(f"GitHub API error: {resp.text[:300]}", resp.status_code)
            return resp.json()
        except http_requests.exceptions.Timeout:
            raise GitHubAPIError("GitHub API request timed out.")
        except http_requests.exceptions.ConnectionError:
            raise GitHubAPIError("Cannot connect to GitHub API.")

    # ---- OAuth ----

    @staticmethod
    def get_oauth_url(state=None):
        """Build the GitHub OAuth authorization URL."""
        client_id = getattr(settings, 'GITHUB_CLIENT_ID', '') or ''
        if not client_id:
            raise GitHubAPIError("GITHUB_CLIENT_ID not configured on server.")

        redirect_uri = getattr(settings, 'GITHUB_REDIRECT_URI', '') or ''
        params = {
            'client_id': client_id,
            'scope': 'repo read:user user:email',
            'allow_signup': 'true',
        }
        if redirect_uri:
            params['redirect_uri'] = redirect_uri
        if state:
            params['state'] = state

        qs = '&'.join(f"{k}={v}" for k, v in params.items())
        return f"{GITHUB_OAUTH_AUTHORIZE}?{qs}"

    @staticmethod
    def exchange_code_for_token(code):
        """Exchange an OAuth code for an access token."""
        client_id = getattr(settings, 'GITHUB_CLIENT_ID', '') or ''
        client_secret = getattr(settings, 'GITHUB_CLIENT_SECRET', '') or ''

        if not client_id or not client_secret:
            raise GitHubAPIError("GitHub OAuth credentials not configured on server.")

        resp = http_requests.post(
            GITHUB_OAUTH_TOKEN,
            json={
                'client_id': client_id,
                'client_secret': client_secret,
                'code': code,
            },
            headers={'Accept': 'application/json'},
            timeout=30,
        )

        if resp.status_code != 200:
            raise GitHubAPIError(f"Failed to exchange code: {resp.text[:300]}", resp.status_code)

        data = resp.json()
        if 'error' in data:
            raise GitHubAPIError(f"OAuth error: {data.get('error_description', data['error'])}")

        return {
            'access_token': data['access_token'],
            'token_type': data.get('token_type', 'bearer'),
            'scope': data.get('scope', ''),
        }

    # ---- User ----

    def get_user(self):
        """Get the authenticated GitHub user."""
        return self._get(f'{GITHUB_API_BASE}/user')

    def get_user_emails(self):
        """Get user's verified emails."""
        return self._get(f'{GITHUB_API_BASE}/user/emails')

    # ---- Repositories ----

    def list_repos(self, page=1, per_page=30, sort='updated'):
        """List repositories the authenticated user has access to."""
        return self._get(
            f'{GITHUB_API_BASE}/user/repos',
            params={
                'page': page,
                'per_page': per_page,
                'sort': sort,
                'direction': 'desc',
                'affiliation': 'owner,collaborator,organization_member',
            }
        )

    def get_repo(self, owner, repo):
        """Get a specific repository's metadata."""
        return self._get(f'{GITHUB_API_BASE}/repos/{owner}/{repo}')

    def check_repo_access(self, owner, repo):
        """
        Verify the user has at least read access to the repo.
        Returns repo data on success, raises on failure.
        """
        return self.get_repo(owner, repo)

    def get_repo_branches(self, owner, repo):
        """List branches for a repository."""
        return self._get(
            f'{GITHUB_API_BASE}/repos/{owner}/{repo}/branches',
            params={'per_page': 30}
        )

    def get_repo_tree(self, owner, repo, sha='HEAD', recursive=True):
        """Get the file tree of a repository."""
        params = {}
        if recursive:
            params['recursive'] = '1'
        return self._get(
            f'{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{sha}',
            params=params
        )

    def get_repo_languages(self, owner, repo):
        """Get language breakdown for a repository."""
        return self._get(f'{GITHUB_API_BASE}/repos/{owner}/{repo}/languages')


def parse_github_url(url):
    """
    Parse a GitHub URL into (owner, repo).
    Handles:
      https://github.com/owner/repo
      https://github.com/owner/repo.git
      https://github.com/owner/repo/
    Returns (owner, repo) or raises ValueError.
    """
    import re
    url = url.strip().rstrip('/')
    if url.endswith('.git'):
        url = url[:-4]
    match = re.match(r'^https?://github\.com/([a-zA-Z0-9._-]+)/([a-zA-Z0-9._-]+)$', url)
    if not match:
        raise ValueError(f"Invalid GitHub URL: {url}")
    return match.group(1), match.group(2)
