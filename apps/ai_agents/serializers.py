from rest_framework import serializers
from .models import AgentRun, ProductPrompt


class AgentRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentRun
        fields = [
            'id', 'agent_type', 'status', 'input_data', 'output_data',
            'error_message', 'started_at', 'completed_at', 'duration_seconds',
            'tokens_used', 'organization', 'project', 'created_by', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RunAgentSerializer(serializers.Serializer):
    workflow = serializers.ChoiceField(choices=[
        ('full_pipeline', 'Full Pipeline'),
        ('evidence_to_insights', 'Evidence to Insights'),
        ('insights_to_opportunities', 'Insights to Opportunities'),
        ('what_to_build', 'What To Build Next'),
        ('generate_spec', 'Generate Spec'),
        ('predict_impact', 'Predict Impact'),
        ('score_opportunities', 'Score Opportunities'),
        ('edit_spec', 'Edit Spec'),
        ('analyze_codebase', 'Analyze Codebase'),
        ('market_trends', 'Market Trends'),
        ('feature_discovery', 'Feature Discovery'),
        ('full_discovery', 'Full Discovery Pipeline'),
    ])
    project_id = serializers.UUIDField()
    input_data = serializers.JSONField(required=False, default=dict)


class ProductPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductPrompt
        fields = [
            'id', 'agent_type', 'name', 'prompt_template', 'version',
            'is_active', 'metadata', 'organization', 'project',
            'created_by', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']
