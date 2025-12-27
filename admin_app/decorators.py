from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from functools import wraps

def admin_required(view_func):
    """Decorator to ensure user is an admin"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if hasattr(request.user, 'profile') and request.user.profile.user_type == 'admin':
            return view_func(request, *args, **kwargs)
        return redirect('admin_app:login')
    return wrapper


def coordinator_required(view_func):
    """Decorator to ensure user is a coordinator"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if hasattr(request.user, 'profile') and request.user.profile.user_type == 'coordinator':
            return view_func(request, *args, **kwargs)
        return redirect('admin_app:login')
    return wrapper