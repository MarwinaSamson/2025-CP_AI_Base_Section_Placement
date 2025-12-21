from django.shortcuts import render

def family_data_form(request):
    """
    Render the family data form - second step of enrollment
    """
    if request.method == 'POST':
        # For now, just pass through - will handle form processing later
        pass
    
    context = {
        'page_title': 'Family Data Form',
    }
    return render(request, 'enrollment_app/familyData.html', context)