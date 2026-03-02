from django.shortcuts import render, get_object_or_404
from enrollment_app.models import Student  # adjust to your actual model

def student_details(request, lrn):
    # Build your context here
    student = get_object_or_404(Student, lrn=lrn)
    
    context = {
        'student': student,
        # add whatever else your template needs
    }

    if request.GET.get('partial') == '1':
        return render(request, 'coordinator_app/coor_studentdetails_partial.html', context)
    
    return render(request, 'coordinator_app/coor-studentdetails.html', context)