from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import AuditEvent
from .serializers import AuditEventSerializer


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AuditEventSerializer
    queryset = AuditEvent.objects.all()
    filterset_fields = ['organization', 'action', 'entity']

    def get_queryset(self):
        qs = super().get_queryset()
        org_ids = self.request.user.memberships.values_list('organization_id', flat=True)
        return qs.filter(organization_id__in=org_ids)
