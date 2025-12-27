from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
def enrollment_list(request):
    return render(request, 'admin_app/enrollment.html')

@login_required
def enrollment_detail(request, student_id):
    return render(request, 'admin_app/enrollment.html', {'student_id': student_id})