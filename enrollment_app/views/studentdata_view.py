# from django.shortcuts import render, redirect
# from django.contrib import messages
# from ..services.lrn_verification import LRNVerificationService
# from ..services.session_manager import EnrollmentSessionManager
# from admin_app.models import SchoolYear
# import os
# import uuid
# from django.conf import settings


# def student_data_form(request):
#     """
#     Handle student data form with LRN verification
#     Data is stored in session until all forms are completed
#     """
    
#     if request.method == 'POST':
#         # Get LRN from form
#         lrn = request.POST.get('lrn', '').strip()
#         first_name = request.POST.get('first_name', '').strip()
#         last_name = request.POST.get('last_name', '').strip()
        
#         # Verify LRN against LIS database
#         verification_result = LRNVerificationService.verify_lrn(
#             lrn,
#             first_name=first_name,
#             last_name=last_name,
#         )
        
#         if not verification_result['is_valid']:
#             # LRN not found - show error and preserve form data
#             messages.error(request, verification_result['message'])
#             return render(request, 'enrollment_app/studentData.html', {
#                 'form_data': request.POST,
#             })
        
#         # LRN is VALID - Prepare data for session
#         form_data = {
#             'lrn': lrn,
#             'email': request.POST.get('email', ''),
#             'enrolling_as': request.POST.getlist('enrolling_as'),
#             'is_sped': request.POST.get('is_sped') == 'yes',
#             'sped_details': request.POST.get('sped_details', ''),
#             'is_working_student': request.POST.get('is_working_student') == 'yes',
#             'working_details': request.POST.get('working_details', ''),
#             'last_name': last_name,
#             'first_name': first_name,
#             'middle_name': request.POST.get('middle_name', ''),
#             'gender': request.POST.get('gender', ''),
#             'date_of_birth': request.POST.get('date_of_birth', ''),
#             'place_of_birth': request.POST.get('place_of_birth', ''),
#             'religion': request.POST.get('religion', ''),
#             'dialect_spoken': request.POST.get('dialect_spoken', ''),
#             'ethnic_tribe': request.POST.get('ethnic_tribe', ''),
#             'address': request.POST.get('address', ''),
#             'last_school_attended': request.POST.get('last_school_attended', ''),
#             'previous_grade_section': request.POST.get('previous_grade_section', ''),
#             'last_school_year': request.POST.get('last_school_year', ''),
#         }
        
#         # Get existing photo data from session first
#         existing_data = EnrollmentSessionManager.get_student_data(request) or {}
#         form_data['student_photo_path'] = existing_data.get('student_photo_path', '')
#         form_data['student_photo_name'] = existing_data.get('student_photo_name', '')
        
#         # Handle file upload (store file temporarily) - only update if new file uploaded
#         if 'student_photo' in request.FILES:
#             photo = request.FILES['student_photo']
            
#             # Create temp directory if it doesn't exist
#             temp_dir = os.path.join(settings.BASE_DIR, 'temp_uploads')
#             os.makedirs(temp_dir, exist_ok=True)
            
#             # Generate unique filename
#             file_extension = os.path.splitext(photo.name)[1]
#             unique_filename = f"{uuid.uuid4()}{file_extension}"
#             temp_file_path = os.path.join(temp_dir, unique_filename)
            
#             # Save file to temp location
#             with open(temp_file_path, 'wb+') as destination:
#                 for chunk in photo.chunks():
#                     destination.write(chunk)
            
#             # Store only file path and name in session (NO base64)
#             form_data['student_photo_path'] = temp_file_path
#             form_data['student_photo_name'] = photo.name
        
#         # Save to session
#         EnrollmentSessionManager.save_student_data(request, form_data)
#         EnrollmentSessionManager.set_lrn_verified(request, True)
        
#         messages.success(request, f'LRN {lrn} verified successfully! Please continue with Family Data.')
#         return redirect('enrollment_app:family_data')
    
#     # GET request - check if there's existing session data
#     existing_data = EnrollmentSessionManager.get_student_data(request)
    
#     # Get active school year
#     active_school_year = SchoolYear.objects.filter(is_active=True).first()
    
