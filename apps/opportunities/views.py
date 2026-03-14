from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.core.mixins import TenantQuerySetMixin, SetCreatedByMixin, AuditMixin
from .models import Opportunity, OpportunityScore, OutcomeMetric
from .serializers import OpportunitySerializer, OpportunityScoreSerializer, OutcomeMetricSerializer


class OpportunityViewSet(TenantQuerySetMixin, SetCreatedByMixin, AuditMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OpportunitySerializer
    queryset = Opportunity.objects.prefetch_related('scores', 'outcomes', 'supporting_insights', 'evidence_refs')
    filterset_fields = ['organization', 'project', 'status']
    search_fields = ['title', 'problem_statement']
    ordering_fields = ['created_at', 'status']

    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        project_id = request.query_params.get('project')
        qs = self.get_queryset()
        if project_id:
            qs = qs.filter(project_id=project_id)

        # Get opportunities with their top scores, ordered by score
        scored = []
        for opp in qs:
            top = opp.scores.first()
            scored.append({
                'id': str(opp.id),
                'title': opp.title,
                'status': opp.status,
                'total_score': top.total_score if top else 0,
                'confidence': top.confidence_score if top else 0,
                'affected_segments': opp.affected_segments,
            })
        scored.sort(key=lambda x: x['total_score'], reverse=True)
        return Response(scored[:20])

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        opp = self.get_object()
        new_status = request.data.get('status')
        valid = [c[0] for c in Opportunity._meta.get_field('status').choices]
        if new_status not in valid:
            return Response({'error': f'Invalid status. Must be one of: {valid}'}, status=400)
        opp.status = new_status
        opp.save()
        return Response(OpportunitySerializer(opp).data)

    @action(detail=True, methods=['post'])
    def add_outcome(self, request, pk=None):
        opp = self.get_object()
        serializer = OutcomeMetricSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            opportunity=opp,
            organization=opp.organization,
            project=opp.project,
            created_by=request.user
        )
        return Response(serializer.data, status=201)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        project_id = request.query_params.get('project')
        qs = self.get_queryset()
        if project_id:
            qs = qs.filter(project_id=project_id)

        return Response({
            'total': qs.count(),
            'discovered': qs.filter(status='discovered').count(),
            'evaluating': qs.filter(status='evaluating').count(),
            'approved': qs.filter(status='approved').count(),
            'in_progress': qs.filter(status='in_progress').count(),
            'shipped': qs.filter(status='shipped').count(),
            'rejected': qs.filter(status='rejected').count(),
        })
