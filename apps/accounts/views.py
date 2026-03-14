from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .models import User


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = RefreshToken.for_user(user)

        # Auto-create a default organization and project for new users
        org_data = self._setup_default_org(user, request.data)

        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(tokens.access_token),
                'refresh': str(tokens),
            },
            'organization': org_data,
        }, status=status.HTTP_201_CREATED)

    def _setup_default_org(self, user, data):
        """Create a default organization and project for newly registered users."""
        from apps.organizations.models import Organization, OrgMembership
        from apps.projects.models import Project
        from django.utils.text import slugify
        import uuid

        org_name = data.get('organization_name', f"{user.display_name}'s Workspace")
        slug_base = slugify(org_name)[:80] or 'workspace'
        slug = slug_base
        counter = 1
        while Organization.objects.filter(slug=slug).exists():
            slug = f"{slug_base}-{counter}"
            counter += 1

        org = Organization.objects.create(
            name=org_name,
            slug=slug,
            description=f"Workspace for {user.display_name}",
        )
        OrgMembership.objects.create(
            organization=org,
            user=user,
            role='org-owner',
        )

        # Create a default project
        project_name = data.get('project_name', 'My Product')
        proj_slug = slugify(project_name)[:80] or 'my-product'
        proj_counter = 1
        while Project.objects.filter(organization=org, slug=proj_slug).exists():
            proj_slug = f"{slugify(project_name)[:70]}-{proj_counter}"
            proj_counter += 1

        Project.objects.create(
            name=project_name,
            slug=proj_slug,
            description='Default project',
            organization=org,
            created_by=user,
        )

        return {
            'id': str(org.id),
            'name': org.name,
            'slug': org.slug,
        }


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        tokens = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(tokens.access_token),
                'refresh': str(tokens),
            }
        })


class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
