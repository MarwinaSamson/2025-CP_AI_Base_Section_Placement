from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def analytics(request):
    return render(request, 'admin_app/analytics.html')