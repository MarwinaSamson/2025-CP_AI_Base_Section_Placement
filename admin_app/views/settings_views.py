from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.db import transaction
from django.core.exceptions import ValidationError
from admin_app.models import UserProfile, Position, Department, Program, SystemSettings, StaffMember, ActivityLog, Building, Room, Section, SchoolYear, DocumentRequirement, Teacher
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from datetime import datetime
import json
import base64
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseNotAllowed, HttpResponseBadRequest, HttpResponseNotFound

# --- User CRUD API Endpoints ---
from django.contrib.auth.models import User

from django.contrib.auth.decorators import login_required

@login_required
def get_user_profile(request, user_id):
    """
    GET /api/users/<user_id>/
    Returns user profile data including position_id, department_id, program_id
    so the edit modal can pre-select the correct dropdown options.
    """
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    try:
        user = User.objects.get(pk=user_id)
        profile = None
        try:
            profile = user.profile
        except Exception:
            pass

        data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_active': user.is_active,
            'date_joined': user.date_joined.strftime('%b %d, %Y'),
        }

        if profile:
            data.update({
                'employee_id': getattr(profile, 'employee_id', ''),
                'user_type': getattr(profile, 'user_type', ''),
                'position': profile.get_position_name() if hasattr(profile, 'get_position_name') else '',
                'department': profile.get_department_name() if hasattr(profile, 'get_department_name') else '',
                'position_id': profile.position_id if profile.position_id else None,
                'department_id': profile.department_id if profile.department_id else None,
                'program_id': profile.program_id if profile.program_id else None,
            })

        return JsonResponse({'user': data})
    except User.DoesNotExist:
        return HttpResponseNotFound('User not found')
    
@csrf_exempt
@login_required
def update_user_profile(request, user_id):
    """
    PUT /api/users/<user_id>/update/
    Updates user and profile fields.
    Accepts position_id, department_id, program_id as integers.
    """
    if request.method != 'PUT':
        return HttpResponseNotAllowed(['PUT'])
    try:
        user = User.objects.get(pk=user_id)
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            return HttpResponseBadRequest('Invalid JSON')

        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.email = data.get('email', user.email)

        if User.objects.filter(email=user.email).exclude(pk=user_id).exists():
            return JsonResponse({'error': 'Email already in use by another account'}, status=400)

        user.save()

        try:
            profile = user.profile
        except Exception:
            return JsonResponse({'success': True, 'message': 'User updated (no profile found)'})

        if 'employee_id' in data:
            new_emp_id = data['employee_id']
            if UserProfile.objects.filter(employee_id=new_emp_id).exclude(pk=profile.pk).exists():
                return JsonResponse({'error': 'Employee ID already in use'}, status=400)
            profile.employee_id = new_emp_id

        if 'user_type' in data:
            profile.user_type = data['user_type']
            user.is_staff = (data['user_type'] == 'admin')
            user.save(update_fields=['is_staff'])

        if 'position_id' in data:
            pos_id = data['position_id']
            if pos_id:
                try:
                    profile.position = Position.objects.get(pk=pos_id)
                except Position.DoesNotExist:
                    return JsonResponse({'error': 'Invalid position ID'}, status=400)
            else:
                profile.position = None

        if 'department_id' in data:
            dept_id = data['department_id']
            if dept_id:
                try:
                    profile.department = Department.objects.get(pk=dept_id)
                except Department.DoesNotExist:
                    return JsonResponse({'error': 'Invalid department ID'}, status=400)
            else:
                profile.department = None

        if 'program_id' in data:
            prog_id = data['program_id']
            if prog_id:
                try:
                    profile.program = Program.objects.get(pk=prog_id)
                except Program.DoesNotExist:
                    return JsonResponse({'error': 'Invalid program ID'}, status=400)
            else:
                profile.program = None

        profile.save()

        log_activity(
            user=request.user,
            action='user_updated',
            description=f'Updated user profile: {user.get_full_name() or user.username}',
            request=request
        )

        return JsonResponse({
            'success': True,
            'message': 'User updated successfully',
            'user': {
                'id': user.id,
                'full_name': f'{user.first_name} {user.last_name}'.strip() or user.username,
                'email': user.email,
            }
        })

    except User.DoesNotExist:
        return HttpResponseNotFound('User not found')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@login_required
def delete_user_profile(request, user_id):
    if request.method != 'DELETE':
        return HttpResponseNotAllowed(['DELETE'])
    try:
        user = User.objects.get(pk=user_id)
        log_activity(
            user=request.user,
            action='user_deleted',
            description=f'Deleted user: {user.get_full_name() or user.username}',
            request=request
        )
        user.delete()
        return JsonResponse({'success': True, 'message': 'User deleted'})
    except User.DoesNotExist:
        return HttpResponseNotFound('User not found')

