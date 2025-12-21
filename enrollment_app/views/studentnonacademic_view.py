from django.shortcuts import render

def non_academic_form(request):
    """
    Render the non-academic student survey form - third step of enrollment
    """
    if request.method == 'POST':
        # For now, just pass through - will handle form processing later
        pass
    
    context = {
        'page_title': 'Non-Academic Student Survey',
    }
    return render(request, 'enrollment_app/studentNonAcademic.html', context)