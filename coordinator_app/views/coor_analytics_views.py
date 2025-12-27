from django.shortcuts import render

def analytics(request):
    return render(request, 'coordinator_app/analytics.html')