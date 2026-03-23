from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count, Avg, Q, F
from django.db.models.functions import TruncMonth
from django.contrib.auth.decorators import login_required
from admin_app.decorators import admin_required
from admin_app.models import SchoolYear, UserProfile, Section, GradeLevel, Program
from enrollment_app.models import (
    Student, StudentEnrollment, StudentData, ProgramSelection,
    StudentDocumentSubmission, AcademicData
)
from coordinator_app.models import (
    AcademicPerformance, CoordinatorActivityLog,
    Qualified_for_ste, ProbationRecord
)
from datetime import timedelta
from django.utils import timezone


def _get_active_sy():
    return SchoolYear.objects.filter(is_active=True).first()


def _safe_pct(part, total):
    return round((part / total * 100), 1) if total > 0 else 0


# ============================================================================
# ANALYTICS VIEW
# ============================================================================

@admin_required
def analytics(request):
    active_sy = SchoolYear.objects.filter(is_active=True).first()
    try:
        user_profile = UserProfile.objects.select_related(
            'program', 'position', 'department'
        ).get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None

    context = {
        'user':               request.user,
        'user_profile':       user_profile,
        'active_page':        'analytics',
        'active_school_year': active_sy,
    }
    return render(request, 'admin_app/analytics.html', context)


# ============================================================================
# MAIN ANALYTICS DATA API
# ============================================================================

