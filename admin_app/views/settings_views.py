from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def settings(request):
    return render(request, 'admin_app/settings.html')

@login_required
def manage_users(request):
    return render(request, 'admin_app/settings.html', {'tab': 'users'})

@login_required
def manage_content(request):
    return render(request, 'admin_app/settings.html', {'tab': 'content'})