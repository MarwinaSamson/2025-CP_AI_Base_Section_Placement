from django.shortcuts import render, redirect
from django.contrib import messages
from ..services.lrn_verification import LRNVerificationService
from ..services.session_manager import EnrollmentSessionManager


def student_data_form(request):
    """
    Handle student data form with LRN verification
    Data is stored in session until all forms are completed
    """
    
    if request.method == 'POST':
        # Get LRN from form
        lrn = request.POST.get('lrn', '').strip()
        
        # Verify LRN against LIS database
        verification_result = LRNVerificationService.verify_lrn(lrn)
        
        if not verification_result['is_valid']:
            # LRN not found - show error and preserve form data
            messages.error(request, verification_result['message'])
            return render(request, 'enrollment_app/studentData.html', {
                'form_data': request.POST,
            })
        
        # LRN is VALID - Prepare data for session
        form_data = {
            'lrn': lrn,
            'email': request.POST.get('email', ''),
            'enrolling_as': request.POST.getlist('enrolling_as'),
            'is_sped': request.POST.get('is_sped') == 'yes',
            'sped_details': request.POST.get('sped_details', ''),
            'is_working_student': request.POST.get('is_working_student') == 'yes',
            'working_details': request.POST.get('working_details', ''),
            'last_name': request.POST.get('last_name', ''),
            'first_name': request.POST.get('first_name', ''),
            'middle_name': request.POST.get('middle_name', ''),
            'gender': request.POST.get('gender', ''),
            'date_of_birth': request.POST.get('date_of_birth', ''),
            'place_of_birth': request.POST.get('place_of_birth', ''),
            'religion': request.POST.get('religion', ''),
            'dialect_spoken': request.POST.get('dialect_spoken', ''),
            'ethnic_tribe': request.POST.get('ethnic_tribe', ''),
            'address': request.POST.get('address', ''),
            'last_school_attended': request.POST.get('last_school_attended', ''),
            'previous_grade_section': request.POST.get('previous_grade_section', ''),
            'last_school_year': request.POST.get('last_school_year', ''),
        }
        
        # Handle file upload (store file temporarily in session as base64 or file path)
        if 'student_photo' in request.FILES:
            # For now, we'll handle the file in the final submission
            # Store file info in session
            photo = request.FILES['student_photo']
            form_data['student_photo_name'] = photo.name
            # You can also store the file temporarily or convert to base64
        
        # Save to session
        EnrollmentSessionManager.save_student_data(request, form_data)
        EnrollmentSessionManager.set_lrn_verified(request, True)
        
        messages.success(request, f'LRN {lrn} verified successfully! Please continue with Family Data.')
        return redirect('enrollment_app:family_data')
    
    # GET request - check if there's existing session data
    existing_data = EnrollmentSessionManager.get_student_data(request)
    
    return render(request, 'enrollment_app/studentData.html', {
        'form_data': existing_data or {}
    })