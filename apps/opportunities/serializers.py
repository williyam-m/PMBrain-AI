from rest_framework import serializers
from .models import Opportunity, OpportunityScore, OutcomeMetric


class OpportunityScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpportunityScore
        fields = [
            'id', 'frequency_score', 'revenue_impact', 'retention_impact',
            'strategic_alignment', 'effort_estimate', 'confidence_score',
            'total_score', 'weights_used', 'created_at'
        ]
        read_only_fields = ['id', 'total_score', 'created_at']


class OutcomeMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutcomeMetric
        fields = [
            'id', 'metric_type', 'predicted_value', 'actual_value',
            'measured_at', 'notes', 'created_at'
        ]


class OpportunitySerializer(serializers.ModelSerializer):
    scores = OpportunityScoreSerializer(many=True, read_only=True)
    outcomes = OutcomeMetricSerializer(many=True, read_only=True)
    top_score = serializers.SerializerMethodField()
    insight_count = serializers.SerializerMethodField()
    evidence_count = serializers.SerializerMethodField()

    class Meta:
        model = Opportunity
        fields = [
            'id', 'title', 'problem_statement', 'affected_segments',
            'proposed_solution', 'assumptions', 'risks', 'alternatives',
            'implementation_outline', 'status',
            'supporting_insights', 'evidence_refs',
            'scores', 'outcomes', 'top_score', 'insight_count', 'evidence_count',
            'organization', 'project', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_top_score(self, obj):
        score = obj.scores.first()
        return score.total_score if score else 0

    def get_insight_count(self, obj):
        return obj.supporting_insights.count()

    def get_evidence_count(self, obj):
        return obj.evidence_refs.count()
