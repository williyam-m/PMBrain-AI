from rest_framework import serializers
from .models import InsightCluster, InsightTrend


class InsightTrendSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsightTrend
        fields = ['id', 'period', 'mention_count', 'severity_score', 'notes', 'created_at']


class InsightClusterSerializer(serializers.ModelSerializer):
    trends = InsightTrendSerializer(many=True, read_only=True)
    evidence_count = serializers.SerializerMethodField()

    class Meta:
        model = InsightCluster
        fields = [
            'id', 'title', 'summary', 'frequency', 'severity',
            'segments_affected', 'representative_quotes', 'trend_direction',
            'confidence', 'topics', 'evidence_refs', 'is_validated',
            'trends', 'evidence_count',
            'organization', 'project', 'created_by', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']

    def get_evidence_count(self, obj):
        return obj.evidence_refs.count()
