from django.shortcuts import render
from admin_app.decorators import coordinator_required

@coordinator_required
def dashboard(request):
    context = {
        'user': request.user,
        'program': request.user.profile.program if hasattr(request.user, 'profile') else None
    }
    return render(request, 'coordinator_app/dashboard.html', context)