from django.urls import path
from .views import (
    landing_page,
    clear_session,
    student_data_form,
    family_data_form,
    non_academic_form,
    academic_form,
    section_placement,
    serve_temp_image,
    verify_grades_ajax,
    confirm_program_selection_ajax,
)

app_name = 'enrollment_app'

urlpatterns = [
    # Landing page - main entry point
    path('', landing_page, name='landing'),
    
    # Clear session
    path('clear-session/', clear_session, name='clear_session'),
    
    # Student enrollment flow
    path('student-data/', student_data_form, name='student_data'),
    path('family-data/', family_data_form, name='family_data'),
    path('non-academic/', non_academic_form, name='non_academic'),
    path('academic/', academic_form, name='academic'),
    path('section-placement/', section_placement, name='section_placement'),
    
    # AJAX endpoints
    path('temp-image/<str:filename>/', serve_temp_image, name='serve_temp_image'),
    path('verify-grades/', verify_grades_ajax, name='verify_grades_ajax'),
    path('confirm-program/', confirm_program_selection_ajax, name='confirm_program_ajax'),
]