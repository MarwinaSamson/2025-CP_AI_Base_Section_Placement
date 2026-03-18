from django.shortcuts import render
from django.db.models import Avg
from django.http import JsonResponse
from admin_app.decorators import coordinator_required
from admin_app.models import Section, ActivityLog, SchoolYear, Program, GradeLevel
from enrollment_app.models import ProgramSelection, AcademicData


# ─────────────────────────────────────────────
#  HELPERS: session grade filter
# ─────────────────────────────────────────────

def get_active_grade_level(request):
    """
    Returns the GradeLevel object stored in the session, or None (= all grades).
    Session stores 'active_grade_code' which matches GradeLevel.code (e.g. 'G7').
    """
    code = request.session.get('active_grade_code', 'all')
    if not code or code == 'all':
        return None
    return GradeLevel.objects.filter(code=code, is_active=True).first()


def get_active_grade_name(request):
    """Returns the human-readable label for the active grade (e.g. 'Grade 7')."""
    return request.session.get('active_grade_name', 'All Grades')


def get_program_code(program_obj):
    """
    Extract the program code (e.g. 'SPTVE', 'STE') from a Program object or string.
    Program.__str__ returns "CODE - Name", so we split on ' - '.
    """
    if program_obj is None:
        return 'STE'
    program_str = str(program_obj)
    if ' - ' in program_str:
        return program_str.split(' - ')[0].strip().upper()
    return program_str.strip().upper()


# ─────────────────────────────────────────────
#  STE STATS
# ─────────────────────────────────────────────

def get_ste_program_stats(program_obj, active_grade_level=None):
    """
    STE dashboard stats, filtered by GradeLevel FK if active_grade_level is set.
    """
    school_year = SchoolYear.objects.filter(is_active=True).first()

    # --- Total Applicants ---
    applicants_qs = ProgramSelection.objects.filter(selected_program_code='STE')
    if active_grade_level:
        applicants_qs = applicants_qs.filter(
            assigned_section__grade_level=active_grade_level
        )
    total_applicants = applicants_qs.count()

    # --- Qualified ---
    try:
        from coordinator_app.models import Qualified_for_ste
        qualified_qs = Qualified_for_ste.objects.filter(status='qualified')
        if school_year:
            qualified_qs = qualified_qs.filter(school_year=school_year)
        if active_grade_level:
            qualified_qs = qualified_qs.filter(grade_level=active_grade_level)
        qualified_count = qualified_qs.count()
    except Exception:
        qualified_count = 0

    # --- Pending (submitted but not yet approved/rejected) ---
    pending_qs = ProgramSelection.objects.filter(
        selected_program_code='STE',
        admin_approved=False,
        admin_rejected=False,
    )
    if active_grade_level:
        pending_qs = pending_qs.filter(
            assigned_section__grade_level=active_grade_level
        )
    pending_count = pending_qs.count()

    # --- Sections ---
    sections_qs = Section.objects.filter(program=program_obj)
    if school_year:
        sections_qs = sections_qs.filter(school_year=school_year)
    if active_grade_level:
        sections_qs = sections_qs.filter(grade_level=active_grade_level)
    section_count = sections_qs.count()

    stats = {
        'stat1_label': 'Total Applicants',
        'stat1_value': str(total_applicants),
        'stat1_desc':  'For STE Program',
        'stat2_label': 'Qualified',
        'stat2_value': str(qualified_count),
        'stat2_desc':  'Qualified for STE',
        'stat3_label': 'Pending Review',
        'stat3_value': str(pending_count),
        'stat3_desc':  'Require Evaluation',
        'stat4_label': 'Sections',
        'stat4_value': str(section_count),
        'stat4_desc':  'STE Sections',
    }
    return stats, None


# ─────────────────────────────────────────────
#  SPTVE STATS
# ─────────────────────────────────────────────

