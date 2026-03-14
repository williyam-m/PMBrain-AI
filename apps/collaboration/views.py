from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.core.mixins import TenantQuerySetMixin, SetCreatedByMixin
from .models import Comment, Approval, ReviewRequest
from .serializers import CommentSerializer, ApprovalSerializer, ReviewRequestSerializer


class CommentViewSet(TenantQuerySetMixin, SetCreatedByMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()
    filterset_fields = ['organization', 'entity_type', 'entity_id']


class ApprovalViewSet(TenantQuerySetMixin, SetCreatedByMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ApprovalSerializer
    queryset = Approval.objects.all()
    filterset_fields = ['organization', 'entity_type', 'entity_id', 'status']


class ReviewRequestViewSet(TenantQuerySetMixin, SetCreatedByMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewRequestSerializer
    queryset = ReviewRequest.objects.all()
    filterset_fields = ['organization', 'status', 'reviewer']
