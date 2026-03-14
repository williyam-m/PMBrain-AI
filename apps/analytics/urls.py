from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('insights/', views.InsightAnalyticsView.as_view(), name='insight-analytics'),
    path('opportunities/', views.OpportunityAnalyticsView.as_view(), name='opportunity-analytics'),
]
