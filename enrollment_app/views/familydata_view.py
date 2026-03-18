


from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from admin_app.models import SchoolYear
import os
import uuid
from ..services.session_manager import EnrollmentSessionManager


def family_data_form(request):
    from enrollment_app.models import Student, FamilyData

    if not EnrollmentSessionManager.is_lrn_verified(request):
        messages.error(request, 'Please complete the Student Data form first.')
        return redirect('enrollment_app:student_data')

    student_data = EnrollmentSessionManager.get_student_data(request)
    existing_family_data = EnrollmentSessionManager.get_family_data(request) or {}

    enrollment_type = (
        request.session.get('enrollment_type')
        or (student_data.get('enrollment_type') if student_data else None)
        or 'new'
    )

    # ── OLD STUDENT: Pre-fill family data from DB if not already in session ──
    if enrollment_type == 'old' and not existing_family_data:
        lrn = student_data.get('lrn') if student_data else None
        if lrn:
            try:
                fd = FamilyData.objects.select_related(
                    'father', 'mother', 'other_guardian'
                ).get(student__lrn=lrn)

                prefilled_family = {
                    'guardian_type': fd.official_guardian_type or '',
                }

                # Father
                if fd.father:
                    prefilled_family.update({
                        'father_family_name':    fd.father.family_name or '',
                        'father_first_name':     fd.father.first_name or '',
                        'father_middle_name':    fd.father.middle_name or '',
                        'father_dob':            str(fd.father.date_of_birth) if fd.father.date_of_birth else '',
                        'father_occupation':     fd.father.occupation or '',
                        'father_address':        fd.father.address or '',
                        'father_contact_number': fd.father.contact_number or '',
                        'father_email':          fd.father.email or '',
                    })

                # Mother
                if fd.mother:
                    prefilled_family.update({
                        'mother_family_name':    fd.mother.family_name or '',
                        'mother_first_name':     fd.mother.first_name or '',
                        'mother_middle_name':    fd.mother.middle_name or '',
                        'mother_dob':            str(fd.mother.date_of_birth) if fd.mother.date_of_birth else '',
                        'mother_occupation':     fd.mother.occupation or '',
                        'mother_address':        fd.mother.address or '',
                        'mother_contact_number': fd.mother.contact_number or '',
                        'mother_email':          fd.mother.email or '',
                    })

                # Other guardian
                if fd.other_guardian:
                    prefilled_family.update({
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

                # Preserve existing parent photo
                if fd.parent_photo:
                    prefilled_family['parent_photo_path'] = fd.parent_photo.name
                    prefilled_family['parent_photo_name'] = fd.parent_photo.name.split('/')[-1]

                prefilled_family['prefilled_from_db'] = True
                existing_family_data = prefilled_family
                EnrollmentSessionManager.save_family_data(request, prefilled_family)

            except FamilyData.DoesNotExist:
                pass  # No previous family data — student fills it fresh

    if request.method == 'POST':
        family_data = {
            'father_family_name':    request.POST.get('father_family_name', ''),
            'father_first_name':     request.POST.get('father_first_name', ''),
            'father_middle_name':    request.POST.get('father_middle_name', ''),
            'father_dob':            request.POST.get('father_dob', ''),
            'father_occupation':     request.POST.get('father_occupation', ''),
            'father_address':        request.POST.get('father_address', ''),
            'father_contact_number': request.POST.get('father_contact_number', ''),
            'father_email':          request.POST.get('father_email', ''),

            'mother_family_name':    request.POST.get('mother_family_name', ''),
            'mother_first_name':     request.POST.get('mother_first_name', ''),
            'mother_middle_name':    request.POST.get('mother_middle_name', ''),
            'mother_dob':            request.POST.get('mother_dob', ''),
            'mother_occupation':     request.POST.get('mother_occupation', ''),
            'mother_address':        request.POST.get('mother_address', ''),
            'mother_contact_number': request.POST.get('mother_contact_number', ''),
            'mother_email':          request.POST.get('mother_email', ''),

            'guardian_type':           request.POST.get('guardian_type', ''),
            'guardian_family_name':    request.POST.get('guardian_family_name', ''),
            'guardian_first_name':     request.POST.get('guardian_first_name', ''),
            'guardian_middle_name':    request.POST.get('guardian_middle_name', ''),
            'guardian_dob':            request.POST.get('guardian_dob', ''),
            'guardian_occupation':     request.POST.get('guardian_occupation', ''),
            'guardian_address':        request.POST.get('guardian_address', ''),
            'guardian_relationship':   request.POST.get('guardian_relationship', ''),
            'guardian_contact_number': request.POST.get('guardian_contact_number', ''),
            'guardian_email':          request.POST.get('guardian_email', ''),
        }

        # Preserve existing photo data from session
        family_data['parent_photo_path'] = existing_family_data.get('parent_photo_path', '')
        family_data['parent_photo_name'] = existing_family_data.get('parent_photo_name', '')

        # Handle parent photo upload
        if 'parent_photo' in request.FILES:
            photo = request.FILES['parent_photo']
            temp_dir = os.path.join(settings.BASE_DIR, 'temp_uploads')
            os.makedirs(temp_dir, exist_ok=True)
            file_extension = os.path.splitext(photo.name)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            temp_file_path = os.path.join(temp_dir, unique_filename)
            with open(temp_file_path, 'wb+') as destination:
                for chunk in photo.chunks():
                    destination.write(chunk)
            family_data['parent_photo_path'] = temp_file_path
            family_data['parent_photo_name'] = photo.name

        # Validate guardian selection
        if not family_data['guardian_type']:
            messages.error(request, "Please select who will be the student's official guardian.")
            return render(request, 'enrollment_app/familyData.html', {
                'form_data': {**family_data, 'prefilled_from_db': existing_family_data.get('prefilled_from_db', False)},
                'student_info': student_data,
                'school_year': SchoolYear.objects.filter(is_active=True).first(),
                'enrollment_type': enrollment_type,
            })

        # Validate other guardian fields if needed
        if family_data['guardian_type'] == 'other':
            required_guardian_fields = [
                'guardian_family_name', 'guardian_first_name', 'guardian_dob',
                'guardian_occupation', 'guardian_address', 'guardian_relationship',
                'guardian_contact_number'
            ]
            missing_fields = [f for f in required_guardian_fields if not family_data.get(f)]
            if missing_fields:
                messages.error(request, 'Please fill in all required guardian information fields.')
                return render(request, 'enrollment_app/familyData.html', {
                    'form_data': {**family_data, 'prefilled_from_db': existing_family_data.get('prefilled_from_db', False)},
                    'student_info': student_data,
                    'school_year': SchoolYear.objects.filter(is_active=True).first(),
                    'enrollment_type': enrollment_type,
                })

        # Save to session
        EnrollmentSessionManager.save_family_data(request, family_data)

        if enrollment_type == 'old':
            # Use PRG pattern — clear success message after redirect
            # Don't add message here; let enrollment_complete_old render the success page directly
            return redirect('enrollment_app:enrollment_complete_old')
        elif enrollment_type == 'transferee':
            messages.success(request, 'Family data saved. Please upload your required documents.')
            return redirect('enrollment_app:transferee_documents')
        else:
            messages.success(request, 'Family data saved successfully! Please continue with the survey.')
            return redirect('enrollment_app:non_academic')

    # GET
    return render(request, 'enrollment_app/familyData.html', {
        'form_data': existing_family_data,
        'student_info': student_data,
        'school_year': SchoolYear.objects.filter(is_active=True).first(),
        'enrollment_type': enrollment_type,
    })