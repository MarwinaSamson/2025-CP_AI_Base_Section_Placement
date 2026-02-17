from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from admin_app.decorators import coordinator_required
from admin_app.models import Section
from enrollment_app.models import ProgramSelection
from coordinator_app.models import CoordinatorActivityLog

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
        
        # Query students flagged for manual review by AI
        if program:
            under_review_students = ProgramSelection.objects.filter(
                selected_program_code=program.code,
                admin_approved=False,
                admin_rejected=False,
                student__enrollment_status='under_review',
            ).select_related('student', 'student__student_data', 'student__academic_data')
            under_review_count = under_review_students.count()
        else:
            under_review_students = ProgramSelection.objects.none()
            under_review_count = 0

        context = {
            'user': request.user,
            'program': program,
            'sections': sections,
            'top5_sections': top5_sections,
            'hetero_sections': hetero_sections,
            'other_sections': other_sections,
            'user_profile': user_profile,
            'is_regular_program': program.code == 'REGULAR' if program else False,
            'under_review_students': under_review_students,
            'under_review_count': under_review_count,
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


@coordinator_required
@require_POST
def toggle_masterlist_published(request, section_id):
    """Toggle the masterlist_published flag for a section."""
    user_profile = request.user.profile
    program = user_profile.program

    section = get_object_or_404(Section, id=section_id, program=program)
    section.masterlist_published = not section.masterlist_published
    section.save(update_fields=['masterlist_published'])

    # Log the action
    action = 'masterlist_published' if section.masterlist_published else 'masterlist_unpublished'
    CoordinatorActivityLog.log(
        user=request.user,
        program=program,
        action=action,
        category='section',
        description=f"{'Published' if section.masterlist_published else 'Unpublished'} masterlist for {section.name}",
        section_name=section.name,
        request=request
    )

    return JsonResponse({
        'success': True,
        'published': section.masterlist_published,
        'section_name': section.name,
    })