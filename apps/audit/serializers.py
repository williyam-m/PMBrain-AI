from rest_framework import serializers
from .models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditEvent
        fields = [
            'id', 'actor', 'actor_name', 'action', 'entity', 'entity_id',
            'organization', 'metadata', 'timestamp', 'ip_address'
        ]

    def get_actor_name(self, obj):
        return obj.actor.display_name if obj.actor else 'System'
