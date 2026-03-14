from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('codebases', views.CodebaseViewSet, basename='codebases')
router.register('analyses', views.CodebaseAnalysisViewSet, basename='codebase-analyses')
router.register('trends', views.MarketTrendViewSet, basename='market-trends')
router.register('features', views.FeatureDiscoveryViewSet, basename='feature-discoveries')

urlpatterns = [
    path('', include(router.urls)),
]
