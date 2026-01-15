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
    SurveyData, AcademicData, ProgramSelection, StudentDocumentSubmission, EnrollmentStatusLog
)
from admin_app.models import Program, SchoolYear, Section, DocumentRequirement


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
    
    # Get all programs for selection
    programs = Program.objects.all()
    
    # Get document requirements for the student's school year
    document_requirements = []
    if student.school_year:
        document_requirements = DocumentRequirement.objects.filter(
            school_year=student.school_year,
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
    }
    
    return render(request, 'coordinator_app/studentEdit.html', context)


@login_required
@require_http_methods(["GET"])
def get_student_details(request, student_id):
    """API endpoint to fetch all student details"""
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
                'last_name': sd.last_name,
                'first_name': sd.first_name,
                'middle_name': sd.middle_name or '',
                'gender': sd.gender,
                'date_of_birth': sd.date_of_birth.strftime('%Y-%m-%d'),
                'place_of_birth': sd.place_of_birth or '',
                'religion': sd.religion or '',
                'dialect_spoken': sd.dialect_spoken or '',
                'ethnic_tribe': sd.ethnic_tribe or '',
                'address': sd.address or '',
                'enrolling_as': sd.enrolling_as,
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
            }
        else:
            data['student_data'] = None
        
        # Family Data
        if hasattr(student, 'family_data'):
            fd = student.family_data
            
            # Father's information
            if fd.father:
                data['father'] = {
                    'id': fd.father.id,
                    'family_name': fd.father.family_name,
                    'first_name': fd.father.first_name,
                    'middle_name': fd.father.middle_name or '',
                    'date_of_birth': fd.father.date_of_birth.strftime('%Y-%m-%d'),
                    'occupation': fd.father.occupation,
                    'address': fd.father.address or '',
                    'contact_number': fd.father.contact_number,
                    'email': fd.father.email or '',
                    'age': fd.father.age,
                    'full_name': fd.father.full_name,
                }
            else:
                data['father'] = None
            
            # Mother's information
            if fd.mother:
                data['mother'] = {
                    'id': fd.mother.id,
                    'family_name': fd.mother.family_name,
                    'first_name': fd.mother.first_name,
                    'middle_name': fd.mother.middle_name or '',
                    'date_of_birth': fd.mother.date_of_birth.strftime('%Y-%m-%d'),
                    'occupation': fd.mother.occupation,
                    'address': fd.mother.address or '',
                    'contact_number': fd.mother.contact_number,
                    'email': fd.mother.email or '',
                    'age': fd.mother.age,
                    'full_name': fd.mother.full_name,
                }
            else:
                data['mother'] = None
            
            # Guardian information
            data['guardian'] = {
                'official_guardian_type': fd.official_guardian_type,
            }
            
            if fd.other_guardian:
                data['guardian']['other_guardian'] = {
                    'id': fd.other_guardian.id,
                    'family_name': fd.other_guardian.family_name,
                    'first_name': fd.other_guardian.first_name,
                    'middle_name': fd.other_guardian.middle_name or '',
                    'date_of_birth': fd.other_guardian.date_of_birth.strftime('%Y-%m-%d'),
                    'occupation': fd.other_guardian.occupation,
                    'address': fd.other_guardian.address or '',
                    'contact_number': fd.other_guardian.contact_number,
                    'email': fd.other_guardian.email or '',
                    'relationship_to_student': fd.other_guardian.relationship_to_student,
                    'age': fd.other_guardian.age,
                    'full_name': fd.other_guardian.full_name,
                }
            else:
                data['guardian']['other_guardian'] = None
            
            data['guardian']['parent_photo'] = fd.parent_photo.url if fd.parent_photo else None
        else:
            data['father'] = None
            data['mother'] = None
            data['guardian'] = None
        
        # Survey Data
        if hasattr(student, 'survey_data'):
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
                'enjoyed_subjects': survey.enjoyed_subjects,
                'interested_program': survey.interested_program or '',
                'program_motivation': survey.program_motivation or '',
                'enjoyed_activities': survey.enjoyed_activities,
                'enjoyed_activities_other': survey.enjoyed_activities_other or '',
                'assignments_on_time': survey.assignments_on_time or '',
                'handle_difficult_lessons': survey.handle_difficult_lessons or '',
                'device_availability': survey.device_availability or '',
                'internet_access': survey.internet_access or '',
                'absences': survey.absences or '',
                'absence_reason': survey.absence_reason or '',
                'participation': survey.participation or '',
                'difficulty_areas': survey.difficulty_areas,
                'extra_support': survey.extra_support or '',
                'quiet_place': survey.quiet_place or '',
                'distance_from_school': survey.distance_from_school or '',
                'travel_difficulty': survey.travel_difficulty or '',
            }
        else:
            data['survey_data'] = None
        
        # Academic Data
        if hasattr(student, 'academic_data'):
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
                'report_card': acad.report_card.url if acad.report_card else None,
                'is_working_student': acad.is_working_student,
                'working_type': acad.working_type or '',
                'is_pwd': acad.is_pwd,
                'disability_type': acad.disability_type or '',
                'overall_average': float(acad.overall_average),
            }
        else:
            data['academic_data'] = None
        
        # Program Selection
        if hasattr(student, 'program_selection'):
            prog = student.program_selection
            data['program_selection'] = {
                'selected_program_code': prog.selected_program_code,
                'program_description': prog.program_description,
                'selection_reason': prog.selection_reason or '',
                'admin_approved': prog.admin_approved,
                'admin_notes': prog.admin_notes or '',
                'approved_by': prog.approved_by or '',
                'assigned_section': prog.assigned_section or '',
            }
        else:
            data['program_selection'] = None
        
        return JsonResponse({'success': True, 'data': data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


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
                          'last_school_year', 'sped_details', 'working_details']:
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
    API endpoint to approve enrollment and place student in section.
    
    Logic:
    1. Check if student is already approved (prevent double placement)
    2. Check sequential section filling (previous sections must be full before using this one)
    3. Get actual student counts from database (not by incrementing field)
    4. Update counts from database after approval
    """
    try:
        with transaction.atomic():
            student = get_object_or_404(Student, lrn=student_id)
            data = json.loads(request.body)
            
            section_id = data.get('section_id')
            admin_notes = data.get('admin_notes', '')
            
            if not section_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Section ID is required for approval'
                }, status=400)
            
            # Get the section
            section = get_object_or_404(Section, id=section_id)
            
            # Get program selection
            program_selection = get_object_or_404(ProgramSelection, student=student)
            
            # RULE 1: Avoid double placement - if already approved, reject
            if program_selection.admin_approved and program_selection.assigned_section:
                return JsonResponse({
                    'success': False,
                    'error': f'Student is already approved and placed in a section. Cannot approve again.'
                }, status=400)
            
            # RULE 2: Check sequential section filling
            # Get all sections for this program, ordered by creation (sequential filling)
            program_sections = Section.objects.filter(
                program=section.program,
                school_year=section.school_year
            ).order_by('created_at')
            
            # All previous sections must be at max capacity before using this one
            can_place_in_this_section = True
            for s in program_sections:
                if s.id == section.id:
                    break  # Reached target section, exit loop
                # All previous sections must be full
                actual_count = s.get_actual_count()
                if actual_count < s.max_students:
                    can_place_in_this_section = False
                    break
            
            if not can_place_in_this_section:
                return JsonResponse({
                    'success': False,
                    'error': f'Cannot place in {section.name}. Previous sections must be full first.'
                }, status=400)
            
            # RULE 4: Get actual count from database (not from field)
            actual_section_count = section.get_actual_count()
            
            # Check if section has capacity
            if actual_section_count >= section.max_students:
                return JsonResponse({
                    'success': False,
                    'error': f'Section {section.name} is full ({actual_section_count}/{section.max_students})'
                }, status=400)
            
            # Approve and place student
            program_selection.admin_approved = True
            program_selection.admin_notes = admin_notes
            program_selection.approved_by = request.user.get_full_name() or request.user.username
            program_selection.approved_at = timezone.now()
            program_selection.assigned_section = str(section.id)
            program_selection.section_assigned_at = timezone.now()
            program_selection.save()
            
            # Update Student enrollment status
            old_status = student.enrollment_status
            student.enrollment_status = 'approved'
            student.save()
            
            # RULE 4: Update counts from database (count actual enrollments, don't increment)
            section.update_current_students_count()
            
            # Log the status change
            EnrollmentStatusLog.objects.create(
                student=student,
                old_status=old_status,
                new_status='approved',
                changed_by=request.user.get_full_name() or request.user.username,
                change_reason=f'Enrollment approved and placed in section {section.name}'
            )
            
            # Get student name for response
            student_name = "Student"
            if hasattr(student, 'student_data'):
                student_name = student.student_data.full_name
            
            return JsonResponse({
                'success': True,
                'message': f'Enrollment approved! {student_name} has been placed in {section.name}',
                'new_status': 'approved',
                'section_name': section.name,
                'section_id': section.id,
                'section_current_students': section.current_students,
                'section_max_students': section.max_students
            })
            
    except Section.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Selected section not found'
        }, status=404)
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
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

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