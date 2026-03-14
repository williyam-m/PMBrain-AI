from rest_framework import serializers
from .models import Comment, Approval, ReviewRequest
from apps.accounts.serializers import UserSerializer


class CommentSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'entity_type', 'entity_id', 'text', 'mentions',
            'parent', 'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']

    def get_created_by_name(self, obj):
        return obj.created_by.display_name if obj.created_by else 'Unknown'


class ApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Approval
        fields = [
            'id', 'entity_type', 'entity_id', 'status', 'reviewer',
            'notes', 'organization', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ReviewRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewRequest
        fields = [
            'id', 'entity_type', 'entity_id', 'requested_by',
            'reviewer', 'message', 'status', 'organization', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
