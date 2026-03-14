"""
Codebase analysis views.
Handles file upload, analysis triggering, and results viewing.
"""
import os
import zipfile
import tarfile
import tempfile
import shutil
import logging
from pathlib import Path

from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from apps.core.mixins import TenantQuerySetMixin, SetCreatedByMixin
from apps.organizations.models import OrgMembership
from .models import Codebase, CodebaseAnalysis, MarketTrend, FeatureDiscovery
from .serializers import (
    CodebaseSerializer, CodebaseAnalysisSerializer,
    MarketTrendSerializer, FeatureDiscoverySerializer
)

logger = logging.getLogger('pmbrain')

# Dangerous file extensions to skip during analysis
SKIP_EXTENSIONS = {
    '.exe', '.dll', '.so', '.dylib', '.bin', '.o', '.a',
    '.pyc', '.pyo', '.class', '.jar', '.war',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg', '.webp',
    '.mp3', '.mp4', '.avi', '.mov', '.wav',
    '.zip', '.tar', '.gz', '.rar', '.7z',
    '.woff', '.woff2', '.ttf', '.eot',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    '.db', '.sqlite', '.sqlite3',
    '.lock', '.map',
}

# File extensions we want to analyze
CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.rb',
    '.html', '.css', '.scss', '.sass', '.less',
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.env',
    '.md', '.txt', '.rst',
    '.sql', '.graphql', '.proto',
    '.sh', '.bash', '.dockerfile',
    '.xml', '.csv',
}

MAX_FILE_SIZE = 100 * 1024  # 100KB per file for analysis
MAX_FILES_TO_ANALYZE = 200


