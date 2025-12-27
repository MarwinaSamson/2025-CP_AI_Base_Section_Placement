from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

@login_required
def reports(request):
    return render(request, 'admin_app/reports.html')

@login_required
def generate_report(request):
    # This will handle AJAX requests for generating reports
    if request.method == 'POST':
        return JsonResponse({'status': 'success', 'message': 'Report generated'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})