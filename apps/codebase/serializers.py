from rest_framework import serializers
from .models import Codebase, CodebaseAnalysis, MarketTrend, FeatureDiscovery


class CodebaseSerializer(serializers.ModelSerializer):
    latest_analysis = serializers.SerializerMethodField()

    class Meta:
        model = Codebase
        fields = [
            'id', 'name', 'source_type', 'storage_path', 'git_url',
            'file_size_bytes', 'file_count', 'uploaded_by', 'is_active',
            'latest_analysis', 'organization', 'project', 'created_by', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'file_size_bytes', 'file_count', 'storage_path']

    def get_latest_analysis(self, obj):
        analysis = obj.analyses.first()
        if analysis:
            return {
                'id': str(analysis.id),
                'status': analysis.status,
                'system_summary': analysis.system_summary[:200] if analysis.system_summary else '',
                'completed_at': analysis.completed_at,
            }
        return None


class CodebaseAnalysisSerializer(serializers.ModelSerializer):
    codebase_name = serializers.SerializerMethodField()

    class Meta:
        model = CodebaseAnalysis
        fields = [
            'id', 'codebase', 'codebase_name', 'status', 'system_summary',
            'major_modules', 'existing_features', 'api_endpoints',
            'database_models', 'capability_map', 'technology_stack',
            'architecture_patterns', 'missing_capabilities', 'improvement_areas',
            'competitor_comparison', 'new_feature_opportunities',
            'file_structure', 'error_message',
            'completed_at', 'organization', 'project', 'created_by', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']

    def get_codebase_name(self, obj):
        return obj.codebase.name if obj.codebase else ''


class MarketTrendSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketTrend
        fields = [
            'id', 'trend_summary', 'emerging_features', 'competitor_features',
            'market_gap_opportunities', 'industry_trends', 'analysis_context',
            'organization', 'project', 'created_by', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']


class FeatureDiscoverySerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureDiscovery
        fields = [
            'id', 'feature_name', 'problem_statement', 'evidence_links',
            'code_integration_points', 'implementation_complexity',
            'execution_plan', 'expected_impact', 'trend_alignment', 'source_type',
            'organization', 'project', 'created_by', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']
