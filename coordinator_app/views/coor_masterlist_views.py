from django.shortcuts import render, get_object_or_404
from admin_app.decorators import coordinator_required
from admin_app.models import Section
from enrollment_app.models import Student

@coordinator_required
def masterlist_by_section(request, section_id):
    """View to display masterlist for a specific section"""
    try:
        # Get coordinator's profile and program
        user_profile = request.user.profile
        program = user_profile.program
        
        # Get the section (ensure it belongs to coordinator's program)
        section = get_object_or_404(
            Section.objects.select_related('program', 'school_year', 'adviser'),
            id=section_id,
            program=program
        )
        
        # Get students enrolled in this section
        students = Student.objects.filter(
            final_section=section
        ).select_related('program').order_by('last_name', 'first_name')
        
        context = {
            'user': request.user,
            'section': section,
            'students': students,
            'program': program,
            'user_profile': user_profile,
        }
        return render(request, 'coordinator_app/cor-masterlist.html', context)
    except Exception as e:
        context = {
            'user': request.user,
            'error': str(e)
        }
        return render(request, 'coordinator_app/cor-masterlist.html', context)
