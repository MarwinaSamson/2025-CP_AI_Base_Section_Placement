from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from admin_app.models import GradeLevel
import json


@login_required
@require_http_methods(["POST"])
def set_active_grade_level(request):
    try:
        data = json.loads(request.body)
        grade_code = data.get('grade_code')

        if grade_code == 'all':
            request.session['active_grade_code'] = 'all'
            request.session['active_grade_name'] = 'All Grades'
            request.session.modified = True
            return JsonResponse({'success': True, 'grade_code': None, 'grade_name': 'All Grades'})

        grade = GradeLevel.objects.filter(code=grade_code, is_active=True).first()
        if not grade:
            return JsonResponse({'error': 'Invalid grade level'}, status=400)

        request.session['active_grade_code'] = grade.code
        request.session['active_grade_name'] = grade.name
        request.session.modified = True
        return JsonResponse({
            'success': True,
            'grade_code': grade.code,
            'grade_name': grade.name
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_grade_levels(request):
    grades = GradeLevel.objects.filter(is_active=True).order_by('name')
    grades = sorted(grades, key=lambda g: int(''.join(filter(str.isdigit, g.name))) if any(c.isdigit() for c in g.name) else 0)
    return JsonResponse({
        'success': True,
        'grades': [{'code': g.code, 'name': g.name} for g in grades],
        'active_code': request.session.get('active_grade_code'),
        'active_name': request.session.get('active_grade_name', 'All Grades'),
    })