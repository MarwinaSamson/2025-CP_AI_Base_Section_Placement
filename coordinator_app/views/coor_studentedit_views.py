from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import json

from enrollment_app.models import (
    Student, StudentData, FamilyData, Parent, Guardian,
    SurveyData, AcademicData, ProgramSelection, StudentDocumentSubmission, EnrollmentStatusLog, StudentEnrollment
)
from admin_app.models import Program, SchoolYear, Section, DocumentRequirement
from coordinator_app.models import CoordinatorActivityLog


@login_required
def student_edit(request, student_id):
    """Main view for student edit page"""
    student = get_object_or_404(Student, lrn=student_id)
    
    # Get coordinator info
    user_profile = getattr(request.user, 'profile', None)
    program_code = user_profile.program.code if user_profile and user_profile.program else None
    user_full_name = request.user.get_full_name() or request.user.username
    user_type = f"{program_code} Coordinator" if program_code else "Coordinator"
    user_photo = user_profile.photo.url if user_profile and user_profile.photo else None
    
    # Generate initials
    name_parts = user_full_name.split()
    user_initials = ''.join([part[0].upper() for part in name_parts[:2]]) if name_parts else 'CO'
    
    # Get all school years for the filter
    school_years = SchoolYear.objects.all().order_by('-year_label')
    active_school_year = SchoolYear.objects.filter(is_active=True).first()
    
    # SECURITY: Only show the coordinator's own program (no dropdown)
    # Verify that the student's program selection matches coordinator's program
    program_selection = ProgramSelection.objects.filter(student=student).first()
    if program_selection and program_code:
        if program_selection.selected_program_code != program_code:
            # Student is not in this coordinator's program - deny access
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("You do not have permission to view this student.")
    
    # Only get the coordinator's own program
    programs = Program.objects.filter(code=program_code) if program_code else Program.objects.none()
    
    # Get document requirements for the active school year (not deprecated student.school_year)
    document_requirements = []
    target_school_year = active_school_year or SchoolYear.objects.order_by('-start_date').first()
    if target_school_year:
        document_requirements = DocumentRequirement.objects.filter(
            school_year=target_school_year,
            is_active=True
        ).order_by('order', 'name')
    
    # Get student's submitted documents
    submitted_documents = StudentDocumentSubmission.objects.filter(
        student=student
    ).select_related('requirement')
    
    # Create a map of requirement_id to submission status
    submitted_docs_map = {
        doc.requirement.id: doc.status for doc in submitted_documents
    }
    
    # Coordinators can edit
    is_readonly = False
    
    context = {
        'student': student,
        'student_id': student_id,
        'school_years': school_years,
        'active_school_year': active_school_year,
        'programs': programs,
        'is_readonly': is_readonly,
        'document_requirements': document_requirements,
        'submitted_docs_map': submitted_docs_map,
        'user_full_name': user_full_name,
        'user_type': user_type,
        'user_photo': user_photo,
        'user_initials': user_initials,
        'program_code': program_code,
    }
    
    return render(request, 'coordinator_app/studentEdit.html', context)