@admin_required
def analytics_data(request):
    """
    Returns all analytics data for the dashboard.
    Accepts:
      ?grade=G7|G8|G9|G10
      ?program=REGULAR|STE|SPTVE|SPFL
      ?enrollee=new|continuing|transferee|returnee
    """
    grade_filter   = request.GET.get('grade',   None)
    program_filter = request.GET.get('program', None)
    enrollee_filter= request.GET.get('enrollee',None)

    sy = _get_active_sy()

    # ── Base enrollment queryset ──────────────────────────────────────────
    enrollments = StudentEnrollment.objects.filter(school_year=sy) if sy else StudentEnrollment.objects.none()
    if grade_filter:
        enrollments = enrollments.filter(grade_level__code=grade_filter)
    if enrollee_filter:
        enrollments = enrollments.filter(enrollee_type=enrollee_filter)

    # Program filter needs a join through ProgramSelection
    if program_filter:
        lrns_with_program = ProgramSelection.objects.filter(
            school_year=sy,
            selected_program_code=program_filter
        ).values_list('student__lrn', flat=True)
        enrollments = enrollments.filter(student__lrn__in=lrns_with_program)

    total    = enrollments.count()
    approved = enrollments.filter(enrollment_status='approved').count()
    pending  = enrollments.filter(enrollment_status__in=['submitted','under_review']).count()
    rejected = enrollments.filter(enrollment_status='rejected').count()
    sections = Section.objects.filter(school_year=sy).count() if sy else 0

    approval_rate = _safe_pct(approved, total)

    # ── Funnel ────────────────────────────────────────────────────────────
    funnel = {
        'labels': ['Submitted','Under Review','Approved','Rejected'],
        'data': [
            enrollments.filter(enrollment_status='submitted').count(),
            enrollments.filter(enrollment_status='under_review').count(),
            approved, rejected,
        ],
        'colors': ['#3b82f6','#f59e0b','#10b981','#ef4444'],
    }

    # ── Enrollee types ────────────────────────────────────────────────────
    enrollee_types = {
        'new':        enrollments.filter(enrollee_type='new').count(),
        'continuing': enrollments.filter(enrollee_type='continuing').count(),
        'transferee': enrollments.filter(enrollee_type='transferee').count(),
        'returnee':   enrollments.filter(enrollee_type='returnee').count(),
    }

    # ── Program distribution ──────────────────────────────────────────────
    student_lrns = enrollments.values_list('student__lrn', flat=True)
    prog_qs = (
        ProgramSelection.objects
        .filter(school_year=sy, student__lrn__in=student_lrns)
        .values('selected_program_code')
        .annotate(count=Count('student'))
        .order_by('-count')
    )
    program_dist = {
        'labels': [p['selected_program_code'] or 'Unknown' for p in prog_qs],
        'data':   [p['count'] for p in prog_qs],
        'colors': ['#991b1b','#10b981','#3b82f6','#f59e0b','#8b5cf6','#ef4444','#6b7280','#14b8a6'],
    }

    # ── Grade level distribution (only when no grade filter) ──────────────
    grade_dist = None
    if not grade_filter:
        grade_qs = (
            enrollments
            .values('grade_level__name','grade_level__code')
            .annotate(count=Count('student'))
            .order_by('grade_level__code')
        )
        grade_dist = {
            'labels': [g['grade_level__name'] or 'Unknown' for g in grade_qs],
            'data':   [g['count'] for g in grade_qs],
            'colors': ['#991b1b','#3b82f6','#10b981','#f59e0b'],
        }

    # ── Gender ────────────────────────────────────────────────────────────
    gender_qs = (
        StudentData.objects
        .filter(student__lrn__in=student_lrns)
        .values('gender')
        .annotate(count=Count('student'))
    )
    gmap = {g['gender']: g['count'] for g in gender_qs}
    gender_dist = {
        'male':   gmap.get('male', 0),
        'female': gmap.get('female', 0),
        'other':  gmap.get('other', 0),
    }

    # ── Monthly trend ─────────────────────────────────────────────────────
    nine_months_ago = timezone.now() - timedelta(days=270)
    monthly_qs = (
        StudentEnrollment.objects
        .filter(school_year=sy, created_at__gte=nine_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(
            total=Count('id'),
            approved_count=Count('id', filter=Q(enrollment_status='approved'))
        )
        .order_by('month')
    )
    if grade_filter:
        monthly_qs = monthly_qs.filter(grade_level__code=grade_filter)
    if enrollee_filter:
        monthly_qs = monthly_qs.filter(enrollee_type=enrollee_filter)

    trend = {
        'labels':   [m['month'].strftime('%b') for m in monthly_qs],
        'total':    [m['total'] for m in monthly_qs],
        'approved': [m['approved_count'] for m in monthly_qs],
    }

    # ── Section capacity ──────────────────────────────────────────────────
    sec_qs = Section.objects.filter(school_year=sy).select_related('program','grade_level')
    if grade_filter:
        sec_qs = sec_qs.filter(grade_level__code=grade_filter)
    if program_filter:
        sec_qs = sec_qs.filter(program__code=program_filter)

    section_capacity = []
    for sec in sec_qs.order_by('grade_level__code','name')[:12]:
        actual = sec.get_actual_count()
        pct = _safe_pct(actual, sec.max_students)
        section_capacity.append({
            'name':    f"{sec.grade_level.name if sec.grade_level else ''} — {sec.name}",
            'current': actual,
            'max':     sec.max_students,
            'pct':     pct,
            'status':  'full' if pct >= 95 else 'almost' if pct >= 80 else 'ok',
            'track':   sec.regular_track or '',
        })

    # ── Document completion ───────────────────────────────────────────────
    docs_qs = StudentDocumentSubmission.objects.filter(student__lrn__in=student_lrns)
    doc_stats = {
        'labels': ['Approved','Pending','Rejected'],
        'data': [
            docs_qs.filter(status='approved').values('student').distinct().count(),
            docs_qs.filter(status='pending').values('student').distinct().count(),
            docs_qs.filter(status='rejected').values('student').distinct().count(),
        ],
        'colors': ['#10b981','#f59e0b','#ef4444'],
    }

    # ── Academic performance ──────────────────────────────────────────────
    acad_qs = (
        AcademicPerformance.objects
        .filter(student__lrn__in=student_lrns, quarter=5)
        .values('grade_level__name','grade_level__code')
        .annotate(avg_grade=Avg('grade'))
        .order_by('grade_level__code')
    )
    acad_perf = {
        'labels': [a['grade_level__name'] or 'Unknown' for a in acad_qs],
        'data':   [round(float(a['avg_grade']), 2) if a['avg_grade'] else 0 for a in acad_qs],
    }

    # ── Probation ─────────────────────────────────────────────────────────
    prob_qs = ProbationRecord.objects.filter(school_year=sy, is_active=True)
    if grade_filter:
        prob_qs = prob_qs.filter(grade_level__code=grade_filter)
    prob_by_prog = prob_qs.values('previous_program').annotate(count=Count('id')).order_by('-count')
    probation = {
        'total':  prob_qs.count(),
        'labels': [p['previous_program'] for p in prob_by_prog],
        'data':   [p['count'] for p in prob_by_prog],
    }

    # ── STE qualification ─────────────────────────────────────────────────
    ste_qs = Qualified_for_ste.objects.filter(school_year=sy)
    if grade_filter:
        ste_qs = ste_qs.filter(grade_level__code=grade_filter)
    ste = {
        'qualified':     ste_qs.filter(status='qualified').count(),
        'not_qualified': ste_qs.filter(status='not_qualified').count(),
        'pending':       ste_qs.filter(status='pending').count(),
        'waitlisted':    ste_qs.filter(status='waitlisted').count(),
        'total':         ste_qs.count(),
    }

    # ── Coordinator activity (last 30 days) ───────────────────────────────
    thirty_ago = timezone.now() - timedelta(days=30)
    coord_qs = (
        CoordinatorActivityLog.objects
        .filter(created_at__gte=thirty_ago)
        .values('action')
        .annotate(count=Count('id'))
        .order_by('-count')[:6]
    )
    coord_activity = {
        'labels': [c['action'].replace('_',' ').title() for c in coord_qs],
        'data':   [c['count'] for c in coord_qs],
        'colors': ['#10b981','#3b82f6','#f59e0b','#8b5cf6','#ef4444','#6b7280'],
    }

    # ── AI acceptance rate ────────────────────────────────────────────────
    ai_total    = ProgramSelection.objects.filter(school_year=sy, requires_program_selection=True).count()
    ai_approved = ProgramSelection.objects.filter(school_year=sy, requires_program_selection=True, admin_approved=True).count()
    ai_rate     = _safe_pct(ai_approved, ai_total)

    # ── Auto insights ─────────────────────────────────────────────────────
    insights = []
    if approval_rate >= 75:
        insights.append({'icon':'fa-arrow-trend-up','color':'#10b981','bg':'#f0fdf4',
                         'text':f'Approval rate is {approval_rate}% — above the 75% target.'})
    else:
        insights.append({'icon':'fa-exclamation-triangle','color':'#f59e0b','bg':'#fffbeb',
                         'text':f'Approval rate is {approval_rate}% — below the 75% target.'})
    if pending > 0:
        insights.append({'icon':'fa-hourglass-half','color':'#3b82f6','bg':'#eff6ff',
                         'text':f'{pending} student{"s" if pending>1 else ""} pending coordinator review.'})
    if probation['total'] > 0:
        insights.append({'icon':'fa-exclamation-circle','color':'#ef4444','bg':'#fef2f2',
                         'text':f'{probation["total"]} student{"s" if probation["total"]>1 else ""} on academic probation.'})
    full_secs = [s for s in section_capacity if s['status']=='full']
    if full_secs:
        insights.append({'icon':'fa-lock','color':'#8b5cf6','bg':'#f5f3ff',
                         'text':f'{len(full_secs)} section{"s are" if len(full_secs)>1 else " is"} at full capacity.'})
    if ste['total'] > 0:
        insights.append({'icon':'fa-flask','color':'#14b8a6','bg':'#f0fdfa',
                         'text':f'{ste["qualified"]} of {ste["total"]} STE applicants qualified.'})
    if gender_dist['female'] > gender_dist['male']:
        diff = gender_dist['female'] - gender_dist['male']
        insights.append({'icon':'fa-venus','color':'#ec4899','bg':'#fdf2f8',
                         'text':f'Female students outnumber males by {diff}.'})
    elif gender_dist['male'] > gender_dist['female']:
        diff = gender_dist['male'] - gender_dist['female']
        insights.append({'icon':'fa-mars','color':'#3b82f6','bg':'#eff6ff',
                         'text':f'Male students outnumber females by {diff}.'})
    if ai_rate > 0:
        insights.append({'icon':'fa-robot','color':'#f59e0b','bg':'#fffbeb',
                         'text':f'AI-recommended placements have a {ai_rate}% approval rate.'})

    return JsonResponse({
        'sy_label':        sy.year_label if sy else 'N/A',
        'kpis': {
            'total': total, 'approved': approved, 'pending': pending,
            'rejected': rejected, 'sections': sections,
            'approval_rate': approval_rate, 'ai_rate': ai_rate,
        },
        'funnel':           funnel,
        'enrollee_types':   enrollee_types,
        'program_dist':     program_dist,
        'grade_dist':       grade_dist,
        'gender_dist':      gender_dist,
        'trend':            trend,
        'section_capacity': section_capacity,
        'doc_stats':        doc_stats,
        'acad_perf':        acad_perf,
        'probation':        probation,
        'ste':              ste,
        'coord_activity':   coord_activity,
        'insights':         insights[:6],
    })


@admin_required
def analytics_header_data(request):
    active_school_year = SchoolYear.get_active_school_year()
    try:
        user_profile = UserProfile.objects.select_related(
            'program','position','department'
        ).get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None

    user = request.user
    full_name = f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else user.username
    if user.first_name and user.last_name:
        initials = f"{user.first_name[0]}{user.last_name[0]}".upper()
    elif user.first_name:
        initials = user.first_name[0].upper()
    elif user.last_name:
        initials = user.last_name[0].upper()
    else:
        initials = user.username[0].upper() if user.username else "U"

    return JsonResponse({
        'school_year': active_school_year.year_label if active_school_year else 'No Active Year',
        'full_name':   full_name,
        'role':        user_profile.get_user_type_display() if user_profile else "Admin",
        'initials':    initials,
        'photo_url':   user_profile.photo.url if user_profile and user_profile.photo else None,
    })


# ============================================================================
# REPORTS / SETTINGS (unchanged)
# ============================================================================

@admin_required
def reports(request):
    try:
        user_profile = UserProfile.objects.select_related(
            'program','position','department'
        ).get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None
    return render(request, 'admin_app/reports.html', {'user': request.user, 'user_profile': user_profile})


@admin_required
def reports_header_data(request):
    active_school_year = SchoolYear.get_active_school_year()
    try:
        user_profile = UserProfile.objects.select_related(
            'program','position','department'
        ).get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None
    user = request.user
    full_name = f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else user.username
    if user.first_name and user.last_name:
        initials = f"{user.first_name[0]}{user.last_name[0]}".upper()
    elif user.first_name:
        initials = user.first_name[0].upper()
    elif user.last_name:
        initials = user.last_name[0].upper()
    else:
        initials = user.username[0].upper() if user.username else "U"
    return JsonResponse({
        'school_year': active_school_year.year_label if active_school_year else 'No Active Year',
        'full_name': full_name,
        'role': user_profile.get_user_type_display() if user_profile else "Admin",
        'initials': initials,
        'photo_url': user_profile.photo.url if user_profile and user_profile.photo else None,
    })


@admin_required
def settings(request):
    try:
        user_profile = UserProfile.objects.select_related(
            'program','position','department'
        ).get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None
    return render(request, 'admin_app/settings.html', {'user': request.user, 'user_profile': user_profile})


@admin_required
def settings_header_data(request):
    active_school_year = SchoolYear.get_active_school_year()
    try:
        user_profile = UserProfile.objects.select_related(
            'program','position','department'
        ).get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None
    user = request.user
    full_name = f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else user.username
    if user.first_name and user.last_name:
        initials = f"{user.first_name[0]}{user.last_name[0]}".upper()
    elif user.first_name:
        initials = user.first_name[0].upper()
    elif user.last_name:
        initials = user.last_name[0].upper()
    else:
        initials = user.username[0].upper() if user.username else "U"
    return JsonResponse({
        'school_year': active_school_year.year_label if active_school_year else 'No Active Year',
        'full_name': full_name,
        'role': user_profile.get_user_type_display() if user_profile else "Admin",
        'initials': initials,
        'photo_url': user_profile.photo.url if user_profile and user_profile.photo else None,
    })