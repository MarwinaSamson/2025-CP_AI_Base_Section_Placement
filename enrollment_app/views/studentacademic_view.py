from django.shortcuts import render

def academic_form(request):
    """
    Render the academic form - fourth step of enrollment
    """
    if request.method == 'POST':
        # For now, just pass through - will handle form processing later
        pass
    
    context = {
        'page_title': 'Student Academic Form',
    }
    return render(request, 'enrollment_app/studentAcademic.html', context)