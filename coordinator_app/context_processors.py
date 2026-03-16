from admin_app.models import SchoolYear

def active_grade_level(request):
    return {
        'active_grade_code': request.session.get('active_grade_level_code'),
        'active_grade_name': request.session.get('active_grade_level_name', 'All Grades'),
    }
    
def active_school_year(request):
    """Injects active_school_year into every coordinator template context."""
    try:
        sy = SchoolYear.objects.filter(is_active=True).first()
        return {'active_school_year': sy}
    except Exception:
        return {'active_school_year': None}