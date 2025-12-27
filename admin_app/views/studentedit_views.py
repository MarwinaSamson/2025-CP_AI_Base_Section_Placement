from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
def student_edit(request, student_id):
    return render(request, 'admin_app/studentEdit.html', {'student_id': student_id})