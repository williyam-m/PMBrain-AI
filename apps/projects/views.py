from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.core.mixins import TenantQuerySetMixin, SetCreatedByMixin, AuditMixin
from .models import Project
from .serializers import ProjectSerializer


class ProjectViewSet(TenantQuerySetMixin, SetCreatedByMixin, AuditMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectSerializer
    queryset = Project.objects.all()
    filterset_fields = ['organization', 'is_active']
    search_fields = ['name', 'description']
