from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json

def admin_login(request):
    """Unified login view for both Admin and Coordinator"""
    
    # If user is already authenticated, redirect to appropriate dashboard
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile'):
            if request.user.profile.user_type == 'admin':
                return redirect('admin_app:dashboard')
            elif request.user.profile.user_type == 'coordinator':
                return redirect('coordinator:dashboard')
        return redirect('admin_app:dashboard')  # Default fallback
    
    if request.method == 'POST':
        try:
            # Get form data
            username = request.POST.get('username')
            password = request.POST.get('password')
            user_type = request.POST.get('user_type', 'admin')  # From role selection
            program = request.POST.get('program', '')  # For coordinators
            
            # Validate inputs
            if not username or not password:
                return JsonResponse({
                    'success': False,
                    'message': 'Username and password are required.'
                }, status=400)
            
            # Authenticate user
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Check if user has a profile
                if not hasattr(user, 'profile'):
                    return JsonResponse({
                        'success': False,
                        'message': 'User profile not found. Please contact administrator.'
                    }, status=400)
                
                # Verify user type matches selected role
                if user.profile.user_type != user_type:
                    return JsonResponse({
                        'success': False,
                        'message': f'Invalid credentials for {user_type} login.'
                    }, status=400)
                
                # Additional validation for coordinator
                if user_type == 'coordinator':
                    if not program:
                        return JsonResponse({
                            'success': False,
                            'message': 'Please select a program.'
                        }, status=400)
                    
                    # Verify coordinator's program
                    if user.profile.program != program:
                        return JsonResponse({
                            'success': False,
                            'message': 'Invalid program selection for this coordinator.'
                        }, status=400)
                
                # Login successful
                login(request, user)
                
                # Determine redirect URL based on user type
                if user.profile.user_type == 'admin':
                    redirect_url = '/admin-portal/dashboard/'
                    dashboard_name = 'Admin Dashboard'
                else:  # coordinator
                    redirect_url = '/coordinator/dashboard/'
                    dashboard_name = f'{program} Coordinator Dashboard'
                
                return JsonResponse({
                    'success': True,
                    'message': f'Welcome to {dashboard_name}!',
                    'redirect_url': redirect_url,
                    'user_type': user.profile.user_type,
                    'username': user.get_full_name() or user.username
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid username or password.'
                }, status=401)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'An error occurred: {str(e)}'
            }, status=500)
    
    # GET request - render login page
    return render(request, 'admin_app/login.html')


@login_required
def admin_logout(request):
    """Logout view for both Admin and Coordinator"""
    logout(request)
    return redirect('admin_app:login')


def logout_page(request):
    """Render logout confirmation page"""
    return render(request, 'admin_app/logout.html')