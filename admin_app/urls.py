from django.urls import path
from .views import (
    analytics_views,
    dashboard_views,
    enrollment_views,
    log_in_out_views,
    masterlist_views,
    reports_views,
    sections_views,
    settings_views,
    studentdetails_views,
    studentedit_views,
    move_request_views,

)

app_name = 'admin_app'

urlpatterns = [
    # Authentication
    path('login/', log_in_out_views.admin_login, name='login'),
    path('logout/', log_in_out_views.admin_logout, name='logout'),
    
    # Dashboard
    path('', dashboard_views.dashboard, name='dashboard'),
    path('dashboard/', dashboard_views.dashboard, name='dashboard_alt'),
    
    # Dashboard API Endpoints
    path('api/dashboard/header/', dashboard_views.dashboard_header_data, name='api_dashboard_header'),
    path('api/dashboard/statistics/', dashboard_views.dashboard_statistics, name='api_dashboard_statistics'),
    path('api/dashboard/notifications/', dashboard_views.dashboard_notifications, name='api_dashboard_notifications'),
    path('api/dashboard/programs/', dashboard_views.dashboard_programs_overview, name='api_dashboard_programs'),
    
    
    # Analytics
    path('analytics/', analytics_views.analytics, name='analytics'),
    path('api/analytics/header/', analytics_views.analytics_header_data, name='api_analytics_header'),
    path('api/analytics/data/', analytics_views.analytics_data, name='analytics_data'),
    
    # Enrollment
    path('enrollment/', enrollment_views.enrollment_list, name='enrollment'),
    path('enrollment/<str:student_id>/', enrollment_views.enrollment_detail, name='enrollment_detail'),

    # Enrollment API
    path('api/enrollment/header/', enrollment_views.enrollment_header_data, name='api_enrollment_header'),
    path('api/enrollment/summary/', enrollment_views.enrollment_summary, name='api_enrollment_summary'),
    path('api/enrollment/requests/', enrollment_views.enrollment_requests, name='api_enrollment_requests'),
    
    # Sections
    path('sections/', sections_views.sections_list, name='sections'),
    path('api/sections/header/', sections_views.sections_header_data, name='api_sections_header'),
    path('sections/<str:program>/', sections_views.sections_by_program, name='sections_by_program'),
    path('sections/<str:program>/<int:section_id>/', sections_views.section_detail, name='section_detail'),

    # Sections/Subjects/Buildings API
    path('api/programs/', sections_views.get_programs, name='api_get_programs'),
    path('api/programs/all/', sections_views.get_all_programs, name='api_get_all_programs'),
    path('api/programs/add/', sections_views.add_program, name='api_add_program'),
    path('api/programs/<int:program_id>/update/', sections_views.update_program, name='api_update_program'),
    path('api/programs/<int:program_id>/delete/', sections_views.delete_program, name='api_delete_program'),
    path('api/programs/<int:program_id>/toggle-status/', sections_views.toggle_program_status, name='api_toggle_program_status'),
    path('api/teachers/', sections_views.get_teachers, name='api_get_teachers'),
    path('api/buildings/', sections_views.get_buildings, name='api_get_buildings'),
    path('api/rooms/', sections_views.get_rooms, name='api_get_rooms'),
    path('api/subjects/', sections_views.get_subjects, name='api_get_subjects'),
    path('api/subjects/add/', sections_views.add_subject, name='api_add_subject'),
    path('api/subjects/<int:subject_id>/update/', sections_views.update_subject, name='api_update_subject'),
    path('api/subjects/<int:subject_id>/delete/', sections_views.delete_subject, name='api_delete_subject'),
    path('api/sections/', sections_views.get_sections, name='api_get_sections'),
    path('api/sections/add/', sections_views.add_section, name='api_add_section'),
    path('api/sections/<int:section_id>/update/', sections_views.update_section, name='api_update_section'),
    path('api/sections/<int:section_id>/delete/', sections_views.delete_section, name='api_delete_section'),
    
    # Masterlist
    path('masterlist/', masterlist_views.masterlist, name='masterlist'),
    path('masterlist/<int:section_id>/', masterlist_views.masterlist_by_section, name='masterlist_by_section'),
    
    # Student Details & Edit
    path('student/<str:lrn>/', studentdetails_views.student_details, name='student_details'),
    path('student/<str:student_id>/edit/', studentedit_views.student_edit, name='student_edit'),
    
    # student edit-move
    path('api/move-requests/pending/', move_request_views.get_pending_move_requests, name='api_pending_move_requests'), 
    path('api/move-requests/<int:move_request_id>/review/', move_request_views.review_move_request, name='api_review_move_request'),
    path('api/move-requests/sections/', move_request_views.get_sections_for_program, name='api_sections_for_program'),
    path('api/sections/', studentedit_views.get_sections_by_program, name='api_sections'),
path('api/admin-move/', studentedit_views.admin_move_student, name='api_admin_move'),
    
    # Student Edit API Endpoints
    path('api/student/<str:student_id>/details/', studentedit_views.get_student_details, name='api_get_student_details'),
    path('api/student/<str:student_id>/update/student-data/', studentedit_views.update_student_data, name='api_update_student_data'),
    path('api/student/<str:student_id>/update/family-data/', studentedit_views.update_family_data, name='api_update_family_data'),
    path('api/student/<str:student_id>/update/survey-data/', studentedit_views.update_survey_data, name='api_update_survey_data'),
    path('api/student/<str:student_id>/update/academic-data/', studentedit_views.update_academic_data, name='api_update_academic_data'),
    path('api/student/<str:student_id>/update/program-selection/', studentedit_views.update_program_selection, name='api_update_program_selection'),
    path('api/student/<str:student_id>/update/status/', studentedit_views.update_enrollment_status, name='api_update_enrollment_status'),
    path('api/student/<str:student_id>/upload/', studentedit_views.upload_student_file, name='api_upload_student_file'),
    
    # Reports
    path('reports/', reports_views.reports, name='reports'),
    path('api/reports/header/', reports_views.reports_header_data, name='api_reports_header'),
    path('reports/generate/', reports_views.generate_report, name='generate_report'),
    path('api/reports/summary/', reports_views.reports_summary, name='api_reports_summary'),
    path('api/reports/preview/', reports_views.get_report_preview, name='api_reports_preview'),
    path('api/reports/export/enrolled/', reports_views.export_enrolled_students, name='export_enrolled'),
    path('api/reports/export/sections/', reports_views.export_section_list, name='export_sections'),
    path('api/reports/export/promotion/', reports_views.export_promotion_status, name='export_promotion'),
    path('api/reports/export/pending/', reports_views.export_pending_enrollments, name='export_pending'),
    path('api/reports/export/masterlist/', reports_views.export_masterlist, name='export_masterlist'),
    path('api/reports/export/transferees/', reports_views.export_transferees, name='export_transferees'),
    path('api/reports/export/probation/', reports_views.export_probation_list, name='export_probation'),
    path('api/reports/export/ai-vs-manual/', reports_views.export_ai_vs_manual, name='export_ai_vs_manual'),
    path('api/reports/export/no-section/', reports_views.export_no_section, name='export_no_section'),
    path('api/reports/export/documents/', reports_views.export_document_compliance, name='export_documents'),
    path('api/reports/export/activity-log/', reports_views.export_activity_log, name='export_activity_log'),
    path('api/reports/export/enrollee-breakdown/', reports_views.export_enrollee_type_breakdown, name='export_enrollee_breakdown'),
    path('api/reports/export/move-requests/', reports_views.export_move_requests, name='export_move_requests'),
    
    # Settings
    path('settings/', settings_views.settings, name='settings'),
    path('api/settings/header/', settings_views.settings_header_data, name='api_settings_header'),
    path('settings/users/', settings_views.manage_users, name='manage_users'),
    path('settings/content/', settings_views.manage_content, name='manage_content'),
    path('api/generate-promotion-statuses/', settings_views.generate_promotion_statuses, name='api_generate_promotion_statuses'),
    
    # Settings API Endpoints
    path('api/users/', settings_views.get_users, name='api_get_users'),
    path('api/users/add/', settings_views.add_user, name='api_add_user'),
        # User CRUD API Endpoints (Settings > Users)
        path('api/users/<int:user_id>/', settings_views.get_user_profile, name='api_get_user_profile'),
        path('api/users/<int:user_id>/update/', settings_views.update_user_profile, name='api_update_user_profile'),
        path('api/users/<int:user_id>/delete/', settings_views.delete_user_profile, name='api_delete_user_profile'),
    path('api/positions/', settings_views.get_positions, name='api_get_positions'),
    path('api/positions/add/', settings_views.add_position, name='api_add_position'),
    path('api/positions/<int:position_id>/update/', settings_views.update_position, name='api_update_position'),
    path('api/positions/<int:position_id>/delete/', settings_views.delete_position, name='api_delete_position'),
    path('api/departments/', settings_views.get_departments, name='api_get_departments'),
    path('api/departments/add/', settings_views.add_department, name='api_add_department'),
    path('api/departments/<int:department_id>/update/', settings_views.update_department, name='api_update_department'),
    path('api/departments/<int:department_id>/delete/', settings_views.delete_department, name='api_delete_department'),
    # Teacher Management API Endpoints
    path('api/settings/teachers/', settings_views.get_teachers_for_settings, name='api_get_teachers_for_settings'),
    path('api/settings/teachers/add/', settings_views.add_teacher, name='api_add_teacher'),
    path('api/settings/teachers/<int:teacher_id>/update/', settings_views.update_teacher, name='api_update_teacher'),
    path('api/settings/teachers/<int:teacher_id>/delete/', settings_views.delete_teacher, name='api_delete_teacher'),
    # School Years API Endpoints
    path('api/school-years/', settings_views.get_school_years, name='api_get_school_years'),
    path('api/school-years/add/', settings_views.add_school_year, name='api_add_school_year'),
    path('api/school-years/<int:school_year_id>/update/', settings_views.update_school_year, name='api_update_school_year'),
    path('api/school-years/<int:school_year_id>/delete/', settings_views.delete_school_year, name='api_delete_school_year'),
    
    # Document Requirements API Endpoints (Settings > Others)
    path('api/document-requirements/', settings_views.get_document_requirements, name='api_get_document_requirements'),
    path('api/document-requirements/add/', settings_views.add_document_requirement, name='api_add_document_requirement'),
    path('api/document-requirements/<int:requirement_id>/update/', settings_views.update_document_requirement, name='api_update_document_requirement'),
    path('api/document-requirements/<int:requirement_id>/delete/', settings_views.delete_document_requirement, name='api_delete_document_requirement'),
    
    # Content Management API Endpoints
    path('api/content/settings/', settings_views.get_content_settings, name='api_get_content_settings'),
    path('api/content/save/', settings_views.save_content_setting, name='api_save_content_setting'),
    path('api/content/upload-image/', settings_views.upload_content_image, name='api_upload_content_image'),
    path('api/staff/', settings_views.get_staff_members, name='api_get_staff_members'),
    path('api/staff/add/', settings_views.add_staff_member, name='api_add_staff_member'),
    path('api/staff/<int:staff_id>/update/', settings_views.update_staff_member, name='api_update_staff_member'),
    path('api/staff/<int:staff_id>/delete/', settings_views.delete_staff_member, name='api_delete_staff_member'),
    path('api/content/delete-image/', settings_views.delete_content_image, name='delete_content_image'),
    
    # Buildings & Rooms API Endpoints
    path('api/buildings/', settings_views.get_buildings_with_rooms, name='api_get_buildings_with_rooms'),
    path('api/buildings/add/', settings_views.add_building, name='api_add_building'),
    path('api/buildings/<int:building_id>/update/', settings_views.update_building, name='api_update_building'),
    path('api/buildings/<int:building_id>/delete/', settings_views.delete_building, name='api_delete_building'),
    # Note: api/rooms/ is handled by sections_views.get_rooms (line 42)
    path('api/rooms/add/', settings_views.add_room, name='api_add_room'),
    path('api/rooms/<int:room_id>/update/', settings_views.update_room, name='api_update_room'),
    path('api/rooms/<int:room_id>/delete/', settings_views.delete_room, name='api_delete_room'),
    
    # Grade Level API Endpoints (Settings > Others)
    path('api/grade-levels/', settings_views.get_grade_levels, name='api_get_grade_levels'),
    path('api/grade-levels/add/', settings_views.add_grade_level, name='api_add_grade_level'),
    path('api/grade-levels/<int:grade_level_id>/update/', settings_views.update_grade_level, name='api_update_grade_level'),
    path('api/grade-levels/<int:grade_level_id>/delete/', settings_views.delete_grade_level, name='api_delete_grade_level'),

    # Activity Logs API Endpoint
    path('api/activity-logs/', settings_views.get_activity_logs, name='api_get_activity_logs'),
]