@login_required
@require_http_methods(["GET"])
def get_student_details(request, student_id):
    """API endpoint to fetch all student details"""
    import logging
    import traceback
    logger = logging.getLogger(__name__)
    
    try:
        student = get_object_or_404(Student, lrn=student_id)
        
        # Prepare response data
        data = {
            'student': {
                'lrn': student.lrn,
                'email': student.email,
                'enrollment_status': student.enrollment_status,
                'school_year': student.school_year.year_label if student.school_year else None,
                'is_lis_verified': student.is_lis_verified,
                'created_at': student.created_at.strftime('%Y-%m-%d'),
            }
        }
        
        # Student Data
        if hasattr(student, 'student_data'):
            sd = student.student_data
            data['student_data'] = {
                'last_name': sd.last_name or '',
                'first_name': sd.first_name or '',
                'middle_name': sd.middle_name or '',
                'gender': sd.gender or '',
                'date_of_birth': sd.date_of_birth.strftime('%Y-%m-%d') if sd.date_of_birth else '',
                'place_of_birth': sd.place_of_birth or '',
                'religion': sd.religion or '',
                'dialect_spoken': sd.dialect_spoken or '',
                'ethnic_tribe': sd.ethnic_tribe or '',
                'address': sd.address or '',
                'enrolling_as': sd.enrolling_as or '',
                'is_sped': sd.is_sped,
                'sped_details': sd.sped_details or '',
                'is_working_student': sd.is_working_student,
                'working_details': sd.working_details or '',
                'last_school_attended': sd.last_school_attended or '',
                'previous_grade_section': sd.previous_grade_section or '',
                'last_school_year': sd.last_school_year or '',
                'student_photo': sd.student_photo.url if sd.student_photo else None,
                'age': sd.age,
                'full_name': sd.full_name,
                'transferee_grade_level': sd.transferee_grade_level or '',
                'previous_program': sd.previous_program or '',
                'coordinator_selected_track': sd.coordinator_selected_track or '',
            }
        else:
            data['student_data'] = None
        
        # Family Data
        if hasattr(student, 'family_data'):
            fd = student.family_data
            
            # Father's information
            if fd.father:
                try:
                    data['father'] = {
                        'id': fd.father.id,
                        'family_name': fd.father.family_name or '',
                        'first_name': fd.father.first_name or '',
                        'middle_name': fd.father.middle_name or '',
                        'date_of_birth': fd.father.date_of_birth.strftime('%Y-%m-%d') if fd.father.date_of_birth else '',
                        'occupation': fd.father.occupation or '',
                        'address': fd.father.address or '',
                        'contact_number': fd.father.contact_number or '',
                        'email': fd.father.email or '',
                        'age': fd.father.age if fd.father.date_of_birth else None,
                        'full_name': fd.father.full_name,
                    }
                except Exception as e_father:
                    logger.warning(f"Error accessing father data for student {student_id}: {str(e_father)}")
                    data['father'] = {'error': str(e_father)}
            else:
                data['father'] = None
            
            # Mother's information
            if fd.mother:
                try:
                    data['mother'] = {
                        'id': fd.mother.id,
                        'family_name': fd.mother.family_name or '',
                        'first_name': fd.mother.first_name or '',
                        'middle_name': fd.mother.middle_name or '',
                        'date_of_birth': fd.mother.date_of_birth.strftime('%Y-%m-%d') if fd.mother.date_of_birth else '',
                        'occupation': fd.mother.occupation or '',
                        'address': fd.mother.address or '',
                        'contact_number': fd.mother.contact_number or '',
                        'email': fd.mother.email or '',
                        'age': fd.mother.age if fd.mother.date_of_birth else None,
                        'full_name': fd.mother.full_name,
                    }
                except Exception as e_mother:
                    logger.warning(f"Error accessing mother data for student {student_id}: {str(e_mother)}")
                    data['mother'] = {'error': str(e_mother)}
            else:
                data['mother'] = None
            
            # Guardian information
            data['guardian'] = {
                'official_guardian_type': fd.official_guardian_type,
            }
            
            if fd.other_guardian:
                try:
                    data['guardian']['other_guardian'] = {
                        'id': fd.other_guardian.id,
                        'family_name': fd.other_guardian.family_name or '',
                        'first_name': fd.other_guardian.first_name or '',
                        'middle_name': fd.other_guardian.middle_name or '',
                        'date_of_birth': fd.other_guardian.date_of_birth.strftime('%Y-%m-%d') if fd.other_guardian.date_of_birth else '',
                        'occupation': fd.other_guardian.occupation or '',
                        'address': fd.other_guardian.address or '',
                        'contact_number': fd.other_guardian.contact_number or '',
                        'email': fd.other_guardian.email or '',
                        'relationship_to_student': fd.other_guardian.relationship_to_student or '',
                        'age': fd.other_guardian.age if fd.other_guardian.date_of_birth else None,
                        'full_name': fd.other_guardian.full_name,
                    }
                except Exception as e_guardian:
                    logger.warning(f"Error accessing guardian data for student {student_id}: {str(e_guardian)}")
                    data['guardian']['other_guardian'] = {'error': str(e_guardian)}
            else:
                data['guardian']['other_guardian'] = None
            
            try:
                data['guardian']['parent_photo'] = fd.parent_photo.url if fd.parent_photo else None
            except Exception as e_photo:
                logger.warning(f"Error accessing parent photo for student {student_id}: {str(e_photo)}")
                data['guardian']['parent_photo'] = None
        else:
            data['father'] = None
            data['mother'] = None
            data['guardian'] = None
        
        # Survey Data
        if hasattr(student, 'survey_data'):
            try:
                survey = student.survey_data
                data['survey_data'] = {
                    'student_name': survey.student_name or '',
                    'age': survey.age,
                    'current_grade_section': survey.current_grade_section or '',
                    'residence_barangay': survey.residence_barangay or '',
                    'gender': survey.gender or '',
                    'learning_style': survey.learning_style or '',
                    'study_hours': survey.study_hours or '',
                    'study_environment': survey.study_environment or '',
                    'schoolwork_support': survey.schoolwork_support or '',
                    'enjoyed_subjects': survey.enjoyed_subjects if survey.enjoyed_subjects else [],
                    'interested_program': survey.interested_program or '',
                    'program_motivation': survey.program_motivation or '',
                    'enjoyed_activities': survey.enjoyed_activities if survey.enjoyed_activities else [],
                    'enjoyed_activities_other': survey.enjoyed_activities_other or '',
                    'assignments_on_time': survey.assignments_on_time or '',
                    'handle_difficult_lessons': survey.handle_difficult_lessons or '',
                    'device_availability': survey.device_availability or '',
                    'internet_access': survey.internet_access or '',
                    'absences': survey.absences or '',
                    'absence_reason': survey.absence_reason or '',
                    'participation': survey.participation or '',
                    'difficulty_areas': survey.difficulty_areas if survey.difficulty_areas else [],
                    'extra_support': survey.extra_support or '',
                    'quiet_place': survey.quiet_place or '',
                    'distance_from_school': survey.distance_from_school or '',
                    'travel_difficulty': survey.travel_difficulty or '',
                }
            except Exception as e_survey:
                logger.warning(f"Error accessing survey data for student {student_id}: {str(e_survey)}")
                data['survey_data'] = {'error': str(e_survey)}
        else:
            data['survey_data'] = None
        
        # Academic Data
        if hasattr(student, 'academic_data'):
            try:
                acad = student.academic_data
                data['academic_data'] = {
                    'dost_exam_result': acad.dost_exam_result or '',
                    'mathematics': float(acad.mathematics) if acad.mathematics else None,
                    'araling_panlipunan': float(acad.araling_panlipunan) if acad.araling_panlipunan else None,
                    'english': float(acad.english) if acad.english else None,
                    'edukasyon_sa_pagpapakatao': float(acad.edukasyon_sa_pagpapakatao) if acad.edukasyon_sa_pagpapakatao else None,
                    'science': float(acad.science) if acad.science else None,
                    'edukasyon_pangkabuhayan': float(acad.edukasyon_pangkabuhayan) if acad.edukasyon_pangkabuhayan else None,
                    'filipino': float(acad.filipino) if acad.filipino else None,
                    'mapeh': float(acad.mapeh) if acad.mapeh else None,
                    'report_card': acad.report_card.url if (hasattr(acad, 'report_card') and acad.report_card) else None,
                    'is_working_student': acad.is_working_student,
                    'working_type': acad.working_type or '',
                    'is_pwd': acad.is_pwd,
                    'disability_type': acad.disability_type or '',
                    'overall_average': float(acad.overall_average) if acad.overall_average else None,
                }
            except Exception as e_acad:
                logger.warning(f"Error accessing academic data for student {student_id}: {str(e_acad)}")
                data['academic_data'] = {'error': str(e_acad)}
        else:
            data['academic_data'] = None
        
        # Program Selection
        if hasattr(student, 'program_selection'):
            prog = student.program_selection

            # For continuing students, look up their prior assigned section name
            # from the CoordinatorActivityLog (logged at approval time each SY)
            suggested_section_name = None
            student_data = getattr(student, 'student_data', None)
            is_continuing = (student.enrollee_type == 'continuing' or 
                           (student_data and 'continuing' in (student_data.enrolling_as or [])))
            if is_continuing:
                from coordinator_app.models import CoordinatorActivityLog
                prior_log = CoordinatorActivityLog.objects.filter(
                    student_lrn=student.lrn,
                    action='student_approved',
                ).order_by('-created_at').first()
                if prior_log and prior_log.section_name:
                    suggested_section_name = prior_log.section_name

            # Serialize assigned section if present
            assigned_section_data = None
            if prog.assigned_section:
                try:
                    assigned_section_data = {
                        'id': prog.assigned_section.id,
                        'name': prog.assigned_section.name,
                        'program_code': prog.assigned_section.program.code if prog.assigned_section.program else None,
                        'grade_level': prog.assigned_section.grade_level.code if prog.assigned_section.grade_level else None,
                        'regular_track': prog.assigned_section.regular_track if hasattr(prog.assigned_section, 'regular_track') else None,
                    }
                except Exception as e_section:
                    logger.warning(f"Error serializing section data for student {student_id}: {str(e_section)}")
                    assigned_section_data = {'name': str(prog.assigned_section)}

            data['program_selection'] = {
                'selected_program_code': prog.selected_program_code,
                'program_description': prog.program_description,
                'selection_reason': prog.selection_reason or '',
                'admin_approved': prog.admin_approved,
                'admin_notes': prog.admin_notes or '',
                'approved_by': prog.approved_by or '',
                'assigned_section': assigned_section_data,
                # Phase 5: continuing student suggestion
                'enrollee_type': student.enrollee_type or '',
                'suggested_section_name': suggested_section_name,
            }
        else:
            data['program_selection'] = None
        
        return JsonResponse({'success': True, 'data': data})
        
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        error_msg = f"Error in get_student_details for student {student_id}: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        print(f"[ERROR] {error_msg}")
        return JsonResponse({'success': False, 'error': str(e), 'detailed_error': error_msg}, status=500)