def get_sptve_program_stats(program_obj, active_grade_level=None):
    """
    SPTVE dashboard stats, filtered by GradeLevel FK if active_grade_level is set.
    Section.name is the trade course name.
    """
    school_year = SchoolYear.objects.filter(is_active=True).first()

    sections_qs = Section.objects.filter(program=program_obj)
    if school_year:
        sections_qs = sections_qs.filter(school_year=school_year)
    if active_grade_level:
        sections_qs = sections_qs.filter(grade_level=active_grade_level)

    section_ids   = sections_qs.values_list('id', flat=True)
    section_count = sections_qs.count()

    trainees = ProgramSelection.objects.filter(
        assigned_section__in=section_ids,
        admin_approved=True,
    )
    total_trainees = trainees.count()

    pending_enrollments = ProgramSelection.objects.filter(
        assigned_section__in=section_ids,
        admin_approved=False,
        admin_rejected=False,
    ).count()

    stats = {
        'stat1_label': 'Total SPTVE Students',
        'stat1_value': str(total_trainees),
        'stat1_desc':  'Currently Enrolled',
        'stat2_label': 'SPTVE Sections',
        'stat2_value': str(section_count),
        'stat2_desc':  'Active Sections',
        'stat3_label': 'Trade Courses',
        'stat3_value': str(sections_qs.values('name').distinct().count()),
        'stat3_desc':  'Unique Courses',
        'stat4_label': 'Pending Enrollments',
        'stat4_value': str(pending_enrollments),
        'stat4_desc':  'Awaiting Approval',
    }

    trade_cards_html = []
    for section in sections_qs:
        student_count = trainees.filter(assigned_section=section).count()
        trade_cards_html.append(
            f'<div class="bg-white/20 backdrop-blur-sm rounded-lg p-3 hover:bg-white/30 transition-all">'
            f'<div class="flex justify-between items-center">'
            f'<span class="font-semibold">{section.name}</span>'
            f'<span class="bg-white/30 px-3 py-1 rounded-full text-sm font-semibold">{student_count} Students</span>'
            f'</div></div>'
        )
    trade_cards_joined = ''.join(trade_cards_html) if trade_cards_html else \
        '<p class="text-white/70 text-sm">No trade courses found for this grade level.</p>'

    info_cards = f'''
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div style="background:#d97706;color:white;" class="rounded-2xl p-6 shadow-lg">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-xl font-bold flex items-center gap-2">
                        <i class="fas fa-wrench"></i> Active Trade Courses
                    </h3>
                </div>
                <div class="space-y-3">{trade_cards_joined}</div>
            </div>
            <div class="bg-white rounded-2xl p-6 shadow-lg border border-gray-200">
                <h3 class="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                    <i class="fas fa-user-check text-green-600"></i> Enrollment Status
                </h3>
                <div class="space-y-4">
                    <div class="flex justify-between">
                        <span class="text-sm font-semibold text-gray-700">Approved</span>
                        <span class="text-sm font-bold text-green-600">{total_trainees}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-sm font-semibold text-gray-700">Pending</span>
                        <span class="text-sm font-bold text-yellow-600">{pending_enrollments}</span>
                    </div>
                </div>
            </div>
        </div>
    '''
    return stats, info_cards


# ─────────────────────────────────────────────
#  SPFL STATS
# ─────────────────────────────────────────────

