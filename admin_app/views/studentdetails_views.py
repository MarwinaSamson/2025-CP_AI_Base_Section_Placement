from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
def student_details(request, student_id):
    return render(request, 'admin_app/studentDetails.html', {'student_id': student_id})