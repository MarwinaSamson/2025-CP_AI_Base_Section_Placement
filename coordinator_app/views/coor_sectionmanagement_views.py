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
            ).select_related('adviser', 'program', 'school_year').order_by('created_at')
            
            # Update all section counts from database to ensure accuracy
            for section in sections:
                section.update_current_students_count()
            
            # For REGULAR program, separate sections by track
            top5_sections = []
            hetero_sections = []
            other_sections = []
            
            if program.code == 'REGULAR':
                for section in sections:
                    if section.regular_track == 'TOP5':
                        top5_sections.append(section)
                    elif section.regular_track == 'HETERO':
                        hetero_sections.append(section)
                    else:
                        other_sections.append(section)
            else:
                # For non-REGULAR programs, just use all sections
                other_sections = list(sections)
        else:
            sections = Section.objects.none()
            top5_sections = []
            hetero_sections = []
            other_sections = []
        
        context = {
            'user': request.user,
            'program': program,
            'sections': sections,
            'top5_sections': top5_sections,
            'hetero_sections': hetero_sections,
            'other_sections': other_sections,
            'user_profile': user_profile,
            'is_regular_program': program.code == 'REGULAR' if program else False,
        }
        return render(request, 'coordinator_app/section_management.html', context)
    except Exception as e:
        context = {
            'user': request.user,
            'sections': [],
            'top5_sections': [],
            'hetero_sections': [],
            'other_sections': [],
            'is_regular_program': False,
            'error': str(e)
        }
        return render(request, 'coordinator_app/section_management.html', context)