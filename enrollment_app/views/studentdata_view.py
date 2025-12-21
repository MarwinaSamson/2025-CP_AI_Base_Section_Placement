from django.shortcuts import render

def student_data_form(request):
    """
    Render the student data form - first step of enrollment
    """
    if request.method == 'POST':
        # For now, just pass through - will handle form processing later
        pass
    
    context = {
        'page_title': 'Student Data Form',
    }
    return render(request, 'enrollment_app/studentData.html', context)