def get_spfl_program_stats(program_obj, active_grade_level=None):
    """
    SPFL dashboard stats, filtered by GradeLevel FK if active_grade_level is set.
    Section.name is the language name (e.g. 'Japanese', 'Korean').
    """
    school_year = SchoolYear.objects.filter(is_active=True).first()

    sections_qs = Section.objects.filter(program=program_obj)
    if school_year:
        sections_qs = sections_qs.filter(school_year=school_year)
    if active_grade_level:
        sections_qs = sections_qs.filter(grade_level=active_grade_level)

    section_ids   = sections_qs.values_list('id', flat=True)
    languages     = list(sections_qs.values_list('name', flat=True).distinct())
    num_languages = len(languages)

    enrollees = ProgramSelection.objects.filter(
        assigned_section__in=section_ids,
        admin_approved=True,
    )
    total_enrollees = enrollees.count()

    # High proficiency: overall_average >= 90 (AcademicData.overall_average)
    try:
        high_proficiency = AcademicData.objects.filter(
            student__program_selection__assigned_section__in=section_ids,
            student__program_selection__admin_approved=True,
            overall_average__gte=90,
        ).count()
    except Exception:
        high_proficiency = 0

    stats = {
        'stat1_label': 'Total Enrollees',
        'stat1_value': str(total_enrollees),
        'stat1_desc':  'Active Students',
        'stat2_label': 'Languages Offered',
        'stat2_value': str(num_languages),
        'stat2_desc':  ', '.join(languages) if languages else 'N/A',
        'stat3_label': 'High Proficiency',
        'stat3_value': str(high_proficiency),
        'stat3_desc':  'Average 90 and above',
        'stat4_label': 'Sections',
        'stat4_value': str(sections_qs.count()),
        'stat4_desc':  'Active Sections',
    }

    cards_html = []
    for section in sections_qs:
        count = enrollees.filter(assigned_section=section).count()
        lang  = section.name
        cards_html.append(
            f'<div class="bg-white/20 backdrop-blur-sm rounded-xl p-4 hover:bg-white/30 transition-all cursor-pointer">'
            f'<div class="flex items-center gap-3 mb-2">'
            f'<div class="text-3xl">🌐</div>'
            f'<div class="text-lg font-bold">{lang[:2].upper()}</div>'
            f'</div>'
            f'<h4 class="font-bold text-lg">{lang}</h4>'
            f'<p class="text-purple-100 text-sm">{count} Students</p>'
            f'</div>'
        )
    cards_joined = ''.join(cards_html) if cards_html else \
        '<p class="text-white/70 text-sm col-span-3">No language programs found for this grade level.</p>'

    info_cards = f'''
        <div style="background:#7e22ce;color:white;" class="rounded-2xl p-6 shadow-lg">
            <h3 class="text-xl font-bold mb-4 flex items-center gap-2">
                <i class="fas fa-language"></i> Language Programs
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">{cards_joined}</div>
        </div>
    '''
    return stats, info_cards


# ─────────────────────────────────────────────
#  REGULAR STATS
# ─────────────────────────────────────────────

