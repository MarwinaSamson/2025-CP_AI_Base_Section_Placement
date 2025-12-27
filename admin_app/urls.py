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
]