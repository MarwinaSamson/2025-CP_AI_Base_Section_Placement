import json
from django.shortcuts import render
from django.db.models import Count, Avg, Q
from admin_app.decorators import coordinator_required
from admin_app.models import Section, SchoolYear
from enrollment_app.models import ProgramSelection, AcademicData, StudentData


# Subject fields used for GWA calculation
SUBJECT_FIELDS = [
    'mathematics', 'science', 'english', 'filipino',
    'araling_panlipunan', 'edukasyon_sa_pagpapakatao',
    'edukasyon_pangkabuhayan', 'mapeh'
]

# Human-readable subject labels
SUBJECT_LABELS = {
    'mathematics': 'Math',
    'science': 'Science',
    'english': 'English',
    'filipino': 'Filipino',
    'araling_panlipunan': 'AP',
    'edukasyon_sa_pagpapakatao': 'ESP',
    'edukasyon_pangkabuhayan': 'TLE',
    'mapeh': 'MAPEH'
}

# Program full names
PROGRAM_NAMES = {
    'STE': 'Science, Technology & Engineering',
    'REGULAR': 'General Academic Curriculum',
    'SPFL': 'Special Program in Foreign Language',
    'SPTVE': 'Special Program in Technical-Vocational Education',
    'OHSP': 'Online Hospitality & Service Program',
    'SNED': 'Special Needs Education Program',
}

# Program-specific key subjects to highlight
PROGRAM_KEY_SUBJECTS = {
    'STE': ['mathematics', 'science'],
    'SPFL': ['english', 'filipino'],
    'SPTVE': ['edukasyon_pangkabuhayan'],
    'REGULAR': ['mathematics', 'english', 'science'],
    'OHSP': ['english', 'mathematics'],
    'SNED': ['english', 'filipino', 'mathematics'],
}


def get_program_code(program_obj):
    """Extract the program code from various formats."""
    if program_obj is None:
        return 'STE'

    program_str = str(program_obj)

    if ' - ' in program_str:
        program_code = program_str.split(' - ')[0].strip().upper()
    else:
        program_code = program_str.strip().upper()

    return program_code


def _calculate_gwa(academic_record):
    """Calculate GWA from an AcademicData record. Returns float or None."""
    grades = []
    for field in SUBJECT_FIELDS:
        grade = getattr(academic_record, field, None)
        if grade is not None:
            try:
                grades.append(float(grade))
            except (ValueError, TypeError):
                pass
    if grades:
        return sum(grades) / len(grades)
    return None


def _get_gwa_distribution(lrns):
    """Calculate GWA distribution for a list of student LRNs."""
    ranges = {'75-79': 0, '80-84': 0, '85-89': 0, '90-94': 0, '95-100': 0}
    gwa_list = []

    if not lrns:
        return ranges, gwa_list

    academic_records = AcademicData.objects.filter(student__lrn__in=lrns)
    for record in academic_records:
        avg = _calculate_gwa(record)
        if avg is not None:
            gwa_list.append(avg)
            if avg >= 95:
                ranges['95-100'] += 1
            elif avg >= 90:
                ranges['90-94'] += 1
            elif avg >= 85:
                ranges['85-89'] += 1
            elif avg >= 80:
                ranges['80-84'] += 1
            else:
                ranges['75-79'] += 1

    return ranges, gwa_list


def _get_gender_distribution(lrns):
    """Get gender distribution for a list of student LRNs."""
    if not lrns:
        return {'Male': 0, 'Female': 0}

    gender_counts = (
        StudentData.objects
        .filter(student__lrn__in=lrns)
        .values('gender')
        .annotate(count=Count('gender'))
    )

    result = {'Male': 0, 'Female': 0}
    for entry in gender_counts:
        gender = entry['gender'] or ''
        if gender.lower() in ('male', 'm'):
            result['Male'] += entry['count']
        elif gender.lower() in ('female', 'f'):
            result['Female'] += entry['count']
    return result


def _get_subject_averages(lrns):
    """Calculate average grade per subject for a list of student LRNs."""
    result = {}
    if not lrns:
        for field in SUBJECT_FIELDS:
            result[field] = 0
        return result

    agg = {}
    for field in SUBJECT_FIELDS:
        agg[field] = Avg(field)

    averages = AcademicData.objects.filter(
        student__lrn__in=lrns
    ).aggregate(**agg)

    for field in SUBJECT_FIELDS:
        val = averages.get(field)
        result[field] = round(float(val), 1) if val is not None else 0

    return result