class CodebaseViewSet(TenantQuerySetMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CodebaseSerializer
    queryset = Codebase.objects.all()
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filterset_fields = ['organization', 'project', 'source_type']

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            uploaded_by=self.request.user
        )

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload(self, request):
        """Upload and extract a codebase (zip/tar.gz)."""
        uploaded_file = request.FILES.get('file')
        project_id = request.data.get('project')
        org_id = request.data.get('organization')
        name = request.data.get('name', '')

        if not uploaded_file:
            return Response({'error': 'No file provided'}, status=400)
        if not project_id or not org_id:
            return Response({'error': 'project and organization are required'}, status=400)

        # Validate membership
        if not OrgMembership.objects.filter(
            organization_id=org_id, user=request.user
        ).exists():
            return Response({'error': 'Not a member of this organization'}, status=403)

        # Check file size
        max_size = settings.MAX_CODEBASE_SIZE_MB * 1024 * 1024
        if uploaded_file.size > max_size:
            return Response({
                'error': f'File too large. Maximum: {settings.MAX_CODEBASE_SIZE_MB}MB'
            }, status=400)

        # Determine source type
        filename = uploaded_file.name.lower()
        if filename.endswith('.zip'):
            source_type = 'zip'
        elif filename.endswith('.tar.gz') or filename.endswith('.tgz'):
            source_type = 'tar'
        else:
            return Response({'error': 'Unsupported format. Use .zip or .tar.gz'}, status=400)

        # Save and extract
        storage_base = Path(settings.BASE_DIR) / settings.CODEBASE_STORAGE_PATH
        storage_base.mkdir(parents=True, exist_ok=True)

        import uuid
        codebase_dir = storage_base / str(uuid.uuid4())
        codebase_dir.mkdir(parents=True)

        try:
            # Save uploaded file
            temp_path = codebase_dir / uploaded_file.name
            with open(temp_path, 'wb') as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)

            # Extract
            extract_dir = codebase_dir / 'source'
            extract_dir.mkdir()

            if source_type == 'zip':
                with zipfile.ZipFile(temp_path, 'r') as zf:
                    # Security: check for path traversal
                    for info in zf.infolist():
                        if info.filename.startswith('/') or '..' in info.filename:
                            return Response({'error': 'Invalid file paths in archive'}, status=400)
                    zf.extractall(extract_dir)
            elif source_type == 'tar':
                with tarfile.open(temp_path, 'r:gz') as tf:
                    # Security: check for path traversal
                    for member in tf.getmembers():
                        if member.name.startswith('/') or '..' in member.name:
                            return Response({'error': 'Invalid file paths in archive'}, status=400)
                    tf.extractall(extract_dir)

            # Clean up the archive file
            temp_path.unlink()

            # Count files
            file_count = sum(1 for _ in extract_dir.rglob('*') if _.is_file())

            codebase = Codebase.objects.create(
                name=name or uploaded_file.name,
                source_type=source_type,
                storage_path=str(codebase_dir),
                file_size_bytes=uploaded_file.size,
                file_count=file_count,
                uploaded_by=request.user,
                organization_id=org_id,
                project_id=project_id,
                created_by=request.user,
            )

            return Response(CodebaseSerializer(codebase).data, status=201)

        except (zipfile.BadZipFile, tarfile.TarError) as e:
            if codebase_dir.exists():
                shutil.rmtree(codebase_dir)
            return Response({'error': f'Invalid archive: {str(e)}'}, status=400)
        except Exception as e:
            if codebase_dir.exists():
                shutil.rmtree(codebase_dir)
            logger.error(f"Codebase upload error: {e}")
            return Response({'error': f'Upload failed: {str(e)}'}, status=500)

    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """Trigger AI analysis of a codebase."""
        codebase = self.get_object()

        # Check membership
        if not codebase.organization.members.filter(user=request.user).exists():
            return Response({'error': 'Not authorized'}, status=403)

        # Create analysis record
        analysis = CodebaseAnalysis.objects.create(
            codebase=codebase,
            status='processing',
            organization=codebase.organization,
            project=codebase.project,
            created_by=request.user,
        )

        try:
            # Extract file structure and code samples
            source_dir = Path(codebase.storage_path) / 'source'
            if not source_dir.exists():
                analysis.status = 'failed'
                analysis.error_message = 'Source directory not found'
                analysis.save()
                return Response({'error': 'Source directory not found'}, status=400)

            file_structure, code_samples = self._extract_code_info(source_dir)

            analysis.file_structure = file_structure

            # Run AI analysis
            from apps.ai_agents.services.agent_orchestrator import WorkflowOrchestrator
            result = WorkflowOrchestrator.run_workflow(
                'analyze_codebase',
                codebase.project,
                request.user,
                {
                    'codebase_id': str(codebase.id),
                    'analysis_id': str(analysis.id),
                    'file_structure': file_structure,
                    'code_samples': code_samples,
                    'product_context': codebase.project.product_context or codebase.project.name,
                }
            )

            # Update analysis with results
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
                # Enhanced v2 fields
                analysis.missing_capabilities = ai_result.get('missing_capabilities', [])
                analysis.improvement_areas = ai_result.get('improvement_areas', [])
                analysis.competitor_comparison = ai_result.get('competitor_comparison', {})
                analysis.new_feature_opportunities = ai_result.get('new_feature_opportunities', [])
                analysis.code_samples = code_samples
                analysis.status = 'completed'
                analysis.completed_at = timezone.now()
            else:
                errors = result.get('errors', [])
                analysis.status = 'failed'
                analysis.error_message = str(errors[0] if errors else 'Unknown error')

            analysis.save()
            return Response(CodebaseAnalysisSerializer(analysis).data)

        except Exception as e:
            analysis.status = 'failed'
            analysis.error_message = str(e)
            analysis.save()
            logger.error(f"Codebase analysis error: {e}")
            return Response({'error': str(e)}, status=500)

    def _extract_code_info(self, source_dir):
        """Extract file structure and code samples from extracted codebase.
        Only performs static analysis — no code execution."""
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
            # Skip hidden dirs, node_modules, venv, etc.
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {
                'node_modules', 'venv', '.venv', 'env', '__pycache__',
                '.git', '.svn', 'dist', 'build', '.next', 'vendor',
                'target', '.idea', '.vscode', 'coverage', '.tox',
            }]

            rel_root = os.path.relpath(root, source_dir)
            if rel_root != '.':
                file_structure['directories'].append(rel_root)
                file_structure['total_dirs'] += 1

            for fname in files:
                fpath = os.path.join(root, fname)
                rel_path = os.path.relpath(fpath, source_dir)
                ext = os.path.splitext(fname)[1].lower()

                # Skip binary and large files
                if ext in SKIP_EXTENSIONS:
                    continue

                file_structure['files'].append(rel_path)
                file_structure['total_files'] += 1

                # Track languages
                if ext in CODE_EXTENSIONS:
                    lang = ext.lstrip('.')
                    file_structure['languages'][lang] = file_structure['languages'].get(lang, 0) + 1

                # Read code samples for analysis
                if ext in CODE_EXTENSIONS and files_analyzed < MAX_FILES_TO_ANALYZE:
                    try:
                        file_size = os.path.getsize(fpath)
                        if file_size <= MAX_FILE_SIZE:
                            with open(fpath, 'r', errors='ignore') as f:
                                content = f.read()
                            code_samples[rel_path] = content[:5000]  # Limit per file
                            files_analyzed += 1
                    except Exception:
                        pass

        return file_structure, code_samples