def get_regular_program_stats(program_obj, active_grade_level=None):
    """
    REGULAR dashboard stats filtered by grade level.
    Section.regular_track = 'TOP5' or 'HETERO' (CharField on Section model).
    AcademicData.overall_average is the persisted GWA field.
    """
    school_year = SchoolYear.objects.filter(is_active=True).first()

    base_sections = Section.objects.filter(program=program_obj)
    if school_year:
        base_sections = base_sections.filter(school_year=school_year)
    if active_grade_level:
        base_sections = base_sections.filter(grade_level=active_grade_level)

    # ── TOP5 ──
    top5_sections    = base_sections.filter(regular_track='TOP5')
    top5_section_ids = top5_sections.values_list('id', flat=True)

    top5_enrollments   = ProgramSelection.objects.filter(
        assigned_section__in=top5_section_ids,
        admin_approved=True,
    )
    top5_total         = top5_enrollments.count()
    top5_section_count = top5_sections.count()

    top5_avg = AcademicData.objects.filter(
        student__program_selection__assigned_section__in=top5_section_ids,
        student__program_selection__admin_approved=True,
        overall_average__isnull=False,
    ).aggregate(avg=Avg('overall_average'))['avg']
    top5_avg_gwa = round(top5_avg, 1) if top5_avg else '—'

    # ── HETERO ──
    hetero_sections    = base_sections.filter(regular_track='HETERO')
    hetero_section_ids = hetero_sections.values_list('id', flat=True)

    hetero_enrollments   = ProgramSelection.objects.filter(
        assigned_section__in=hetero_section_ids,
        admin_approved=True,
    )
    hetero_total         = hetero_enrollments.count()
    hetero_section_count = hetero_sections.count()

    hetero_avg = AcademicData.objects.filter(
        student__program_selection__assigned_section__in=hetero_section_ids,
        student__program_selection__admin_approved=True,
        overall_average__isnull=False,
    ).aggregate(avg=Avg('overall_average'))['avg']
    hetero_avg_gwa = round(hetero_avg, 1) if hetero_avg else '—'

    # ── Overall ──
    all_section_ids = list(top5_section_ids) + list(hetero_section_ids)
    total_students  = top5_total + hetero_total
    total_sections  = top5_section_count + hetero_section_count

    pending_count = ProgramSelection.objects.filter(
        assigned_section__in=all_section_ids,
        admin_approved=False,
        admin_rejected=False,
    ).count()

    honor_count = AcademicData.objects.filter(
        student__program_selection__assigned_section__in=all_section_ids,
        student__program_selection__admin_approved=True,
        overall_average__gte=90,
    ).count()

    stats = {
        'stat1_label': 'Total Students',
        'stat1_value': str(total_students),
        'stat1_desc':  'Enrolled Students',
        'stat2_label': 'Total Sections',
        'stat2_value': str(total_sections),
        'stat2_desc':  'Active Classes',
        'stat3_label': 'Pending Enrollment',
        'stat3_value': str(pending_count),
        'stat3_desc':  'Awaiting Approval',
        'stat4_label': 'Honor Students',
        'stat4_value': str(honor_count),
        'stat4_desc':  'GWA 90 and above',
    }

    info_cards = f'''
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div tyle="background:#1d4ed8;color:white;padding:12px;border-radius:6px;font-family:monospace;white-space:pre-wrap;" class="rounded-2xl p-6 shadow-lg">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-xl font-bold flex items-center gap-2">
                        <i class="fas fa-trophy"></i> TOP5 Sections
                    </h3>
                    <span style="background:rgba(255,255,255,0.25);" class="px-3 py-1 rounded-full text-sm font-bold">High Performers</span>
                </div>
                <p style="color:rgba(255,255,255,0.8);" class="text-sm mb-4">Students with Grade 6 Final Average: 90% and above</p>
                <div class="space-y-3">
                    <div style="background:rgba(255,255,255,0.15);" class="rounded-lg p-3">
                        <div class="flex justify-between items-center">
                            <span class="font-semibold">Total Students</span>
                            <span class="text-2xl font-bold">{top5_total}</span>
                        </div>
                    </div>
                    <div style="background:rgba(255,255,255,0.15);" class="rounded-lg p-3">
                        <div class="flex justify-between items-center">
                            <span class="font-semibold">Number of Sections</span>
                            <span class="text-2xl font-bold">{top5_section_count}</span>
                        </div>
                    </div>
                    <div style="background:rgba(255,255,255,0.15);" class="rounded-lg p-3">
                        <div class="flex justify-between items-center">
                            <span class="font-semibold">Average GWA</span>
                            <span class="text-2xl font-bold">{top5_avg_gwa}</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-white rounded-2xl p-6 shadow-lg border-2 border-gray-300">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-xl font-bold text-gray-800 flex items-center gap-2">
                        <i class="fas fa-users" style="color:#1d4ed8;"></i> Hetero Sections
                    </h3>
                    <span style="background:#dbeafe;color:#1d4ed8;" class="px-3 py-1 rounded-full text-sm font-bold">General</span>
                </div>
                <p class="text-gray-600 text-sm mb-4">Students with Grade 6 Final Average: Below 90%</p>
                <div class="space-y-3">
                    <div class="bg-gray-50 rounded-lg p-3 border border-gray-200">
                        <div class="flex justify-between items-center">
                            <span class="font-semibold text-gray-700">Total Students</span>
                            <span class="text-2xl font-bold" style="color:#1d4ed8;">{hetero_total}</span>
                        </div>
                    </div>
                    <div class="bg-gray-50 rounded-lg p-3 border border-gray-200">
                        <div class="flex justify-between items-center">
                            <span class="font-semibold text-gray-700">Number of Sections</span>
                            <span class="text-2xl font-bold" style="color:#1d4ed8;">{hetero_section_count}</span>
                        </div>
                    </div>
                    <div class="bg-gray-50 rounded-lg p-3 border border-gray-200">
                        <div class="flex justify-between items-center">
                            <span class="font-semibold text-gray-700">Average GWA</span>
                            <span class="text-2xl font-bold" style="color:#1d4ed8;">{hetero_avg_gwa}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    '''
    return stats, info_cards


