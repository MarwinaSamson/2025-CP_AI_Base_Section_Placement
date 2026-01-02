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
)

app_name = 'admin_app'

urlpatterns = [
    # Authentication
    path('login/', log_in_out_views.admin_login, name='login'),
    path('logout/', log_in_out_views.admin_logout, name='logout'),
    
    # Dashboard
    path('', dashboard_views.dashboard, name='dashboard'),
    path('dashboard/', dashboard_views.dashboard, name='dashboard_alt'),
    
    # Analytics
    path('analytics/', analytics_views.analytics, name='analytics'),
    
    # Enrollment
    path('enrollment/', enrollment_views.enrollment_list, name='enrollment'),
    path('enrollment/<int:student_id>/', enrollment_views.enrollment_detail, name='enrollment_detail'),
    
    # Sections
    path('sections/', sections_views.sections_list, name='sections'),
    path('sections/<str:program>/', sections_views.sections_by_program, name='sections_by_program'),
    path('sections/<str:program>/<int:section_id>/', sections_views.section_detail, name='section_detail'),

    # Sections/Subjects/Buildings API
    path('api/programs/', sections_views.get_programs, name='api_get_programs'),
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
    path('student/<int:student_id>/', studentdetails_views.student_details, name='student_details'),
    path('student/<int:student_id>/edit/', studentedit_views.student_edit, name='student_edit'),
    
    # Reports
    path('reports/', reports_views.reports, name='reports'),
    path('reports/generate/', reports_views.generate_report, name='generate_report'),
    
    # Settings
    path('settings/', settings_views.settings, name='settings'),
    path('settings/users/', settings_views.manage_users, name='manage_users'),
    path('settings/content/', settings_views.manage_content, name='manage_content'),
    
    # Settings API Endpoints
    path('api/users/', settings_views.get_users, name='api_get_users'),
    path('api/users/add/', settings_views.add_user, name='api_add_user'),
    path('api/positions/', settings_views.get_positions, name='api_get_positions'),
    path('api/positions/add/', settings_views.add_position, name='api_add_position'),
    path('api/positions/<int:position_id>/update/', settings_views.update_position, name='api_update_position'),
    path('api/positions/<int:position_id>/delete/', settings_views.delete_position, name='api_delete_position'),
    path('api/departments/', settings_views.get_departments, name='api_get_departments'),
    path('api/departments/add/', settings_views.add_department, name='api_add_department'),
    path('api/departments/<int:department_id>/update/', settings_views.update_department, name='api_update_department'),
    path('api/departments/<int:department_id>/delete/', settings_views.delete_department, name='api_delete_department'),
    # School Years API Endpoints
    path('api/school-years/', settings_views.get_school_years, name='api_get_school_years'),
    path('api/school-years/add/', settings_views.add_school_year, name='api_add_school_year'),
    path('api/school-years/<int:school_year_id>/update/', settings_views.update_school_year, name='api_update_school_year'),
    path('api/school-years/<int:school_year_id>/delete/', settings_views.delete_school_year, name='api_delete_school_year'),
    
    # Content Management API Endpoints
    path('api/content/settings/', settings_views.get_content_settings, name='api_get_content_settings'),
    path('api/content/save/', settings_views.save_content_setting, name='api_save_content_setting'),
    path('api/content/upload-image/', settings_views.upload_content_image, name='api_upload_content_image'),
    path('api/staff/', settings_views.get_staff_members, name='api_get_staff_members'),
    path('api/staff/add/', settings_views.add_staff_member, name='api_add_staff_member'),
    path('api/staff/<int:staff_id>/update/', settings_views.update_staff_member, name='api_update_staff_member'),
    path('api/staff/<int:staff_id>/delete/', settings_views.delete_staff_member, name='api_delete_staff_member'),
    
    # Buildings & Rooms API Endpoints
    path('api/buildings/', settings_views.get_buildings_with_rooms, name='api_get_buildings_with_rooms'),
    path('api/buildings/add/', settings_views.add_building, name='api_add_building'),
    path('api/buildings/<int:building_id>/update/', settings_views.update_building, name='api_update_building'),
    path('api/buildings/<int:building_id>/delete/', settings_views.delete_building, name='api_delete_building'),
    # Note: api/rooms/ is handled by sections_views.get_rooms (line 42)
    path('api/rooms/add/', settings_views.add_room, name='api_add_room'),
    path('api/rooms/<int:room_id>/update/', settings_views.update_room, name='api_update_room'),
    path('api/rooms/<int:room_id>/delete/', settings_views.delete_room, name='api_delete_room'),
    
    # Activity Logs API Endpoint
    path('api/activity-logs/', settings_views.get_activity_logs, name='api_get_activity_logs'),
]