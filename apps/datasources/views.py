from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.core.mixins import TenantQuerySetMixin, SetCreatedByMixin, AuditMixin
from .models import DataSource
from .serializers import DataSourceSerializer


class DataSourceViewSet(TenantQuerySetMixin, SetCreatedByMixin, AuditMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = DataSourceSerializer
    queryset = DataSource.objects.all()
    filterset_fields = ['organization', 'project', 'source_type', 'is_active']
    search_fields = ['name', 'description']
