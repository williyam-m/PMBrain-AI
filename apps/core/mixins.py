"""
View mixins for tenant isolation and audit logging.
"""
from rest_framework.exceptions import PermissionDenied


class TenantQuerySetMixin:
    """Filter querysets by user's organization."""
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        org_ids = user.memberships.values_list('organization_id', flat=True)
        if hasattr(qs.model, 'organization'):
            qs = qs.filter(organization_id__in=org_ids)
        return qs


class SetCreatedByMixin:
    """Auto-set created_by and organization on create."""
    def perform_create(self, serializer):
        kwargs = {'created_by': self.request.user}
        org_id = (
            self.request.data.get('organization') or
            self.kwargs.get('org_id') or
            self.request.query_params.get('organization')
        )
        if org_id:
            from apps.organizations.models import Organization
            try:
                org = Organization.objects.get(id=org_id)
                if not org.members.filter(user=self.request.user).exists():
                    raise PermissionDenied("Not a member of this organization.")
                kwargs['organization'] = org
            except Organization.DoesNotExist:
                raise PermissionDenied("Organization not found.")
        serializer.save(**kwargs)


class AuditMixin:
    """Log API actions to audit trail."""
    def perform_create(self, serializer):
        super().perform_create(serializer)
        self._log_audit('create', serializer.instance)

    def perform_update(self, serializer):
        super().perform_update(serializer)
        self._log_audit('update', serializer.instance)

    def perform_destroy(self, instance):
        self._log_audit('delete', instance)
        super().perform_destroy(instance)

    def _log_audit(self, action, instance):
        from apps.audit.models import AuditEvent
        try:
            AuditEvent.objects.create(
                actor=self.request.user,
                action=action,
                entity=instance.__class__.__name__,
                entity_id=str(instance.pk),
                metadata={'view': self.__class__.__name__},
                organization=getattr(instance, 'organization', None)
            )
        except Exception:
            pass
