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
    from enrollment_app.models import Student, StudentData

    if request.method == 'POST':
        lrn = request.POST.get('lrn', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        enrolling_as = request.POST.getlist('enrolling_as')

        # Verify LRN
        verification_result = LRNVerificationService.verify_lrn(
            lrn, first_name=first_name, last_name=last_name,
        )

        if not verification_result['is_valid']:
            messages.error(request, verification_result['message'])
            return render(request, 'enrollment_app/studentData.html', {
                'form_data': request.POST,
                'school_year': SchoolYear.objects.filter(is_active=True).first(),
            })

        # ── OLD STUDENT: Session already populated by AJAX lookup ──────
        # The lookup_old_student AJAX endpoint already saved StudentData
        # and FamilyData to session when the student typed their LRN.
        # So here we just verify session is set and redirect to family data.
        if 'old' in enrolling_as:
            existing_session = EnrollmentSessionManager.get_student_data(request)

            if existing_session and existing_session.get('prefilled_from_db'):
                # AJAX already did the work — update enrolling_as in case
                # student changed anything on the form before submitting
                existing_session.update({
                    'last_name':            request.POST.get('last_name', existing_session.get('last_name', '')),
                    'first_name':           request.POST.get('first_name', existing_session.get('first_name', '')),
                    'middle_name':          request.POST.get('middle_name', existing_session.get('middle_name', '')),
                    'gender':               request.POST.get('gender', existing_session.get('gender', '')),
                    'date_of_birth':        request.POST.get('date_of_birth', existing_session.get('date_of_birth', '')),
                    'place_of_birth':       request.POST.get('place_of_birth', existing_session.get('place_of_birth', '')),
                    'religion':             request.POST.get('religion', existing_session.get('religion', '')),
                    'dialect_spoken':       request.POST.get('dialect_spoken', existing_session.get('dialect_spoken', '')),
                    'ethnic_tribe':         request.POST.get('ethnic_tribe', existing_session.get('ethnic_tribe', '')),
                    'address':              request.POST.get('address', existing_session.get('address', '')),
                    'last_school_attended': request.POST.get('last_school_attended', existing_session.get('last_school_attended', '')),
                    'previous_grade_section': request.POST.get('previous_grade_section', existing_session.get('previous_grade_section', '')),
                    'last_school_year':     request.POST.get('last_school_year', existing_session.get('last_school_year', '')),
                    'is_sped':              request.POST.get('is_sped') == 'yes',
                    'sped_details':         request.POST.get('sped_details', existing_session.get('sped_details', '')),
                    'is_working_student':   request.POST.get('is_working_student') == 'yes',
                    'working_details':      request.POST.get('working_details', existing_session.get('working_details', '')),
                })

                # Handle new photo upload if student chose to update it
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
                    existing_session['student_photo_path'] = temp_file_path
                    existing_session['student_photo_name'] = photo.name

                EnrollmentSessionManager.save_student_data(request, existing_session)
                return redirect('enrollment_app:family_data')

            else:
                # AJAX was not triggered (e.g. JS disabled) — fallback to DB fetch
                try:
                    from enrollment_app.models import Student, StudentData
                    student = Student.objects.select_related('student_data').get(lrn=lrn)
                    sd = student.student_data
                    form_data = {
                        'lrn': lrn,
                        'enrolling_as': enrolling_as,
                        'enrollment_type': 'old',
                        'prefilled_from_db': True,
                        'last_name':            sd.last_name or '',
                        'first_name':           sd.first_name or '',
                        'middle_name':          sd.middle_name or '',
                        'gender':               sd.gender or '',
                        'date_of_birth':        str(sd.date_of_birth) if sd.date_of_birth else '',
                        'place_of_birth':       sd.place_of_birth or '',
                        'religion':             sd.religion or '',
                        'dialect_spoken':       sd.dialect_spoken or '',
                        'ethnic_tribe':         sd.ethnic_tribe or '',
                        'address':              sd.address or '',
                        'last_school_attended': sd.last_school_attended or '',
                        'previous_grade_section': sd.previous_grade_section or '',
                        'last_school_year':     sd.last_school_year or '',
                        'is_sped':              sd.is_sped,
                        'sped_details':         sd.sped_details or '',
                        'is_working_student':   sd.is_working_student,
                        'working_details':      sd.working_details or '',
                        'student_photo_path':   sd.student_photo.name if sd.student_photo else '',
                        'student_photo_name':   sd.student_photo.name.split('/')[-1] if sd.student_photo else '',
                    }
                    EnrollmentSessionManager.save_student_data(request, form_data)
                    EnrollmentSessionManager.set_lrn_verified(request, True)
                    request.session['enrollment_type'] = 'old'
                    messages.info(request, 'Welcome back! Your previous details have been pre-filled.')
                    return render(request, 'enrollment_app/studentData.html', {
                        'form_data': form_data,
                        'school_year': SchoolYear.objects.filter(is_active=True).first(),
                    })
                except Exception:
                    messages.warning(request, 'No previous record found. Please fill in your details.')
                    # fall through to new student flow

        # ── NEW / TRANSFEREE: Normal flow ──────────────────────────────
        primary_type = enrolling_as[0] if enrolling_as else 'new'

        form_data = {
            'lrn': lrn,
            'email': request.POST.get('email', ''),
            'enrolling_as': enrolling_as,
            'enrollment_type': primary_type,
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

        if primary_type == 'transferee':
            form_data['transferee_grade_level'] = request.POST.get('transferee_grade_level', '')
            form_data['previous_program'] = request.POST.get('previous_program', 'REGULAR')

        # Photo handling
        existing_data = EnrollmentSessionManager.get_student_data(request) or {}
        form_data['student_photo_path'] = existing_data.get('student_photo_path', '')
        form_data['student_photo_name'] = existing_data.get('student_photo_name', '')

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

        EnrollmentSessionManager.save_student_data(request, form_data)
        EnrollmentSessionManager.set_lrn_verified(request, True)
        request.session['enrollment_type'] = primary_type

        messages.success(request, f'LRN {lrn} verified successfully! Please continue with Family Data.')
        return redirect('enrollment_app:family_data')

    # GET
    existing_data = EnrollmentSessionManager.get_student_data(request)
    return render(request, 'enrollment_app/studentData.html', {
        'form_data': existing_data or {},
        'school_year': SchoolYear.objects.filter(is_active=True).first(),
    })
    
    
from django.http import JsonResponse

def lookup_old_student(request):
    """
    AJAX endpoint — called when student types 12-digit LRN and selects 'Old Student'.
    Fetches existing StudentData + FamilyData from DB and saves both to session.
    Returns JSON for frontend to auto-fill the form fields.
    """
    from enrollment_app.models import Student, StudentData

    if request.method != 'GET':
        return JsonResponse({'found': False, 'message': 'Invalid request.'}, status=405)

    lrn = request.GET.get('lrn', '').strip()

    if not lrn or len(lrn) != 12 or not lrn.isdigit():
        return JsonResponse({'found': False, 'message': 'Invalid LRN format.'})

    try:
        student = Student.objects.select_related(
            'student_data',
            'family_data',
            'family_data__father',
            'family_data__mother',
            'family_data__other_guardian',
        ).get(lrn=lrn)

    except Student.DoesNotExist:
        return JsonResponse({
            'found': False,
            'message': 'No previous record found for this LRN.'
        })

    # ── StudentData ──────────────────────────────────────────────────
    try:
        sd = student.student_data
    except StudentData.DoesNotExist:
        return JsonResponse({
            'found': False,
            'message': 'LRN exists but no previous data found. Please fill in your details.'
        })

    student_form_data = {
        'lrn':                  lrn,
        'enrolling_as':         ['old'],
        'enrollment_type':      'old',
        'prefilled_from_db':    True,
        'last_name':            sd.last_name or '',
        'first_name':           sd.first_name or '',
        'middle_name':          sd.middle_name or '',
        'gender':               sd.gender or '',
        'date_of_birth':        str(sd.date_of_birth) if sd.date_of_birth else '',
        'place_of_birth':       sd.place_of_birth or '',
        'religion':             sd.religion or '',
        'dialect_spoken':       sd.dialect_spoken or '',
        'ethnic_tribe':         sd.ethnic_tribe or '',
        'address':              sd.address or '',
        'last_school_attended': sd.last_school_attended or '',
        'previous_grade_section': sd.previous_grade_section or '',
        'last_school_year':     sd.last_school_year or '',
        'is_sped':              sd.is_sped,
        'sped_details':         sd.sped_details or '',
        'is_working_student':   sd.is_working_student,
        'working_details':      sd.working_details or '',
        'student_photo_path':   sd.student_photo.name if sd.student_photo else '',
        'student_photo_name':   sd.student_photo.name.split('/')[-1] if sd.student_photo else '',
    }

    # ── FamilyData ───────────────────────────────────────────────────
    family_form_data = {}
    try:
        fd = student.family_data
        family_form_data['guardian_type']    = fd.official_guardian_type or ''
        family_form_data['prefilled_from_db'] = True

        if fd.father:
            family_form_data.update({
                'father_family_name':    fd.father.family_name or '',
                'father_first_name':     fd.father.first_name or '',
                'father_middle_name':    fd.father.middle_name or '',
                'father_dob':            str(fd.father.date_of_birth) if fd.father.date_of_birth else '',
                'father_occupation':     fd.father.occupation or '',
                'father_address':        fd.father.address or '',
                'father_contact_number': fd.father.contact_number or '',
                'father_email':          fd.father.email or '',
            })

        if fd.mother:
            family_form_data.update({
                'mother_family_name':    fd.mother.family_name or '',
                'mother_first_name':     fd.mother.first_name or '',
                'mother_middle_name':    fd.mother.middle_name or '',
                'mother_dob':            str(fd.mother.date_of_birth) if fd.mother.date_of_birth else '',
                'mother_occupation':     fd.mother.occupation or '',
                'mother_address':        fd.mother.address or '',
                'mother_contact_number': fd.mother.contact_number or '',
                'mother_email':          fd.mother.email or '',
            })

        if fd.other_guardian:
            family_form_data.update({
                'guardian_family_name':    fd.other_guardian.family_name or '',
                'guardian_first_name':     fd.other_guardian.first_name or '',
                'guardian_middle_name':    fd.other_guardian.middle_name or '',
                'guardian_dob':            str(fd.other_guardian.date_of_birth) if fd.other_guardian.date_of_birth else '',
                'guardian_occupation':     fd.other_guardian.occupation or '',
                'guardian_address':        fd.other_guardian.address or '',
                'guardian_relationship':   fd.other_guardian.relationship_to_student or '',
                'guardian_contact_number': fd.other_guardian.contact_number or '',
                'guardian_email':          fd.other_guardian.email or '',
            })

        if fd.parent_photo:
            family_form_data['parent_photo_path'] = fd.parent_photo.name
            family_form_data['parent_photo_name'] = fd.parent_photo.name.split('/')[-1]

    except Exception:
        pass  # No family data yet — student fills it fresh on family form

    # ── Save both to session now so Family Data page is pre-filled ───
    EnrollmentSessionManager.save_student_data(request, student_form_data)
    EnrollmentSessionManager.save_family_data(request, family_form_data)
    EnrollmentSessionManager.set_lrn_verified(request, True)
    request.session['enrollment_type'] = 'old'
    request.session.modified = True

    return JsonResponse({
        'found':        True,
        'student_data': student_form_data,
        'family_data':  family_form_data,
        'message':      f"Welcome back, {sd.first_name}! Your previous details have been pre-filled.",
    })