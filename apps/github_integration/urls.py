"""
GitHub Integration URL configuration.
All endpoints under /api/integrations/github/
"""
from django.urls import path
from . import views

urlpatterns = [
    # OAuth flow
    path('connect/', views.GitHubConnectView.as_view(), name='github-connect'),
    path('callback/', views.GitHubCallbackView.as_view(), name='github-callback'),
    path('connect-token/', views.GitHubConnectTokenView.as_view(), name='github-connect-token'),

    # Status & disconnect
    path('status/', views.GitHubStatusView.as_view(), name='github-status'),
    path('disconnect/', views.GitHubDisconnectView.as_view(), name='github-disconnect'),

    # Repository operations
    path('repos/', views.GitHubReposView.as_view(), name='github-repos'),
    path('link-repo/', views.GitHubLinkRepoView.as_view(), name='github-link-repo'),
    path('linked-repos/', views.GitHubLinkedReposView.as_view(), name='github-linked-repos'),
    path('analyze-repo/', views.GitHubAnalyzeRepoView.as_view(), name='github-analyze-repo'),
    path('unlink-repo/', views.GitHubUnlinkRepoView.as_view(), name='github-unlink-repo'),
]
