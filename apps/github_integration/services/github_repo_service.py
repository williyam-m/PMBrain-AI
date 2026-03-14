"""
GitHub Repository Service.
Handles:
  - Secure repository cloning (read-only)
  - File extraction for AI analysis
  - Size limits and security checks
  - Creating Codebase records for the AI pipeline
"""
import logging
import os
import shutil
import subprocess
import uuid
from pathlib import Path

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('pmbrain')

# Maximum repo size in MB for cloning
MAX_REPO_SIZE_MB = int(os.getenv('MAX_GITHUB_REPO_SIZE_MB', '200'))
# Clone timeout in seconds
CLONE_TIMEOUT = int(os.getenv('GITHUB_CLONE_TIMEOUT', '120'))

# Extensions to skip during analysis (binary, media, etc.)
SKIP_EXTENSIONS = {
    '.exe', '.dll', '.so', '.dylib', '.bin', '.o', '.a',
    '.pyc', '.pyo', '.class', '.jar', '.war',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg', '.webp',
    '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac',
    '.zip', '.tar', '.gz', '.rar', '.7z', '.bz2',
    '.woff', '.woff2', '.ttf', '.eot', '.otf',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.pptx',
    '.db', '.sqlite', '.sqlite3',
    '.lock', '.map', '.min.js', '.min.css',
}

# Extensions we want to analyze
CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.rb',
    '.html', '.css', '.scss', '.sass', '.less',
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',
    '.md', '.txt', '.rst',
    '.sql', '.graphql', '.proto',
    '.sh', '.bash', '.dockerfile',
    '.xml', '.csv', '.env.example',
    '.c', '.cpp', '.h', '.hpp', '.cs', '.swift', '.kt',
    '.php', '.pl', '.r', '.scala', '.lua',
}

# Directories to skip
SKIP_DIRS = {
    'node_modules', 'venv', '.venv', 'env', '__pycache__',
    '.git', '.svn', 'dist', 'build', '.next', 'vendor',
    'target', '.idea', '.vscode', 'coverage', '.tox',
    '.eggs', '.mypy_cache', '.pytest_cache', '.gradle',
    'bower_components', '.bundle', '.terraform',
}

MAX_FILE_SIZE = 100 * 1024  # 100KB per file for analysis
MAX_FILES_TO_ANALYZE = 200


class RepoCloneError(Exception):
    """Raised when repository cloning fails."""
    pass