def _get_section_academic_data(sections, all_selections):
    """Calculate average GWA per section and identify highest-performing."""
    section_academics = []
    highest_section = None
    highest_avg = 0

    for section in sections:
        section_id = str(section.id)
        section_lrns = list(
            all_selections.filter(assigned_section=section_id, admin_approved=True)
            .values_list('student__lrn', flat=True)
        )

        if not section_lrns:
            section_academics.append({
                'name': section.name,
                'avg_gwa': 0,
                'count': 0,
                'track': getattr(section, 'regular_track', '') or ''
            })
            continue

        academic_records = AcademicData.objects.filter(student__lrn__in=section_lrns)
        gwas = []
        for record in academic_records:
            gwa = _calculate_gwa(record)
            if gwa is not None:
                gwas.append(gwa)

        avg = round(sum(gwas) / len(gwas), 1) if gwas else 0

        section_academics.append({
            'name': section.name,
            'avg_gwa': avg,
            'count': len(section_lrns),
            'track': getattr(section, 'regular_track', '') or ''
        })

        if avg > highest_avg:
            highest_avg = avg
            highest_section = section.name

    return section_academics, highest_section, highest_avg


def _get_feeder_school_data(lrns, limit=10):
    """Get feeder school distribution for a list of student LRNs."""
    if not lrns:
        return []

    schools = (
        StudentData.objects
        .filter(student__lrn__in=lrns, last_school_attended__isnull=False)
        .exclude(last_school_attended='')
        .values('last_school_attended')
        .annotate(count=Count('last_school_attended'))
        .order_by('-count')[:limit]
    )

    return [{'name': s['last_school_attended'], 'count': s['count']} for s in schools]


def _get_enrollment_growth(program_code, current_school_year):
    """Compare current school year enrollment with previous school year."""
    if not current_school_year:
        return None

    # Find previous school year (the one before current, ordered by start_date)
    prev_school_year = (
        SchoolYear.objects
        .filter(start_date__lt=current_school_year.start_date)
        .order_by('-start_date')
        .first()
    )

    if not prev_school_year:
        return None

    current_count = ProgramSelection.objects.filter(
        selected_program_code=program_code,
        school_year=current_school_year
    ).count()

    prev_count = ProgramSelection.objects.filter(
        selected_program_code=program_code,
        school_year=prev_school_year
    ).count()

    if prev_count == 0:
        growth_pct = 100.0 if current_count > 0 else 0
    else:
        growth_pct = round(((current_count - prev_count) / prev_count) * 100, 1)

    return {
        'current_year': current_school_year.year_label,
        'previous_year': prev_school_year.year_label,
        'current_count': current_count,
        'previous_count': prev_count,
        'growth_pct': growth_pct,
        'growth_direction': 'up' if growth_pct >= 0 else 'down',
    }


