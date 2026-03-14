from rest_framework import serializers
from .models import DataSource


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = [
            'id', 'name', 'source_type', 'description', 'config',
            'is_active', 'last_synced_at', 'evidence_count',
            'organization', 'project', 'created_by', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'evidence_count', 'last_synced_at']