#     return render(request, 'enrollment_app/studentData.html', {
#         'form_data': existing_data or {},
#         'school_year': active_school_year
#     })


from django.shortcuts import render, redirect
from django.contrib import messages
from ..services.lrn_verification import LRNVerificationService
from ..services.session_manager import EnrollmentSessionManager
from admin_app.models import SchoolYear
import os
import uuid
from django.conf import settings


# Enrollment type constants
ENROLLMENT_TYPE_NEW = 'new'
ENROLLMENT_TYPE_OLD = 'old'
ENROLLMENT_TYPE_TRANSFEREE = 'transferee'


def student_data_form(request):
    """
    Handle student data form with LRN verification.
    Routing behavior based on enrollment type:
      - new:        Full flow → family_data → non_academic → academic
      - old:        Shortened flow → family_data only (no survey/academic/ML)
      - transferee: Document flow → family_data → document submission only
    """

    if request.method == 'POST':
        lrn = request.POST.get('lrn', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()

        # Get enrolling_as list (enforced as single-select by JS, but handle list safely)
        enrolling_as = request.POST.getlist('enrolling_as')

        # Verify LRN against LIS database
        verification_result = LRNVerificationService.verify_lrn(
            lrn,
            first_name=first_name,
            last_name=last_name,
        )

        if not verification_result['is_valid']:
            messages.error(request, verification_result['message'])
            return render(request, 'enrollment_app/studentData.html', {
                'form_data': request.POST,
                'school_year': SchoolYear.objects.filter(is_active=True).first(),
            })

        # Determine primary enrollment type (single value expected from JS)
        primary_type = enrolling_as[0] if enrolling_as else ENROLLMENT_TYPE_NEW

        # Build form data for session
        form_data = {
            'lrn': lrn,
            'email': request.POST.get('email', ''),
            'enrolling_as': enrolling_as,
            'enrollment_type': primary_type,  # Store primary type for routing
            'is_sped': request.POST.get('is_sped') == 'yes',
            'sped_details': request.POST.get('sped_details', ''),
            'is_working_student': request.POST.get('is_working_student') == 'yes',
            'working_details': request.POST.get('working_details', ''),
            'last_name': last_name,
            'first_name': first_name,
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

        # Transferee-specific field
        if primary_type == ENROLLMENT_TYPE_TRANSFEREE:
            form_data['transferee_grade_level'] = request.POST.get('transferee_grade_level', '')

        # Preserve existing photo data from session
        existing_data = EnrollmentSessionManager.get_student_data(request) or {}
        form_data['student_photo_path'] = existing_data.get('student_photo_path', '')
        form_data['student_photo_name'] = existing_data.get('student_photo_name', '')

        # Handle file upload (store file temporarily)
        if 'student_photo' in request.FILES:
            photo = request.FILES['student_photo']
            temp_dir = os.path.join(settings.BASE_DIR, 'temp_uploads')
            os.makedirs(temp_dir, exist_ok=True)
            file_extension = os.path.splitext(photo.name)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            temp_file_path = os.path.join(temp_dir, unique_filename)
            with open(temp_file_path, 'wb+') as destination:
                for chunk in photo.chunks():
                    destination.write(chunk)
            form_data['student_photo_path'] = temp_file_path
            form_data['student_photo_name'] = photo.name

        # Save to session
        EnrollmentSessionManager.save_student_data(request, form_data)
        EnrollmentSessionManager.set_lrn_verified(request, True)

        # Clear cached recommendations so they are regenerated with updated
        # PWD / working-student status the next time the academic page runs.
        if EnrollmentSessionManager.get_recommendations(request):
            EnrollmentSessionManager.save_recommendations(request, None)

        # Store enrollment type in session for downstream routing
        request.session['enrollment_type'] = primary_type

        messages.success(request, f'LRN {lrn} verified successfully! Please continue with Family Data.')
        return redirect('enrollment_app:family_data')

    # GET request
    existing_data = EnrollmentSessionManager.get_student_data(request)
    active_school_year = SchoolYear.objects.filter(is_active=True).first()

    return render(request, 'enrollment_app/studentData.html', {
        'form_data': existing_data or {},
        'school_year': active_school_year,
    })