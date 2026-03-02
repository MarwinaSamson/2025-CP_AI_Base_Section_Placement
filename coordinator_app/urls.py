from django.urls import path
from . import views
from .views.uploadmasterlist_view import upload_section_masterlist
from .views import (
    coor_dashboard_views,
    coor_resultsupload_views,
    coor_analytics_views,
    coor_reports_views,
    coor_studentedit_views,
    coor_sectionmanagement_views,
    coor_masterlist_views,
    coor_enrollment_management_views,
    coor_studentdetails,
    coor_grade_level_views,
)


app_name = 'coordinator'

urlpatterns = [
    # Main pages
    path('dashboard/', coor_dashboard_views.dashboard, name='dashboard'),
    path('results-upload/', coor_resultsupload_views.results_upload, name='results_upload'),
     path('upload-section-masterlist/', upload_section_masterlist, name='upload_section_masterlist'),

    # Unified Enrollment Management (New - with dynamic content switching)
    path('enrollment-management/', coor_enrollment_management_views.enrollment_management, name='enrollment_management'),

    # Legacy section assignment (redirect to new enrollment management)
    path('section-assignment/', coor_enrollment_management_views.enrollment_management, name='section_assignment'),

    path('analytics/', coor_analytics_views.analytics, name='analytics'),
    path('reports/', coor_reports_views.reports, name='reports'),
    path('reports/generate/enrollment/', coor_reports_views.generate_enrollment_report, name='generate_enrollment_report'),
    path('reports/generate/academic/', coor_reports_views.generate_academic_report, name='generate_academic_report'),
    path('reports/generate/sections/', coor_reports_views.generate_section_report, name='generate_section_report'),
    path('reports/generate/enrollment-analytics/', coor_reports_views.generate_enrollment_analytics_report, name='generate_enrollment_analytics_report'),
    path('reports/generate/section-analytics/', coor_reports_views.generate_section_analytics_report, name='generate_section_analytics_report'),
    path('reports/generate/program-summary/', coor_reports_views.generate_program_summary_report, name='generate_program_summary_report'),
    path('reports/generate/activity-log/', coor_reports_views.generate_activity_log_report, name='generate_activity_log_report'),
    path('reports/generate/custom/', coor_reports_views.generate_custom_report, name='generate_custom_report'),
    path('reports/download-form-template/', coor_reports_views.download_template, name='download_form_template'),
    path('section-management/', coor_sectionmanagement_views.section_management, name='section_management'),
    path('api/section/<int:section_id>/toggle-publish/', coor_sectionmanagement_views.toggle_masterlist_published, name='toggle_masterlist_published'),
     
    
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
    
    # API Endpoints - Approval and Placement (THE KEY ENDPOINTS)
    path('api/student/<str:student_id>/approve-and-place/', 
         coor_studentedit_views.approve_and_place_student, 
         name='api_approve_and_place'),
    
    path('api/student/<str:student_id>/revert-approval/', 
         coor_studentedit_views.revert_approval, 
         name='api_revert_approval'),
    
    path('api/student/<str:student_id>/reject/', 
         coor_studentedit_views.reject_enrollment, 
         name='api_reject_enrollment'),
    
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

    # Enrollment Management API Endpoints (New - for dynamic content)
    path('api/enrollment/manual-content/', coor_enrollment_management_views.get_manual_mode_content, name='api_manual_content'),
    path('api/enrollment/ai-content/', coor_enrollment_management_views.get_ai_mode_content, name='api_ai_content'),
    path('api/enrollment/refresh/', coor_enrollment_management_views.refresh_enrollment_data, name='api_refresh_enrollment'),
    path('api/toggle-ai-mode/', coor_enrollment_management_views.toggle_ai_mode, name='toggle_ai_mode'),
    
    # Activity Log API
    path('api/activity-logs/', coor_reports_views.get_activity_logs, name='api_activity_logs'),
    path('api/pending-enrollment-count/', coor_dashboard_views.pending_enrollment_count, name='pending_enrollment_count'),
    
    #     Student Details
    path('student-details/<str:lrn>/', coor_studentdetails.student_details, name='student_details'),
    
    path('api/set-grade-level/',  coor_grade_level_views.set_active_grade_level, name='set_grade_level'),
    path('api/get-grade-levels/', coor_grade_level_views.get_grade_levels,  name='get_grade_levels'),
]
