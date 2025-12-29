from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from admin_app.models import Program
import logging

logger = logging.getLogger(__name__)


def admin_login(request):
    """
    Unified login view for Admin and Coordinator
    - GET  : render login page with program list
    - POST : authenticate user and validate role + program
    """

    # Already authenticated
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile'):
            if request.user.profile.user_type == 'admin':
                return redirect('admin_app:dashboard')
            elif request.user.profile.user_type == 'coordinator':
                return redirect('coordinator:dashboard')
        return redirect('admin_app:dashboard')

    # POST (AJAX login)
    if request.method == 'POST':
        try:
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')
            user_type = request.POST.get('user_type', 'admin')
            program_id = request.POST.get('program', '').strip()

            logger.info(f"Login attempt - Username: {username}, Type: {user_type}, Program ID: {program_id}")

            # Basic validation
            if not username or not password:
                return JsonResponse({
                    'success': False,
                    'message': 'Username and password are required.'
                }, status=400)

            # Authenticate
            user = authenticate(request, username=username, password=password)
            if user is None:
                logger.warning(f"Authentication failed for username: {username}")
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid username or password.'
                }, status=401)

            # Profile check
            if not hasattr(user, 'profile'):
                logger.error(f"User {username} has no profile")
                return JsonResponse({
                    'success': False,
                    'message': 'User profile not found. Please contact administrator.'
                }, status=400)

            # Role validation
            if user.profile.user_type != user_type:
                logger.warning(f"Role mismatch for {username}. Expected: {user_type}, Got: {user.profile.user_type}")
                return JsonResponse({
                    'success': False,
                    'message': f'This account is not registered as a {user_type}. Please select the correct role.'
                }, status=403)

            # Coordinator-specific checks
            if user_type == 'coordinator':
                # Check if program was selected
                if not program_id:
                    return JsonResponse({
                        'success': False,
                        'message': 'Please select a program.'
                    }, status=400)

                # Fetch program from DB
                try:
                    selected_program = Program.objects.get(id=program_id)
                    logger.info(f"Selected program: {selected_program.code} (ID: {selected_program.id})")
                except Program.DoesNotExist:
                    logger.error(f"Program ID {program_id} does not exist")
                    return JsonResponse({
                        'success': False,
                        'message': 'Selected program does not exist.'
                    }, status=400)

                # Check if coordinator has a program assigned
                if not user.profile.program:
                    logger.error(f"Coordinator {username} has no program assigned in profile")
                    return JsonResponse({
                        'success': False,
                        'message': 'Your account has no program assigned. Please contact the administrator.'
                    }, status=403)

                # Verify coordinator is assigned to this program
                logger.info(f"User's assigned program: {user.profile.program.code} (ID: {user.profile.program.id})")
                
                if user.profile.program.id != int(program_id):
                    logger.warning(
                        f"Program mismatch for {username}. "
                        f"Selected: {selected_program.code}, "
                        f"Assigned: {user.profile.program.code}"
                    )
                    return JsonResponse({
                        'success': False,
                        'message': f'You are not authorized for {selected_program.code}. '
                                   f'Your assigned program is {user.profile.program.code}.'
                    }, status=403)

            # Login success
            login(request, user)
            logger.info(f"Successful login for {username} as {user_type}")

            if user.profile.user_type == 'admin':
                redirect_url = '/admin-portal/dashboard/'
                dashboard_name = 'Admin Dashboard'
            else:
                redirect_url = '/coordinator/dashboard/'
                dashboard_name = f'{user.profile.program.code} Coordinator Dashboard'

            return JsonResponse({
                'success': True,
                'message': f'Welcome to {dashboard_name}!',
                'redirect_url': redirect_url,
                'user_type': user.profile.user_type,
                'username': user.get_full_name() or user.username
            })

        except Exception as e:
            logger.exception(f"Login error: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'An error occurred: {str(e)}'
            }, status=500)

    # GET (render login page)
    programs = Program.objects.filter(is_active=True).order_by('code')

    return render(request, 'admin_app/login.html', {
        'programs': programs
    })


@login_required
def admin_logout(request):
    """Logout view for both Admin and Coordinator"""
    logout(request)
    return redirect('admin_app:login')


def logout_page(request):
    """Render logout confirmation page"""
    return render(request, 'admin_app/logout.html')