# ─────────────────────────────────────────────
#  RECENT ACTIVITIES
# ─────────────────────────────────────────────

def get_recent_activities(program_obj, limit=5):
    activities = []
    try:
        from coordinator_app.models import CoordinatorActivityLog
        recent_logs = CoordinatorActivityLog.objects.filter(
            program=program_obj
        ).order_by('-created_at')[:limit]

        icon_map  = {'enrollment': 'fa-user-check', 'section': 'fa-users-cog', 'student': 'fa-user-edit', 'report': 'fa-file-alt', 'ai': 'fa-robot', 'system': 'fa-cog'}
        color_map = {'enrollment': 'green', 'section': 'blue', 'student': 'indigo', 'report': 'purple', 'ai': 'yellow', 'system': 'gray'}

        for log in recent_logs:
            activities.append({
                'icon':   icon_map.get(log.category, 'fa-info-circle'),
                'color':  color_map.get(log.category, 'blue'),
                'title':  log.description or log.get_action_display(),
                'time':   log.get_formatted_date() + ', ' + log.get_formatted_time(),
                'status': 'Completed',
            })
    except Exception:
        pass

    if not activities:
        activities = [
            {'icon': 'fa-graduation-cap', 'color': 'blue',   'title': 'Grade 12 final examinations completed',               'time': 'Today, 3:00 PM',     'status': 'Completed'},
            {'icon': 'fa-book',           'color': 'indigo', 'title': 'New curriculum materials distributed to all sections', 'time': 'Yesterday, 9:00 AM', 'status': 'Distributed'},
            {'icon': 'fa-star',           'color': 'yellow', 'title': 'Honor roll students recognized in assembly',           'time': '5 days ago',         'status': 'Completed'},
        ]
    return activities


# ─────────────────────────────────────────────
#  STATIC FALLBACK (OHSP, SNED)
# ─────────────────────────────────────────────