class CodebaseAnalysisViewSet(TenantQuerySetMixin, viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CodebaseAnalysisSerializer
    queryset = CodebaseAnalysis.objects.all()
    filterset_fields = ['organization', 'project', 'status']


class MarketTrendViewSet(TenantQuerySetMixin, viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MarketTrendSerializer
    queryset = MarketTrend.objects.all()
    filterset_fields = ['organization', 'project']

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate market trend analysis."""
        project_id = request.data.get('project_id')
        if not project_id:
            return Response({'error': 'project_id required'}, status=400)

        from apps.projects.models import Project
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=404)

        if not project.organization.members.filter(user=request.user).exists():
            return Response({'error': 'Not authorized'}, status=403)

        from apps.ai_agents.services.agent_orchestrator import WorkflowOrchestrator
        result = WorkflowOrchestrator.run_workflow(
            'market_trends', project, request.user,
            {'product_context': project.product_context or project.name}
        )

        ai_result = result.get('results', {}).get('market_trend', {})
        if ai_result and not result.get('errors'):
            trend = MarketTrend.objects.create(
                trend_summary=ai_result.get('trend_summary', ''),
                emerging_features=ai_result.get('emerging_features', []),
                competitor_features=ai_result.get('competitor_features', []),
                market_gap_opportunities=ai_result.get('market_gap_opportunities', []),
                industry_trends=ai_result.get('industry_trends', []),
                analysis_context=project.product_context or project.name,
                organization=project.organization,
                project=project,
                created_by=request.user,
            )
            return Response(MarketTrendSerializer(trend).data, status=201)
        else:
            errors = result.get('errors', [])
            return Response({
                'error': 'Market trend analysis failed',
                'details': errors
            }, status=500)


class FeatureDiscoveryViewSet(TenantQuerySetMixin, viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FeatureDiscoverySerializer
    queryset = FeatureDiscovery.objects.all()
    filterset_fields = ['organization', 'project', 'source_type', 'implementation_complexity']

    @action(detail=False, methods=['post'])
    def discover(self, request):
        """Run AI feature discovery combining all data sources."""
        project_id = request.data.get('project_id')
        if not project_id:
            return Response({'error': 'project_id required'}, status=400)

        from apps.projects.models import Project
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=404)

        if not project.organization.members.filter(user=request.user).exists():
            return Response({'error': 'Not authorized'}, status=403)

        from apps.ai_agents.services.agent_orchestrator import WorkflowOrchestrator
        result = WorkflowOrchestrator.run_workflow(
            'feature_discovery', project, request.user, {}
        )

        ai_result = result.get('results', {}).get('feature_discovery', {})
        features_data = ai_result.get('new_feature_opportunities', []) if ai_result else []

        created = []
        for fd in features_data:
            feature = FeatureDiscovery.objects.create(
                feature_name=fd.get('feature_name', 'Untitled'),
                problem_statement=fd.get('problem_statement', ''),
                evidence_links=fd.get('evidence_links', []),
                code_integration_points=fd.get('code_integration_points', []),
                implementation_complexity=fd.get('implementation_complexity', 'medium'),
                execution_plan=fd.get('execution_plan', ''),
                expected_impact=fd.get('expected_impact', {}),
                trend_alignment=fd.get('trend_alignment', {}),
                source_type=fd.get('source_type', 'combined'),
                organization=project.organization,
                project=project,
                created_by=request.user,
            )
            created.append(FeatureDiscoverySerializer(feature).data)

        return Response({
            'features_discovered': len(created),
            'features': created,
            'errors': result.get('errors', []),
        }, status=201)
