"""
Role-based permission system for PMBrain AI.
"""
from rest_framework import permissions


class IsOrgMember(permissions.BasePermission):
    """User must be a member of the organization."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'organization'):
            return obj.organization.members.filter(user=request.user).exists()
        return True


class IsOrgOwner(permissions.BasePermission):
    """User must be org-owner."""
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'organization'):
            return obj.organization.members.filter(
                user=request.user, role='org-owner'
            ).exists()
        return False


class IsProductManager(permissions.BasePermission):
    """User must be product-manager or org-owner."""
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'organization'):
            return obj.organization.members.filter(
                user=request.user,
                role__in=['org-owner', 'product-manager']
            ).exists()
        return False


class RolePermission(permissions.BasePermission):
    """
    Generic role-based permission.
    Use: permission_classes = [RolePermission]
    Set allowed_roles on view.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        allowed_roles = getattr(view, 'allowed_roles', None)
        if not allowed_roles:
            return True

        org_id = (
            request.data.get('organization') or
            view.kwargs.get('org_id') or
            request.query_params.get('organization')
        )

        if not org_id:
            return True

        from apps.organizations.models import OrgMembership
        return OrgMembership.objects.filter(
            user=request.user,
            organization_id=org_id,
            role__in=allowed_roles
        ).exists()
