def active_grade_level(request):
    return {
        'active_grade_code': request.session.get('active_grade_level_code'),
        'active_grade_name': request.session.get('active_grade_level_name', 'All Grades'),
    }