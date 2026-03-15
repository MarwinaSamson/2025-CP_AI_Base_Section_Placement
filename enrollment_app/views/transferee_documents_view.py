"""
transferee_documents_view.py
Handles document submission for Transferee students.
Shows required documents, allows upload, then saves everything to DB.
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from ..services.session_manager import EnrollmentSessionManager
from admin_app.models import SchoolYear, DocumentRequirement
from ..models import Student, StudentDocumentSubmission
import os
import uuid
from django.conf import settings
from datetime import datetime


def transferee_documents(request):
    """
    Document submission page for transferee students.
    Requires student + family data to be in session.
    On successful submission, saves all data to DB and clears session.
    """
    if not EnrollmentSessionManager.is_lrn_verified(request):
        messages.error(request, 'Please complete the Student Data form first.')
        return redirect('enrollment_app:student_data')

    student_data = EnrollmentSessionManager.get_student_data(request)
    family_data = EnrollmentSessionManager.get_family_data(request)

    if not student_data:
        messages.error(request, 'Please complete the Student Data form first.')
        return redirect('enrollment_app:student_data')

    if not family_data:
        messages.error(request, 'Please complete the Family Data form first.')
        return redirect('enrollment_app:family_data')

    enrollment_type = request.session.get('enrollment_type', 'transferee')
    if enrollment_type != 'transferee':
        return redirect('enrollment_app:family_data')

    active_school_year = SchoolYear.objects.filter(is_active=True).first()

    # DEBUG: Log the student data to see what we're working with
    print(f"\n{'='*80}")
    print(f"TRANSFEREE_DOCUMENTS VIEW - DEBUG INFO")
    print(f"{'='*80}")
    print(f"LRN: {student_data.get('lrn', 'NONE')}")
    print(f"Enrollment Type: {enrollment_type}")
    print(f"Transferee Grade Level: {student_data.get('transferee_grade_level', 'NOT SET')}")
    print(f"Previous Program: {student_data.get('previous_program', 'NOT SET')}")
    print(f"Last School Attended: {student_data.get('last_school_attended', 'NOT SET')}")
    print(f"Active School Year: {active_school_year}")
    print(f"{'='*80}\n")

    # Get document requirements
    requirements = []
    if active_school_year:
        requirements = list(
            DocumentRequirement.objects.filter(
                school_year=active_school_year,
                is_active=True
            ).order_by('order', 'name').values(
                'id', 'name', 'description', 'requirement_type',
                'file_format', 'max_file_size_mb'
            )
        )
        for req in requirements:
            if req.get('file_format'):
                formats = [f'.{fmt.strip()}' for fmt in req['file_format'].split(',')]
                req['file_format_accept'] = ','.join(formats)
            else:
                req['file_format_accept'] = ''

    existing_docs = EnrollmentSessionManager.get_academic_data(request) or {}
    document_submissions = existing_docs.get('document_submissions', {})

    if request.method == 'POST':
        # Handle document uploads
        for key in request.FILES:
            if key.startswith('document_'):
                req_id = key.replace('document_', '')
                uploaded_file = request.FILES[key]

                temp_dir = os.path.join(settings.BASE_DIR, 'temp_uploads')
                os.makedirs(temp_dir, exist_ok=True)

                file_extension = os.path.splitext(uploaded_file.name)[1]
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                temp_file_path = os.path.join(temp_dir, unique_filename)

                with open(temp_file_path, 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)

                document_submissions[req_id] = {
                    'requirement_id': req_id,
                    'file_path': temp_file_path,
                    'file_name': uploaded_file.name,
                    'file_size': uploaded_file.size,
                    'file_format': file_extension.lstrip('.').lower(),
                    'uploaded_at': datetime.now().isoformat(),
                }

        # Check mandatory requirements are uploaded
        mandatory_ids = [str(r['id']) for r in requirements if r['requirement_type'] == 'mandatory']
        missing_mandatory = [
            r['name'] for r in requirements
            if r['requirement_type'] == 'mandatory'
            and str(r['id']) not in document_submissions
        ]

        if missing_mandatory:
            # Save what we have so far
            existing_docs['document_submissions'] = document_submissions
            EnrollmentSessionManager.save_academic_data(request, existing_docs)
            messages.error(
                request,
                f'Please upload the following required documents: {", ".join(missing_mandatory)}'
            )
            return render(request, 'enrollment_app/transfereeDocuments.html', {
                'student_info': student_data,
                'school_year': active_school_year,
                'requirements': requirements,
                'document_submissions': document_submissions,
                'enrollment_type': enrollment_type,
            })

        # Save docs to session
        existing_docs['document_submissions'] = document_submissions
        EnrollmentSessionManager.save_academic_data(request, existing_docs)

        # Save everything to DB
        try:
            from .enrollment_complete_old_view import _save_old_student_to_db
            from ..services.transferee_service import create_transferee_enrollment
            from admin_app.models import GradeLevel
            
            # Step 1: Create base student record
            student = _save_old_student_to_db(request, student_data, family_data)
            
            # Step 2: Get transferee enrollment details
            lrn = student_data.get('lrn', '')
            grade_level_num = student_data.get('transferee_grade_level', '')
            previous_program = student_data.get('previous_program', 'REGULAR')
            last_school = student_data.get('last_school_attended', '')
            
            print(f"\n{'='*80}")
            print(f"SERVICE CALL DEBUG")
            print(f"{'='*80}")
            print(f"LRN: {lrn}")
            print(f"Grade Level Num: {grade_level_num}")
            print(f"Previous Program: {previous_program}")
            print(f"Last School: {last_school}")
            print(f"Active School Year: {active_school_year}")
            print(f"Condition Check: grade_level_num={bool(grade_level_num)}, lrn={bool(lrn)}, active_sy={bool(active_school_year)}")
            
            # Step 3: Call the transferee service BEFORE saving documents
            # This ensures ProgramSelection exists and enrollment is marked properly
            if grade_level_num and lrn and active_school_year:
                print(f"✓ All conditions met, attempting service call...")
                try:
                    # Convert grade number (7,8,9,10) to GradeLevel code (G7, G8, G9, G10)
                    grade_code = f'G{grade_level_num}'
                    grade_level = GradeLevel.objects.get(code=grade_code)
                    print(f"✓ Grade Level found: {grade_level} (code={grade_code})")
                    create_transferee_enrollment(
                        student_lrn=lrn,
                        new_school_year=active_school_year,
                        grade_level=grade_level,
                        last_school_attended=last_school,
                        selected_program_code=previous_program
                    )
                    print(f"✓ Transferee service called for LRN {lrn}")
                except GradeLevel.DoesNotExist:
                    print(f"✗ Warning: GradeLevel {grade_level_num} not found")
                except Exception as e:
                    print(f"✗ Warning: Transferee service failed: {str(e)}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"✗ Conditions NOT met for service call - skipping")
                if not grade_level_num:
                    print(f"   - grade_level_num is empty")
                if not lrn:
                    print(f"   - lrn is empty")
                if not active_school_year:
                    print(f"   - active_school_year is None")
            print(f"{'='*80}\n")
            
            # Step 4: Now save documents with the school_year
            _save_transferee_documents(student, document_submissions, active_school_year)

            lrn = student_data.get('lrn', '')
            EnrollmentSessionManager.clear_all_enrollment_data(request)
            request.session.pop('enrollment_type', None)

            messages.success(request, 'Documents submitted successfully! Your enrollment has been submitted for review.')
            return render(request, 'enrollment_app/transfereeComplete.html', {
                'student_data': student_data,
                'lrn': lrn,
                'school_year': active_school_year,
                'transferee_grade_level': student_data.get('transferee_grade_level', ''),
                'documents_submitted': len(document_submissions),
            })
        except Exception as e:
            messages.error(request, f'Error saving enrollment: {str(e)}')
            return redirect('enrollment_app:transferee_documents')

    return render(request, 'enrollment_app/transfereeDocuments.html', {
        'student_info': student_data,
        'school_year': active_school_year,
        'requirements': requirements,
        'document_submissions': document_submissions,
        'enrollment_type': enrollment_type,
    })


def _save_transferee_documents(student, document_submissions, school_year=None):
    """
    Save uploaded transferee documents to the database.
    
    Args:
        student: Student instance
        document_submissions: dict of document data
        school_year: SchoolYear instance (required for unique_together constraint)
    """
    from django.core.files import File

    for req_id, doc_info in document_submissions.items():
        try:
            requirement = DocumentRequirement.objects.get(id=req_id)
            temp_file_path = doc_info['file_path']
            if os.path.exists(temp_file_path):
                with open(temp_file_path, 'rb') as temp_file:
                    submission, _ = StudentDocumentSubmission.objects.update_or_create(
                        student=student,
                        requirement=requirement,
                        school_year=school_year,
                        defaults={
                            'file_name': doc_info['file_name'],
                            'file_size': doc_info['file_size'],
                            'file_format': doc_info['file_format'],
                            'status': 'pending',
                        }
                    )
                    submission.document_file.save(
                        doc_info['file_name'],
                        File(temp_file),
                        save=True
                    )
                try:
                    os.remove(temp_file_path)
                except Exception as e:
                    print(f"Warning: Could not delete temp file: {e}")
        except DocumentRequirement.DoesNotExist:
            print(f"Warning: DocumentRequirement {req_id} not found")
        except Exception as e:
            print(f"Error saving document {req_id}: {e}")