"""
PMBrain AI - URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    # API Routes
    path('api/auth/', include('apps.accounts.urls')),
    path('api/organizations/', include('apps.organizations.urls')),
    path('api/projects/', include('apps.projects.urls')),
    path('api/datasources/', include('apps.datasources.urls')),
    path('api/evidence/', include('apps.evidence.urls')),
    path('api/insights/', include('apps.insights.urls')),
    path('api/opportunities/', include('apps.opportunities.urls')),
    path('api/agents/', include('apps.ai_agents.urls')),
    path('api/specs/', include('apps.specs.urls')),
    path('api/collaboration/', include('apps.collaboration.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/audit/', include('apps.audit.urls')),
    path('api/codebase/', include('apps.codebase.urls')),
    path('api/integrations/github/', include('apps.github_integration.urls')),
]

# Landing page at root, App at /dashboard, auth routes
from django.views.generic import TemplateView
urlpatterns += [
    path('dashboard/', TemplateView.as_view(template_name='index.html'), name='frontend'),
    path('signin/', TemplateView.as_view(template_name='index.html'), name='signin'),
    path('signup/', TemplateView.as_view(template_name='index.html'), name='signup'),
    # Legacy /landing/ redirect — backward compatibility
    path('landing/', TemplateView.as_view(template_name='landing.html'), name='landing-legacy'),
    # Landing page is now the homepage
    path('', TemplateView.as_view(template_name='landing.html'), name='landing'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