def get_analytics_data(program_code, program_obj, active_grade=None):
    """
    Universal analytics function for all programs.
    Pulls real data from the database.
    """
    school_year = SchoolYear.objects.filter(is_active=True).first()

    # --- Enrollment Counts ---
    base_filter = {'selected_program_code': program_code}
    if school_year:
        base_filter['school_year'] = school_year

    all_selections = ProgramSelection.objects.filter(**base_filter)
    if active_grade:
        all_selections = all_selections.filter(student__grade_level__code=active_grade)
    total_applicants = all_selections.count()
    approved = all_selections.filter(admin_approved=True).count()
    rejected = all_selections.filter(admin_rejected=True).count()
    under_review = all_selections.filter(
        admin_approved=False, admin_rejected=False,
        student__enrollment_status='under_review'
    ).count()
    pending = total_applicants - approved - rejected - under_review
    assigned = all_selections.filter(assigned_section__isnull=False).count()

    approval_rate = round((approved / total_applicants * 100), 1) if total_applicants > 0 else 0

    # --- Section Data ---
    section_filter = {'program': program_obj}
    if school_year:
        section_filter['school_year'] = school_year
    if active_grade:
        section_filter['grade_level__code'] = active_grade

    sections = Section.objects.filter(**section_filter).order_by('created_at') if program_obj else Section.objects.none()
    total_sections = sections.count()

    section_data = []
    total_capacity = 0
    total_enrolled = 0
    for section in sections:
        actual_count = section.get_actual_count()
        total_capacity += section.max_students
        total_enrolled += actual_count
        section_data.append({
            'name': section.name,
            'count': actual_count,
            'max': section.max_students,
            'track': getattr(section, 'regular_track', '') or ''
        })

    fill_rate = round((total_enrolled / total_capacity * 100), 1) if total_capacity > 0 else 0

    # --- GWA Distribution ---
    all_lrns = list(all_selections.values_list('student__lrn', flat=True))

    gwa_ranges, gwa_list = _get_gwa_distribution(all_lrns)
    avg_gwa = round(sum(gwa_list) / len(gwa_list), 1) if gwa_list else 0

    # --- Gender Distribution ---
    gender_dist = _get_gender_distribution(all_lrns)
    total_gendered = gender_dist['Male'] + gender_dist['Female']
    male_pct = round((gender_dist['Male'] / total_gendered * 100)) if total_gendered > 0 else 0
    female_pct = 100 - male_pct if total_gendered > 0 else 0

    # --- Subject-wise Averages ---
    subject_averages = _get_subject_averages(all_lrns)

    # --- Average Grade per Section ---
    section_academics, highest_section, highest_avg = _get_section_academic_data(sections, all_selections)

    # --- Enrollment Growth vs Last School Year ---
    enrollment_growth = _get_enrollment_growth(program_code, school_year)

    # --- Feeder School Distribution ---
    feeder_schools = _get_feeder_school_data(all_lrns)

    # --- Program-Specific Key Subjects ---
    key_subjects = PROGRAM_KEY_SUBJECTS.get(program_code, ['mathematics', 'english'])
    key_subject_data = []
    for subj in key_subjects:
        avg_val = subject_averages.get(subj, 0)
        # Count students scoring 90+ in this subject
        above_90 = 0
        if all_lrns:
            above_90 = AcademicData.objects.filter(
                student__lrn__in=all_lrns,
                **{f'{subj}__gte': 90}
            ).count()
        pct_above_90 = round((above_90 / len(all_lrns) * 100), 1) if all_lrns else 0
        key_subject_data.append({
            'field': subj,
            'label': SUBJECT_LABELS.get(subj, subj),
            'average': avg_val,
            'above_90_count': above_90,
            'above_90_pct': pct_above_90,
        })

    # --- REGULAR-specific: Track breakdown ---
    top5_count = 0
    hetero_count = 0
    if program_code == 'REGULAR':
        top5_section_ids = [str(s.id) for s in sections.filter(regular_track='TOP5')]
        hetero_section_ids = [str(s.id) for s in sections.filter(regular_track='HETERO')]
        top5_count = all_selections.filter(
            assigned_section__in=top5_section_ids, admin_approved=True
        ).count()
        hetero_count = all_selections.filter(
            assigned_section__in=hetero_section_ids, admin_approved=True
        ).count()

    # --- Build Metrics ---
    metrics = {
        'total_applicants': total_applicants,
        'approved': approved,
        'rejected': rejected,
        'under_review': under_review,
        'pending': pending,
        'assigned': assigned,
        'approval_rate': approval_rate,
        'avg_gwa': avg_gwa,
        'total_sections': total_sections,
        'fill_rate': fill_rate,
        'male_pct': male_pct,
        'female_pct': female_pct,
        'male_count': gender_dist['Male'],
        'female_count': gender_dist['Female'],
        'highest_section': highest_section or 'N/A',
        'highest_section_avg': highest_avg,
    }

    # Add enrollment growth
    if enrollment_growth:
        metrics['growth_pct'] = enrollment_growth['growth_pct']
        metrics['growth_direction'] = enrollment_growth['growth_direction']
        metrics['prev_year'] = enrollment_growth['previous_year']
        metrics['prev_count'] = enrollment_growth['previous_count']

    # Add REGULAR-specific metrics
    if program_code == 'REGULAR':
        metrics['top5_count'] = top5_count
        metrics['hetero_count'] = hetero_count

    # --- Build Chart Data ---
    chart_data = {
        'gwa_distribution': json.dumps({
            'labels': list(gwa_ranges.keys()),
            'data': list(gwa_ranges.values())
        }),
        'section_balance': json.dumps(section_data),
        'enrollment_status': json.dumps({
            'labels': ['Approved', 'Rejected', 'Under Review', 'Pending'],
            'data': [approved, rejected, under_review, pending],
            'colors': ['#10B981', '#EF4444', '#F59E0B', '#6B7280']
        }),
        'gender_distribution': json.dumps({
            'labels': ['Male', 'Female'],
            'data': [gender_dist['Male'], gender_dist['Female']],
            'colors': ['#3B82F6', '#EC4899']
        }),
        'subject_averages': json.dumps({
            'labels': [SUBJECT_LABELS[f] for f in SUBJECT_FIELDS],
            'data': [subject_averages[f] for f in SUBJECT_FIELDS]
        }),
        'section_gwa': json.dumps(section_academics),
        'feeder_schools': json.dumps({
            'labels': [s['name'][:20] for s in feeder_schools],
            'data': [s['count'] for s in feeder_schools]
        }),
    }

    # Enrollment growth chart (current vs previous year)
    if enrollment_growth:
        chart_data['enrollment_growth'] = json.dumps({
            'labels': [enrollment_growth['previous_year'], enrollment_growth['current_year']],
            'data': [enrollment_growth['previous_count'], enrollment_growth['current_count']]
        })

    # REGULAR-specific chart
    if program_code == 'REGULAR':
        chart_data['track_balance'] = json.dumps({
            'labels': ['TOP5', 'HETERO'],
            'data': [top5_count, hetero_count],
            'colors': ['#3B82F6', '#6366F1']
        })

    # --- Build Table Data ---
    table_data = [
        {'metric': 'Total Applicants', 'value': str(total_applicants)},
        {'metric': 'Approved', 'value': str(approved)},
        {'metric': 'Rejected', 'value': str(rejected)},
        {'metric': 'Under Review', 'value': str(under_review)},
        {'metric': 'Pending', 'value': str(pending)},
        {'metric': 'Average GWA', 'value': str(avg_gwa)},
        {'metric': 'Total Sections', 'value': str(total_sections)},
        {'metric': 'Section Fill Rate', 'value': f'{fill_rate}%'},
        {'metric': 'Assigned to Sections', 'value': str(assigned)},
        {'metric': 'Highest Section', 'value': f'{highest_section or "N/A"} ({highest_avg})'},
    ]

    # Add enrollment growth to table
    if enrollment_growth:
        sign = '+' if enrollment_growth['growth_pct'] >= 0 else ''
        table_data.append({
            'metric': f'Growth vs {enrollment_growth["previous_year"]}',
            'value': f'{sign}{enrollment_growth["growth_pct"]}% ({enrollment_growth["previous_count"]} → {enrollment_growth["current_count"]})'
        })

    # Add key subject averages to table
    for ks in key_subject_data:
        table_data.append({
            'metric': f'Avg {ks["label"]} Grade',
            'value': f'{ks["average"]} ({ks["above_90_pct"]}% scored 90+)'
        })

    if program_code == 'REGULAR':
        table_data.insert(5, {'metric': 'TOP5 Students', 'value': str(top5_count)})
        table_data.insert(6, {'metric': 'HETERO Students', 'value': str(hetero_count)})

    return {
        'metrics': metrics,
        'chart_data': chart_data,
        'table_data': table_data,
        'key_subjects': key_subject_data,
        'feeder_schools': feeder_schools,
        'enrollment_growth': enrollment_growth,
        'section_academics': section_academics,
    }


@coordinator_required
def analytics(request):
    # Get the coordinator's program
    program_obj = None
    if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'program'):
        program_obj = request.user.profile.program

    # Extract program code
    program_code = get_program_code(program_obj)
    
    active_grade = request.session.get('active_grade_level_code')

    # Get universal analytics data with real DB queries
    analytics_data = get_analytics_data(program_code, program_obj, active_grade)

    context = {
        'user': request.user,
        'program': program_code,
        'program_full_name': PROGRAM_NAMES.get(program_code, program_code),
        'analytics': analytics_data,
        'metrics': analytics_data.get('metrics', {}),
        'chart_data': analytics_data.get('chart_data', {}),
        'table_data': analytics_data.get('table_data', []),
        'key_subjects': analytics_data.get('key_subjects', []),
        'feeder_schools': analytics_data.get('feeder_schools', []),
        'enrollment_growth': analytics_data.get('enrollment_growth'),
        'section_academics': analytics_data.get('section_academics', []),
    }

    return render(request, 'coordinator_app/analytics.html', context)
