from django.shortcuts import render
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from admin_app.decorators import admin_required
from admin_app.models import Program, SchoolYear, UserProfile
from enrollment_app.models import Student, StudentData, ProgramSelection, SurveyData


def _get_school_year_from_request(request):
    """Resolve school year from query parameter or fall back to active one."""
    school_year_id = request.GET.get('school_year')
    if school_year_id:
        return SchoolYear.objects.filter(id=school_year_id).first()
    return SchoolYear.get_active_school_year()


def _base_student_queryset(school_year=None):
    qs = Student.objects.select_related(
        'student_data',
        'program_selection',
        'survey_data',
        'school_year'
    )
    if school_year:
        qs = qs.filter(school_year=school_year)
    return qs


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
    """Return counts for enrollment requests by status."""
    school_year = _get_school_year_from_request(request)
    program_filter = request.GET.get('program')

    qs = _base_student_queryset(school_year)
    qs = qs.exclude(enrollment_status='draft')

    if program_filter and program_filter.lower() != 'all':
        qs = qs.filter(program_selection__selected_program_code__iexact=program_filter)

    pending_statuses = ['submitted', 'under_review']

    data = {
        'school_year': school_year.year_label if school_year else None,
        'total_requests': qs.count(),
        'approved': qs.filter(enrollment_status='approved').count(),
        'pending': qs.filter(enrollment_status__in=pending_statuses).count(),
        'rejected': qs.filter(enrollment_status='rejected').count(),
    }
    return JsonResponse(data)


@admin_required
def enrollment_requests(request):
    """Return list of enrollment requests with filters."""
    school_year = _get_school_year_from_request(request)
    program_filter = request.GET.get('program')
    status_filter = request.GET.get('status')

    qs = _base_student_queryset(school_year)
    qs = qs.exclude(enrollment_status='draft')

    if program_filter and program_filter.lower() != 'all':
        qs = qs.filter(program_selection__selected_program_code__iexact=program_filter)

    if status_filter and status_filter.lower() != 'all':
        if status_filter == 'pending':
            qs = qs.filter(enrollment_status__in=['submitted', 'under_review'])
        else:
            qs = qs.filter(enrollment_status=status_filter)

    results = []
    for student in qs:
        student_data = getattr(student, 'student_data', None)
        program_selection = getattr(student, 'program_selection', None)
        survey_data = getattr(student, 'survey_data', None)

        full_name = student_data.full_name if student_data else 'N/A'
        program_code = program_selection.selected_program_code if program_selection else 'N/A'
        grade_level = (
            survey_data.current_grade_section
            if survey_data and survey_data.current_grade_section
            else (student_data.previous_grade_section if student_data else None)
        ) or 'N/A'

        results.append({
            'lrn': student.lrn,
            'student_name': full_name,
            'program': program_code,
            'grade': grade_level,
            'submitted_at': student.created_at.strftime('%b %d, %Y'),
            'status': student.enrollment_status,
            'detail_url': reverse('admin_app:student_edit', args=[student.lrn]),
        })

    return JsonResponse({
        'results': results,
        'total': qs.count(),
    })