class GitHubRepoService:
    """
    Handles cloning repos securely and preparing them for AI analysis.
    All cloning is read-only (--depth 1), no code is ever executed.
    """

    @staticmethod
    def get_storage_path(organization_id, project_id, repo_name):
        """Generate the safe storage path for a cloned repo."""
        base = Path(settings.BASE_DIR) / 'storage' / 'repos'
        path = base / str(organization_id) / str(project_id) / repo_name
        return path

    @classmethod
    def clone_repository(cls, github_repo, access_token=None):
        """
        Clone a GitHub repository for analysis.
        Uses shallow clone (depth=1) for efficiency.
        Returns the clone path on success.
        """
        from apps.github_integration.models import GitHubRepository

        repo = github_repo
        owner_repo = repo.repo_full_name  # e.g., "owner/repo"

        # Build clone URL with token for private repos
        if access_token and repo.is_private:
            clone_url = f"https://x-access-token:{access_token}@github.com/{owner_repo}.git"
        else:
            clone_url = f"https://github.com/{owner_repo}.git"

        # Create storage directory
        clone_path = cls.get_storage_path(
            repo.organization_id, repo.project_id, repo.repo_name
        )

        # Clean up existing clone if present
        if clone_path.exists():
            shutil.rmtree(clone_path, ignore_errors=True)

        clone_path.parent.mkdir(parents=True, exist_ok=True)

        # Update status
        repo.clone_status = 'cloning'
        repo.clone_error = ''
        repo.save(update_fields=['clone_status', 'clone_error'])

        try:
            # Shallow clone — only the latest commit, single branch
            cmd = [
                'git', 'clone',
                '--depth', '1',
                '--single-branch',
                '--branch', repo.default_branch or 'main',
                clone_url,
                str(clone_path),
            ]

            logger.info(f"Cloning {owner_repo} (branch: {repo.default_branch})...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=CLONE_TIMEOUT,
                env={
                    **os.environ,
                    'GIT_TERMINAL_PROMPT': '0',  # Never prompt for credentials
                }
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip()
                # Don't leak tokens in error messages
                error_msg = error_msg.replace(access_token or '', '***') if access_token else error_msg
                raise RepoCloneError(f"Git clone failed: {error_msg[:500]}")

            # Verify clone and check size
            total_size = sum(
                f.stat().st_size for f in clone_path.rglob('*') if f.is_file()
            )
            if total_size > MAX_REPO_SIZE_MB * 1024 * 1024:
                shutil.rmtree(clone_path, ignore_errors=True)
                raise RepoCloneError(
                    f"Repository too large ({total_size / (1024*1024):.0f}MB). "
                    f"Maximum: {MAX_REPO_SIZE_MB}MB"
                )

            # Remove .git directory to save space and prevent any git operations
            git_dir = clone_path / '.git'
            if git_dir.exists():
                shutil.rmtree(git_dir, ignore_errors=True)

            # Update repo record
            repo.clone_status = 'completed'
            repo.clone_path = str(clone_path)
            repo.last_cloned_at = timezone.now()
            repo.save(update_fields=['clone_status', 'clone_path', 'last_cloned_at'])

            logger.info(f"Successfully cloned {owner_repo} to {clone_path}")
            return clone_path

        except subprocess.TimeoutExpired:
            if clone_path.exists():
                shutil.rmtree(clone_path, ignore_errors=True)
            repo.clone_status = 'failed'
            repo.clone_error = f"Clone timed out after {CLONE_TIMEOUT}s"
            repo.save(update_fields=['clone_status', 'clone_error'])
            raise RepoCloneError(f"Clone timed out after {CLONE_TIMEOUT}s")

        except RepoCloneError:
            repo.clone_status = 'failed'
            repo.clone_error = str(repo.clone_error) if repo.clone_error else 'Clone failed'
            repo.save(update_fields=['clone_status', 'clone_error'])
            raise

        except Exception as e:
            if clone_path.exists():
                shutil.rmtree(clone_path, ignore_errors=True)
            repo.clone_status = 'failed'
            repo.clone_error = str(e)[:500]
            repo.save(update_fields=['clone_status', 'clone_error'])
            logger.error(f"Failed to clone {owner_repo}: {e}")
            raise RepoCloneError(str(e))

    @classmethod
    def extract_code_info(cls, source_dir):
        """
        Extract file structure and code samples from a cloned repo.
        Only performs static analysis — no code execution.
        Returns (file_structure, code_samples).
        """
        source_dir = Path(source_dir)
        file_structure = {
            'directories': [],
            'files': [],
            'total_files': 0,
            'total_dirs': 0,
            'languages': {},
        }
        code_samples = {}
        files_analyzed = 0

        for root, dirs, files in os.walk(source_dir):
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in SKIP_DIRS]

            rel_root = os.path.relpath(root, source_dir)
            if rel_root != '.':
                file_structure['directories'].append(rel_root)
                file_structure['total_dirs'] += 1

            for fname in files:
                fpath = os.path.join(root, fname)
                rel_path = os.path.relpath(fpath, source_dir)
                ext = os.path.splitext(fname)[1].lower()

                # Skip binary/media files
                if ext in SKIP_EXTENSIONS:
                    continue

                file_structure['files'].append(rel_path)
                file_structure['total_files'] += 1

                # Track languages
                if ext in CODE_EXTENSIONS:
                    lang = ext.lstrip('.')
                    file_structure['languages'][lang] = file_structure['languages'].get(lang, 0) + 1

                # Read code samples for AI analysis
                if ext in CODE_EXTENSIONS and files_analyzed < MAX_FILES_TO_ANALYZE:
                    try:
                        file_size = os.path.getsize(fpath)
                        if file_size <= MAX_FILE_SIZE:
                            with open(fpath, 'r', errors='ignore') as f:
                                content = f.read()
                            code_samples[rel_path] = content[:5000]
                            files_analyzed += 1
                    except Exception:
                        pass

        return file_structure, code_samples

    @classmethod
    def create_codebase_from_repo(cls, github_repo, user):
        """
        Create a Codebase model record from a cloned GitHub repo.
        This integrates with the existing AI pipeline.
        """
        from apps.codebase.models import Codebase

        if not github_repo.clone_path or github_repo.clone_status != 'completed':
            raise RepoCloneError("Repository must be cloned before creating codebase.")

        clone_path = Path(github_repo.clone_path)
        if not clone_path.exists():
            raise RepoCloneError("Clone directory not found. Re-clone the repository.")

        # Count files
        file_count = sum(1 for _ in clone_path.rglob('*') if _.is_file())
        total_size = sum(f.stat().st_size for f in clone_path.rglob('*') if f.is_file())

        # Create or update the Codebase record
        codebase, created = Codebase.objects.update_or_create(
            organization=github_repo.organization,
            project=github_repo.project,
            name=f"GitHub: {github_repo.repo_full_name}",
            defaults={
                'source_type': 'git',
                'storage_path': str(clone_path),
                'git_url': github_repo.repo_url,
                'file_size_bytes': total_size,
                'file_count': file_count,
                'uploaded_by': user,
                'created_by': user,
                'is_active': True,
            }
        )

        # Link repo to codebase
        github_repo.codebase = codebase
        github_repo.save(update_fields=['codebase'])

        return codebase

    @classmethod
    def trigger_analysis(cls, github_repo, user):
        """
        Full pipeline: clone → create codebase → run AI analysis.
        """
        from apps.codebase.models import CodebaseAnalysis
        from apps.ai_agents.services.agent_orchestrator import WorkflowOrchestrator

        # Get access token from integration
        access_token = None
        if github_repo.integration:
            access_token = github_repo.integration.access_token

        # 1. Clone
        clone_path = cls.clone_repository(github_repo, access_token)

        # 2. Create Codebase record
        codebase = cls.create_codebase_from_repo(github_repo, user)

        # 3. Extract file info
        file_structure, code_samples = cls.extract_code_info(clone_path)

        # 4. Create analysis record
        analysis = CodebaseAnalysis.objects.create(
            codebase=codebase,
            status='processing',
            file_structure=file_structure,
            organization=github_repo.organization,
            project=github_repo.project,
            created_by=user,
        )

        # 5. Run AI analysis
        try:
            result = WorkflowOrchestrator.run_workflow(
                'analyze_codebase',
                github_repo.project,
                user,
                {
                    'codebase_id': str(codebase.id),
                    'analysis_id': str(analysis.id),
                    'file_structure': file_structure,
                    'code_samples': code_samples,
                    'product_context': github_repo.project.product_context or github_repo.project.name,
                }
            )

            ai_result = result.get('results', {}).get('code_understanding', {})
            if ai_result and not result.get('errors'):
                analysis.system_summary = ai_result.get('system_summary', '')
                analysis.major_modules = ai_result.get('major_modules', [])
                analysis.existing_features = ai_result.get('existing_features', [])
                analysis.api_endpoints = ai_result.get('api_endpoints', [])
                analysis.database_models = ai_result.get('database_models', [])
                analysis.capability_map = ai_result.get('capability_map', {})
                analysis.technology_stack = ai_result.get('technology_stack', [])
                analysis.architecture_patterns = ai_result.get('architecture_patterns', [])
                analysis.code_samples = code_samples
                analysis.status = 'completed'
                analysis.completed_at = timezone.now()
            else:
                errors = result.get('errors', [])
                analysis.status = 'failed'
                analysis.error_message = str(errors[0] if errors else 'AI analysis failed')

            analysis.save()
            return {
                'codebase': codebase,
                'analysis': analysis,
                'result': result,
            }

        except Exception as e:
            analysis.status = 'failed'
            analysis.error_message = str(e)[:500]
            analysis.save()
            logger.error(f"Analysis failed for {github_repo.repo_full_name}: {e}")
            raise
