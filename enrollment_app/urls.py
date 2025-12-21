from django.urls import path
from .views import (
    landingpage_view,
    studentdata_view,
    familydata_view,
    studentnonacademic_view,
    studentacademic_view,
    sectionplacement_view
)

app_name = 'enrollment_app'

urlpatterns = [
    # Landing page - main entry point
    path('', landingpage_view.landing_page, name='landing'),
    
    # Student enrollment flow
    path('student-data/', studentdata_view.student_data_form, name='student_data'),
    path('family-data/', familydata_view.family_data_form, name='family_data'),
    path('non-academic/', studentnonacademic_view.non_academic_form, name='non_academic'),
    path('academic/', studentacademic_view.academic_form, name='academic'),
    path('section-placement/', sectionplacement_view.section_placement, name='section_placement'),
]