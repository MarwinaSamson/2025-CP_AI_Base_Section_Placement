from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.db import transaction
from django.core.exceptions import ValidationError
from admin_app.models import UserProfile, Position, Department, Program, SystemSettings, StaffMember, ActivityLog, Building, Room, Section, SchoolYear
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from datetime import datetime
import json
import base64

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
def settings(request):
    return render(request, 'admin_app/settings.html')

@login_required
def manage_users(request):
    return render(request, 'admin_app/settings.html', {'tab': 'users'})

@login_required
def manage_content(request):
    return render(request, 'admin_app/settings.html', {'tab': 'content'})


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
                # User without profile, skip or show basic info
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
        
        # Validate required fields
        required_fields = ['username', 'email', 'first_name', 'last_name', 'employee_id', 'password']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'error': f'{field.replace("_", " ").title()} is required'}, status=400)
        
        # Check if username already exists
        if User.objects.filter(username=data['username']).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
        
        # Check if email already exists
        if User.objects.filter(email=data['email']).exists():
            return JsonResponse({'error': 'Email already exists'}, status=400)
        
        # Check if employee_id already exists
        if UserProfile.objects.filter(employee_id=data['employee_id']).exists():
            return JsonResponse({'error': 'Employee ID already exists'}, status=400)
        
        # Determine user type
        user_type = 'admin' if data.get('admin_access') else 'coordinator'
        
        # Validate program for coordinators
        if user_type == 'coordinator' and not data.get('program'):
            return JsonResponse({'error': 'Program is required for coordinators'}, status=400)
        
        # Create user and profile in a transaction
        with transaction.atomic():
            # Create user
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                password=data['password']
            )
            
            # Get position and department if provided
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
            
            # Get program if provided
            program = None
            if data.get('program'):
                try:
                    program = Program.objects.get(id=data['program'])
                except Program.DoesNotExist:
                    pass
            
            # Create user profile
            profile = UserProfile.objects.create(
                user=user,
                user_type=user_type,
                employee_id=data['employee_id'],
                position=position,
                department=department,
                program=program
            )
            
            # Set staff status if admin
            if user_type == 'admin':
                user.is_staff = True
                user.save()
        
        return JsonResponse({
            'message': 'User added successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': f"{user.first_name} {user.last_name}",
                'email': user.email,
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_positions(request):
    """Get all active positions for dropdown"""
    try:
        positions_qs = Position.objects.filter(is_active=True).values('id', 'name', 'description')
        positions = list(positions_qs)
        # Return both keys because dropdowns use `positions` while tables use `data`
        return JsonResponse({'positions': positions, 'data': positions}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_departments(request):
    """Get all active departments for dropdown"""
    try:
        departments_qs = Department.objects.filter(is_active=True).values('id', 'name', 'description')
        departments = list(departments_qs)
        return JsonResponse({'departments': departments, 'data': departments}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def add_position(request):
    """Create a new position"""
    try:
        data = json.loads(request.body)
        name = (data.get('name') or '').strip()
        description = data.get('description') or ''

        if not name:
            return JsonResponse({'error': 'Position name is required'}, status=400)

        if Position.objects.filter(name__iexact=name).exists():
            return JsonResponse({'error': 'Position name already exists'}, status=400)

        position = Position.objects.create(name=name, description=description)
        
        # Log activity
        log_activity(
            user=request.user,
            action='position_added',
            description=f'Added position: {name}',
            request=request
        )
        
        return JsonResponse({
            'message': 'Position added successfully',
            'position': {'id': position.id, 'name': position.name, 'description': position.description}
        }, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["PUT"])
def update_position(request, position_id):
    """Update an existing position"""
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
        
        # Log activity
        log_activity(
            user=request.user,
            action='position_updated',
            description=f'Updated position: {old_name} -> {name}',
            request=request
        )

        return JsonResponse({
            'message': 'Position updated successfully',
            'position': {'id': position.id, 'name': position.name, 'description': position.description}
        }, status=200)
    except Position.DoesNotExist:
        return JsonResponse({'error': 'Position not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_position(request, position_id):
    """Delete a position if no users are linked"""
    try:
        position = Position.objects.get(pk=position_id)
        position_name = position.name

        if not position.can_delete():
            return JsonResponse({'error': 'Cannot delete position with assigned users'}, status=400)

        position.delete()
        
        # Log activity
        log_activity(
            user=request.user,
            action='position_deleted',
            description=f'Deleted position: {position_name}',
            request=request
        )
        
        return JsonResponse({'message': 'Position deleted successfully'}, status=200)
    except Position.DoesNotExist:
        return JsonResponse({'error': 'Position not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def add_department(request):
    """Create a new department"""
    try:
        data = json.loads(request.body)
        name = (data.get('name') or '').strip()
        description = data.get('description') or ''

        if not name:
            return JsonResponse({'error': 'Department name is required'}, status=400)

        if Department.objects.filter(name__iexact=name).exists():
            return JsonResponse({'error': 'Department name already exists'}, status=400)

        department = Department.objects.create(name=name, description=description)
        
        # Log activity
        log_activity(
            user=request.user,
            action='department_added',
            description=f'Added department: {name}',
            request=request
        )
        
        return JsonResponse({
            'message': 'Department added successfully',
            'department': {'id': department.id, 'name': department.name, 'description': department.description}
        }, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["PUT"])
def update_department(request, department_id):
    """Update an existing department"""
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
        
        # Log activity
        log_activity(
            user=request.user,
            action='department_updated',
            description=f'Updated department: {old_name} -> {name}',
            request=request
        )

        return JsonResponse({
            'message': 'Department updated successfully',
            'department': {'id': department.id, 'name': department.name, 'description': department.description}
        }, status=200)
    except Department.DoesNotExist:
        return JsonResponse({'error': 'Department not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_department(request, department_id):
    """Delete a department if no users are linked"""
    try:
        department = Department.objects.get(pk=department_id)
        department_name = department.name

        if not department.can_delete():
            return JsonResponse({'error': 'Cannot delete department with assigned users'}, status=400)

        department.delete()
        
        # Log activity
        log_activity(
            user=request.user,
            action='department_deleted',
            description=f'Deleted department: {department_name}',
            request=request
        )
        
        return JsonResponse({'message': 'Department deleted successfully'}, status=200)
    except Department.DoesNotExist:
        return JsonResponse({'error': 'Department not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_programs(request):
    """Get all active programs for dropdown"""
    try:
        programs = Program.objects.filter(is_active=True).values('id', 'code', 'name')
        # Format the name to show "CODE - Name"
        programs_list = [{'id': p['id'], 'name': f"{p['code']} - {p['name']}"} for p in programs]
        return JsonResponse({'programs': programs_list}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============== CONTENT MANAGEMENT ENDPOINTS ==============

@login_required
@require_http_methods(["GET"])
def get_content_settings(request):
    """Get all content settings for the landing page"""
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
    """Save or update a content setting"""
    try:
        data = json.loads(request.body)
        setting_type = data.get('setting_type')
        setting_value = data.get('setting_value', '')
        
        if not setting_type:
            return JsonResponse({'error': 'Setting type is required'}, status=400)
        
        # Get or create the setting
        setting, created = SystemSettings.objects.get_or_create(
            setting_type=setting_type,
            defaults={'setting_value': setting_value, 'updated_by': request.user}
        )
        
        if not created:
            setting.setting_value = setting_value
            setting.updated_by = request.user
            setting.save()
        
        # Log activity
        action_type = 'content_updated'
        log_activity(
            user=request.user,
            action=action_type,
            description=f'Updated content setting: {setting_type}',
            request=request
        )
        
        return JsonResponse({
            'message': 'Setting saved successfully',
            'setting': {
                'type': setting.setting_type,
                'value': setting.setting_value,
                'updated_at': setting.get_formatted_date()
            }
        }, status=200)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def upload_content_image(request):
    """Upload an image for content settings (logos, announcements, etc.)"""
    try:
        if 'image' not in request.FILES:
            return JsonResponse({'error': 'No image file provided'}, status=400)
        
        setting_type = request.POST.get('setting_type')
        if not setting_type:
            return JsonResponse({'error': 'Setting type is required'}, status=400)
        
        image_file = request.FILES['image']
        
        # Get or create the setting
        setting, created = SystemSettings.objects.get_or_create(
            setting_type=setting_type,
            defaults={'updated_by': request.user}
        )
        
        # Save the image
        setting.image = image_file
        setting.updated_by = request.user
        setting.save()
        
        return JsonResponse({
            'message': 'Image uploaded successfully',
            'image_url': setting.image.url,
            'setting': {
                'type': setting.setting_type,
                'updated_at': setting.get_formatted_date()
            }
        }, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_staff_members(request):
    """Get all staff members for landing page"""
    try:
        staff = StaffMember.objects.filter(is_active=True).order_by('display_order', 'name')
        staff_list = []
        
        for member in staff:
            staff_list.append({
                'id': member.id,
                'name': member.name,
                'position': member.position,
                'photo_url': member.photo.url if member.photo else None,
                'display_order': member.display_order
            })
        
        return JsonResponse({'staff': staff_list}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def add_staff_member(request):
    """Add a new staff member"""
    try:
        name = request.POST.get('name', '').strip()
        position = request.POST.get('position', '').strip()
        display_order = int(request.POST.get('display_order', 0))
        
        if not name or not position:
            return JsonResponse({'error': 'Name and position are required'}, status=400)
        
        staff = StaffMember.objects.create(
            name=name,
            position=position,
            display_order=display_order
        )
        
        # Handle photo upload if provided
        if 'photo' in request.FILES:
            staff.photo = request.FILES['photo']
            staff.save()
        
        return JsonResponse({
            'message': 'Staff member added successfully',
            'staff': {
                'id': staff.id,
                'name': staff.name,
                'position': staff.position,
                'photo_url': staff.photo.url if staff.photo else None
            }
        }, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["PUT"])
def update_staff_member(request, staff_id):
    """Update an existing staff member"""
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
        
        return JsonResponse({
            'message': 'Staff member updated successfully',
            'staff': {
                'id': staff.id,
                'name': staff.name,
                'position': staff.position
            }
        }, status=200)
    except StaffMember.DoesNotExist:
        return JsonResponse({'error': 'Staff member not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_staff_member(request, staff_id):
    """Delete a staff member"""
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
    """Get activity logs with optional filtering"""
    try:
        # Get query parameters for filtering
        action_filter = request.GET.get('action', '')
        user_filter = request.GET.get('user', '')
        search = request.GET.get('search', '')
        limit = int(request.GET.get('limit', 100))
        
        # Start with all logs
        logs = ActivityLog.objects.all().order_by('-created_at')[:limit]
        
        # Apply filters if provided
        if action_filter:
            logs = logs.filter(action=action_filter)
        if user_filter:
            logs = logs.filter(user__username=user_filter)
        if search:
            logs = logs.filter(description__icontains=search)
        
        # Format logs for display
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
        
        return JsonResponse({
            'logs': logs_data,
            'count': len(logs_data)
        }, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============== BUILDINGS MANAGEMENT ==============

@login_required
@require_http_methods(["GET"])
def get_buildings_with_rooms(request):
    """Get all buildings with room count"""
    try:
        buildings = Building.objects.prefetch_related('rooms').all().order_by('name')
        buildings_list = []
        
        for building in buildings:
            buildings_list.append({
                'id': building.id,
                'name': building.name,
                'room_count': building.rooms.count()
            })
        
        return JsonResponse({'buildings': buildings_list}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def add_building(request):
    """Create a new building"""
    try:
        data = json.loads(request.body)
        name = (data.get('name') or '').strip()

        if not name:
            return JsonResponse({'error': 'Building name is required'}, status=400)

        if Building.objects.filter(name__iexact=name).exists():
            return JsonResponse({'error': 'Building name already exists'}, status=400)

        building = Building.objects.create(name=name)
        
        # Log activity
        log_activity(
            user=request.user,
            action='settings_changed',
            description=f'Added building: {name}',
            request=request
        )
        
        return JsonResponse({
            'message': 'Building added successfully',
            'building': {
                'id': building.id,
                'name': building.name,
                'room_count': 0
            }
        }, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["PUT"])
def update_building(request, building_id):
    """Update an existing building"""
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
        
        # Log activity
        log_activity(
            user=request.user,
            action='settings_changed',
            description=f'Updated building: {old_name} -> {name}',
            request=request
        )

        return JsonResponse({
            'message': 'Building updated successfully',
            'building': {
                'id': building.id,
                'name': building.name,
                'room_count': building.rooms.count()
            }
        }, status=200)
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
    """Delete a building and all its rooms"""
    try:
        building = Building.objects.get(pk=building_id)
        building_name = building.name
        room_count = building.rooms.count()
        
        # Check if any rooms are being used by sections
        rooms_in_use = []
        for room in building.rooms.all():
            sections_using_room = Section.objects.filter(
                building=building_name,
                room=room.room_number
            )
            if sections_using_room.exists():
                rooms_in_use.append(room.room_number)
        
        if rooms_in_use:
            return JsonResponse({
                'error': f'Cannot delete building. The following rooms are assigned to sections: {", ".join(rooms_in_use)}'
            }, status=400)

        building.delete()
        
        # Log activity
        log_activity(
            user=request.user,
            action='settings_changed',
            description=f'Deleted building: {building_name} (with {room_count} rooms)',
            request=request
        )
        
        return JsonResponse({'message': 'Building and all its rooms deleted successfully'}, status=200)
    except Building.DoesNotExist:
        return JsonResponse({'error': 'Building not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============== ROOMS MANAGEMENT ==============

@login_required
@require_http_methods(["GET"])
def get_rooms_by_building(request):
    """Get all rooms for a specific building"""
    try:
        print(f"DEBUG: GET params: {request.GET}")
        print(f"DEBUG: Full path: {request.get_full_path()}")
        building_id = request.GET.get('building_id')
        print(f"DEBUG: building_id received: {building_id}")
        if not building_id:
            return JsonResponse({'error': 'Building ID is required'}, status=400)
        
        building = Building.objects.get(pk=building_id)
        rooms = building.rooms.all().order_by('room_number')
        
        rooms_list = []
        for room in rooms:
            rooms_list.append({
                'id': room.id,
                'room_number': room.room_number,
                'building_id': building.id,
                'building_name': building.name
            })
        
        return JsonResponse({'rooms': rooms_list}, status=200)
    except Building.DoesNotExist:
        return JsonResponse({'error': 'Building not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def add_room(request):
    """Add a new room to a building"""
    try:
        data = json.loads(request.body)
        building_id = data.get('building_id')
        room_number = (data.get('room_number') or '').strip()

        if not building_id:
            return JsonResponse({'error': 'Building ID is required'}, status=400)
        
        if not room_number:
            return JsonResponse({'error': 'Room number is required'}, status=400)

        building = Building.objects.get(pk=building_id)
        
        # Check if room number already exists in this building
        if Room.objects.filter(building=building, room_number__iexact=room_number).exists():
            return JsonResponse({'error': 'Room number already exists in this building'}, status=400)

        room = Room.objects.create(
            building=building,
            room_number=room_number
        )
        
        # Log activity
        log_activity(
            user=request.user,
            action='settings_changed',
            description=f'Added room {room_number} to {building.name}',
            request=request
        )
        
        return JsonResponse({
            'message': 'Room added successfully',
            'room': {
                'id': room.id,
                'room_number': room.room_number,
                'building_id': building.id,
                'building_name': building.name
            }
        }, status=201)
    except Building.DoesNotExist:
        return JsonResponse({'error': 'Building not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["PUT"])
def update_room(request, room_id):
    """Update an existing room"""
    try:
        room = Room.objects.select_related('building').get(pk=room_id)
        data = json.loads(request.body)
        room_number = (data.get('room_number') or '').strip()

        if not room_number:
            return JsonResponse({'error': 'Room number is required'}, status=400)

        # Check if new room number already exists in this building (excluding current room)
        if Room.objects.filter(
            building=room.building,
            room_number__iexact=room_number
        ).exclude(pk=room_id).exists():
            return JsonResponse({'error': 'Room number already exists in this building'}, status=400)

        old_room_number = room.room_number
        room.room_number = room_number
        room.save()
        
        # Update sections that use this room
        Section.objects.filter(
            building=room.building.name,
            room=old_room_number
        ).update(room=room_number)
        
        # Log activity
        log_activity(
            user=request.user,
            action='settings_changed',
            description=f'Updated room in {room.building.name}: {old_room_number} -> {room_number}',
            request=request
        )

        return JsonResponse({
            'message': 'Room updated successfully',
            'room': {
                'id': room.id,
                'room_number': room.room_number,
                'building_id': room.building.id,
                'building_name': room.building.name
            }
        }, status=200)
    except Room.DoesNotExist:
        return JsonResponse({'error': 'Room not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_room(request, room_id):
    """Delete a room"""
    try:
        room = Room.objects.select_related('building').get(pk=room_id)
        room_number = room.room_number
        building_name = room.building.name
        
        # Check if room is being used by any section
        sections_using_room = Section.objects.filter(
            building=building_name,
            room=room_number
        )
        
        if sections_using_room.exists():
            section_names = ', '.join([s.name for s in sections_using_room[:3]])
            if sections_using_room.count() > 3:
                section_names += f' and {sections_using_room.count() - 3} more'
            return JsonResponse({
                'error': f'Cannot delete room. It is assigned to the following sections: {section_names}'
            }, status=400)

        room.delete()
        
        # Log activity
        log_activity(
            user=request.user,
            action='settings_changed',
            description=f'Deleted room {room_number} from {building_name}',
            request=request
        )
        
        return JsonResponse({'message': 'Room deleted successfully'}, status=200)
    except Room.DoesNotExist:
        return JsonResponse({'error': 'Room not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============== SCHOOL YEAR MANAGEMENT ==============

def _parse_date(date_str, field_name):
    """Parse a YYYY-MM-DD date string into a date object."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        raise ValidationError({field_name: 'Invalid date format. Use YYYY-MM-DD.'})


def _school_year_to_dict(school_year):
    """Serialize a SchoolYear instance for JSON responses."""
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
        'students_count': school_year.students.count(),
    }


@login_required
@require_http_methods(["GET"])
def get_school_years(request):
    """Return all school years with active/enrollment status."""
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
    """Create a new school year record."""
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

        log_activity(
            user=request.user,
            action='settings_changed',
            description=f'Added school year: {year_label}',
            request=request
        )

        return JsonResponse(
            {
                'message': 'School year added successfully',
                'school_year': _school_year_to_dict(school_year)
            },
            status=201
        )
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
    """Update an existing school year."""
    try:
        school_year = SchoolYear.objects.get(pk=school_year_id)
        payload = json.loads(request.body)

        year_label = (payload.get('year_label') or '').strip()
        start_date_raw = payload.get('start_date')
        end_date_raw = payload.get('end_date')
        is_active = bool(payload.get('is_active'))
        enrollment_open = bool(payload.get('enrollment_open'))

        if not year_label or not start_date_raw or not end_date_raw:
            return JsonResponse({'error': 'Year label, start date, and end date are required'}, status=400)

        school_year.year_label = year_label
        school_year.start_date = _parse_date(start_date_raw, 'start_date')
        school_year.end_date = _parse_date(end_date_raw, 'end_date')
        school_year.is_active = is_active
        school_year.enrollment_open = enrollment_open
        school_year.save()

        log_activity(
            user=request.user,
            action='settings_changed',
            description=f'Updated school year: {year_label}',
            request=request
        )

        return JsonResponse({
            'message': 'School year updated successfully',
            'school_year': _school_year_to_dict(school_year)
        }, status=200)
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
    """Delete a school year if it is not active and has no related data."""
    try:
        school_year = SchoolYear.objects.get(pk=school_year_id)

        if school_year.is_active:
            return JsonResponse({'error': 'Cannot delete the active school year'}, status=400)

        if school_year.sections.exists() or school_year.students.exists():
            sections_count = school_year.sections.count()
            students_count = school_year.students.count()
            return JsonResponse({
                'error': (
                    'Cannot delete school year with existing data '
                    f'(sections: {sections_count}, students: {students_count}).'
                )
            }, status=400)

        year_label = school_year.year_label
        school_year.delete()

        log_activity(
            user=request.user,
            action='settings_changed',
            description=f'Deleted school year: {year_label}',
            request=request
        )

        return JsonResponse({'message': 'School year deleted successfully'}, status=200)
    except SchoolYear.DoesNotExist:
        return JsonResponse({'error': 'School year not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)