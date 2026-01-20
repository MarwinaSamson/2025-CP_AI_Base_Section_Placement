from django.urls import path
from . import views
from .views import (
    coor_dashboard_views,
    coor_resultsupload_views,
    coor_sectionassignment_views,
    coor_analytics_views,
    coor_reports_views,
    coor_studentedit_views,
    coor_sectionmanagement_views,
    coor_masterlist_views
)

app_name = 'coordinator'

urlpatterns = [
    # Main pages
    path('dashboard/', coor_dashboard_views.dashboard, name='dashboard'),
    path('results-upload/', coor_resultsupload_views.results_upload, name='results_upload'),
    path('section-assignment/', coor_sectionassignment_views.section_assignment, name='section_assignment'),
    path('analytics/', coor_analytics_views.analytics, name='analytics'),
    path('reports/', coor_reports_views.reports, name='reports'),
    path('section-management/', coor_sectionmanagement_views.section_management, name='section_management'),
    
    # Masterlist
    path('masterlist/<int:section_id>/', coor_masterlist_views.masterlist_by_section, name='masterlist_by_section'),
    path('masterlist/<int:section_id>/export/excel/', coor_masterlist_views.export_masterlist_excel, name='export_masterlist_excel'),
    path('masterlist/<int:section_id>/export/pdf/', coor_masterlist_views.export_masterlist_pdf, name='export_masterlist_pdf'),
    path('masterlist/<int:section_id>/export/docx/', coor_masterlist_views.export_masterlist_docx, name='export_masterlist_docx'),

    # Student Edit Page
    path('student-edit/<str:student_id>/', coor_studentedit_views.student_edit, name='student_edit'),

    # Student Edit Page
    path('student-edit/<str:student_id>/', coor_studentedit_views.student_edit, name='student_edit'),
    
    # API Endpoints - Student Data Retrieval
    path('api/student/<str:student_id>/details/', 
         coor_studentedit_views.get_student_details, 
         name='api_student_details'),
    
    # API Endpoints - Student Data Updates
    path('api/student/<str:student_id>/update/student-data/', 
         coor_studentedit_views.update_student_data, 
         name='api_update_student_data'),
    
    path('api/student/<str:student_id>/update/family-data/', 
         coor_studentedit_views.update_family_data, 
         name='api_update_family_data'),
    
    path('api/student/<str:student_id>/update/survey-data/', 
         coor_studentedit_views.update_survey_data, 
         name='api_update_survey_data'),
    
    path('api/student/<str:student_id>/update/academic-data/', 
         coor_studentedit_views.update_academic_data, 
         name='api_update_academic_data'),
    
    path('api/student/<str:student_id>/update/program-selection/', 
         coor_studentedit_views.update_program_selection, 
         name='api_update_program_selection'),
    
    # API Endpoints - Approval and Placement (THE KEY ENDPOINT)
    path('api/student/<str:student_id>/approve-and-place/', 
         coor_studentedit_views.approve_and_place_student, 
         name='api_approve_and_place'),
    
    # API Endpoints - Helper Functions
    path('api/sections/', 
         coor_studentedit_views.get_sections_by_program, 
         name='api_sections_by_program'),

    # Results API Endpoints
    path('api/results/manual-entry/', coor_resultsupload_views.manual_entry, name='manual_entry'),
    path('api/results/bulk-upload/', coor_resultsupload_views.bulk_upload, name='bulk_upload'),
    path('api/results/download-template/', coor_resultsupload_views.download_template, name='download_template'),
    path('api/results/export/', coor_resultsupload_views.export_results, name='export_results'),
    path('api/results/<str:lrn>/delete/', coor_resultsupload_views.delete_result, name='delete_result'),
    path('api/results/<str:lrn>/view/', coor_resultsupload_views.view_result, name='view_result'),

    # Section Assignment API Endpoints
    path('export-assignments-pdf/', coor_sectionassignment_views.export_assignments_pdf, name='export_assignments_pdf'),
    path('export-assignments-docx/', coor_sectionassignment_views.export_assignments_docx, name='export_assignments_docx'),
    
     #AI Assistant Mode Toggle
    path('api/toggle-ai-mode/', coor_sectionassignment_views.toggle_ai_mode, name='toggle_ai_mode'),
]