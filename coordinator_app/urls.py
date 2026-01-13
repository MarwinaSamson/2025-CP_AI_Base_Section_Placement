from django.urls import path
from .views import (
    coor_dashboard_views,
    coor_resultsupload_views,
    coor_sectionassignment_views,
    coor_analytics_views,
    coor_reports_views,
    coor_studentedit_views
)

app_name = 'coordinator'

urlpatterns = [
    path('dashboard/', coor_dashboard_views.dashboard, name='dashboard'),
    path('results-upload/', coor_resultsupload_views.results_upload, name='results_upload'),
    path('api/results/manual-entry/', coor_resultsupload_views.manual_entry, name='manual_entry'),
    path('api/results/bulk-upload/', coor_resultsupload_views.bulk_upload, name='bulk_upload'),
    path('api/results/download-template/', coor_resultsupload_views.download_template, name='download_template'),
    path('api/results/export/', coor_resultsupload_views.export_results, name='export_results'),
    path('api/results/<str:lrn>/delete/', coor_resultsupload_views.delete_result, name='delete_result'),
    path('api/results/<str:lrn>/view/', coor_resultsupload_views.view_result, name='view_result'),
    
    # SECTION ASSIGNMENT
    path('section-assignment/', coor_sectionassignment_views.section_assignment, name='section_assignment'),
    path('export-assignments-pdf/', coor_sectionassignment_views.export_assignments_pdf, name='export_assignments_pdf'),
    path('export-assignments-docx/', coor_sectionassignment_views.export_assignments_docx, name='export_assignments_docx'),
    
    path('analytics/', coor_analytics_views.analytics, name='analytics'),
    path('reports/', coor_reports_views.reports, name='reports'),
    path('student-edit/<str:student_id>/', coor_studentedit_views.student_edit, name='student_edit'),
]