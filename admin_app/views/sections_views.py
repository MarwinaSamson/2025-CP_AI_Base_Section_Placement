from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
import json

from admin_app.models import Program, Teacher, Subject, Section, Building, Room, ActivityLog


def log_activity(user, action, description, request=None):
    """
    Helper function to log activities to the database
    """
    try:
        ip_address = None
        user_agent = None
        
        if request:
            # Get IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            # Get user agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        ActivityLog.objects.create(
            user=user,
            action=action,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        # Log silently to avoid breaking the main functionality
        print(f"Error logging activity: {str(e)}")


@login_required
def sections_list(request):
    return render(request, 'admin_app/sections.html')

@login_required
def sections_by_program(request, program):
    return render(request, 'admin_app/sections.html', {'program': program})

@login_required
def section_detail(request, program, section_id):
    return render(request, 'admin_app/sections.html', {
        'program': program,
        'section_id': section_id
    })


# ============== HELPER FUNCTIONS ==============

def _get_program_by_code(code):
    """Get program by code (case-insensitive)"""
    try:
        return Program.objects.get(code__iexact=code)
    except Program.DoesNotExist:
        return None


# ============== API: PROGRAMS ==============

@login_required
@require_http_methods(["GET"])
def get_programs(request):
    """Get all active programs"""
    programs = Program.objects.filter(is_active=True).order_by('code')
    data = [
        {
            'id': p.id,
            'code': p.code,
            'name': p.name,
            'description': p.description or ''
        }
        for p in programs
    ]
    return JsonResponse({'programs': data}, status=200)


