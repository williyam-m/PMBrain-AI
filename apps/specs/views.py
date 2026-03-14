from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.core.mixins import TenantQuerySetMixin, SetCreatedByMixin, AuditMixin
from .models import GeneratedArtifact, ArtifactVersion
from .serializers import GeneratedArtifactSerializer, ArtifactVersionSerializer


class SpecViewSet(TenantQuerySetMixin, SetCreatedByMixin, AuditMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = GeneratedArtifactSerializer
    queryset = GeneratedArtifact.objects.prefetch_related('versions')
    filterset_fields = ['organization', 'project', 'status', 'artifact_type']
    search_fields = ['title']

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        artifact = self.get_object()
        versions = artifact.versions.all()
        return Response(ArtifactVersionSerializer(versions, many=True).data)

    @action(detail=True, methods=['post'])
    def chat(self, request, pk=None):
        """Conversational spec editing."""
        artifact = self.get_object()
        message = request.data.get('message', '')
        if not message:
            return Response({'error': 'message required'}, status=400)

        from apps.ai_agents.services.agent_orchestrator import WorkflowOrchestrator
        result = WorkflowOrchestrator.run_workflow(
            'edit_spec',
            artifact.project,
            request.user,
            {'artifact_id': str(artifact.id), 'message': message}
        )
        return Response(result)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        artifact = self.get_object()
        new_status = request.data.get('status')
        valid = [c[0] for c in GeneratedArtifact._meta.get_field('status').choices]
        if new_status not in valid:
            return Response({'error': f'Invalid. Must be: {valid}'}, status=400)
        artifact.status = new_status
        artifact.save()
        return Response(GeneratedArtifactSerializer(artifact).data)

    @action(detail=True, methods=['post'])
    def rollback(self, request, pk=None):
        """Rollback to a specific version."""
        artifact = self.get_object()
        version_number = request.data.get('version_number')
        if not version_number:
            return Response({'error': 'version_number required'}, status=400)
        try:
            version = artifact.versions.get(version_number=version_number)
            artifact.current_version = version.version_number
            artifact.save()
            return Response(GeneratedArtifactSerializer(artifact).data)
        except ArtifactVersion.DoesNotExist:
            return Response({'error': 'Version not found'}, status=404)

    @action(detail=True, methods=['get'])
    def diff(self, request, pk=None):
        """Compare two versions."""
        artifact = self.get_object()
        v1 = request.query_params.get('v1', 1)
        v2 = request.query_params.get('v2')
        if not v2:
            v2 = artifact.current_version

        try:
            ver1 = artifact.versions.get(version_number=v1)
            ver2 = artifact.versions.get(version_number=v2)
        except ArtifactVersion.DoesNotExist:
            return Response({'error': 'Version not found'}, status=404)

        return Response({
            'version_1': ArtifactVersionSerializer(ver1).data,
            'version_2': ArtifactVersionSerializer(ver2).data,
        })
