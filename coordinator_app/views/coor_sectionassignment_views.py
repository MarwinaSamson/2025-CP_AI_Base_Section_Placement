from django.shortcuts import render

def section_assignment(request):
    return render(request, 'coordinator_app/sectionAssignment.html')