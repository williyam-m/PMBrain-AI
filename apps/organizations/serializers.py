from rest_framework import serializers
from .models import Organization, OrgMembership
from apps.accounts.serializers import UserSerializer


class OrgMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = OrgMembership
        fields = ['id', 'user', 'role', 'joined_at']


class OrganizationSerializer(serializers.ModelSerializer):
    members = OrgMembershipSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ['id', 'name', 'slug', 'description', 'logo_url', 'members', 'member_count', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_member_count(self, obj):
        return obj.members.count()


class OrganizationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['name', 'slug', 'description']
