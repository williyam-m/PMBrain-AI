from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Organization, OrgMembership
from .serializers import OrganizationSerializer, OrganizationCreateSerializer, OrgMembershipSerializer


class OrganizationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        return Organization.objects.filter(
            members__user=self.request.user
        ).prefetch_related('members__user').distinct()

    def get_serializer_class(self):
        if self.action == 'create':
            return OrganizationCreateSerializer
        return OrganizationSerializer

    def perform_create(self, serializer):
        org = serializer.save()
        OrgMembership.objects.create(
            organization=org,
            user=self.request.user,
            role='org-owner'
        )

    @action(detail=True, methods=['post'])
    def invite(self, request, pk=None):
        org = self.get_object()
        membership = org.members.filter(user=request.user).first()
        if not membership or membership.role not in ['org-owner', 'product-manager']:
            return Response({'error': 'Permission denied'}, status=403)

        from apps.accounts.models import User
        email = request.data.get('email')
        role = request.data.get('role', 'reviewer')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        mem, created = OrgMembership.objects.get_or_create(
            organization=org, user=user,
            defaults={'role': role}
        )
        if not created:
            return Response({'error': 'Already a member'}, status=400)
        return Response(OrgMembershipSerializer(mem).data, status=201)

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        org = self.get_object()
        members = org.members.select_related('user').all()
        return Response(OrgMembershipSerializer(members, many=True).data)
