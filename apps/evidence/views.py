from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.core.mixins import TenantQuerySetMixin, SetCreatedByMixin, AuditMixin
from .models import RawEvidence
from .serializers import RawEvidenceSerializer


class EvidenceViewSet(TenantQuerySetMixin, SetCreatedByMixin, AuditMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = RawEvidenceSerializer
    queryset = RawEvidence.objects.all()
    filterset_fields = ['organization', 'project', 'evidence_type', 'customer_segment', 'is_processed', 'sentiment']
    search_fields = ['title', 'text', 'summary']
    ordering_fields = ['created_at', 'urgency']

    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        """Upload multiple evidence items at once."""
        items = request.data.get('items', [])
        if not items:
            return Response({'error': 'No items provided'}, status=400)

        created = []
        for item in items:
            item['created_by'] = request.user.id
            serializer = RawEvidenceSerializer(data=item)
            if serializer.is_valid():
                serializer.save(created_by=request.user)
                created.append(serializer.data)

        return Response({
            'created': len(created),
            'items': created
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get evidence statistics for a project."""
        project_id = request.query_params.get('project')
        qs = self.get_queryset()
        if project_id:
            qs = qs.filter(project_id=project_id)

        total = qs.count()
        processed = qs.filter(is_processed=True).count()
        by_type = {}
        for item in qs.values('evidence_type').annotate(count=models.Count('id')):
            by_type[item['evidence_type']] = item['count']
        by_segment = {}
        for item in qs.values('customer_segment').annotate(count=models.Count('id')):
            by_segment[item['customer_segment']] = item['count']

        return Response({
            'total': total,
            'processed': processed,
            'unprocessed': total - processed,
            'by_type': by_type,
            'by_segment': by_segment,
        })
