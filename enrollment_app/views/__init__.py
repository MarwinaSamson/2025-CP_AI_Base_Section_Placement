# Make the views folder a Python package
# This allows importing views from subdirectories

from .landingpage_view import landing_page, clear_session
from .studentdata_view import student_data_form
from .familydata_view import family_data_form
from .studentnonacademic_view import non_academic_form
from .studentacademic_view import academic_form
from .sectionplacement_view import section_placement

__all__ = [
    'landing_page',
    'clear_session',
    'student_data_form',
    'family_data_form',
    'non_academic_form',
    'academic_form',
    'section_placement',
]