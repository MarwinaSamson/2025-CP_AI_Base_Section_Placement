from django.urls import path
from .views import (
    landing_page,
    enrollment_guide,
    programs_overview,
    about_us,
    contact_us,
    clear_session,
    student_data_form,
    family_data_form,
    non_academic_form,
    academic_form,
    section_placement,
    serve_temp_image,
    verify_grades_ajax,
    confirm_program_selection_ajax,
    document_submission_page,
    upload_document,
    delete_document,
    get_requirements_api,
    download_document,
    get_section_students,
    download_section_masterlist,
    # Session status view
    session_status,
    transferee_documents,
    enrollment_complete_old,
)

app_name = 'enrollment_app'

urlpatterns = [
    # Landing page - main entry point
    path('', landing_page, name='landing'),


    # Session status endpoint for AJAX check
    path('session-status/', session_status, name='session_status'),

    path('guide/', enrollment_guide, name='enrollment_guide'),
    path('programs/', programs_overview, name='programs_overview'),
    path('about/', about_us, name='about_us'),
    path('contact/', contact_us, name='contact_us'),

    
    # Clear session
    path('clear-session/', clear_session, name='clear_session'),
    
    # Student enrollment flow
    path('student-data/', student_data_form, name='student_data'),
    path('family-data/', family_data_form, name='family_data'),
    path('non-academic/', non_academic_form, name='non_academic'),
    path('academic/', academic_form, name='academic'),
    path('section-placement/', section_placement, name='section_placement'),
    
    # Document submission
    path('documents/', document_submission_page, name='documents'),
    path('documents/download/<int:submission_id>/', download_document, name='download_document'),
    
    # AJAX endpoints
    path('temp-image/<str:filename>/', serve_temp_image, name='serve_temp_image'),
    path('verify-grades/', verify_grades_ajax, name='verify_grades_ajax'),
    path('confirm-program/', confirm_program_selection_ajax, name='confirm_program_ajax'),
    path('api/requirements/', get_requirements_api, name='api_requirements'),
    path('api/upload/<int:requirement_id>/', upload_document, name='api_upload_document'),
    path('api/delete/<int:requirement_id>/', delete_document, name='api_delete_document'),

    # Section Assignment - public API for landing page
    path('api/section/<int:section_id>/students/', get_section_students, name='api_section_students'),
    path('api/section/<int:section_id>/download-pdf/', download_section_masterlist, name='download_section_masterlist'),
    
    # Old student enrollment completion
    path('enrollment/complete/old/', enrollment_complete_old, name='enrollment_complete_old'),  # from enrollment_complete_old_view.py
        
    # Transferee document submission
    path('enrollment/transferee/documents/', transferee_documents, name='transferee_documents' ),  # from transferee_documents_view.py
        
                     
        
   
]