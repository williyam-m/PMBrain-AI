from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.core.mixins import TenantQuerySetMixin
from apps.projects.models import Project
from apps.organizations.models import OrgMembership
from .models import AgentRun
from .serializers import AgentRunSerializer, RunAgentSerializer
from .services.agent_orchestrator import WorkflowOrchestrator


def _validate_project_access(user, project_id):
    """Validate user has access to the project via organization membership.
    Returns (project, error_response) tuple."""
    try:
        project = Project.objects.select_related('organization').get(id=project_id)
    except Project.DoesNotExist:
        return None, Response({'error': 'Project not found'}, status=404)

    # Check org membership
    has_access = OrgMembership.objects.filter(
        organization=project.organization,
        user=user
    ).exists()

    if not has_access:
        return None, Response(
            {'error': 'Not a member of this organization. Please create or join an organization first.'},
            status=403
        )

    return project, None


class AgentRunViewSet(TenantQuerySetMixin, viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AgentRunSerializer
    queryset = AgentRun.objects.all()
    filterset_fields = ['organization', 'project', 'agent_type', 'status']


class RunAgentView(APIView):
    """Execute an AI agent workflow."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RunAgentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        workflow = serializer.validated_data['workflow']
        project_id = serializer.validated_data['project_id']
        input_data = serializer.validated_data.get('input_data', {})

        project, error = _validate_project_access(request.user, project_id)
        if error:
            return error

        # Run workflow
        result = WorkflowOrchestrator.run_workflow(
            workflow, project, request.user, input_data
        )

        # Send WebSocket notification
        try:
            self._notify_websocket(request.user, project, workflow, result)
        except Exception:
            pass

        return Response(result, status=200)

    def _notify_websocket(self, user, project, workflow, result):
        """Send real-time update via WebSocket."""
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"project_{project.id}",
                    {
                        "type": "agent_update",
                        "message": {
                            "workflow": workflow,
                            "status": "completed" if not result.get('errors') else "completed_with_errors",
                        }
                    }
                )
        except Exception:
            pass


class WhatToBuildView(APIView):
    """
    The flagship endpoint: "What should we build next?"
    Enhanced with codebase and market trend awareness.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        project_id = request.data.get('project_id')
        query = request.data.get('query', 'What should we build next?')

        if not project_id:
            return Response({'error': 'project_id required'}, status=400)

        project, error = _validate_project_access(request.user, project_id)
        if error:
            return error

        result = WorkflowOrchestrator.run_workflow(
            'what_to_build', project, request.user, {'query': query}
        )

        return Response(result)
