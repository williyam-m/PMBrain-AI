from rest_framework import serializers
from .models import RawEvidence, EvidenceAttachment


class EvidenceAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceAttachment
        fields = ['id', 'file_name', 'file_url', 'file_type', 'content_text']


class RawEvidenceSerializer(serializers.ModelSerializer):
    attachments = EvidenceAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = RawEvidence
        fields = [
            'id', 'data_source', 'evidence_type', 'title', 'text',
            'customer_segment', 'source_name', 'sentiment', 'urgency',
            'metadata', 'summary', 'pain_points', 'key_quotes', 'topics',
            'is_processed', 'processed_at', 'attachments',
            'organization', 'project', 'created_by', 'created_at'
        ]
        read_only_fields = [
            'id', 'created_by', 'created_at', 'summary', 'pain_points',
            'key_quotes', 'topics', 'is_processed', 'processed_at'
        ]


class BulkEvidenceSerializer(serializers.Serializer):
    """Upload multiple evidence items at once."""
    evidence_items = RawEvidenceSerializer(many=True)

    def create(self, validated_data):
        items = validated_data['evidence_items']
        created = []
        for item_data in items:
            evidence = RawEvidence.objects.create(**item_data)
            created.append(evidence)
        return created