@login_required
@require_http_methods(["GET"])
def get_all_programs(request):
    """Get all programs including inactive ones"""
    programs = Program.objects.all().order_by('code')
    data = [
        {
            'id': p.id,
            'code': p.code,
            'name': p.name,
            'description': p.description or '',
            'is_active': p.is_active,
            'created_at': p.created_at.strftime('%Y-%m-%d'),
            'sections_count': p.sections.count()
        }
        for p in programs
    ]
    return JsonResponse({'programs': data}, status=200)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def add_program(request):
    """Add a new program"""
    try:
        data = json.loads(request.body)
        code = (data.get('code') or '').strip().upper()
        name = (data.get('name') or '').strip()
        description = (data.get('description') or '').strip()
        is_active = data.get('is_active', True)
        
        if not code:
            return JsonResponse({'error': 'Program code is required'}, status=400)
        
        if not name:
            return JsonResponse({'error': 'Program name is required'}, status=400)
        
        # Check if program already exists
        if Program.objects.filter(code__iexact=code).exists():
            return JsonResponse({'error': f'Program "{code}" already exists'}, status=400)
        
        # Create program
        program = Program.objects.create(
            code=code,
            name=name,
            description=description,
            is_active=is_active
        )
        
        # Log activity
        log_activity(
            user=request.user,
            action='program_added',
            description=f'Added program: {program.code}',
            request=request
        )
        
        return JsonResponse({
            'message': f'Program "{code}" added successfully',
            'program': {
                'id': program.id,
                'code': program.code,
                'name': program.name,
                'description': program.description or '',
                'is_active': program.is_active
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def update_program(request, program_id):
    """Update an existing program"""
    try:
        program = Program.objects.get(pk=program_id)
        data = json.loads(request.body)
        
        code = (data.get('code') or '').strip().upper()
        name = (data.get('name') or '').strip()
        description = (data.get('description') or '').strip()
        is_active = data.get('is_active', program.is_active)
        
        if not code:
            return JsonResponse({'error': 'Program code is required'}, status=400)
        
        if not name:
            return JsonResponse({'error': 'Program name is required'}, status=400)
        
        # Check if code is changing and if new code already exists
        if code != program.code and Program.objects.filter(code__iexact=code).exists():
            return JsonResponse({'error': f'Program "{code}" already exists'}, status=400)
        
        # Update program
        program.code = code
        program.name = name
        program.description = description
        program.is_active = is_active
        program.save()
        
        # Log activity
        log_activity(
            user=request.user,
            action='program_updated',
            description=f'Updated program: {program.code}',
            request=request
        )
        
        return JsonResponse({
            'message': f'Program "{code}" updated successfully',
            'program': {
                'id': program.id,
                'code': program.code,
                'name': program.name,
                'description': program.description or '',
                'is_active': program.is_active
            }
        }, status=200)
        
    except Program.DoesNotExist:
        return JsonResponse({'error': 'Program not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def delete_program(request, program_id):
    """Delete a program"""
    try:
        program = Program.objects.get(pk=program_id)
        
        # Check if program has sections
        sections_count = program.sections.count()
        if sections_count > 0:
            return JsonResponse({
                'error': f'Cannot delete program "{program.code}". It has {sections_count} section(s) assigned to it.'
            }, status=400)
        
        program_code = program.code
        program.delete()
        
        # Log activity
        log_activity(
            user=request.user,
            action='program_deleted',
            description=f'Deleted program: {program_code}',
            request=request
        )
        
        return JsonResponse({
            'message': f'Program "{program_code}" deleted successfully'
        }, status=200)
        
    except Program.DoesNotExist:
        return JsonResponse({'error': 'Program not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def toggle_program_status(request, program_id):
    """Toggle program active status"""
    try:
        program = Program.objects.get(pk=program_id)
        program.is_active = not program.is_active
        program.save()
        
        status_text = 'activated' if program.is_active else 'deactivated'
        
        # Log activity
        log_activity(
            user=request.user,
            action='program_updated',
            description=f'{status_text.capitalize()} program: {program.code}',
            request=request
        )
        
        return JsonResponse({
            'message': f'Program "{program.code}" {status_text} successfully',
            'is_active': program.is_active
        }, status=200)
        
    except Program.DoesNotExist:
        return JsonResponse({'error': 'Program not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============== API: TEACHERS ==============

@login_required
@require_http_methods(["GET"])
def get_teachers(request):
    """Get all teachers with their adviser status"""
    teachers = Teacher.objects.all().order_by('last_name', 'first_name')
    data = []
    for t in teachers:
        data.append({
            'id': t.id,
            'name': t.get_full_name(),
            'is_adviser': t.is_adviser,
            'advisory_section_id': getattr(t, 'advisory_section', None).id if getattr(t, 'advisory_section', None) else None,
            'position': t.position.name if t.position else '',
            'department': t.department.name if t.department else ''
        })
    return JsonResponse({'teachers': data}, status=200)


# ============== API: BUILDINGS & ROOMS ==============

@login_required
@require_http_methods(["GET"])
def get_buildings(request):
    """Get all buildings with their rooms"""
    buildings = Building.objects.prefetch_related('rooms').all().order_by('name')
    data = []
    for building in buildings:
        rooms = [
            {
                'id': room.id,
                'room_number': room.room_number
            }
            for room in building.rooms.all().order_by('room_number')
        ]
        data.append({
            'id': building.id,
            'name': building.name,
            'rooms': rooms
        })
    return JsonResponse({'buildings': data}, status=200)


@login_required
@require_http_methods(["GET"])
def get_rooms(request):
    """Get rooms for a specific building"""
    building_id = request.GET.get('building')
    if not building_id:
        return JsonResponse({'error': 'Building ID is required'}, status=400)
    
    try:
        building = Building.objects.get(id=building_id)
        rooms = building.rooms.all().order_by('room_number')
        data = [
            {
                'id': room.id,
                'room_number': room.room_number,
                'building_id': room.building.id,
                'building_name': room.building.name
            }
            for room in rooms
        ]
        return JsonResponse({'rooms': data}, status=200)
    except Building.DoesNotExist:
        return JsonResponse({'error': 'Building not found'}, status=404)


# ============== API: SUBJECTS ==============

@login_required
@require_http_methods(["GET"])
def get_subjects(request):
    """Get subjects, optionally filtered by program"""
    program_code = request.GET.get('program')
    qs = Subject.objects.filter(is_active=True)
    if program_code:
        program = _get_program_by_code(program_code)
        if not program:
            return JsonResponse({'error': 'Program not found'}, status=404)
        qs = qs.filter(program=program)
    qs = qs.select_related('program').order_by('program__code', 'name')
    subjects = [
        {
            'id': s.id,
            'name': s.name,
            'code': s.code,
            'description': s.description or '',
            'program_code': s.program.code,
            'program_name': s.program.name,
        }
        for s in qs
    ]
    return JsonResponse({'subjects': subjects}, status=200)


@login_required
@require_http_methods(["POST"])
def add_subject(request):
    """Add a new subject"""
    try:
        data = json.loads(request.body)
        name = (data.get('name') or '').strip()
        code = (data.get('code') or '').strip().upper()
        description = data.get('description') or ''
        program_code = data.get('program')
        
        if not program_code:
            return JsonResponse({'error': 'Program is required'}, status=400)
        
        program = _get_program_by_code(program_code)
        if not program:
            return JsonResponse({'error': 'Program not found'}, status=404)
        
        if not name:
            return JsonResponse({'error': 'Subject name is required'}, status=400)
        if not code:
            return JsonResponse({'error': 'Subject code is required'}, status=400)
        
        # Check if subject code already exists for this program
        if Subject.objects.filter(program=program, code=code).exists():
            return JsonResponse({'error': f'Subject code {code} already exists for this program'}, status=400)
        
        subject = Subject.objects.create(
            program=program,
            name=name,
            code=code,
            description=description
        )
        
        # Log activity
        log_activity(
            user=request.user,
            action='section_management',
            description=f'Added subject: {code} - {name} for {program.code}',
            request=request
        )
        
        return JsonResponse({
            'message': 'Subject added successfully',
            'subject': {
                'id': subject.id,
                'name': subject.name,
                'code': subject.code,
                'description': subject.description or '',
                'program_code': subject.program.code,
                'program_name': subject.program.name,
            }
        }, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["PUT"])
def update_subject(request, subject_id):
    """Update an existing subject"""
    try:
        subject = Subject.objects.get(pk=subject_id)
        data = json.loads(request.body)
        name = (data.get('name') or '').strip()
        code = (data.get('code') or '').strip().upper()
        description = data.get('description') or ''
        
        if not name:
            return JsonResponse({'error': 'Subject name is required'}, status=400)
        if not code:
            return JsonResponse({'error': 'Subject code is required'}, status=400)
        
        # Check if new code conflicts with another subject in same program
        if Subject.objects.filter(program=subject.program, code=code).exclude(pk=subject_id).exists():
            return JsonResponse({'error': f'Subject code {code} already exists for this program'}, status=400)
        
        old_code = subject.code
        old_name = subject.name
        subject.name = name
        subject.code = code
        subject.description = description
        subject.save()
        
        # Log activity
        log_activity(
            user=request.user,
            action='section_management',
            description=f'Updated subject: {old_code} -> {code} ({old_name} -> {name}) for {subject.program.code}',
            request=request
        )
        
        return JsonResponse({
            'message': 'Subject updated successfully',
            'subject': {
                'id': subject.id,
                'name': subject.name,
                'code': subject.code,
                'description': subject.description or '',
                'program_code': subject.program.code,
                'program_name': subject.program.name,
            }
        }, status=200)
    except Subject.DoesNotExist:
        return JsonResponse({'error': 'Subject not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_subject(request, subject_id):
    """Delete a subject"""
    try:
        subject = Subject.objects.get(pk=subject_id)
        subject_name = subject.name
        subject_code = subject.code
        program_code = subject.program.code
        subject.delete()
        
        # Log activity
        log_activity(
            user=request.user,
            action='section_management',
            description=f'Deleted subject: {subject_code} - {subject_name} from {program_code}',
            request=request
        )
        
        return JsonResponse({'message': f'Subject "{subject_name}" deleted successfully'}, status=200)
    except Subject.DoesNotExist:
        return JsonResponse({'error': 'Subject not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============== API: SECTIONS ==============

@login_required
@require_http_methods(["GET"])
def get_sections(request):
    """Get sections, optionally filtered by program"""
    program_code = request.GET.get('program')
    qs = Section.objects.select_related('program', 'adviser').order_by('program__code', 'name')
    
    if program_code:
        program = _get_program_by_code(program_code)
        if not program:
            return JsonResponse({'error': 'Program not found'}, status=404)
        qs = qs.filter(program=program)
    
    sections = []
    for s in qs:
        sections.append({
            'id': s.id,
            'name': s.name,
            'program_code': s.program.code,
            'program_name': s.program.name,
            'adviser_id': s.adviser.id if s.adviser else None,
            'adviser_name': s.adviser.get_full_name() if s.adviser else '',
            'building': s.building or '',
            'room': s.room or '',
            'max_students': s.max_students,
            'current_students': s.current_students,
            'location': f"Bldg {s.building} Room {s.room}".strip() if s.building or s.room else '',
        })
    return JsonResponse({'sections': sections}, status=200)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def add_section(request):
    """Add a new section"""
    try:
        data = json.loads(request.body)
        name = (data.get('name') or '').strip()
        program_code = data.get('program')
        adviser_id = data.get('adviser')
        building_id = data.get('building')
        room_id = data.get('room')
        max_students = int(data.get('max_students') or 40)
        
        # Validate required fields
        if not name:
            return JsonResponse({'error': 'Section name is required'}, status=400)
        
        if not program_code:
            return JsonResponse({'error': 'Program is required'}, status=400)
        
        # Get program
        program = _get_program_by_code(program_code)
        if not program:
            return JsonResponse({'error': 'Program not found'}, status=404)
        
        # Check if section name already exists for this program
        if Section.objects.filter(program=program, name=name).exists():
            return JsonResponse({'error': f'Section "{name}" already exists in {program.code} program'}, status=400)
        
        # Handle adviser
        adviser = None
        if adviser_id:
            try:
                adviser = Teacher.objects.get(pk=adviser_id)
                # Check if teacher is already an adviser
                if adviser.is_adviser:
                    return JsonResponse({'error': f'{adviser.get_full_name()} is already assigned as an adviser to another section'}, status=400)
            except Teacher.DoesNotExist:
                return JsonResponse({'error': 'Selected adviser not found'}, status=404)
        
        # Handle building and room
        building_name = ''
        room_number = ''
        if building_id and room_id:
            try:
                building = Building.objects.get(pk=building_id)
                room = Room.objects.get(pk=room_id, building=building)
                building_name = building.name
                room_number = room.room_number
            except Building.DoesNotExist:
                return JsonResponse({'error': 'Selected building not found'}, status=404)
            except Room.DoesNotExist:
                return JsonResponse({'error': 'Selected room not found or does not belong to the building'}, status=404)
        
        # Create section
        section = Section.objects.create(
            program=program,
            name=name,
            adviser=adviser,
            building=building_name,
            room=room_number,
            max_students=max_students,
        )
        
        # Update adviser flag
        if adviser:
            adviser.is_adviser = True
            adviser.save(update_fields=['is_adviser'])
        
        # Log activity
        location = f"Bldg {building_name} Room {room_number}" if building_name and room_number else "No location"
        adviser_info = f" with adviser {adviser.get_full_name()}" if adviser else ""
        log_activity(
            user=request.user,
            action='section_management',
            description=f'Created section: {program.code} - {name} at {location}{adviser_info}',
            request=request
        )
        
        return JsonResponse({
            'message': f'Section "{name}" created successfully',
            'section': {
                'id': section.id,
                'name': section.name,
                'program_code': section.program.code,
                'program_name': section.program.name,
                'adviser_id': adviser.id if adviser else None,
                'adviser_name': adviser.get_full_name() if adviser else '',
                'building': section.building or '',
                'room': section.room or '',
                'max_students': section.max_students,
                'current_students': section.current_students,
            }
        }, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except ValueError as e:
        return JsonResponse({'error': f'Invalid data format: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["PUT"])
@transaction.atomic
def update_section(request, section_id):
    """Update an existing section"""
    try:
        section = Section.objects.select_related('adviser', 'program').get(pk=section_id)
        data = json.loads(request.body)
        
        name = (data.get('name') or '').strip()
        adviser_id = data.get('adviser')
        building_id = data.get('building')
        room_id = data.get('room')
        max_students = int(data.get('max_students') or section.max_students)
        
        # Validate required fields
        if not name:
            return JsonResponse({'error': 'Section name is required'}, status=400)
        
        # Check if new name conflicts with another section in same program
        if Section.objects.filter(program=section.program, name=name).exclude(pk=section_id).exists():
            return JsonResponse({'error': f'Section "{name}" already exists in {section.program.code} program'}, status=400)
        
        # Handle adviser change
        old_adviser = section.adviser
        new_adviser = None
        
        if adviser_id:
            try:
                new_adviser = Teacher.objects.get(pk=adviser_id)
                # Check if new adviser is already assigned (excluding current section)
                if new_adviser != old_adviser and new_adviser.is_adviser:
                    return JsonResponse({'error': f'{new_adviser.get_full_name()} is already assigned as an adviser to another section'}, status=400)
            except Teacher.DoesNotExist:
                return JsonResponse({'error': 'Selected adviser not found'}, status=404)
        
        # Handle building and room
        building_name = ''
        room_number = ''
        if building_id and room_id:
            try:
                building = Building.objects.get(pk=building_id)
                room = Room.objects.get(pk=room_id, building=building)
                building_name = building.name
                room_number = room.room_number
            except Building.DoesNotExist:
                return JsonResponse({'error': 'Selected building not found'}, status=404)
            except Room.DoesNotExist:
                return JsonResponse({'error': 'Selected room not found or does not belong to the building'}, status=404)
        
        # Update section
        section.name = name
        section.adviser = new_adviser
        section.building = building_name
        section.room = room_number
        section.max_students = max_students
        section.save()
        
        # Update adviser flags
        if old_adviser and old_adviser != new_adviser:
            old_adviser.is_adviser = False
            old_adviser.save(update_fields=['is_adviser'])
        
        if new_adviser and new_adviser != old_adviser:
            new_adviser.is_adviser = True
            new_adviser.save(update_fields=['is_adviser'])
        
        # Log activity
        changes = []
        if section.name != name:
            changes.append(f"name: {section.name} -> {name}")
        if old_adviser != new_adviser:
            old_adv = old_adviser.get_full_name() if old_adviser else "None"
            new_adv = new_adviser.get_full_name() if new_adviser else "None"
            changes.append(f"adviser: {old_adv} -> {new_adv}")
        location = f"Bldg {building_name} Room {room_number}" if building_name and room_number else "No location"
        change_desc = ", ".join(changes) if changes else "details"
        log_activity(
            user=request.user,
            action='section_management',
            description=f'Updated section: {section.program.code} - {name} ({change_desc}) at {location}',
            request=request
        )
        
        return JsonResponse({
            'message': f'Section "{name}" updated successfully',
            'section': {
                'id': section.id,
                'name': section.name,
                'program_code': section.program.code,
                'program_name': section.program.name,
                'adviser_id': section.adviser.id if section.adviser else None,
                'adviser_name': section.adviser.get_full_name() if section.adviser else '',
                'building': section.building or '',
                'room': section.room or '',
                'max_students': section.max_students,
                'current_students': section.current_students,
            }
        }, status=200)
    except Section.DoesNotExist:
        return JsonResponse({'error': 'Section not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except ValueError as e:
        return JsonResponse({'error': f'Invalid data format: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
@transaction.atomic
def delete_section(request, section_id):
    """Delete a section"""
    try:
        section = Section.objects.select_related('adviser', 'program').get(pk=section_id)
        section_name = section.name
        program_code = section.program.code
        adviser = section.adviser
        adviser_name = adviser.get_full_name() if adviser else "No adviser"
        
        # Delete the section
        section.delete()
        
        # Update adviser flag if exists
        if adviser:
            adviser.is_adviser = False
            adviser.save(update_fields=['is_adviser'])
        
        # Log activity
        log_activity(
            user=request.user,
            action='section_management',
            description=f'Deleted section: {program_code} - {section_name} (Adviser: {adviser_name})',
            request=request
        )
        
        return JsonResponse({'message': f'Section "{section_name}" deleted successfully'}, status=200)
    except Section.DoesNotExist:
        return JsonResponse({'error': 'Section not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)