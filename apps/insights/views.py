from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg
from apps.core.mixins import TenantQuerySetMixin, SetCreatedByMixin, AuditMixin
from .models import InsightCluster
from .serializers import InsightClusterSerializer


class InsightViewSet(TenantQuerySetMixin, SetCreatedByMixin, AuditMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = InsightClusterSerializer
    queryset = InsightCluster.objects.all()
    filterset_fields = ['organization', 'project', 'severity', 'trend_direction', 'is_validated']
    search_fields = ['title', 'summary']
    ordering_fields = ['frequency', 'severity', 'created_at', 'confidence']

    @action(detail=False, methods=['get'])
    def top_unmet_needs(self, request):
        project_id = request.query_params.get('project')
        qs = self.get_queryset()
        if project_id:
            qs = qs.filter(project_id=project_id)

        insights = qs.order_by('-frequency', '-confidence')[:10]
        return Response(InsightClusterSerializer(insights, many=True).data)

    @action(detail=False, methods=['get'])
    def by_segment(self, request):
        project_id = request.query_params.get('project')
        qs = self.get_queryset()
        if project_id:
            qs = qs.filter(project_id=project_id)

        segment_data = {}
        for insight in qs:
            for seg in (insight.segments_affected or []):
                if seg not in segment_data:
                    segment_data[seg] = {'count': 0, 'insights': []}
                segment_data[seg]['count'] += 1
                segment_data[seg]['insights'].append({
                    'id': str(insight.id),
                    'title': insight.title,
                    'severity': insight.severity,
                })
        return Response(segment_data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        project_id = request.query_params.get('project')
        qs = self.get_queryset()
        if project_id:
            qs = qs.filter(project_id=project_id)

        return Response({
            'total': qs.count(),
            'critical': qs.filter(severity='critical').count(),
            'high': qs.filter(severity='high').count(),
            'medium': qs.filter(severity='medium').count(),
            'low': qs.filter(severity='low').count(),
            'rising': qs.filter(trend_direction='rising').count(),
            'avg_confidence': qs.aggregate(avg=Avg('confidence'))['avg'] or 0,
        })