def log_activity(user, action, description, request=None):
    """Helper function to log activities to the database"""
    try:
        ip_address = None
        user_agent = None
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        ActivityLog.objects.create(
            user=user,
            action=action,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        print(f"Error logging activity: {str(e)}")


# ── NEW: Document requirement carry-over helper ───────────────────────────────

def _carry_over_document_requirements(from_sy, to_sy):
    """
    Auto-copy active document requirements from a previous school year to a
    new school year. Called when a new school year is activated.

    Args:
        from_sy: SchoolYear instance being deactivated (the previous SY).
        to_sy:   SchoolYear instance being activated (the new SY).
    """
    if from_sy is None or to_sy is None:
        return

    old_reqs = DocumentRequirement.objects.filter(school_year=from_sy, is_active=True)
    copied = 0
    for req in old_reqs:
        # Only create if a requirement with the same name doesn't already exist
        if not DocumentRequirement.objects.filter(school_year=to_sy, name=req.name).exists():
            DocumentRequirement.objects.create(
                school_year=to_sy,
                name=req.name,
                description=req.description,
                requirement_type=req.requirement_type,
                file_format=req.file_format,
                max_file_size_mb=req.max_file_size_mb,
                is_active=req.is_active,
                order=req.order,
            )
            copied += 1
    print(f'[SY ACTIVATION] Carried over {copied} document requirements to {to_sy.year_label}')


# ─────────────────────────────────────────────────────────────────────────────

@login_required
def settings(request):
    return render(request, 'admin_app/settings.html', {'active_page': 'settings'})

@login_required
@require_http_methods(["GET"])
def settings_header_data(request):
    """API endpoint for settings header data"""
    from admin_app.models import SchoolYear, UserProfile
    active_school_year = SchoolYear.get_active_school_year()
    try:
        user_profile = UserProfile.objects.select_related(
            'program', 'position', 'department'
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

    role = user_profile.get_user_type_display() if user_profile else "Admin"
    photo_url = user_profile.photo.url if user_profile and user_profile.photo else None

    return JsonResponse({
        'school_year': active_school_year.year_label if active_school_year else 'No Active Year',
        'full_name': full_name,
        'role': role,
        'initials': initials,
        'photo_url': photo_url,
    })

@login_required
def manage_users(request):
    return render(request, 'admin_app/settings.html', {'tab': 'users', 'active_page': 'settings'})

@login_required
def manage_content(request):
    return render(request, 'admin_app/settings.html', {'tab': 'content', 'active_page': 'settings'})


# ============== API ENDPOINTS ==============

@login_required
@require_http_methods(["GET"])
def get_users(request):
    """Get all users with their profiles"""
    try:
        users_data = []
        users = User.objects.select_related('profile').all().order_by('-date_joined')
        for user in users:
            try:
                profile = user.profile
                users_data.append({
                    'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                    'email': user.email,
                    'employee_id': profile.employee_id if hasattr(profile, 'employee_id') else 'N/A',
                    'position': profile.get_position_name(),
                    'department': profile.get_department_name(),
                    'user_type': profile.user_type,
                    'access_badges': profile.get_access_badges(),
                    'last_login': profile.get_last_login_formatted(),
                    'date_joined': profile.get_date_joined_formatted(),
                    'is_active': user.is_active,
                })
            except UserProfile.DoesNotExist:
                users_data.append({
                    'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                    'email': user.email,
                    'employee_id': 'N/A',
                    'position': 'N/A',
                    'department': 'N/A',
                    'user_type': 'N/A',
                    'access_badges': [],
                    'last_login': 'Never',
                    'date_joined': user.date_joined.strftime('%b %d, %Y'),
                    'is_active': user.is_active,
                })
        return JsonResponse({'users': users_data}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def add_user(request):
    """Add a new user with profile"""
    try:
        data = json.loads(request.body)
        required_fields = ['username', 'email', 'first_name', 'last_name', 'employee_id', 'password']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'error': f'{field.replace("_", " ").title()} is required'}, status=400)
        if User.objects.filter(username=data['username']).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
        if User.objects.filter(email=data['email']).exists():
            return JsonResponse({'error': 'Email already exists'}, status=400)
        if UserProfile.objects.filter(employee_id=data['employee_id']).exists():
            return JsonResponse({'error': 'Employee ID already exists'}, status=400)
        user_type = 'admin' if data.get('admin_access') else 'coordinator'
        if user_type == 'coordinator' and not data.get('program'):
            return JsonResponse({'error': 'Program is required for coordinators'}, status=400)
        with transaction.atomic():
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                password=data['password']
            )
            position = None
            if data.get('position'):
                try:
                    position = Position.objects.get(id=data['position'])
                except Position.DoesNotExist:
                    pass
            department = None
            if data.get('department'):
                try:
                    department = Department.objects.get(id=data['department'])
                except Department.DoesNotExist:
                    pass
            program = None
            if data.get('program'):
                try:
                    program = Program.objects.get(id=data['program'])
                except Program.DoesNotExist:
                    pass
            profile = UserProfile.objects.create(
                user=user,
                user_type=user_type,
                employee_id=data['employee_id'],
                position=position,
                department=department,
                program=program
            )
            if user_type == 'admin':
                user.is_staff = True
                user.save()
        return JsonResponse({
            'message': 'User added successfully',
            'user': {'id': user.id, 'username': user.username,
                     'full_name': f"{user.first_name} {user.last_name}", 'email': user.email}
        }, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_positions(request):
    try:
        positions_qs = Position.objects.filter(is_active=True).values('id', 'name', 'description')
        positions = list(positions_qs)
        return JsonResponse({'positions': positions, 'data': positions}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_departments(request):
    try:
        departments_qs = Department.objects.filter(is_active=True).values('id', 'name', 'description')
        departments = list(departments_qs)
        return JsonResponse({'departments': departments, 'data': departments}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def add_position(request):
    try:
        data = json.loads(request.body)
        name = (data.get('name') or '').strip()
        description = data.get('description') or ''
        if not name:
            return JsonResponse({'error': 'Position name is required'}, status=400)
        if Position.objects.filter(name__iexact=name).exists():
            return JsonResponse({'error': 'Position name already exists'}, status=400)
        position = Position.objects.create(name=name, description=description)
        log_activity(user=request.user, action='position_added',
                     description=f'Added position: {name}', request=request)
        return JsonResponse({'message': 'Position added successfully',
                             'position': {'id': position.id, 'name': position.name,
                                          'description': position.description}}, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["PUT"])
def update_position(request, position_id):
    try:
        position = Position.objects.get(pk=position_id)
        data = json.loads(request.body)
        name = (data.get('name') or '').strip()
        description = data.get('description') or ''
        if not name:
            return JsonResponse({'error': 'Position name is required'}, status=400)
        if Position.objects.filter(name__iexact=name).exclude(pk=position_id).exists():
            return JsonResponse({'error': 'Another position with this name already exists'}, status=400)
        old_name = position.name
        position.name = name
        position.description = description
        position.save()
        log_activity(user=request.user, action='position_updated',
                     description=f'Updated position: {old_name} -> {name}', request=request)
        return JsonResponse({'message': 'Position updated successfully',
                             'position': {'id': position.id, 'name': position.name,
                                          'description': position.description}}, status=200)
    except Position.DoesNotExist:
        return JsonResponse({'error': 'Position not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_position(request, position_id):
    try:
        position = Position.objects.get(pk=position_id)
        position_name = position.name
        if not position.can_delete():
            return JsonResponse({'error': 'Cannot delete position with assigned users'}, status=400)
        position.delete()
        log_activity(user=request.user, action='position_deleted',
                     description=f'Deleted position: {position_name}', request=request)
        return JsonResponse({'message': 'Position deleted successfully'}, status=200)
    except Position.DoesNotExist:
        return JsonResponse({'error': 'Position not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def add_department(request):
    try:
        data = json.loads(request.body)
        name = (data.get('name') or '').strip()
        description = data.get('description') or ''
        if not name:
            return JsonResponse({'error': 'Department name is required'}, status=400)
        if Department.objects.filter(name__iexact=name).exists():
            return JsonResponse({'error': 'Department name already exists'}, status=400)
        department = Department.objects.create(name=name, description=description)
        log_activity(user=request.user, action='department_added',
                     description=f'Added department: {name}', request=request)
        return JsonResponse({'message': 'Department added successfully',
                             'department': {'id': department.id, 'name': department.name,
                                            'description': department.description}}, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["PUT"])
def update_department(request, department_id):
    try:
        department = Department.objects.get(pk=department_id)
        data = json.loads(request.body)
        name = (data.get('name') or '').strip()
        description = data.get('description') or ''
        if not name:
            return JsonResponse({'error': 'Department name is required'}, status=400)
        if Department.objects.filter(name__iexact=name).exclude(pk=department_id).exists():
            return JsonResponse({'error': 'Another department with this name already exists'}, status=400)
        old_name = department.name
        department.name = name
        department.description = description
        department.save()
        log_activity(user=request.user, action='department_updated',
                     description=f'Updated department: {old_name} -> {name}', request=request)
        return JsonResponse({'message': 'Department updated successfully',
                             'department': {'id': department.id, 'name': department.name,
                                            'description': department.description}}, status=200)
    except Department.DoesNotExist:
        return JsonResponse({'error': 'Department not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_department(request, department_id):
    try:
        department = Department.objects.get(pk=department_id)
        department_name = department.name
        if not department.can_delete():
            return JsonResponse({'error': 'Cannot delete department with assigned users'}, status=400)
        department.delete()
        log_activity(user=request.user, action='department_deleted',
                     description=f'Deleted department: {department_name}', request=request)
        return JsonResponse({'message': 'Department deleted successfully'}, status=200)
    except Department.DoesNotExist:
        return JsonResponse({'error': 'Department not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_programs(request):
    try:
        programs = Program.objects.filter(is_active=True).values('id', 'code', 'name')
        programs_list = [{'id': p['id'], 'name': f"{p['code']} - {p['name']}"} for p in programs]
        return JsonResponse({'programs': programs_list}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============== CONTENT MANAGEMENT ENDPOINTS ==============

@login_required
@require_http_methods(["GET"])
def get_content_settings(request):
    try:
        settings = SystemSettings.objects.all()
        settings_dict = {}
        for setting in settings:
            settings_dict[setting.setting_type] = {
                'value': setting.setting_value,
                'image_url': setting.image.url if setting.image else None,
                'updated_at': setting.get_formatted_date(),
                'updated_by': setting.updated_by.get_full_name() if setting.updated_by else 'System'
            }
        return JsonResponse({'settings': settings_dict}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def save_content_setting(request):
    try:
        data = json.loads(request.body)
        setting_type = data.get('setting_type')
        setting_value = data.get('setting_value', '')
        if not setting_type:
            return JsonResponse({'error': 'Setting type is required'}, status=400)
        setting, created = SystemSettings.objects.get_or_create(
            setting_type=setting_type,
            defaults={'setting_value': setting_value, 'updated_by': request.user}
        )
        if not created:
            setting.setting_value = setting_value
            setting.updated_by = request.user
            setting.save()
        log_activity(user=request.user, action='content_updated',
                     description=f'Updated content setting: {setting_type}', request=request)
        return JsonResponse({'message': 'Setting saved successfully',
                             'setting': {'type': setting.setting_type, 'value': setting.setting_value,
                                         'updated_at': setting.get_formatted_date()}}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def upload_content_image(request):
    try:
        if 'image' not in request.FILES:
            return JsonResponse({'error': 'No image file provided'}, status=400)
        setting_type = request.POST.get('setting_type')
        if not setting_type:
            return JsonResponse({'error': 'Setting type is required'}, status=400)
        image_file = request.FILES['image']
        setting, created = SystemSettings.objects.get_or_create(
            setting_type=setting_type,
            defaults={'updated_by': request.user}
        )
        setting.image = image_file
        setting.updated_by = request.user
        setting.save()
        return JsonResponse({'message': 'Image uploaded successfully', 'image_url': setting.image.url,
                             'setting': {'type': setting.setting_type,
                                         'updated_at': setting.get_formatted_date()}}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_staff_members(request):
    try:
        staff = StaffMember.objects.filter(is_active=True).order_by('display_order', 'name')
        staff_list = [{'id': m.id, 'name': m.name, 'position': m.position,
                       'photo_url': m.photo.url if m.photo else None,
                       'display_order': m.display_order} for m in staff]
        return JsonResponse({'staff': staff_list}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def add_staff_member(request):
    try:
        name = request.POST.get('name', '').strip()
        position = request.POST.get('position', '').strip()
        display_order = int(request.POST.get('display_order', 0))
        if not name or not position:
            return JsonResponse({'error': 'Name and position are required'}, status=400)
        staff = StaffMember.objects.create(name=name, position=position, display_order=display_order)
        if 'photo' in request.FILES:
            staff.photo = request.FILES['photo']
            staff.save()
        return JsonResponse({'message': 'Staff member added successfully',
                             'staff': {'id': staff.id, 'name': staff.name, 'position': staff.position,
                                       'photo_url': staff.photo.url if staff.photo else None}}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["PUT"])
def update_staff_member(request, staff_id):
    try:
        staff = StaffMember.objects.get(pk=staff_id)
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        position = data.get('position', '').strip()
        if not name or not position:
            return JsonResponse({'error': 'Name and position are required'}, status=400)
        staff.name = name
        staff.position = position
        staff.display_order = int(data.get('display_order', staff.display_order))
        staff.save()
        return JsonResponse({'message': 'Staff member updated successfully',
                             'staff': {'id': staff.id, 'name': staff.name, 'position': staff.position}}, status=200)
    except StaffMember.DoesNotExist:
        return JsonResponse({'error': 'Staff member not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_staff_member(request, staff_id):
    try:
        staff = StaffMember.objects.get(pk=staff_id)
        staff.delete()
        return JsonResponse({'message': 'Staff member deleted successfully'}, status=200)
    except StaffMember.DoesNotExist:
        return JsonResponse({'error': 'Staff member not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_activity_logs(request):
    try:
        action_filter = request.GET.get('action', '')
        user_filter = request.GET.get('user', '')
        search = request.GET.get('search', '')
        limit = int(request.GET.get('limit', 100))
        logs = ActivityLog.objects.all().order_by('-created_at')
        if action_filter:
            logs = logs.filter(action=action_filter)
        if user_filter:
            logs = logs.filter(user__username=user_filter)
        if search:
            logs = logs.filter(description__icontains=search)
        logs = logs[:limit]
        logs_data = []
        for log in logs:
            logs_data.append({
                'id': log.id,
                'user': log.user.get_full_name() or log.user.username if log.user else 'System',
                'action': log.get_action_display(),
                'action_code': log.action,
                'description': log.description,
                'ip_address': log.ip_address or 'N/A',
                'date': log.created_at.strftime('%Y-%m-%d'),
                'time': log.created_at.strftime('%H:%M:%S'),
                'timestamp': log.created_at.isoformat(),
            })
        return JsonResponse({'logs': logs_data, 'count': len(logs_data)}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============== BUILDINGS MANAGEMENT ==============

@login_required
@require_http_methods(["GET"])
def get_buildings_with_rooms(request):
    try:
        buildings = Building.objects.prefetch_related('rooms').all().order_by('name')
        buildings_list = [{'id': b.id, 'name': b.name, 'room_count': b.rooms.count()} for b in buildings]
        return JsonResponse({'buildings': buildings_list}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def add_building(request):
    try:
        data = json.loads(request.body)
        name = (data.get('name') or '').strip()
        if not name:
            return JsonResponse({'error': 'Building name is required'}, status=400)
        if Building.objects.filter(name__iexact=name).exists():
            return JsonResponse({'error': 'Building name already exists'}, status=400)
        building = Building.objects.create(name=name)
        log_activity(user=request.user, action='settings_changed',
                     description=f'Added building: {name}', request=request)
        return JsonResponse({'message': 'Building added successfully',
                             'building': {'id': building.id, 'name': building.name, 'room_count': 0}}, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["PUT"])
def update_building(request, building_id):
    try:
        building = Building.objects.get(pk=building_id)
        data = json.loads(request.body)
        name = (data.get('name') or '').strip()
        if not name:
            return JsonResponse({'error': 'Building name is required'}, status=400)
        if Building.objects.filter(name__iexact=name).exclude(pk=building_id).exists():
            return JsonResponse({'error': 'Another building with this name already exists'}, status=400)
        old_name = building.name
        building.name = name
        building.save()
        log_activity(user=request.user, action='settings_changed',
                     description=f'Updated building: {old_name} -> {name}', request=request)
        return JsonResponse({'message': 'Building updated successfully',
                             'building': {'id': building.id, 'name': building.name,
                                          'room_count': building.rooms.count()}}, status=200)
    except Building.DoesNotExist:
        return JsonResponse({'error': 'Building not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
@transaction.atomic
def delete_building(request, building_id):
    try:
        building = Building.objects.get(pk=building_id)
        building_name = building.name
        room_count = building.rooms.count()
        rooms_in_use = []
        for room in building.rooms.all():
            if Section.objects.filter(building=building_name, room=room.room_number).exists():
                rooms_in_use.append(room.room_number)
        if rooms_in_use:
            return JsonResponse({
                'error': f'Cannot delete building. The following rooms are assigned to sections: {", ".join(rooms_in_use)}'
            }, status=400)
        building.delete()
        log_activity(user=request.user, action='settings_changed',
                     description=f'Deleted building: {building_name} (with {room_count} rooms)', request=request)
        return JsonResponse({'message': 'Building and all its rooms deleted successfully'}, status=200)
    except Building.DoesNotExist:
        return JsonResponse({'error': 'Building not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============== ROOMS MANAGEMENT ==============

@login_required
@require_http_methods(["GET"])
def get_rooms_by_building(request):
    try:
        building_id = request.GET.get('building_id')
        if not building_id:
            return JsonResponse({'error': 'Building ID is required'}, status=400)
        building = Building.objects.get(pk=building_id)
        rooms = building.rooms.all().order_by('room_number')
        rooms_list = [{'id': r.id, 'room_number': r.room_number,
                       'building_id': building.id, 'building_name': building.name} for r in rooms]
        return JsonResponse({'rooms': rooms_list}, status=200)
    except Building.DoesNotExist:
        return JsonResponse({'error': 'Building not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def add_room(request):
    try:
        data = json.loads(request.body)
        building_id = data.get('building_id')
        room_number = (data.get('room_number') or '').strip()
        if not building_id:
            return JsonResponse({'error': 'Building ID is required'}, status=400)
        if not room_number:
            return JsonResponse({'error': 'Room number is required'}, status=400)
        building = Building.objects.get(pk=building_id)
        if Room.objects.filter(building=building, room_number__iexact=room_number).exists():
            return JsonResponse({'error': 'Room number already exists in this building'}, status=400)
        room = Room.objects.create(building=building, room_number=room_number)
        log_activity(user=request.user, action='settings_changed',
                     description=f'Added room {room_number} to {building.name}', request=request)
        return JsonResponse({'message': 'Room added successfully',
                             'room': {'id': room.id, 'room_number': room.room_number,
                                      'building_id': building.id, 'building_name': building.name}}, status=201)
    except Building.DoesNotExist:
        return JsonResponse({'error': 'Building not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["PUT"])
def update_room(request, room_id):
    try:
        room = Room.objects.select_related('building').get(pk=room_id)
        data = json.loads(request.body)
        room_number = (data.get('room_number') or '').strip()
        if not room_number:
            return JsonResponse({'error': 'Room number is required'}, status=400)
        if Room.objects.filter(building=room.building, room_number__iexact=room_number).exclude(pk=room_id).exists():
            return JsonResponse({'error': 'Room number already exists in this building'}, status=400)
        old_room_number = room.room_number
        room.room_number = room_number
        room.save()
        Section.objects.filter(building=room.building.name, room=old_room_number).update(room=room_number)
        log_activity(user=request.user, action='settings_changed',
                     description=f'Updated room in {room.building.name}: {old_room_number} -> {room_number}',
                     request=request)
        return JsonResponse({'message': 'Room updated successfully',
                             'room': {'id': room.id, 'room_number': room.room_number,
                                      'building_id': room.building.id, 'building_name': room.building.name}}, status=200)
    except Room.DoesNotExist:
        return JsonResponse({'error': 'Room not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_room(request, room_id):
    try:
        room = Room.objects.select_related('building').get(pk=room_id)
        room_number = room.room_number
        building_name = room.building.name
        sections_using_room = Section.objects.filter(building=building_name, room=room_number)
        if sections_using_room.exists():
            section_names = ', '.join([s.name for s in sections_using_room[:3]])
            if sections_using_room.count() > 3:
                section_names += f' and {sections_using_room.count() - 3} more'
            return JsonResponse({
                'error': f'Cannot delete room. It is assigned to the following sections: {section_names}'
            }, status=400)
        room.delete()
        log_activity(user=request.user, action='settings_changed',
                     description=f'Deleted room {room_number} from {building_name}', request=request)
        return JsonResponse({'message': 'Room deleted successfully'}, status=200)
    except Room.DoesNotExist:
        return JsonResponse({'error': 'Room not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============== SCHOOL YEAR MANAGEMENT ==============

def _parse_date(date_str, field_name):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        raise ValidationError({field_name: 'Invalid date format. Use YYYY-MM-DD.'})


def _school_year_to_dict(school_year):
    return {
        'id': school_year.id,
        'year_label': school_year.year_label,
        'start_date': school_year.start_date.isoformat(),
        'end_date': school_year.end_date.isoformat(),
        'is_active': school_year.is_active,
        'enrollment_open': school_year.enrollment_open,
        'created_at': school_year.created_at.isoformat(),
        'updated_at': school_year.updated_at.isoformat(),
        'sections_count': school_year.sections.count(),
        'students_count': school_year.get_total_students(),
    }


@login_required
@require_http_methods(["GET"])
def get_school_years(request):
    try:
        school_years = SchoolYear.objects.all().order_by('-year_label')
        data = [_school_year_to_dict(sy) for sy in school_years]
        active_year = next((sy for sy in data if sy['is_active']), None)
        return JsonResponse({'school_years': data, 'active_year': active_year}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def add_school_year(request):
    try:
        payload = json.loads(request.body)
        year_label = (payload.get('year_label') or '').strip()
        start_date_raw = payload.get('start_date')
        end_date_raw = payload.get('end_date')
        is_active = bool(payload.get('is_active'))
        enrollment_open = bool(payload.get('enrollment_open'))

        if not year_label or not start_date_raw or not end_date_raw:
            return JsonResponse({'error': 'Year label, start date, and end date are required'}, status=400)

        start_date = _parse_date(start_date_raw, 'start_date')
        end_date = _parse_date(end_date_raw, 'end_date')

        school_year = SchoolYear(
            year_label=year_label,
            start_date=start_date,
            end_date=end_date,
            is_active=is_active,
            enrollment_open=enrollment_open
        )
        school_year.save()

        log_activity(user=request.user, action='settings_changed',
                     description=f'Added school year: {year_label}', request=request)

        return JsonResponse({'message': 'School year added successfully',
                             'school_year': _school_year_to_dict(school_year)}, status=201)
    except ValidationError as ve:
        error_messages = (
            '; '.join([f"{field}: {', '.join(msgs)}" for field, msgs in ve.message_dict.items()])
            if hasattr(ve, 'message_dict') else str(ve)
        )
        return JsonResponse({'error': error_messages}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["PUT"])
def update_school_year(request, school_year_id):
    """
    Update an existing school year.
    When is_active is flipped to True, the previously active SY is deactivated
    and its document requirements are automatically carried over to the new SY.
    """
    try:
        school_year = SchoolYear.objects.get(pk=school_year_id)
        payload = json.loads(request.body)

        year_label = (payload.get('year_label') or '').strip()
        start_date_raw = payload.get('start_date')
        end_date_raw = payload.get('end_date')
        new_is_active = bool(payload.get('is_active'))
        enrollment_open = bool(payload.get('enrollment_open'))

        if not year_label or not start_date_raw or not end_date_raw:
            return JsonResponse({'error': 'Year label, start date, and end date are required'}, status=400)

        # ── Detect activation transition ─────────────────────────────────────
        was_inactive = not school_year.is_active
        being_activated = new_is_active and was_inactive

        # Capture the previously active SY BEFORE saving (SchoolYear.save()
        # may deactivate it automatically depending on your model logic).
        previous_active_sy = None
        if being_activated:
            previous_active_sy = SchoolYear.objects.filter(
                is_active=True
            ).exclude(pk=school_year_id).first()

        # ── Persist changes ──────────────────────────────────────────────────
        school_year.year_label = year_label
        school_year.start_date = _parse_date(start_date_raw, 'start_date')
        school_year.end_date = _parse_date(end_date_raw, 'end_date')
        school_year.is_active = new_is_active
        school_year.enrollment_open = enrollment_open
        school_year.save()

        # ── Carry over document requirements when activating ─────────────────
        if being_activated and previous_active_sy:
            _carry_over_document_requirements(
                from_sy=previous_active_sy,
                to_sy=school_year,
            )

        log_activity(user=request.user, action='settings_changed',
                     description=f'Updated school year: {year_label}', request=request)

        return JsonResponse({'message': 'School year updated successfully',
                             'school_year': _school_year_to_dict(school_year)}, status=200)

    except SchoolYear.DoesNotExist:
        return JsonResponse({'error': 'School year not found'}, status=404)
    except ValidationError as ve:
        error_messages = (
            '; '.join([f"{field}: {', '.join(msgs)}" for field, msgs in ve.message_dict.items()])
            if hasattr(ve, 'message_dict') else str(ve)
        )
        return JsonResponse({'error': error_messages}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_school_year(request, school_year_id):
    try:
        school_year = SchoolYear.objects.get(pk=school_year_id)
        if school_year.is_active:
            return JsonResponse({'error': 'Cannot delete the active school year'}, status=400)
        if school_year.sections.exists() or school_year.get_total_students() > 0:
            sections_count = school_year.sections.count()
            students_count = school_year.get_total_students()
            return JsonResponse({
                'error': (
                    'Cannot delete school year with existing data '
                    f'(sections: {sections_count}, students: {students_count}).'
                )
            }, status=400)
        year_label = school_year.year_label
        school_year.delete()
        log_activity(user=request.user, action='settings_changed',
                     description=f'Deleted school year: {year_label}', request=request)
        return JsonResponse({'message': 'School year deleted successfully'}, status=200)
    except SchoolYear.DoesNotExist:
        return JsonResponse({'error': 'School year not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============== DOCUMENT REQUIREMENTS MANAGEMENT ==============

def _document_requirement_to_dict(req: DocumentRequirement):
    return {
        'id': req.id,
        'school_year_id': req.school_year_id,
        'school_year': req.school_year.year_label if req.school_year else None,
        'name': req.name,
        'description': req.description,
        'requirement_type': req.requirement_type,
        'file_format': req.file_format,
        'allowed_extensions': req.get_allowed_extensions(),
        'max_file_size_mb': float(req.max_file_size_mb),
        'is_active': req.is_active,
        'order': req.order,
        'created_at': req.created_at.isoformat(),
        'updated_at': req.updated_at.isoformat(),
    }


@login_required
@require_http_methods(["GET"])
def get_document_requirements(request):
    try:
        school_year_id = request.GET.get('school_year_id')
        search = (request.GET.get('search') or '').strip()
        qs = DocumentRequirement.objects.select_related('school_year').all().order_by(
            'school_year__year_label', 'order', 'name')
        if school_year_id:
            qs = qs.filter(school_year_id=school_year_id)
        if search:
            qs = qs.filter(name__icontains=search)
        data = [_document_requirement_to_dict(r) for r in qs]
        return JsonResponse({'requirements': data, 'count': len(data)}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def add_document_requirement(request):
    try:
        payload = json.loads(request.body)
        school_year_id = payload.get('school_year_id')
        name = (payload.get('name') or '').strip()
        description = payload.get('description') or ''
        requirement_type = (payload.get('requirement_type') or 'mandatory').strip()
        file_format = (payload.get('file_format') or 'pdf,jpg,jpeg,png').strip()
        max_file_size_mb = payload.get('max_file_size_mb', 5.0)
        is_active = bool(payload.get('is_active', True))
        order = int(payload.get('order', 0))

        if not school_year_id:
            return JsonResponse({'error': 'school_year_id is required'}, status=400)
        if not name:
            return JsonResponse({'error': 'name is required'}, status=400)

        try:
            school_year = SchoolYear.objects.get(pk=school_year_id)
        except SchoolYear.DoesNotExist:
            return JsonResponse({'error': 'School year not found'}, status=404)

        if DocumentRequirement.objects.filter(school_year=school_year, name__iexact=name).exists():
            return JsonResponse(
                {'error': 'A requirement with this name already exists for the selected school year'}, status=400)

        req = DocumentRequirement(
            school_year=school_year, name=name, description=description,
            requirement_type=requirement_type, file_format=file_format,
            max_file_size_mb=max_file_size_mb, is_active=is_active, order=order,
            created_by=request.user,
        )
        req.save()

        log_activity(user=request.user, action='settings_changed',
                     description=f'Added document requirement "{name}" for {school_year.year_label}',
                     request=request)

        return JsonResponse({'message': 'Requirement added successfully',
                             'requirement': _document_requirement_to_dict(req)}, status=201)
    except ValidationError as ve:
        error_messages = (
            '; '.join([f"{field}: {', '.join(msgs)}" for field, msgs in ve.message_dict.items()])
            if hasattr(ve, 'message_dict') else str(ve)
        )
        return JsonResponse({'error': error_messages}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["PUT"])
def update_document_requirement(request, requirement_id: int):
    try:
        try:
            req = DocumentRequirement.objects.select_related('school_year').get(pk=requirement_id)
        except DocumentRequirement.DoesNotExist:
            return JsonResponse({'error': 'Requirement not found'}, status=404)

        payload = json.loads(request.body)
        name = (payload.get('name') or req.name).strip()
        description = payload.get('description', req.description)
        requirement_type = (payload.get('requirement_type') or req.requirement_type).strip()
        file_format = (payload.get('file_format') or req.file_format).strip()
        max_file_size_mb = payload.get('max_file_size_mb', float(req.max_file_size_mb))
        is_active = bool(payload.get('is_active', req.is_active))
        order = int(payload.get('order', req.order))

        if not name:
            return JsonResponse({'error': 'name is required'}, status=400)

        if DocumentRequirement.objects.filter(
            school_year=req.school_year, name__iexact=name
        ).exclude(pk=req.id).exists():
            return JsonResponse(
                {'error': 'Another requirement with this name already exists for this school year'}, status=400)

        old_name = req.name
        req.name = name
        req.description = description
        req.requirement_type = requirement_type
        req.file_format = file_format
        req.max_file_size_mb = max_file_size_mb
        req.is_active = is_active
        req.order = order
        req.save()

        log_activity(user=request.user, action='settings_changed',
                     description=f'Updated document requirement: {old_name} -> {req.name} ({req.school_year.year_label})',
                     request=request)

        return JsonResponse({'message': 'Requirement updated successfully',
                             'requirement': _document_requirement_to_dict(req)}, status=200)
    except ValidationError as ve:
        error_messages = (
            '; '.join([f"{field}: {', '.join(msgs)}" for field, msgs in ve.message_dict.items()])
            if hasattr(ve, 'message_dict') else str(ve)
        )
        return JsonResponse({'error': error_messages}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_document_requirement(request, requirement_id: int):
    try:
        try:
            req = DocumentRequirement.objects.select_related('school_year').get(pk=requirement_id)
        except DocumentRequirement.DoesNotExist:
            return JsonResponse({'error': 'Requirement not found'}, status=404)

        name = req.name
        year_label = req.school_year.year_label if req.school_year else 'Unknown'
        req.delete()

        log_activity(user=request.user, action='settings_changed',
                     description=f'Deleted document requirement "{name}" ({year_label})', request=request)

        return JsonResponse({'message': 'Requirement deleted successfully'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============== GRADE LEVEL MANAGEMENT ==============

@login_required
@require_http_methods(["GET"])
def get_grade_levels(request):
    try:
        from admin_app.models import GradeLevel
        qs = GradeLevel.objects.all().order_by('code')
        data = [{'id': gl.id, 'code': gl.code, 'name': gl.name,
                 'description': gl.description or '', 'is_active': gl.is_active} for gl in qs]
        return JsonResponse({'grade_levels': data, 'count': len(data)}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def add_grade_level(request):
    try:
        from admin_app.models import GradeLevel
        payload = json.loads(request.body)
        code = (payload.get('code') or '').strip().upper()
        name = (payload.get('name') or '').strip()
        description = payload.get('description') or ''
        is_active = bool(payload.get('is_active', True))
        if not code:
            return JsonResponse({'error': 'Code is required'}, status=400)
        if not name:
            return JsonResponse({'error': 'Name is required'}, status=400)
        if GradeLevel.objects.filter(code__iexact=code).exists():
            return JsonResponse({'error': f'A grade level with code "{code}" already exists'}, status=400)
        if GradeLevel.objects.filter(name__iexact=name).exists():
            return JsonResponse({'error': f'A grade level named "{name}" already exists'}, status=400)
        gl = GradeLevel.objects.create(code=code, name=name, description=description, is_active=is_active)
        log_activity(user=request.user, action='settings_changed',
                     description=f'Added grade level "{name}" ({code})', request=request)
        return JsonResponse({'message': 'Grade level added successfully',
                             'grade_level': {'id': gl.id, 'code': gl.code, 'name': gl.name,
                                             'description': gl.description or '', 'is_active': gl.is_active}}, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["PUT"])
def update_grade_level(request, grade_level_id):
    try:
        from admin_app.models import GradeLevel
        try:
            gl = GradeLevel.objects.get(pk=grade_level_id)
        except GradeLevel.DoesNotExist:
            return JsonResponse({'error': 'Grade level not found'}, status=404)
        payload = json.loads(request.body)
        code = (payload.get('code') or gl.code).strip().upper()
        name = (payload.get('name') or gl.name).strip()
        description = payload.get('description', gl.description) or ''
        is_active = bool(payload.get('is_active', gl.is_active))
        if not code:
            return JsonResponse({'error': 'Code is required'}, status=400)
        if not name:
            return JsonResponse({'error': 'Name is required'}, status=400)
        if GradeLevel.objects.filter(code__iexact=code).exclude(pk=grade_level_id).exists():
            return JsonResponse({'error': f'Another grade level with code "{code}" already exists'}, status=400)
        if GradeLevel.objects.filter(name__iexact=name).exclude(pk=grade_level_id).exists():
            return JsonResponse({'error': f'Another grade level named "{name}" already exists'}, status=400)
        old = f'{gl.name} ({gl.code})'
        gl.code, gl.name, gl.description, gl.is_active = code, name, description, is_active
        gl.save()
        log_activity(user=request.user, action='settings_changed',
                     description=f'Updated grade level: {old} → {gl.name} ({gl.code})', request=request)
        return JsonResponse({'message': 'Grade level updated successfully',
                             'grade_level': {'id': gl.id, 'code': gl.code, 'name': gl.name,
                                             'description': gl.description or '', 'is_active': gl.is_active}}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_grade_level(request, grade_level_id):
    try:
        from admin_app.models import GradeLevel
        try:
            gl = GradeLevel.objects.get(pk=grade_level_id)
        except GradeLevel.DoesNotExist:
            return JsonResponse({'error': 'Grade level not found'}, status=404)
        from enrollment_app.models import Student
        student_count = Student.objects.filter(grade_level=gl).count()
        section_count = gl.sections.count() if hasattr(gl, 'sections') else 0
        if student_count or section_count:
            return JsonResponse({
                'error': f'Cannot delete: {student_count} student(s) and {section_count} section(s) still reference this grade level.'
            }, status=400)
        label = f'{gl.name} ({gl.code})'
        gl.delete()
        log_activity(user=request.user, action='settings_changed',
                     description=f'Deleted grade level "{label}"', request=request)
        return JsonResponse({'message': 'Grade level deleted successfully'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============== TEACHER MANAGEMENT ==============

@login_required
@require_http_methods(["GET"])
def get_teachers_for_settings(request):
    try:
        teachers = Teacher.objects.select_related(
            'position', 'department').all().order_by('last_name', 'first_name')
        data = []
        for t in teachers:
            data.append({
                'id': t.id,
                'first_name': t.first_name,
                'middle_name': t.middle_name or '',
                'last_name': t.last_name,
                'full_name': t.get_full_name(),  # Use the model method
                'email': t.email,
                'position_id': t.position_id,
                'position_name': t.position.name if t.position else '',
                'department_id': t.department_id,
                'department_name': t.department.name if t.department else '',
                'address': t.address or '',
                'is_adviser': t.is_adviser,
                'created_at': t.created_at.strftime('%b %d, %Y') if t.created_at else '',
            })
        return JsonResponse({'teachers': data, 'data': data}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def add_teacher(request):
    try:
        data = json.loads(request.body)
        first_name = (data.get('first_name') or '').strip()
        middle_name = (data.get('middle_name') or '').strip() or None
        last_name = (data.get('last_name') or '').strip()
        email = (data.get('email') or '').strip().lower()
        address = (data.get('address') or '').strip() or None
        position_id = data.get('position_id')
        department_id = data.get('department_id')
        if not first_name:
            return JsonResponse({'error': 'First name is required'}, status=400)
        if not last_name:
            return JsonResponse({'error': 'Last name is required'}, status=400)
        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)
        if Teacher.objects.filter(email__iexact=email).exists():
            return JsonResponse({'error': 'A teacher with this email already exists'}, status=400)
        position = None
        department = None
        if position_id:
            try:
                position = Position.objects.get(pk=position_id)
            except Position.DoesNotExist:
                return JsonResponse({'error': 'Invalid position'}, status=400)
        if department_id:
            try:
                department = Department.objects.get(pk=department_id)
            except Department.DoesNotExist:
                return JsonResponse({'error': 'Invalid department'}, status=400)
        teacher = Teacher.objects.create(
            first_name=first_name, middle_name=middle_name, last_name=last_name,
            email=email, address=address, position=position, department=department
        )
        log_activity(user=request.user, action='teacher_added',
                     description=f'Added teacher: {teacher.get_full_name()}', request=request)
        return JsonResponse({'message': 'Teacher added successfully',
                             'teacher': {'id': teacher.id, 'full_name': teacher.get_full_name(),
                                         'email': teacher.email}}, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except ValidationError as ve:
        error_messages = (
            '; '.join([f"{field}: {', '.join(msgs)}" for field, msgs in ve.message_dict.items()])
            if hasattr(ve, 'message_dict') else str(ve)
        )
        return JsonResponse({'error': error_messages}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["PUT"])
def update_teacher(request, teacher_id):
    try:
        teacher = Teacher.objects.get(pk=teacher_id)
        data = json.loads(request.body)
        first_name = (data.get('first_name') or '').strip()
        middle_name = (data.get('middle_name') or '').strip() or None
        last_name = (data.get('last_name') or '').strip()
        email = (data.get('email') or '').strip().lower()
        address = (data.get('address') or '').strip() or None
        position_id = data.get('position_id')
        department_id = data.get('department_id')
        if not first_name:
            return JsonResponse({'error': 'First name is required'}, status=400)
        if not last_name:
            return JsonResponse({'error': 'Last name is required'}, status=400)
        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)
        if Teacher.objects.filter(email__iexact=email).exclude(pk=teacher_id).exists():
            return JsonResponse({'error': 'Another teacher with this email already exists'}, status=400)
        position = None
        department = None
        if position_id:
            try:
                position = Position.objects.get(pk=position_id)
            except Position.DoesNotExist:
                return JsonResponse({'error': 'Invalid position'}, status=400)
        if department_id:
            try:
                department = Department.objects.get(pk=department_id)
            except Department.DoesNotExist:
                return JsonResponse({'error': 'Invalid department'}, status=400)
        old_name = teacher.get_full_name()
        teacher.first_name = first_name
        teacher.middle_name = middle_name
        teacher.last_name = last_name
        teacher.email = email
        teacher.address = address
        teacher.position = position
        teacher.department = department
        teacher.save()
        log_activity(user=request.user, action='teacher_updated',
                     description=f'Updated teacher: {old_name} -> {teacher.get_full_name()}', request=request)
        return JsonResponse({'message': 'Teacher updated successfully',
                             'teacher': {'id': teacher.id, 'full_name': teacher.get_full_name(),
                                         'email': teacher.email}}, status=200)
    except Teacher.DoesNotExist:
        return JsonResponse({'error': 'Teacher not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except ValidationError as ve:
        error_messages = (
            '; '.join([f"{field}: {', '.join(msgs)}" for field, msgs in ve.message_dict.items()])
            if hasattr(ve, 'message_dict') else str(ve)
        )
        return JsonResponse({'error': error_messages}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_teacher(request, teacher_id):
    try:
        teacher = Teacher.objects.get(pk=teacher_id)
        teacher_name = teacher.get_full_name()
        if teacher.is_adviser:
            return JsonResponse({'error': 'Cannot delete teacher who is assigned as a section adviser'}, status=400)
        if Section.objects.filter(adviser=teacher).exists():
            return JsonResponse({'error': 'Cannot delete teacher who is assigned as a section adviser'}, status=400)
        teacher.delete()
        log_activity(user=request.user, action='teacher_deleted',
                     description=f'Deleted teacher: {teacher_name}', request=request)
        return JsonResponse({'message': 'Teacher deleted successfully'}, status=200)
    except Teacher.DoesNotExist:
        return JsonResponse({'error': 'Teacher not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def delete_content_image(request):
    try:
        setting_type = request.POST.get('setting_type')
        if not setting_type:
            return JsonResponse({'error': 'Setting type is required'}, status=400)
        try:
            setting = SystemSettings.objects.get(setting_type=setting_type)
            if setting.image:
                storage = setting.image.storage
                path = setting.image.name
                setting.image = None
                setting.updated_by = request.user
                setting.save()
                if storage.exists(path):
                    storage.delete(path)
            return JsonResponse({'message': 'Image removed successfully'}, status=200)
        except SystemSettings.DoesNotExist:
            return JsonResponse({'message': 'Nothing to delete'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def generate_promotion_statuses(request):
    """
    Admin endpoint to manually trigger StudentAcademicYearStatus generation
    for a specific school year.
    POST body: { school_year_id: <id>, overwrite: true/false }
    """
    try:
        data = json.loads(request.body)
        school_year_id = data.get('school_year_id')
        overwrite = data.get('overwrite', False)

        if school_year_id:
            school_year = get_object_or_404(SchoolYear, pk=school_year_id)
        else:
            school_year = SchoolYear.objects.filter(
                is_active=False
            ).order_by('-year_label').first()
            if not school_year:
                return JsonResponse({'success': False, 'error': 'No inactive school year found'}, status=400)

        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        call_command(
            'generate_academic_statuses',
            school_year=school_year.year_label,
            **(({'overwrite': True}) if overwrite else {}),
            stdout=out,
        )

        return JsonResponse({
            'success': True,
            'school_year': school_year.year_label,
            'message': f'Promotion statuses generated for {school_year.year_label}.',
            'details': out.getvalue(),
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)