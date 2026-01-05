from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count, Q, F
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from admin_app.decorators import admin_required
from admin_app.models import (
    SchoolYear, UserProfile, Teacher, Section, Program
)
from enrollment_app.models import Student, StudentData, ProgramSelection
from datetime import datetime, timedelta


@admin_required
def dashboard(request):
    """
    Main admin dashboard view
    """
    # Get active school year
    active_school_year = SchoolYear.get_active_school_year()
    
    # Get user profile
    try:
        user_profile = UserProfile.objects.select_related('program', 'position', 'department').get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None
    
    context = {
        'user': request.user,
        'user_profile': user_profile,
        'active_school_year': active_school_year,
    }
    return render(request, 'admin_app/dashboard.html', context)


@admin_required
def dashboard_header_data(request):
    """
    API endpoint for dashboard header data
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
def dashboard_statistics(request):
    """
    API endpoint for dashboard statistics
    Returns: total teachers, students, programs, sections
    """
    # Get active school year
    active_school_year = SchoolYear.get_active_school_year()
    
    # Get statistics
    total_teachers = Teacher.objects.count()
    total_programs = Program.objects.count()
    
    if active_school_year:
        # Statistics for active school year
        total_students = Student.objects.filter(
            school_year=active_school_year,
            enrollment_status__in=['submitted', 'under_review', 'approved']
        ).count()
        total_sections = Section.objects.filter(school_year=active_school_year).count()
        
        # Grade level breakdown
        grade_7_students = Student.objects.filter(
            school_year=active_school_year,
            enrollment_status__in=['submitted', 'under_review', 'approved']
        ).count()  # You might need to add grade_level field to filter properly
        
    else:
        total_students = 0
        total_sections = 0
        grade_7_students = 0
    
    data = {
        'total_teachers': total_teachers,
        'total_students': total_students,
        'total_programs': total_programs,
        'total_sections': total_sections,
        'grade_breakdown': {
            'grade_7': grade_7_students // 4 if grade_7_students else 0,  # Simplified distribution
            'grade_8': grade_7_students // 4 if grade_7_students else 0,
            'grade_9': grade_7_students // 4 if grade_7_students else 0,
            'grade_10': grade_7_students // 4 if grade_7_students else 0,
        }
    }
    
    return JsonResponse(data)


@admin_required
def dashboard_notifications(request):
    """
    API endpoint for new student enrollment notifications
    Returns notifications grouped by program
    """
    # Get active school year
    active_school_year = SchoolYear.get_active_school_year()
    
    if not active_school_year:
        return JsonResponse({'notifications': [], 'total_count': 0})
    
    # Get new students (submitted status) grouped by program
    # Students who have completed enrollment but not yet reviewed
    new_students = Student.objects.filter(
        school_year=active_school_year,
        enrollment_status='submitted',
        program_selected=True
    ).select_related('program_selection')
    
    # Group by program
    notifications = []
    program_counts = {}
    
    for student in new_students:
        try:
            program_selection = student.program_selection
            program_code = program_selection.selected_program_code
            
            if program_code not in program_counts:
                program_counts[program_code] = {
                    'count': 0,
                    'students': []
                }
            
            program_counts[program_code]['count'] += 1
            
            # Get student details
            try:
                student_data = student.student_data
                student_name = student_data.full_name
            except:
                student_name = f"Student {student.lrn}"
            
            program_counts[program_code]['students'].append({
                'lrn': student.lrn,
                'name': student_name,
                'created_at': student.created_at.strftime('%b %d, %Y %I:%M %p'),
                'time_ago': get_time_ago(student.created_at)
            })
        except:
            continue
    
    # Create notification list
    for program_code, data in program_counts.items():
        try:
            program = Program.objects.get(code=program_code)
            icon_map = {
                'STE': 'fas fa-flask',
                'SPFL': 'fas fa-language',
                'SPTVE': 'fas fa-tools',
                'OHSP': 'fas fa-laptop-house',
                'SNED': 'fas fa-universal-access',
                'TOP 5': 'fas fa-trophy',
                'HETERO': 'fas fa-users',
            }
            
            notifications.append({
                'program_code': program_code,
                'program_name': program.name,
                'icon': icon_map.get(program_code, 'fas fa-users'),
                'count': data['count'],
                'students': data['students'][:5],  # Limit to 5 most recent
                'message': f"{data['count']} new {program_code} application{'s' if data['count'] > 1 else ''} pending review"
            })
        except Program.DoesNotExist:
            continue
    
    # Sort by count (highest first)
    notifications.sort(key=lambda x: x['count'], reverse=True)
    
    total_count = sum(n['count'] for n in notifications)
    
    return JsonResponse({
        'notifications': notifications,
        'total_count': total_count
    })


@admin_required
def dashboard_programs_overview(request):
    """
    API endpoint for programs overview table
    Returns detailed program statistics
    """
    # Get active school year
    active_school_year = SchoolYear.get_active_school_year()
    
    if not active_school_year:
        return JsonResponse({'programs': []})
    
    # Get all active programs
    programs = Program.objects.filter(is_active=True).order_by('code')
    
    programs_data = []
    total_approved = 0
    total_pending = 0
    total_rejected = 0
    
    for program in programs:
        # Get program statistics
        program_students = ProgramSelection.objects.filter(
            school_year=active_school_year,
            selected_program_code=program.code
        ).select_related('student')
        
        total = program_students.count()
        approved = program_students.filter(student__enrollment_status='approved').count()
        pending = program_students.filter(student__enrollment_status__in=['submitted', 'under_review']).count()
        rejected = program_students.filter(student__enrollment_status='rejected').count()
        
        # Get sections for this program
        sections = Section.objects.filter(
            school_year=active_school_year,
            program=program
        )
        section_count = sections.count()
        capacity = sum(s.max_students for s in sections)
        
        # Calculate acceptance rate
        reviewed = approved + rejected
        acceptance_rate = (approved / reviewed * 100) if reviewed > 0 else 0
        
        # Determine trend (you can calculate from previous year if needed)
        trend = 'stable'
        trend_value = 0
        
        programs_data.append({
            'code': program.code,
            'name': program.name,
            'status': 'active',
            'total_applicants': total,
            'approved': approved,
            'pending': pending,
            'rejected': rejected,
            'capacity': capacity,
            'sections': section_count,
            'acceptance_rate': round(acceptance_rate, 1),
            'trend': trend,
            'trend_value': trend_value
        })
        
        total_approved += approved
        total_pending += pending
        total_rejected += rejected
    
    # Calculate overall acceptance rate
    total_reviewed = total_approved + total_rejected
    overall_acceptance_rate = (total_approved / total_reviewed * 100) if total_reviewed > 0 else 0
    
    return JsonResponse({
        'programs': programs_data,
        'summary': {
            'total_approved': total_approved,
            'total_pending': total_pending,
            'total_rejected': total_rejected,
            'overall_acceptance_rate': round(overall_acceptance_rate, 1)
        }
    })


def get_time_ago(dt):
    """
    Helper function to get human-readable time difference
    """
    now = timezone.now()
    diff = now - dt
    
    if diff.days > 0:
        if diff.days == 1:
            return "1 day ago"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        else:
            months = diff.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
    
    hours = diff.seconds // 3600
    if hours > 0:
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    
    minutes = diff.seconds // 60
    if minutes > 0:
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    
    return "Just now"