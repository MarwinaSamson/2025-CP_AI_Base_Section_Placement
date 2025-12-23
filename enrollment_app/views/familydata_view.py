from django.shortcuts import render, redirect
from django.contrib import messages
from ..services.lrn_verification import LRNVerificationService
from ..services.session_manager import EnrollmentSessionManager

def family_data_form(request):
    """
    Handle family data form
    Requires LRN verification from previous step
    """
    
    # Check if LRN is verified
    if not EnrollmentSessionManager.is_lrn_verified(request):
        messages.error(request, 'Please complete the Student Data form first.')
        return redirect('enrollment_app:student_data')
    
    # Get student info from session
    student_data = EnrollmentSessionManager.get_student_data(request)
    
    if request.method == 'POST':
        # Prepare family data
        family_data = {
            # Father's Information
            'father_family_name': request.POST.get('father_family_name', ''),
            'father_first_name': request.POST.get('father_first_name', ''),
            'father_middle_name': request.POST.get('father_middle_name', ''),
            'father_dob': request.POST.get('father_dob', ''),
            'father_occupation': request.POST.get('father_occupation', ''),
            'father_address': request.POST.get('father_address', ''),
            'father_contact_number': request.POST.get('father_contact_number', ''),
            'father_email': request.POST.get('father_email', ''),
            
            # Mother's Information
            'mother_family_name': request.POST.get('mother_family_name', ''),
            'mother_first_name': request.POST.get('mother_first_name', ''),
            'mother_middle_name': request.POST.get('mother_middle_name', ''),
            'mother_dob': request.POST.get('mother_dob', ''),
            'mother_occupation': request.POST.get('mother_occupation', ''),
            'mother_address': request.POST.get('mother_address', ''),
            'mother_contact_number': request.POST.get('mother_contact_number', ''),
            'mother_email': request.POST.get('mother_email', ''),
            
            # Guardian Selection
            'guardian_type': request.POST.get('guardian_type', ''),
            
            # Other Guardian Information (if selected)
            'guardian_family_name': request.POST.get('guardian_family_name', ''),
            'guardian_first_name': request.POST.get('guardian_first_name', ''),
            'guardian_middle_name': request.POST.get('guardian_middle_name', ''),
            'guardian_dob': request.POST.get('guardian_dob', ''),
            'guardian_occupation': request.POST.get('guardian_occupation', ''),
            'guardian_address': request.POST.get('guardian_address', ''),
            'guardian_relationship': request.POST.get('guardian_relationship', ''),
            'guardian_contact_number': request.POST.get('guardian_contact_number', ''),
            'guardian_email': request.POST.get('guardian_email', ''),
        }
        
        # Handle parent photo upload
        if 'parent_photo' in request.FILES:
            photo = request.FILES['parent_photo']
            family_data['parent_photo_name'] = photo.name
            # Store file temporarily or convert to base64 if needed
        
        # Validate guardian selection
        if not family_data['guardian_type']:
            messages.error(request, 'Please select who will be the student\'s official guardian.')
            return render(request, 'enrollment_app/familyData.html', {
                'form_data': request.POST,
                'student_info': student_data
            })
        
        # If "other" guardian is selected, validate those fields
        if family_data['guardian_type'] == 'other':
            required_guardian_fields = [
                'guardian_family_name', 'guardian_first_name', 'guardian_dob',
                'guardian_occupation', 'guardian_address', 'guardian_relationship',
                'guardian_contact_number'
            ]
            
            missing_fields = [field for field in required_guardian_fields if not family_data.get(field)]
            
            if missing_fields:
                messages.error(request, 'Please fill in all required guardian information fields.')
                return render(request, 'enrollment_app/familyData.html', {
                    'form_data': request.POST,
                    'student_info': student_data
                })
        
        # Save to session
        EnrollmentSessionManager.save_family_data(request, family_data)
        
        messages.success(request, 'Family data saved successfully! Please continue with the survey.')
        return redirect('enrollment_app:non_academic')  # or whatever your next form URL is
    
    # GET request - check for existing session data
    existing_family_data = EnrollmentSessionManager.get_family_data(request)
    
    return render(request, 'enrollment_app/familyData.html', {
        'form_data': existing_family_data or {},
        'student_info': student_data
    })