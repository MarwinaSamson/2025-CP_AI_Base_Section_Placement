from django.shortcuts import render
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from admin_app.decorators import admin_required
from admin_app.models import Program, SchoolYear, UserProfile
from enrollment_app.models import StudentEnrollment, StudentData, ProgramSelection, SurveyData
from enrollment_app.models import Student


def _get_school_year_from_request(request):
    """Resolve school year from query parameter or fall back to active one."""
    school_year_id = request.GET.get('school_year')
    if school_year_id:
        return SchoolYear.objects.filter(id=school_year_id).first()
    return SchoolYear.get_active_school_year()


@admin_required
def enrollment_list(request):
    """Render enrollment page with dynamic filter options."""
    school_years = SchoolYear.objects.all().order_by('-id')
    programs = Program.objects.all().order_by('code')
    active_school_year = SchoolYear.get_active_school_year()
    
    # Get user profile
    try:
        user_profile = UserProfile.objects.select_related('program', 'position', 'department').get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None
    
    context = {
        'school_years': school_years,
        'programs': programs,
        'active_school_year': active_school_year,
        'user': request.user,
        'user_profile': user_profile,
        'active_page': 'enrollment',
    }
    return render(request, 'admin_app/enrollment.html', context)


@admin_required
def enrollment_detail(request, student_id):
    """Render enrollment detail page."""
    # Get user profile
    try:
        user_profile = UserProfile.objects.select_related('program', 'position', 'department').get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None
    
    context = {
        'student_id': student_id,
        'user': request.user,
        'user_profile': user_profile,
        'active_page': 'enrollment',
    }
    return render(request, 'admin_app/enrollment.html', context)


@admin_required
def enrollment_header_data(request):
    """
    API endpoint for enrollment header data
    Returns: school year, user fullname, role, and photo/initials
    """
    # Get active school year
    active_school_year = SchoolYear.get_active_school_year()
    
    # Get user profile
    try:
        user_profile = UserProfile.objects.select_related('program', 'position', 'department').get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None
    
    # Get user's full name
    user = request.user
    full_name = f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else user.username
    
    # Get initials
    if user.first_name and user.last_name:
        initials = f"{user.first_name[0]}{user.last_name[0]}".upper()
    elif user.first_name:
        initials = user.first_name[0].upper()
    elif user.last_name:
        initials = user.last_name[0].upper()
    else:
        initials = user.username[0].upper() if user.username else "U"
    
    # Get role
    role = user_profile.get_user_type_display() if user_profile else "Admin"
    
    # Get photo URL
    photo_url = None
    if user_profile and user_profile.photo:
        photo_url = user_profile.photo.url
    
    data = {
        'school_year': active_school_year.year_label if active_school_year else 'No Active Year',
        'full_name': full_name,
        'role': role,
        'initials': initials,
        'photo_url': photo_url,
        'program': user_profile.get_program_name() if user_profile else 'N/A',
    }
    
    return JsonResponse(data)


@admin_required
def enrollment_summary(request):
    """Return per-grade-level counts for the 4 grade cards."""
    school_year = _get_school_year_from_request(request)

    pending_statuses = ['submitted', 'under_review']

    # Grade level codes and their display names
    grade_levels = [
        ('G7',  'Grade 7'),
        ('G8',  'Grade 8'),
        ('G9',  'Grade 9'),
        ('G10', 'Grade 10'),
    ]

    grades_data = []
    for code, name in grade_levels:
        qs = StudentEnrollment.objects.filter(
            school_year=school_year,
            grade_level__code=code
        ).exclude(enrollment_status='draft')
        total = qs.count()
        pending = qs.filter(enrollment_status__in=pending_statuses).count()
        approved = qs.filter(enrollment_status='approved').count()

        grades_data.append({
            'code':     code,
            'name':     name,
            'total':    total,
            'pending':  pending,
            'approved': approved,
        })

    return JsonResponse({
        'school_year': school_year.year_label if school_year else None,
        'grades': grades_data,
    })


@admin_required
def enrollment_requests(request):
    """Return list of enrollment requests with filters including grade level."""
    school_year = _get_school_year_from_request(request)
    program_filter     = request.GET.get('program')
    status_filter      = request.GET.get('status')
    grade_filter       = request.GET.get('grade')   # NEW

    qs = StudentEnrollment.objects.filter(
        school_year=school_year
    ).exclude(enrollment_status='draft').select_related(
        'student__student_data',
        'student__program_selection',
        'student__survey_data',
        'grade_level',
        'student'
    )

    # DB filters applied BEFORE slicing
    if grade_filter and grade_filter.lower() != 'all':
        qs = qs.filter(grade_level__code=grade_filter)

    if status_filter and status_filter.lower() != 'all':
        if status_filter == 'pending':
            qs = qs.filter(enrollment_status__in=['submitted', 'under_review'])
        else:
            qs = qs.filter(enrollment_status=status_filter)

    # Slice AFTER all DB filters are applied
    qs = qs[:500]

    # Python filter for program (avoids join error)
    filtered_qs = []
    for enrollment in qs:
        student = enrollment.student
        program_selection = getattr(student, 'program_selection', None)
        program_code = program_selection.selected_program_code if program_selection else None

        if program_filter and program_filter.lower() != 'all' and (
            not program_code or program_code.lower() != program_filter.lower()
        ):
            continue
        filtered_qs.append(enrollment)

    results = []
    for enrollment in filtered_qs:
        student = enrollment.student
        student_data = getattr(student, 'student_data', None)
        program_selection = getattr(student, 'program_selection', None)
        survey_data = getattr(student, 'survey_data', None)

        full_name = student_data.full_name if student_data else 'N/A'
        program_code = program_selection.selected_program_code if program_selection else 'N/A'
        grade_level = enrollment.grade_level.name if enrollment.grade_level else (
            getattr(survey_data, 'current_grade_section', None) or 'N/A'
        )

        results.append({
            'lrn': student.lrn,
            'student_name': full_name,
            'program': program_code,
            'grade': grade_level,
            'submitted_at': student.created_at.strftime('%b %d, %Y'),
            'status': enrollment.enrollment_status,  # Use enrollment status!
            'detail_url': reverse('admin_app:student_edit', args=[student.lrn]),
        })

    return JsonResponse({
        'results': results, 
        'total': len(filtered_qs)
    })

