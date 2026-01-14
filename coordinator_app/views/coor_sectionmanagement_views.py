from django.shortcuts import render
from admin_app.decorators import coordinator_required
from admin_app.models import Section, UserProfile

@coordinator_required
def section_management(request):
    """View to manage sections for the coordinator's program"""
    try:
        # Get coordinator's profile
        user_profile = request.user.profile
        program = user_profile.program
        
        # Fetch sections for the coordinator's program
        if program:
            sections = Section.objects.filter(
                program=program
            ).select_related('adviser', 'program', 'school_year').order_by('name')
        else:
            sections = Section.objects.none()
        
        context = {
            'user': request.user,
            'program': program,
            'sections': sections,
            'user_profile': user_profile,
        }
        return render(request, 'coordinator_app/section_management.html', context)
    except Exception as e:
        context = {
            'user': request.user,
            'sections': [],
            'error': str(e)
        }
        return render(request, 'coordinator_app/section_management.html', context)