@login_required
@require_http_methods(["POST"])
def update_student_data(request, student_id):
    """API endpoint to update student information"""
    try:
        with transaction.atomic():
            student = get_object_or_404(Student, lrn=student_id)
            data = json.loads(request.body)
            
            # Update Student basic info
            if 'email' in data:
                student.email = data['email']
                student.save()
            
            # Update StudentData
            student_data, created = StudentData.objects.get_or_create(student=student)
            
            # Update fields
            for field in ['last_name', 'first_name', 'middle_name', 'gender', 
                          'date_of_birth', 'place_of_birth', 'religion', 
                          'dialect_spoken', 'ethnic_tribe', 'address',
                          'last_school_attended', 'previous_grade_section', 
                          'last_school_year', 'sped_details', 'working_details',
                          'enrolling_as', 'transferee_grade_level', 'previous_program']:
                if field in data:
                    setattr(student_data, field, data[field])
            
            # Boolean fields
            if 'is_sped' in data:
                student_data.is_sped = data['is_sped'] == 'yes'
            if 'is_working' in data:
                student_data.is_working_student = data['is_working'] == 'yes'
            
            student_data.save()
            
            return JsonResponse({'success': True, 'message': 'Student data updated successfully'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def update_family_data(request, student_id):
    """API endpoint to update family/guardian information"""
    try:
        with transaction.atomic():
            student = get_object_or_404(Student, lrn=student_id)
            data = json.loads(request.body)
            
            family_data, created = FamilyData.objects.get_or_create(student=student)
            
            # Update Father
            if any(k.startswith('father_') for k in data.keys()):
                if family_data.father:
                    father = family_data.father
                else:
                    father = Parent(parent_type='father')
                
                father_map = {
                    'father_family_name': 'family_name',
                    'father_first_name': 'first_name',
                    'father_middle_name': 'middle_name',
                    'father_date_of_birth': 'date_of_birth',
                    'father_occupation': 'occupation',
                    'father_contact_number': 'contact_number',
                    'father_email': 'email',
                }
                
                for form_field, model_field in father_map.items():
                    if form_field in data:
                        setattr(father, model_field, data[form_field])
                
                father.save()
                family_data.father = father
            
            # Update Mother
            if any(k.startswith('mother_') for k in data.keys()):
                if family_data.mother:
                    mother = family_data.mother
                else:
                    mother = Parent(parent_type='mother')
                
                mother_map = {
                    'mother_family_name': 'family_name',
                    'mother_first_name': 'first_name',
                    'mother_middle_name': 'middle_name',
                    'mother_date_of_birth': 'date_of_birth',
                    'mother_occupation': 'occupation',
                    'mother_contact_number': 'contact_number',
                    'mother_email': 'email',
                }
                
                for form_field, model_field in mother_map.items():
                    if form_field in data:
                        setattr(mother, model_field, data[form_field])
                
                mother.save()
                family_data.mother = mother
            
            # Update Guardian
            if any(k.startswith('guardian_') for k in data.keys()):
                if family_data.other_guardian:
                    guardian = family_data.other_guardian
                else:
                    guardian = Guardian()
                
                guardian_map = {
                    'guardian_family_name': 'family_name',
                    'guardian_first_name': 'first_name',
                    'guardian_middle_name': 'middle_name',
                    'guardian_date_of_birth': 'date_of_birth',
                    'guardian_occupation': 'occupation',
                    'guardian_address': 'address',
                    'guardian_contact_number': 'contact_number',
                    'guardian_email': 'email',
                    'guardian_relationship': 'relationship_to_student',
                }
                
                for form_field, model_field in guardian_map.items():
                    if form_field in data:
                        setattr(guardian, model_field, data[form_field])
                
                guardian.save()
                family_data.other_guardian = guardian
                family_data.official_guardian_type = 'other'
            
            family_data.save()
            
            return JsonResponse({'success': True, 'message': 'Family data updated successfully'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def update_survey_data(request, student_id):
    """API endpoint to update survey/non-academic profile"""
    try:
        student = get_object_or_404(Student, lrn=student_id)
        data = json.loads(request.body)
        
        survey_data, created = SurveyData.objects.get_or_create(student=student)
        
        # Update all survey fields (these are read-only but keeping the endpoint)
        for field in ['student_name', 'age', 'current_grade_section', 
                      'residence_barangay', 'gender', 'learning_style', 
                      'study_hours', 'study_environment', 'schoolwork_support',
                      'interested_program', 'program_motivation', 
                      'enjoyed_activities_other', 'assignments_on_time',
                      'handle_difficult_lessons', 'device_availability',
                      'internet_access', 'absences', 'absence_reason',
                      'participation', 'extra_support', 'quiet_place',
                      'distance_from_school', 'travel_difficulty']:
            if field in data:
                setattr(survey_data, field, data[field])
        
        survey_data.save()
        
        return JsonResponse({'success': True, 'message': 'Survey data updated successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def update_academic_data(request, student_id):
    """API endpoint to update academic information and grades"""
    try:
        student = get_object_or_404(Student, lrn=student_id)
        data = json.loads(request.body)
        
        academic_data, created = AcademicData.objects.get_or_create(student=student)
        
        # Update DOST result
        if 'dost_exam_result' in data:
            academic_data.dost_exam_result = data['dost_exam_result']
        
        # Update grades - map form field names to model field names
        grade_map = {
            'grade_mathematics': 'mathematics',
            'grade_araling_panlipunan': 'araling_panlipunan',
            'grade_english': 'english',
            'grade_edukasyon_sa_pagpapakatao': 'edukasyon_sa_pagpapakatao',
            'grade_science': 'science',
            'grade_edukasyon_pangkabuhayan': 'edukasyon_pangkabuhayan',
            'grade_filipino': 'filipino',
            'grade_mapeh': 'mapeh',
        }
        
        for form_field, model_field in grade_map.items():
            if form_field in data and data[form_field]:
                setattr(academic_data, model_field, Decimal(str(data[form_field])))
        
        academic_data.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Academic data updated successfully',
            'overall_average': float(academic_data.overall_average)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def update_program_selection(request, student_id):
    """API endpoint to update program selection (WITHOUT triggering placement)"""
    try:
        student = get_object_or_404(Student, lrn=student_id)
        data = json.loads(request.body)
        
        program_selection, created = ProgramSelection.objects.get_or_create(student=student)
        
        # Update program selection fields
        if 'selected_program_code' in data:
            program_selection.selected_program_code = data['selected_program_code']
        
        # Update admin notes (can be updated without approval)
        if 'admin_notes' in data:
            program_selection.admin_notes = data['admin_notes']
        
        # DO NOT update admin_approved or assigned_section here
        # Those will be handled by the approve_and_place endpoint
        
        program_selection.save()
        
        return JsonResponse({'success': True, 'message': 'Program selection updated successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def approve_and_place_student(request, student_id):
    """
    API endpoint to approve enrollment and auto-assign student to section.
    
    Logic:
    1. Check if student is already approved (prevent double placement)
    2. For REGULAR program: Use AI recommendation to pick TOP5 vs HETERO section
    3. For other programs (STE, SPFL, SPTVE): Use sequential fill algorithm
    4. Auto-assign to appropriate section with available capacity
    5. Update database counts
    """
    try:
        with transaction.atomic():
            import sys
            student = get_object_or_404(Student, lrn=student_id)
            data = json.loads(request.body)
            
            admin_notes = data.get('admin_notes', '')
            coordinator_selected_track = data.get('coordinator_selected_track', None)
            transferee_grade_level_from_request = data.get('transferee_grade_level', None)  # Sent from frontend
            
            # DEBUG: Log what we received
            print(f"\n{'='*80}", file=sys.stderr)
            print(f"🎯 APPROVAL REQUEST RECEIVED", file=sys.stderr)
            print(f"{'='*80}", file=sys.stderr)
            print(f"Student LRN: {student_id}", file=sys.stderr)
            print(f"Enrollee Type: {student.enrollee_type}", file=sys.stderr)
            print(f"Request Data Received:", file=sys.stderr)
            print(f"  - admin_notes: {admin_notes}", file=sys.stderr)
            print(f"  - coordinator_selected_track: {coordinator_selected_track}", file=sys.stderr)
            print(f"  - transferee_grade_level_from_request: {transferee_grade_level_from_request} (type: {type(transferee_grade_level_from_request).__name__})", file=sys.stderr)
            
            # Get the program selection
            program_selection = get_object_or_404(ProgramSelection, student=student)
            
            # Save coordinator-selected track to StudentData if provided (for transferees)
            if coordinator_selected_track:
                student_data, _ = StudentData.objects.get_or_create(student=student)
                student_data.coordinator_selected_track = coordinator_selected_track
                student_data.save()
            
            # RULE 1: Avoid double placement - if already approved, reject
            if program_selection.admin_approved and program_selection.assigned_section:
                return JsonResponse({
                    'success': False,
                    'error': f'Student is already approved and placed in a section. Cannot approve again.'
                }, status=400)

            # ── PROBATION CHECK ───────────────────────────────────────────
            # If student has an active probation record, force them to REGULAR
            # regardless of what program was selected. This applies to ALL
            # approval paths — manual and AI.
            from coordinator_app.models import ProbationRecord
            active_probation = ProbationRecord.get_active_for_student(student)
            if active_probation:
                original_program = program_selection.selected_program_code
                program_code = 'REGULAR'
                program_selection.selected_program_code = 'REGULAR'
                program_selection.regular_track = 'TOP5'
                program_selection.admin_notes = (
                    f'[PROBATION OVERRIDE] Student was on active STE probation. '
                    f'Program forced from {original_program} to REGULAR (TOP5). '
                    f'Probation reason: {active_probation.reason[:120]}'
                )
                program_selection.save(update_fields=[
                    'selected_program_code', 'regular_track', 'admin_notes'
                ])
                print(
                    f"[MANUAL-APPROVAL] PROBATION DETECTED for {student.lrn} — "
                    f"forcing {original_program} → REGULAR",
                    file=sys.stderr
                )
            
            # Get the program code and school year
            program_code = program_selection.selected_program_code
            school_year = program_selection.school_year
            print(f"Program Code: {program_code}", file=sys.stderr)
            print(f"School Year: {school_year}", file=sys.stderr)
            
            # Determine target track/grade for placement
            target_track = None
            target_grade_code = None
            
            # SPECIAL HANDLING FOR TRANSFEREES
            # Check both Student.enrollee_type and StudentData.enrolling_as
            student_data = getattr(student, 'student_data', None)
            is_transferee = (student.enrollee_type == 'transferee' or 
                           (student_data and 'transferee' in (student_data.enrolling_as or [])))
            
            enrolling_as_display = (student_data.enrolling_as if student_data else 'N/A')
            print(f"Enrollee Type Check: student.enrollee_type={student.enrollee_type}, enrolling_as={enrolling_as_display} (is list: {isinstance(enrolling_as_display, list)}), is_transferee={is_transferee}", file=sys.stderr)
            
            if is_transferee:
                # Get the grade level they're enrolling in - check request first, then StudentData
                grade_level = transferee_grade_level_from_request or (student_data.transferee_grade_level if student_data else None)
                print(f"  - grade_level determined: {grade_level} (type: {type(grade_level).__name__})", file=sys.stderr)
                
                if grade_level:
                    # Convert to grade code (ensure it's a string)
                    target_grade_code = f'G{grade_level}'.strip()
                    print(f"  ✓ target_grade_code set to: {target_grade_code}", file=sys.stderr)
                else:
                    print(f"  ❌ NO GRADE LEVEL - will place without grade filtering!", file=sys.stderr)
                
                # For REGULAR program: use coordinator-selected track
                if program_code == 'REGULAR':
                    if coordinator_selected_track:
                        target_track = coordinator_selected_track
                        print(f"  - Using coordinator-selected track from REQUEST: {target_track}", file=sys.stderr)
                    elif student_data and student_data.coordinator_selected_track:
                        target_track = student_data.coordinator_selected_track
                        print(f"  - Using coordinator-selected track from DATABASE: {target_track}", file=sys.stderr)
                    else:
                        # Fallback if no track selected
                        target_track = 'HETERO'
                        print(f"  - No track selected, using FALLBACK: {target_track}", file=sys.stderr)
            
            # For NEW/CONTINUING students: use AI recommendation
            elif program_code == 'REGULAR':
                # Use AI recommendation to determine track (TOP5 vs HETERO)
                target_track = _get_ai_recommended_track(student)
                if not target_track:
                    # Fallback if recommendation fails
                    target_track = 'HETERO'
            
            # Phase 5: For continuing students, first try to honour their prior section name
            # by matching on section name within the same program + school year.
            available_section = None
            is_continuing_check = (student.enrollee_type == 'continuing' or 
                           (student_data and 'continuing' in (student_data.enrolling_as or [])))
            if is_continuing_check:
                prior_log = CoordinatorActivityLog.objects.filter(
                    student_lrn=student.lrn,
                    action='student_approved',
                ).order_by('-created_at').first()
                if prior_log and prior_log.section_name:
                    # Look for a matching-name section in the CURRENT SY / program
                    matching_qs = Section.objects.filter(
                        program__code=program_code,
                        school_year=school_year,
                        name=prior_log.section_name,
                    )
                    if program_code == 'REGULAR' and target_track:
                        matching_qs = matching_qs.filter(regular_track=target_track)
                    for section in matching_qs:
                        if section.get_actual_count() < section.max_students:
                            available_section = section
                            break

            # Find the first available section using sequential fill algorithm
            # (used as fallback when continuing-student hint yielded nothing)
            # For REGULAR: filter by program, track, and optionally grade (for transferees)
            # For others: just filter by program (and grade for transferees)
            if not available_section:
                # DEBUG LOGGING
                import sys
                enrolling_as_display = (student_data.enrolling_as if student_data else 'N/A')
                print(f"\n{'='*80}", file=sys.stderr)
                print(f"🔍 PLACEMENT SEARCH FOR {student.lrn}", file=sys.stderr)
                print(f"   Is Transferee: {is_transferee} (enrollee_type={student.enrollee_type}, enrolling_as={enrolling_as_display})", file=sys.stderr)
                print(f"   Program: {program_code}", file=sys.stderr)
                print(f"   Target Grade: {target_grade_code}", file=sys.stderr)
                print(f"   Target Track: {target_track}", file=sys.stderr)
                print(f"{'='*80}\n", file=sys.stderr)
                
                if program_code == 'REGULAR':
                    if target_grade_code:
                        # Transferee: filter by program + track + grade
                        print(f"🎓 TRANSFEREE PLACEMENT: Filtering by Grade {target_grade_code} + Track {target_track}", file=sys.stderr)
                        program_sections = Section.objects.filter(
                            program__code=program_code,
                            school_year=school_year,
                            grade_level__code=target_grade_code,
                            regular_track=target_track
                        ).order_by('created_at')
                        print(f"   Found {program_sections.count()} sections", file=sys.stderr)
                        for sec in program_sections:
                            print(f"   • {sec.name} [{sec.regular_track}]: {sec.get_actual_count()}/{sec.max_students}", file=sys.stderr)
                    else:
                        # New/Continuing: filter by program + track only
                        print(f"📚 NEW/CONTINUING PLACEMENT: Filtering by Track {target_track} only", file=sys.stderr)
                        program_sections = Section.objects.filter(
                            program__code=program_code,
                            school_year=school_year,
                            regular_track=target_track
                        ).order_by('created_at')
                else:
                    if target_grade_code:
                        # Transferee in non-REGULAR program: filter by program + grade
                        print(f"🎓 TRANSFEREE ({program_code}): Filtering by Grade {target_grade_code}", file=sys.stderr)
                        program_sections = Section.objects.filter(
                            program__code=program_code,
                            school_year=school_year,
                            grade_level__code=target_grade_code
                        ).order_by('created_at')
                    else:
                        # New/Continuing in non-REGULAR: filter by program only
                        print(f"📚 NEW/CONTINUING ({program_code}): Filtering by program only", file=sys.stderr)
                        program_sections = Section.objects.filter(
                            program__code=program_code,
                            school_year=school_year
                        ).order_by('created_at')

                for section in program_sections:
                    # Always get fresh count from database
                    actual_count = section.get_actual_count()
                    if actual_count < section.max_students:
                        available_section = section
                        print(f"✅ SELECTED: {section.name} ({actual_count}/{section.max_students})", file=sys.stderr)
                        break
            
            # If no section available in recommended track, try the other track (for REGULAR only)
            # But skip this for transferees who explicitly selected a track
            if not available_section and program_code == 'REGULAR' and not target_grade_code:
                alternative_track = 'TOP5' if target_track == 'HETERO' else 'HETERO'
                program_sections = Section.objects.filter(
                    program__code=program_code,
                    school_year=school_year,
                    regular_track=alternative_track
                ).order_by('created_at')
                
                for section in program_sections:
                    # Always get fresh count from database
                    actual_count = section.get_actual_count()
                    if actual_count < section.max_students:
                        available_section = section
                        # Update the track used (since we're using fallback)
                        target_track = alternative_track
                        break
            
            if not available_section:
                track_info = f" {target_track}" if target_track else ""
                return JsonResponse({
                    'success': False,
                    'error': f'No available sections in {program_code}{track_info}. All sections are full.'
                }, status=400)
            
            # Approve and place student in the available section
            program_selection.admin_approved = True
            program_selection.admin_notes = admin_notes
            program_selection.approved_by = request.user.get_full_name() or request.user.username
            program_selection.approved_at = timezone.now()
            program_selection.assigned_section = available_section
            program_selection.section_assigned_at = timezone.now()
            program_selection.save()
            
            # Update Student enrollment status (deprecated field, for backward compat)
            old_status = student.enrollment_status
            student.enrollment_status = 'approved'
            student.save()
            
            # Update StudentEnrollment status (NEW primary field)
            if school_year:
                student_enrollment = StudentEnrollment.objects.filter(
                    student=student,
                    school_year=school_year
                ).first()
                if student_enrollment:
                    student_enrollment.enrollment_status = 'approved'
                    student_enrollment.save()
                    print(f"✅ Updated StudentEnrollment.enrollment_status to 'approved' for {student.lrn}", file=sys.stderr)
            
            # Update section counts
            available_section.update_current_students_count()
            
            # Log the status change
            EnrollmentStatusLog.objects.create(
                student=student,
                old_status=old_status,
                new_status='approved',
                changed_by=request.user.get_full_name() or request.user.username,
                change_reason=f'Enrollment approved and auto-placed in section {available_section.name}'
            )
            
            # Get student and program names for response
            student_name = "Student"
            if hasattr(student, 'student_data') and student.student_data:
                student_name = student.student_data.full_name
            
            program_obj = available_section.program
            program_name = program_obj.name if program_obj else program_code
            
            # Log coordinator activity
            CoordinatorActivityLog.log(
                user=request.user,
                action='student_approved',
                description=f'Approved enrollment for {student_name} and assigned to section {available_section.name}',
                category='enrollment',
                program=program_obj,
                student_lrn=student.lrn,
                student_name=student_name,
                section_name=available_section.name,
                metadata={'admin_notes': admin_notes, 'track': target_track},
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return JsonResponse({
                'success': True,
                'message': f'{student_name} has successfully enrolled under the program {program_name} in {available_section.name}',
                'student_name': student_name,
                'program_name': program_name,
                'section_name': available_section.name,
                'section_id': available_section.id,
                'new_status': 'approved',
                'section_current_students': available_section.current_students,
                'section_max_students': available_section.max_students
            })
            
    except ProgramSelection.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student has not selected a program yet'
        }, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def _get_ai_recommended_track(student):
    """
    Get AI recommendation for REGULAR program track (TOP5 vs HETERO).
    
    Returns: 'Top-5 Regular' or 'Hetero' based on ML model prediction
    """
    try:
        from TRAINING_ARC.placement_recommender import PlacementRecommender
        
        # Load recommender
        recommender = PlacementRecommender(model_path='TRAINING_ARC/models')
        if not recommender.load_model():
            return None
        
        # Prepare student data for prediction
        student_features = _prepare_student_features(student)
        if student_features is None:
            return None
        
        # Get recommendations
        recommendations = recommender.recommend(student_features, top_n=5)
        
        # Find REGULAR track recommendation (Top-5 or Hetero)
        for rec in recommendations:
            if rec['placement'] == 'Top-5 Regular':
                return 'Top-5 Regular'
            elif rec['placement'] == 'Hetero':
                return 'Hetero'
        
        # Fallback to Hetero if no clear recommendation
        return 'Hetero'
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Fallback: assign to Hetero if recommendation fails
        return 'Hetero'


def _prepare_student_features(student):
    """
    Prepare student features for ML model prediction.
    Extract survey answers, academic data, etc.
    
    Returns: pandas DataFrame with student features or None if data missing
    """
    try:
        import pandas as pd
        
        # Get survey data
        if not hasattr(student, 'survey_data') or not student.survey_data:
            return None
        
        survey = student.survey_data
        
        # Extract subject enjoyment from enjoyed_subjects list
        enjoyed_subjects = survey.enjoyed_subjects or []
        difficulty_areas = survey.difficulty_areas or []
        
        # Build feature dictionary based on actual SurveyData model fields
        features = {
            'enjoy_math': 1 if 'Math' in enjoyed_subjects else 0,
            'enjoy_science': 1 if 'Science' in enjoyed_subjects else 0,
            'enjoy_english': 1 if 'English' in enjoyed_subjects else 0,
            'enjoy_filipino': 1 if 'Filipino' in enjoyed_subjects else 0,
            'enjoy_arpan': 1 if 'ARPAN' in enjoyed_subjects else 0,
            'enjoy_mapeh': 1 if 'MAPEH' in enjoyed_subjects else 0,
            'enjoy_tle': 1 if 'TLE' in enjoyed_subjects else 0,
            'difficulty_reading': 1 if 'Reading' in difficulty_areas else 0,
            'difficulty_writing': 1 if 'Writing' in difficulty_areas else 0,
            'difficulty_math': 1 if 'Math' in difficulty_areas else 0,
            'difficulty_focusing': 1 if 'Focusing' in difficulty_areas else 0,
            'difficulty_social_interaction': 1 if 'Social Interaction' in difficulty_areas else 0,
            'award_highest_honors': 1 if getattr(survey, 'extra_support', '') == 'Highest Honors' else 0,
            'award_high_honors': 1 if getattr(survey, 'extra_support', '') == 'High Honors' else 0,
            'award_with_honors': 1 if getattr(survey, 'extra_support', '') == 'With Honors' else 0,
            'sped_learner': 1 if 'SPED' in difficulty_areas else 0,
            'working_student': 1 if getattr(survey, 'survey_responses_json', {}).get('working_student') else 0,
        }
        
        # Create DataFrame
        df = pd.DataFrame([features])
        return df
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None



@login_required
@require_http_methods(["POST"])
def revert_approval(request, student_id):
    """
    API endpoint to revert a student's approval back to pending.
    Useful for undoing accidental approvals.
    
    Removes section assignment and sets status back to pending.
    """
    try:
        with transaction.atomic():
            student = get_object_or_404(Student, lrn=student_id)
            data = json.loads(request.body)
            
            revert_reason = data.get('revert_reason', 'Reverted by coordinator')
            
            # Get program selection
            program_selection = get_object_or_404(ProgramSelection, student=student)
            
            # Check if approved
            if not program_selection.admin_approved:
                return JsonResponse({
                    'success': False,
                    'error': 'Student enrollment is not approved yet. Nothing to revert.'
                }, status=400)
            
            # Check if already rejected
            if program_selection.admin_rejected:
                return JsonResponse({
                    'success': False,
                    'error': 'Cannot revert a rejected enrollment. Create new program selection.'
                }, status=400)
            
            # Get the section before removing assignment
            old_section = None
            if program_selection.assigned_section:
                try:
                    old_section = program_selection.assigned_section
                except Exception:
                    pass
            
            # Revert approval
            program_selection.admin_approved = False
            program_selection.assigned_section = None
            program_selection.section_assigned_at = None
            program_selection.approved_by = None
            program_selection.approved_at = None
            program_selection.admin_notes = f"[REVERTED] {revert_reason}"
            program_selection.save()
            
            # Update Student enrollment status back to pending
            old_status = student.enrollment_status
            student.enrollment_status = 'pending'
            student.save()
            
            # Update section counts if had a section assigned
            if old_section:
                old_section.update_current_students_count()
            
            # Log the status change
            EnrollmentStatusLog.objects.create(
                student=student,
                old_status=old_status,
                new_status='pending',
                changed_by=request.user.get_full_name() or request.user.username,
                change_reason=f'Enrollment approval reverted: {revert_reason}'
            )
            
            # Get student name for response
            student_name = "Student"
            if hasattr(student, 'student_data') and student.student_data:
                student_name = student.student_data.full_name
            
            # Get program for logging
            program_obj = None
            try:
                program_obj = Program.objects.get(code=program_selection.selected_program_code)
            except:
                pass
            
            # Log coordinator activity
            CoordinatorActivityLog.log(
                user=request.user,
                action='student_reverted',
                description=f'Reverted enrollment approval for {student_name}. Reason: {revert_reason}',
                category='enrollment',
                program=program_obj,
                student_lrn=student.lrn,
                student_name=student_name,
                section_name=old_section.name if old_section else None,
                metadata={'revert_reason': revert_reason},
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return JsonResponse({
                'success': True,
                'message': f'{student_name}\'s approval has been reverted to pending',
                'student_name': student_name,
                'new_status': 'pending',
                'section_removed': old_section.name if old_section else None
            })
            
    except ProgramSelection.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student has not selected a program yet'
        }, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def reject_enrollment(request, student_id):
    """
    API endpoint to reject a student's enrollment.
    
    Marks the enrollment as rejected with reason.
    """
    try:
        with transaction.atomic():
            student = get_object_or_404(Student, lrn=student_id)
            data = json.loads(request.body)
            
            rejection_reason = data.get('rejection_reason', '')
            
            # Get program selection
            program_selection = get_object_or_404(ProgramSelection, student=student)
            
            # Check if already rejected
            if program_selection.admin_rejected:
                return JsonResponse({
                    'success': False,
                    'error': 'Student enrollment is already rejected'
                }, status=400)
            
            # Mark as rejected
            program_selection.admin_rejected = True
            program_selection.rejection_reason = rejection_reason
            program_selection.rejected_by = request.user.get_full_name() or request.user.username
            program_selection.rejected_at = timezone.now()
            program_selection.admin_approved = False  # Make sure not approved
            program_selection.save()
            
            # Update Student enrollment status
            old_status = student.enrollment_status
            student.enrollment_status = 'rejected'
            student.save()
            
            # Log the status change
            EnrollmentStatusLog.objects.create(
                student=student,
                old_status=old_status,
                new_status='rejected',
                changed_by=request.user.get_full_name() or request.user.username,
                change_reason=f'Enrollment rejected: {rejection_reason}'
            )
            
            # Get student name for response
            student_name = "Student"
            if hasattr(student, 'student_data') and student.student_data:
                student_name = student.student_data.full_name
            
            # Get program for logging
            program_obj = None
            try:
                program_obj = Program.objects.get(code=program_selection.selected_program_code)
            except:
                pass
            
            # Log coordinator activity
            CoordinatorActivityLog.log(
                user=request.user,
                action='student_rejected',
                description=f'Rejected enrollment for {student_name}. Reason: {rejection_reason}',
                category='enrollment',
                program=program_obj,
                student_lrn=student.lrn,
                student_name=student_name,
                metadata={'rejection_reason': rejection_reason},
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return JsonResponse({
                'success': True,
                'message': f'{student_name}\'s enrollment has been rejected',
                'student_name': student_name,
                'new_status': 'rejected'
            })
            
    except ProgramSelection.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student has not selected a program yet'
        }, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def review_document_submission(request, student_id, submission_id):
    """API endpoint for coordinators to review a student's document submission.

    Expects JSON: { 'action': 'approve'|'reject'|'resubmit', 'review_notes': '...' }
    """
    try:
        data = json.loads(request.body)
        action = data.get('action')
        review_notes = data.get('review_notes', '')

        submission = get_object_or_404(StudentDocumentSubmission, pk=submission_id, student__lrn=student_id)

        if action not in ('approve', 'reject', 'resubmit'):
            return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)

        if action == 'approve':
            submission.status = 'approved'
        elif action == 'reject':
            submission.status = 'rejected'
        else:
            submission.status = 'resubmit'

        submission.review_notes = review_notes
        submission.reviewed_by = request.user
        submission.reviewed_at = timezone.now()
        submission.save()

        # Log coordinator activity
        try:
            program_obj = None
            ps = getattr(submission.student, 'program_selection', None)
            if ps and ps.selected_program_code:
                from admin_app.models import Program
                try:
                    program_obj = Program.objects.filter(code=ps.selected_program_code).first()
                except Exception:
                    program_obj = None

            CoordinatorActivityLog.log(
                user=request.user,
                action='student_approved' if action == 'approve' else 'student_rejected',
                description=f'Document {submission.requirement.name} {submission.status} by coordinator',
                category='enrollment',
                program=program_obj,
                student_lrn=submission.student.lrn,
                student_name=getattr(getattr(submission.student, 'student_data', None), 'full_name', None),
                section_name=getattr(getattr(ps, 'assigned_section', None), 'name', None),
                metadata={'requirement_id': submission.requirement.id, 'action': action},
                ip_address=request.META.get('REMOTE_ADDR')
            )
        except Exception:
            pass

        return JsonResponse({'success': True, 'submission_status': submission.status})

    except StudentDocumentSubmission.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Submission not found'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def get_sections_by_program(request):
    """API endpoint to get sections by program code"""
    try:
        program_code = request.GET.get('program')
        
        if not program_code:
            return JsonResponse({'success': False, 'error': 'Program code is required'}, status=400)
        
        # Get active school year
        active_school_year = SchoolYear.objects.filter(is_active=True).first()
        
        if not active_school_year:
            return JsonResponse({'success': False, 'error': 'No active school year found'}, status=404)
        
        # Get sections for this program and school year
        sections = Section.objects.filter(
            program__code=program_code,
            school_year=active_school_year
        ).select_related('adviser', 'program')
        
        sections_data = []
        for section in sections:
            sections_data.append({
                'id': section.id,
                'name': section.name,
                'adviser_name': section.adviser.get_full_name() if section.adviser else None,
                'current_students': section.current_students,
                'max_students': section.max_students,
                'building': section.building or '',
                'room': section.room or '',
            })
        
        return JsonResponse({'success': True, 'sections': sections_data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)