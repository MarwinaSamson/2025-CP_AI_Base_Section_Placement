from django.urls import path
from .views import (
    coor_dashboard_views,
    coor_resultsupload_views,
    coor_sectionassignment_views,
    coor_analytics_views,
    coor_reports_views
)

app_name = 'coordinator'

urlpatterns = [
    path('dashboard/', coor_dashboard_views.dashboard, name='dashboard'),
    path('results-upload/', coor_resultsupload_views.results_upload, name='results_upload'),
    path('section-assignment/', coor_sectionassignment_views.section_assignment, name='section_assignment'),
    path('analytics/', coor_analytics_views.analytics, name='analytics'),
    path('reports/', coor_reports_views.reports, name='reports'),
]