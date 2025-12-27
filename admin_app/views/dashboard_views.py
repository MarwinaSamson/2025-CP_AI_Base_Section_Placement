from django.shortcuts import render
from admin_app.decorators import admin_required

@admin_required
def dashboard(request):
    context = {
        'user': request.user,
    }
    return render(request, 'admin_app/dashboard.html', context)