from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('runs', views.AgentRunViewSet, basename='agent-runs')

urlpatterns = [
    path('', include(router.urls)),
    path('run/', views.RunAgentView.as_view(), name='run-agent'),
    path('what-to-build/', views.WhatToBuildView.as_view(), name='what-to-build'),
]
