from django.urls import path
from .views import (
    coor_dashboard_views,
    coor_resultsupload_views,
    coor_sectionassignment_views,
    coor_analytics_views,
    coor_reports_views,
    coor_studentedit_views,
    coor_sectionmanagement_views
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
    # path('student-edit/<str:student_id>/', coor_studentedit_views.student_edit, name='student_edit'),
    path('student-edit/<str:student_id>/', coor_studentedit_views.student_edit, name='student_edit'),
    path('api/student/<str:student_id>/details/', coor_studentedit_views.get_student_details, name='get_student_details'),
    path('api/student/<str:student_id>/update/student-data/', coor_studentedit_views.update_student_data, name='update_student_data'),
    path('api/student/<str:student_id>/update/family-data/', coor_studentedit_views.update_family_data, name='update_family_data'),
    path('api/student/<str:student_id>/update/survey-data/', coor_studentedit_views.update_survey_data, name='update_survey_data'),
    path('api/student/<str:student_id>/update/academic-data/', coor_studentedit_views.update_academic_data, name='update_academic_data'),
    path('api/student/<str:student_id>/update/program-selection/', coor_studentedit_views.update_program_selection, name='update_program_selection'),
    path('api/student/<str:student_id>/update/enrollment-status/', coor_studentedit_views.update_enrollment_status, name='update_enrollment_status'),
    path('api/student/<str:student_id>/upload/', coor_studentedit_views.upload_student_file, name='upload_student_file'),
    path('api/student/<str:student_id>/approve/', coor_studentedit_views.approve_enrollment, name='approve_enrollment'),
    path('api/sections/', coor_studentedit_views.get_sections_by_program, name='get_sections_by_program'),
    
    
    path('sections/', coor_sectionmanagement_views.section_management, name='section_management'),
]