from django.shortcuts import render, redirect
from django.contrib.auth import login, logout

def admin_login(request):
    if request.user.is_authenticated:
        return redirect('admin_app:dashboard')
    return render(request, 'admin_app/login.html')

def admin_logout(request):
    logout(request)
    return render(request, 'admin_app/logout.html')