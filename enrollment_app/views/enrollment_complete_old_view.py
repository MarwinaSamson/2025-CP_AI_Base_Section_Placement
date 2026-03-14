"""
enrollment_complete_old_view.py
Handles the completion page for Old Students (no survey/academic/ML needed).
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from ..services.session_manager import EnrollmentSessionManager
from admin_app.models import SchoolYear
from ..models import Student, StudentEnrollment, StudentData, Parent, Guardian, FamilyData
import os
import uuid
import shutil
from django.conf import settings


def enrollment_complete_old(request):
    """
    Final step for OLD STUDENTS.
    Saves student + family data to the database, then clears session.
    """
    if not EnrollmentSessionManager.is_lrn_verified(request):
        messages.error(request, 'Please complete the Student Data form first.')
        return redirect('enrollment_app:student_data')

    student_data = EnrollmentSessionManager.get_student_data(request)
    family_data = EnrollmentSessionManager.get_family_data(request)

    if not student_data or not family_data:
        messages.error(request, 'Incomplete enrollment data. Please start again.')
        return redirect('enrollment_app:student_data')

    enrollment_type = request.session.get('enrollment_type', 'old')
    if enrollment_type != 'old':
        return redirect('enrollment_app:family_data')

    # Save to DB on GET (idempotent via update_or_create)
    try:
        student = _save_old_student_to_db(request, student_data, family_data)
        lrn = student_data.get('lrn', '')
        EnrollmentSessionManager.clear_all_enrollment_data(request)
        request.session.pop('enrollment_type', None)

        active_school_year = SchoolYear.objects.filter(is_active=True).first()
        return render(request, 'enrollment_app/enrollmentCompleteOld.html', {
            'student_data': student_data,
            'lrn': lrn,
            'school_year': active_school_year,
        })
    except Exception as e:
        messages.error(request, f'Error saving enrollment: {str(e)}')
        return redirect('enrollment_app:family_data')


def _save_old_student_to_db(request, student_data, family_data):
    """Save old student and family data to database."""
    from datetime import datetime

    lrn = student_data.get('lrn')
    if not lrn:
        raise ValueError("LRN not found in session data")

    school_year = SchoolYear.objects.filter(is_active=True).first()

    with transaction.atomic():
        guardian_type = family_data.get('guardian_type', 'mother')
        guardian_email = ''
        if guardian_type == 'father':
            guardian_email = family_data.get('father_email', '')
        elif guardian_type == 'mother':
            guardian_email = family_data.get('mother_email', '')
        elif guardian_type == 'other':
            guardian_email = family_data.get('guardian_email', '')

        student, _ = Student.objects.get_or_create(
            lrn=lrn,
            defaults={
                'email': guardian_email or '',
                'is_lis_verified': True,
                'lis_verified_at': timezone.now(),
            }
        )
        student.email = guardian_email or ''
        student.is_lis_verified = True
        student.lis_verified_at = timezone.now()
        student.save()

        # Create/get StudentEnrollment for this school year
        enrollment, _ = StudentEnrollment.objects.get_or_create(
            student=student,
            school_year=school_year,
            defaults={
                'enrollee_type': 'continuing',
                'enrollment_status': 'submitted',
            }
        )
        enrollment.enrollment_status = 'submitted'
        enrollment.save()

        # Parse DOB
        date_of_birth_value = student_data.get('date_of_birth')
        if isinstance(date_of_birth_value, str):
            try:
                date_of_birth_value = datetime.strptime(date_of_birth_value, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                date_of_birth_value = None

        # Handle student photo
        student_photo_path = student_data.get('student_photo_path', '')
        student_photo_file = None
        if student_photo_path and os.path.exists(student_photo_path):
            media_dir = os.path.join(settings.MEDIA_ROOT, 'student_photos')
            os.makedirs(media_dir, exist_ok=True)
            file_extension = os.path.splitext(student_photo_path)[1]
            new_filename = f"{uuid.uuid4().hex}{file_extension}"
            permanent_path = os.path.join(media_dir, new_filename)
            shutil.move(student_photo_path, permanent_path)
            student_photo_file = f"student_photos/{new_filename}"

        StudentData.objects.update_or_create(
            student=student,
            defaults={
                'last_name': (student_data.get('last_name', '') or '')[:100],
                'first_name': (student_data.get('first_name', '') or '')[:100],
                'middle_name': (student_data.get('middle_name', '') or '')[:100],
                'gender': student_data.get('gender', '')[:10],
                'date_of_birth': date_of_birth_value,
                'place_of_birth': (student_data.get('place_of_birth', '') or '')[:255],
                'religion': (student_data.get('religion', '') or '')[:100],
                'dialect_spoken': (student_data.get('dialect_spoken', '') or '')[:100],
                'ethnic_tribe': (student_data.get('ethnic_tribe', '') or '')[:100],
                'address': student_data.get('address', ''),
                'enrolling_as': student_data.get('enrolling_as', []),
                'is_sped': student_data.get('is_sped', False),
                'sped_details': student_data.get('sped_details', ''),
                'is_working_student': student_data.get('is_working_student', False),
                'working_details': student_data.get('working_details', ''),
                'last_school_attended': (student_data.get('last_school_attended', '') or '')[:255],
                'previous_grade_section': (student_data.get('previous_grade_section', '') or '')[:50],
                'last_school_year': (student_data.get('last_school_year', '') or '')[:20],
                **(({'student_photo': student_photo_file}) if student_photo_file else {}),
            }
        )

        # Save parents
        parents = {}
        for parent_type in ['father', 'mother']:
            fp = parent_type
            first_name = family_data.get(f'{fp}_first_name', '')
            family_name = family_data.get(f'{fp}_family_name', '')
            if first_name and family_name:
                dob = family_data.get(f'{fp}_dob')
                if isinstance(dob, str):
                    try:
                        dob = datetime.strptime(dob, '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        dob = None
                occupation = family_data.get(f'{fp}_occupation', '')
                contact = family_data.get(f'{fp}_contact_number', '').strip()[:20]
                if first_name and family_name and dob and occupation and contact:
                    try:
                        parent, _ = Parent.objects.get_or_create(
                            family_name=family_name, first_name=first_name,
                            date_of_birth=dob, parent_type=parent_type,
                            defaults={
                                'middle_name': family_data.get(f'{fp}_middle_name', '') or '',
                                'occupation': occupation,
                                'address': family_data.get(f'{fp}_address', ''),
                                'contact_number': contact,
                                'email': family_data.get(f'{fp}_email', '') or '',
                            }
                        )
                        parents[parent_type] = parent
                    except Exception as e:
                        print(f"Error creating {parent_type}: {e}")

        # Save other guardian if needed
        other_guardian = None
        if family_data.get('guardian_first_name') and family_data.get('guardian_family_name'):
            dob = family_data.get('guardian_dob')
            if isinstance(dob, str):
                try:
                    dob = datetime.strptime(dob, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    dob = None
            contact = family_data.get('guardian_contact_number', '').strip()[:20]
            if dob and contact:
                try:
                    other_guardian, _ = Guardian.objects.get_or_create(
                        family_name=family_data.get('guardian_family_name'),
                        first_name=family_data.get('guardian_first_name'),
                        date_of_birth=dob,
                        relationship_to_student=family_data.get('guardian_relationship', 'Guardian'),
                        defaults={
                            'middle_name': family_data.get('guardian_middle_name', '') or '',
                            'occupation': family_data.get('guardian_occupation', ''),
                            'address': family_data.get('guardian_address', ''),
                            'contact_number': contact,
                            'email': family_data.get('guardian_email', '') or '',
                        }
                    )
                except Exception as e:
                    print(f"Error creating other guardian: {e}")

        # Determine guardian record
        primary_type = family_data.get('guardian_type', 'mother')
        guardian_record = None
        if primary_type == 'father':
            guardian_record = parents.get('father')
        elif primary_type == 'mother':
            guardian_record = parents.get('mother')
        elif primary_type == 'other':
            guardian_record = other_guardian

        if guardian_record:
            parent_photo_path = family_data.get('parent_photo_path', '')
            parent_photo_file = None
            if parent_photo_path and os.path.exists(parent_photo_path):
                media_dir = os.path.join(settings.MEDIA_ROOT, 'parent_photos')
                os.makedirs(media_dir, exist_ok=True)
                file_extension = os.path.splitext(parent_photo_path)[1]
                new_filename = f"{uuid.uuid4().hex}{file_extension}"
                permanent_path = os.path.join(media_dir, new_filename)
                shutil.move(parent_photo_path, permanent_path)
                parent_photo_file = f"parent_photos/{new_filename}"

            FamilyData.objects.update_or_create(
                student=student,
                defaults={
                    'father': parents.get('father'),
                    'mother': parents.get('mother'),
                    'other_guardian': other_guardian if primary_type == 'other' else None,
                    'official_guardian_type': primary_type,
                    **(({'parent_photo': parent_photo_file}) if parent_photo_file else {}),
                }
            )

        # Update StudentEnrollment form completion flags (not Student)
        enrollment.family_data_completed = True
        enrollment.family_data_completed_at = timezone.now()
        enrollment.student_data_completed = True
        enrollment.student_data_completed_at = timezone.now()
        enrollment.save()

    return student