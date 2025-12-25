from django.shortcuts import render, redirect
from django.contrib import messages
from ..services.lrn_verification import LRNVerificationService
from ..services.session_manager import EnrollmentSessionManager
import os
import uuid
from django.conf import settings


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
        
        # Get existing photo data from session first
        existing_data = EnrollmentSessionManager.get_student_data(request) or {}
        form_data['student_photo_path'] = existing_data.get('student_photo_path', '')
        form_data['student_photo_name'] = existing_data.get('student_photo_name', '')
        
        # Handle file upload (store file temporarily) - only update if new file uploaded
        if 'student_photo' in request.FILES:
            photo = request.FILES['student_photo']
            
            # Create temp directory if it doesn't exist
            temp_dir = os.path.join(settings.BASE_DIR, 'temp_uploads')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Generate unique filename
            file_extension = os.path.splitext(photo.name)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            temp_file_path = os.path.join(temp_dir, unique_filename)
            
            # Save file to temp location
            with open(temp_file_path, 'wb+') as destination:
                for chunk in photo.chunks():
                    destination.write(chunk)
            
            # Store only file path and name in session (NO base64)
            form_data['student_photo_path'] = temp_file_path
            form_data['student_photo_name'] = photo.name
        
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