from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('comments', views.CommentViewSet, basename='comments')
router.register('approvals', views.ApprovalViewSet, basename='approvals')
router.register('reviews', views.ReviewRequestViewSet, basename='review-requests')

urlpatterns = [
    path('', include(router.urls)),
]
