from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.core.files.storage import default_storage
from decimal import Decimal
import json

from enrollment_app.models import (
    Student, StudentData, FamilyData, Parent, Guardian,
    SurveyData, AcademicData, ProgramSelection
)
from admin_app.models import Program, SchoolYear


@login_required
def student_edit(request, student_id):
    """Main view for student edit page"""
    student = get_object_or_404(Student, lrn=student_id)
    
    # Get all school years for the filter
    school_years = SchoolYear.objects.all().order_by('-year_label')
    active_school_year = SchoolYear.objects.filter(is_active=True).first()
    
    # Get all programs for selection
    programs = Program.objects.all()
    
    context = {
        'student': student,
        'student_id': student_id,
        'school_years': school_years,
        'active_school_year': active_school_year,
        'programs': programs,
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
            if 'student_data' in data:
                sd_data = data['student_data']
                student_data, created = StudentData.objects.get_or_create(student=student)
                
                # Update fields
                for field in ['last_name', 'first_name', 'middle_name', 'gender', 
                              'date_of_birth', 'place_of_birth', 'religion', 
                              'dialect_spoken', 'ethnic_tribe', 'address',
                              'last_school_attended', 'previous_grade_section', 
                              'last_school_year', 'sped_details', 'working_details']:
                    if field in sd_data:
                        setattr(student_data, field, sd_data[field])
                
                # Boolean fields
                if 'is_sped' in sd_data:
                    student_data.is_sped = sd_data['is_sped']
                if 'is_working_student' in sd_data:
                    student_data.is_working_student = sd_data['is_working_student']
                
                # JSON fields
                if 'enrolling_as' in sd_data:
                    student_data.enrolling_as = sd_data['enrolling_as']
                
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
            if 'father' in data:
                father_data = data['father']
                if family_data.father:
                    father = family_data.father
                else:
                    father = Parent(parent_type='father')
                
                for field in ['family_name', 'first_name', 'middle_name', 
                              'date_of_birth', 'occupation', 'address', 
                              'contact_number', 'email']:
                    if field in father_data:
                        setattr(father, field, father_data[field])
                
                father.save()
                family_data.father = father
            
            # Update Mother
            if 'mother' in data:
                mother_data = data['mother']
                if family_data.mother:
                    mother = family_data.mother
                else:
                    mother = Parent(parent_type='mother')
                
                for field in ['family_name', 'first_name', 'middle_name', 
                              'date_of_birth', 'occupation', 'address', 
                              'contact_number', 'email']:
                    if field in mother_data:
                        setattr(mother, field, mother_data[field])
                
                mother.save()
                family_data.mother = mother
            
            # Update Guardian info
            if 'official_guardian_type' in data:
                family_data.official_guardian_type = data['official_guardian_type']
            
            if 'other_guardian' in data and data['other_guardian']:
                guardian_data = data['other_guardian']
                if family_data.other_guardian:
                    guardian = family_data.other_guardian
                else:
                    guardian = Guardian()
                
                for field in ['family_name', 'first_name', 'middle_name', 
                              'date_of_birth', 'occupation', 'address', 
                              'contact_number', 'email', 'relationship_to_student']:
                    if field in guardian_data:
                        setattr(guardian, field, guardian_data[field])
                
                guardian.save()
                family_data.other_guardian = guardian
            
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
        
        # Update all survey fields
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
        
        # JSON array fields
        for field in ['enjoyed_subjects', 'enjoyed_activities', 'difficulty_areas']:
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
        
        # Update grades
        grade_fields = ['mathematics', 'araling_panlipunan', 'english', 
                       'edukasyon_sa_pagpapakatao', 'science', 
                       'edukasyon_pangkabuhayan', 'filipino', 'mapeh']
        
        for field in grade_fields:
            if field in data and data[field]:
                setattr(academic_data, field, Decimal(str(data[field])))
        
        # Update special cases
        if 'is_working_student' in data:
            academic_data.is_working_student = data['is_working_student']
        if 'working_type' in data:
            academic_data.working_type = data['working_type']
        if 'is_pwd' in data:
            academic_data.is_pwd = data['is_pwd']
        if 'disability_type' in data:
            academic_data.disability_type = data['disability_type']
        
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
    """API endpoint to update program selection and admin approval"""
    try:
        student = get_object_or_404(Student, lrn=student_id)
        data = json.loads(request.body)
        
        program_selection, created = ProgramSelection.objects.get_or_create(student=student)
        
        # Update program selection fields
        if 'selected_program_code' in data:
            program_selection.selected_program_code = data['selected_program_code']
        if 'program_description' in data:
            program_selection.program_description = data['program_description']
        if 'selection_reason' in data:
            program_selection.selection_reason = data['selection_reason']
        
        # Admin fields
        if 'admin_approved' in data:
            program_selection.admin_approved = data['admin_approved']
        if 'admin_notes' in data:
            program_selection.admin_notes = data['admin_notes']
        if 'approved_by' in data:
            program_selection.approved_by = data['approved_by']
        if 'assigned_section' in data:
            program_selection.assigned_section = data['assigned_section']
        
        program_selection.save()
        
        return JsonResponse({'success': True, 'message': 'Program selection updated successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def update_enrollment_status(request, student_id):
    """API endpoint to update student enrollment status"""
    try:
        student = get_object_or_404(Student, lrn=student_id)
        data = json.loads(request.body)
        
        if 'enrollment_status' in data:
            old_status = student.enrollment_status
            new_status = data['enrollment_status']
            
            student.enrollment_status = new_status
            student.save()
            
            # Log the status change
            from enrollment_app.models import EnrollmentStatusLog
            EnrollmentStatusLog.objects.create(
                student=student,
                old_status=old_status,
                new_status=new_status,
                changed_by=request.user.username if hasattr(request.user, 'username') else 'admin',
                change_reason=data.get('reason', '')
            )
            
            return JsonResponse({'success': True, 'message': 'Enrollment status updated successfully'})
        else:
            return JsonResponse({'success': False, 'error': 'Status not provided'}, status=400)
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def upload_student_file(request, student_id):
    """API endpoint to handle file uploads (photos, documents)"""
    try:
        student = get_object_or_404(Student, lrn=student_id)
        file_type = request.POST.get('file_type')
        
        if 'file' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No file provided'}, status=400)
        
        uploaded_file = request.FILES['file']
        
        if file_type == 'student_photo':
            student_data = StudentData.objects.get(student=student)
            student_data.student_photo = uploaded_file
            student_data.save()
            file_url = student_data.student_photo.url
            
        elif file_type == 'parent_photo':
            family_data = FamilyData.objects.get(student=student)
            family_data.parent_photo = uploaded_file
            family_data.save()
            file_url = family_data.parent_photo.url
            
        elif file_type == 'report_card':
            academic_data = AcademicData.objects.get(student=student)
            academic_data.report_card = uploaded_file
            academic_data.save()
            file_url = academic_data.report_card.url
        else:
            return JsonResponse({'success': False, 'error': 'Invalid file type'}, status=400)
        
        return JsonResponse({'success': True, 'file_url': file_url, 'message': 'File uploaded successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)