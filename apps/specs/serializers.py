from rest_framework import serializers
from .models import GeneratedArtifact, ArtifactVersion


class ArtifactVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtifactVersion
        fields = [
            'id', 'version_number', 'content', 'change_summary',
            'readiness_score', 'created_by', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class GeneratedArtifactSerializer(serializers.ModelSerializer):
    versions = ArtifactVersionSerializer(many=True, read_only=True)
    latest_content = serializers.SerializerMethodField()
    readiness_score = serializers.FloatField(read_only=True)

    class Meta:
        model = GeneratedArtifact
        fields = [
            'id', 'opportunity', 'artifact_type', 'title', 'current_version',
            'status', 'metadata', 'versions', 'latest_content', 'readiness_score',
            'organization', 'project', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_latest_content(self, obj):
        v = obj.latest_version
        return v.content if v else {}
