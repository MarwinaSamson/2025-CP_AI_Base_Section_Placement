from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from admin_app.models import SchoolYear, UserProfile

@login_required
def reports(request):
    """Reports main view"""
    return render(request, 'admin_app/reports.html')


@login_required
@require_http_methods(["GET"])
def reports_header_data(request):
    """
    API endpoint for reports header data
    Returns: school year, user fullname, role, and photo/initials
    """
    # Get active school year
    active_school_year = SchoolYear.get_active_school_year()
    
    # Get user profile
    try:
        user_profile = UserProfile.objects.select_related(
            'program', 'position', 'department'
        ).get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None
    
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
def generate_report(request):
    """Handle AJAX requests for generating reports"""
    if request.method == 'POST':
        return JsonResponse({'status': 'success', 'message': 'Report generated'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})