PROGRAM_DATA = {
    'OHSP': {
        'full_name': 'Online Hospitality & Service Program',
        'stats': {
            'stat1_label': 'Total Trainees',  'stat1_value': '142', 'stat1_desc': 'Active Enrollment',
            'stat2_label': 'Service Areas',   'stat2_value': '3',   'stat2_desc': 'Food & Beverage, Front Office, Housekeeping',
            'stat3_label': 'Certified',        'stat3_value': '98',  'stat3_desc': 'Industry Certified',
            'stat4_label': 'Job Placement',    'stat4_value': '76',  'stat4_desc': '53% Placed in Hotels',
        },
        'info_cards': None,
        'recent_activities': [
            {'icon': 'fa-concierge-bell', 'color': 'teal',  'title': 'Front office training completed - 18 students',    'time': 'Today, 1:45 PM',      'status': 'Completed'},
            {'icon': 'fa-hotel',          'color': 'cyan',  'title': 'Partnership agreement signed with Marriott Hotel', 'time': 'Yesterday, 10:00 AM', 'status': 'Active'},
            {'icon': 'fa-utensils',       'color': 'green', 'title': 'Culinary arts practical exam scheduled',           'time': '3 days ago',          'status': 'Scheduled'},
        ],
    },
    'SNED': {
        'full_name': 'Special Needs Education Program',
        'stats': {
            'stat1_label': 'Enrolled Students', 'stat1_value': '58',  'stat1_desc': 'Active Students',
            'stat2_label': 'Active IEPs',        'stat2_value': '58',  'stat2_desc': 'Individualized Plans',
            'stat3_label': 'Support Staff',      'stat3_value': '12',  'stat3_desc': 'Specialists & Aides',
            'stat4_label': 'Achievements',       'stat4_value': '124', 'stat4_desc': 'Student Milestones',
        },
        'info_cards': None,
        'recent_activities': [
            {'icon': 'fa-heart',         'color': 'pink',   'title': 'IEP review meeting completed for 8 students',        'time': 'Today, 2:00 PM',      'status': 'Completed'},
            {'icon': 'fa-hands-helping', 'color': 'rose',   'title': 'New speech therapy equipment installed',             'time': 'Yesterday, 11:30 AM', 'status': 'Active'},
            {'icon': 'fa-chart-line',    'color': 'purple', 'title': '15 students showed significant progress this month', 'time': '4 days ago',          'status': 'Progress'},
        ],
    },
}


# ─────────────────────────────────────────────
#  DASHBOARD VIEW
# ─────────────────────────────────────────────

@coordinator_required
def dashboard(request):
    program_obj = None
    if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'program'):
        program_obj = request.user.profile.program

    program_code = get_program_code(program_obj)

    # GradeLevel object or None
    active_grade_level = get_active_grade_level(request)
    active_grade_name  = get_active_grade_name(request)

    if program_code == 'STE' and program_obj:
        stats, info_cards = get_ste_program_stats(program_obj, active_grade_level)
        recent_activities = get_recent_activities(program_obj)

    elif program_code == 'SPTVE' and program_obj:
        stats, info_cards = get_sptve_program_stats(program_obj, active_grade_level)
        recent_activities = get_recent_activities(program_obj)

    elif program_code == 'SPFL' and program_obj:
        stats, info_cards = get_spfl_program_stats(program_obj, active_grade_level)
        recent_activities = get_recent_activities(program_obj)

    elif program_code == 'REGULAR' and program_obj:
        stats, info_cards = get_regular_program_stats(program_obj, active_grade_level)
        recent_activities = get_recent_activities(program_obj)

    else:
        program_info      = PROGRAM_DATA.get(program_code, PROGRAM_DATA['SNED'])
        stats             = program_info['stats']
        info_cards        = program_info['info_cards']
        recent_activities = program_info['recent_activities']

    context = {
        'user':              request.user,
        'program':           program_code,
        'stats':             stats,
        'info_cards':        info_cards,
        'recent_activities': recent_activities,
        'active_grade_name': active_grade_name,
        'active_school_year': SchoolYear.objects.filter(is_active=True).first(),
    }
    return render(request, 'coordinator_app/dashboard.html', context)


# ─────────────────────────────────────────────
#  PENDING ENROLLMENT COUNT (bell notification)
# ─────────────────────────────────────────────

@coordinator_required
def pending_enrollment_count(request):
    program_obj = None
    if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'program'):
        program_obj = request.user.profile.program

    program_code = get_program_code(program_obj)

    active_sy = SchoolYear.objects.filter(is_active=True).first()

    pending = ProgramSelection.objects.filter(
        admin_approved=False,
        admin_rejected=False,
        selected_program_code=program_code,
    )
    if active_sy:
        pending = pending.filter(school_year=active_sy)

    pending = pending.select_related('student__student_data').order_by('-created_at')

    names = list(pending.values_list('student__student_data__first_name', flat=True))

    return JsonResponse({
        'count': pending.count(),
        'names': names,
    })