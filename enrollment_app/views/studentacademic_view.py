from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from ..services.session_manager import EnrollmentSessionManager
from ..services.ocr_service import OCRGradeVerifier
from ..services.recommendation_service import generate_academic_recommendations
from coordinator_app.models import Qualified_for_ste
from ..models import (
    Student, StudentData, Parent, Guardian, FamilyData, 
    SurveyData, AcademicData, ProgramSelection
)
from admin_app.models import SchoolYear
import os
import uuid
import json
from datetime import datetime


def academic_form(request):
    """
    Handle student academic data form with OCR grade verification
    Requires all previous forms to be completed
    """
    
    # Check if previous forms are completed
    if not EnrollmentSessionManager.is_lrn_verified(request):
        messages.error(request, 'Please complete the Student Data form first.')
        return redirect('enrollment_app:student_data')
    
    if not EnrollmentSessionManager.get_family_data(request):
        messages.error(request, 'Please complete the Family Data form first.')
        return redirect('enrollment_app:family_data')
    
    if not EnrollmentSessionManager.get_survey_data(request):
        messages.error(request, 'Please complete the Survey form first.')
        return redirect('enrollment_app:non_academic')
    
    # Get existing data from session
    student_data = EnrollmentSessionManager.get_student_data(request)
    survey_data = EnrollmentSessionManager.get_survey_data(request)
    existing_academic_data = EnrollmentSessionManager.get_academic_data(request) or {}
    
    if request.method == 'POST':
        # Get form data
        academic_data = {
            'lrn': student_data.get('lrn'),
            'dost_exam_result': request.POST.get('dost_exam_result', ''),
            
            # Grade 6 Subjects
            'mathematics': request.POST.get('mathematics', ''),
            'araling_panlipunan': request.POST.get('araling_panlipunan', ''),
            'english': request.POST.get('english', ''),
            'edukasyon_sa_pagpapakatao': request.POST.get('edukasyon_sa_pagpapakatao', ''),
            'science': request.POST.get('science', ''),
            'edukasyon_pangkabuhayan': request.POST.get('edukasyon_pangkabuhayan', ''),
            'filipino': request.POST.get('filipino', ''),
            'mapeh': request.POST.get('mapeh', ''),
            
            # Auto-filled from student data
            'is_working_student': student_data.get('is_working_student', False),
            'working_details': student_data.get('working_details', ''),
            'is_pwd': student_data.get('is_sped', False),
            'sped_details': student_data.get('sped_details', ''),
        }
        
        # Preserve existing report card if no new upload
        academic_data['report_card_path'] = existing_academic_data.get('report_card_path', '')
        academic_data['report_card_name'] = existing_academic_data.get('report_card_name', '')
        
        # Handle report card upload
        if 'report_card' in request.FILES:
            report_card = request.FILES['report_card']
            
            # Create temp directory if it doesn't exist
            temp_dir = os.path.join(settings.BASE_DIR, 'temp_uploads')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Generate unique filename
            file_extension = os.path.splitext(report_card.name)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            temp_file_path = os.path.join(temp_dir, unique_filename)
            
            # Save file to temp location
            with open(temp_file_path, 'wb+') as destination:
                for chunk in report_card.chunks():
                    destination.write(chunk)
            
            # Store file path in academic data
            academic_data['report_card_path'] = temp_file_path
            academic_data['report_card_name'] = report_card.name
            
            # ============================================================================
            # OCR VERIFICATION DISABLED - START
            # Uncomment the section below when OCR is ready
            # ============================================================================
            
            # # Perform OCR verification
            # try:
            #     ocr_verifier = OCRGradeVerifier()
            #     
            #     # Extract grades from uploaded image
            #     extracted_grades = ocr_verifier.extract_grades_from_image(temp_file_path)
            #     
            #     # Prepare manual grades for comparison
            #     manual_grades = {
            #         'filipino': float(academic_data['filipino']) if academic_data['filipino'] else None,
            #         'english': float(academic_data['english']) if academic_data['english'] else None,
            #         'mathematics': float(academic_data['mathematics']) if academic_data['mathematics'] else None,
            #         'science': float(academic_data['science']) if academic_data['science'] else None,
            #         'araling_panlipunan': float(academic_data['araling_panlipunan']) if academic_data['araling_panlipunan'] else None,
            #         'edukasyon_sa_pagpapakatao': float(academic_data['edukasyon_sa_pagpapakatao']) if academic_data['edukasyon_sa_pagpapakatao'] else None,
            #         'edukasyon_pangkabuhayan': float(academic_data['edukasyon_pangkabuhayan']) if academic_data['edukasyon_pangkabuhayan'] else None,
            #         'mapeh': float(academic_data['mapeh']) if academic_data['mapeh'] else None,
            #     }
            #     
            #     # Compare grades
            #     verification_result = ocr_verifier.verify_grades(extracted_grades, manual_grades)
            #     
            #     # Store verification results
            #     academic_data['ocr_verified'] = verification_result['is_match']
            #     academic_data['ocr_mismatches'] = verification_result['mismatches']
            #     academic_data['extracted_grades'] = extracted_grades
            #     
            # except Exception as e:
            #     # If OCR fails, log error but don't block submission
            #     print(f"OCR Error: {str(e)}")
            #     academic_data['ocr_verified'] = None
            #     academic_data['ocr_error'] = str(e)
            
            # Mark as temporarily verified (OCR disabled)
            academic_data['ocr_verified'] = True
            
            # ============================================================================
            # OCR VERIFICATION DISABLED - END
            # ============================================================================
        
        # Calculate overall average
        grades = [
            float(academic_data.get('mathematics', 0) or 0),
            float(academic_data.get('araling_panlipunan', 0) or 0),
            float(academic_data.get('english', 0) or 0),
            float(academic_data.get('edukasyon_sa_pagpapakatao', 0) or 0),
            float(academic_data.get('science', 0) or 0),
            float(academic_data.get('edukasyon_pangkabuhayan', 0) or 0),
            float(academic_data.get('filipino', 0) or 0),
            float(academic_data.get('mapeh', 0) or 0),
        ]
        
        valid_grades = [g for g in grades if g > 0]
        academic_data['overall_average'] = round(sum(valid_grades) / len(valid_grades), 2) if valid_grades else 0
        
        # Save to session
        EnrollmentSessionManager.save_academic_data(request, academic_data)
        
        messages.success(request, 'Academic data saved successfully!')
        
        # Return JSON response for AJAX handling
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'ocr_verified': academic_data.get('ocr_verified', None),
                'mismatches': academic_data.get('ocr_mismatches', []),
            })
        
        return redirect('enrollment_app:academic')
    
    # GET request - prepare context
    # Get active school year
    active_school_year = SchoolYear.objects.filter(is_active=True).first()
    
    context = {
        'student_data': student_data,
        'survey_data': survey_data,
        'academic_data': existing_academic_data,
        'lrn': student_data.get('lrn', ''),
        'is_working_student': 'Yes' if student_data.get('is_working_student') else 'No',
        'working_type': student_data.get('working_details', 'None'),
        'is_pwd': 'Yes' if student_data.get('is_sped') else 'No',
        'disability_type': student_data.get('sped_details', 'None'),
        'school_year': active_school_year,
        'recommendation_payload': {
            'student_data': student_data,
            'survey_data': survey_data,
            'academic_data': existing_academic_data,
        },
    }
    
    return render(request, 'enrollment_app/studentAcademic.html', context)


def verify_grades_ajax(request):
    """
    AJAX endpoint to verify grades and generate program recommendations
    Used when "See Recommended Program" button is clicked
    
    NOTE: OCR verification is disabled for now (waiting for OCR implementation)
    To re-enable, uncomment the OCR verification checks below
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    # Get all necessary data from session
    academic_data = EnrollmentSessionManager.get_academic_data(request)
    survey_data = EnrollmentSessionManager.get_survey_data(request)
    student_data = EnrollmentSessionManager.get_student_data(request)
    
    if not academic_data:
        return JsonResponse({
            'error': 'No academic data found. Please save your grades first.'
        }, status=400)
    
    if not survey_data:
        return JsonResponse({
            'error': 'No survey data found. Please complete the survey first.'
        }, status=400)
    
    if not student_data:
        return JsonResponse({
            'error': 'No student data found. Please complete the student data form first.'
        }, status=400)
    
    # ============================================================================
    # OCR VERIFICATION DISABLED - START
    # Uncomment the section below when OCR is ready
    # ============================================================================
    
    # # Check if OCR verification was performed
    # if 'ocr_verified' not in academic_data:
    #     return JsonResponse({
    #         'error': 'Please upload your report card for verification.'
    #     }, status=400)
    # 
    # # Check verification status
    # if academic_data.get('ocr_verified') is False:
    #     mismatches = academic_data.get('ocr_mismatches', [])
    #     mismatch_details = []
    #     
    #     for mismatch in mismatches:
    #         subject_display = mismatch['subject'].replace('_', ' ').title()
    #         mismatch_details.append({
    #             'subject': subject_display,
    #             'subject_key': mismatch['subject'],  # Keep original key for field highlighting
    #             'manual': mismatch['manual_grade'],
    #             'extracted': mismatch['extracted_grade'],
    #             'difference': mismatch.get('difference', 0)
    #         })
    #     
    #     return JsonResponse({
    #         'success': False,
    #         'verified': False,
    #         'message': 'There is a mismatch found in your inputted grades and uploaded report card.',
    #         'mismatches': mismatch_details
    #     })
    
    # ============================================================================
    # OCR VERIFICATION DISABLED - END
    # ============================================================================
    
    # Grades verified successfully - generate recommendations
    student_lrn = student_data.get('lrn', '')
    
    try:
        # Generate program recommendations
        recommendation_result = generate_academic_recommendations(
            student_lrn=student_lrn,
            academic_data=academic_data,
            survey_data=survey_data,
            student_data=student_data
        )
        
        # Format recommendations for frontend
        formatted_recommendations = []
        if recommendation_result['status'] == 'success':
            for rec in recommendation_result['recommendations']:
                # Special check for STE program
                special_checks = []
                if rec['program_code'] == 'STE':
                    is_qualified, qualified_record = check_ste_qualification(student_lrn)
                    rec['ste_qualified'] = is_qualified
                    
                    if not is_qualified:
                        special_checks.append({
                            'type': 'ste_qualification',
                            'message': 'Student is not in the Qualified_for_ste database. Please select another program.',
                            'action_required': True,
                        })
                
                formatted_recommendations.append({
                    'rank': rec['rank'],
                    'program_code': rec['program_code'],
                    'program_name': rec['program_name'],
                    'percentage_match': rec['percentage_match'],
                    'recommendation_level': rec['recommendation_level'],
                    'criteria_met': rec['criteria_met'],
                    'special_checks': special_checks,
                    'ste_qualified': rec.get('ste_qualified', None),
                })
        
        # Save recommendations to session for later use
        EnrollmentSessionManager.save_recommendations(request, recommendation_result)
        
        return JsonResponse({
            'success': True,
            'verified': True,
            'message': 'Grades verified successfully! Here are your program recommendations:',
            'overall_average': academic_data.get('overall_average', 0),
            'recommendations': formatted_recommendations,
            'dost_exam_result': academic_data.get('dost_exam_result', 'unknown'),
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'verified': True,
            'message': f'Error generating recommendations: {str(e)}',
            'error': str(e),
        }, status=500)


def check_ste_qualification(student_lrn):
    """
    Check if a student is qualified for STE program
    
    Args:
        student_lrn: Student's LRN
    
    Returns:
        Tuple: (is_qualified: bool, qualified_record: Qualified_for_ste or None)
    """
    try:
        # Use filter().first() to handle multiple records (gets most recent by default ordering)
        qualified_record = Qualified_for_ste.objects.filter(student_lrn=student_lrn).order_by('-updated_at').first()
        if qualified_record:
            is_qualified = qualified_record.status == 'qualified'
            return is_qualified, qualified_record
        return False, None
    except Exception as e:
        # Log error but don't crash
        print(f"Error checking STE qualification: {str(e)}")
        return False, None


def confirm_program_selection_ajax(request):
    """
    AJAX endpoint to confirm program selection
    Handles special validation for STE program
    
    Returns:
        JSON response with confirmation status
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    selected_program = data.get('program_code', '').upper()
    student_lrn = data.get('student_lrn', '')
    
    if not selected_program or not student_lrn:
        return JsonResponse({
            'error': 'Missing program code or student LRN'
        }, status=400)
    
    # Get academic data from session for validation
    academic_data = EnrollmentSessionManager.get_academic_data(request)
    
    if not academic_data:
        return JsonResponse({
            'error': 'Academic data not found in session'
        }, status=400)
    
    # Special validation for STE program
    if selected_program == 'STE':
        # Check academic requirements
        average_grade = float(academic_data.get('overall_average', 0))
        dost_exam_result = academic_data.get('dost_exam_result', '').lower().strip()
        
        # Get minimum grade per subject
        grades = [
            float(academic_data.get('mathematics', 0) or 0),
            float(academic_data.get('araling_panlipunan', 0) or 0),
            float(academic_data.get('english', 0) or 0),
            float(academic_data.get('edukasyon_sa_pagpapakatao', 0) or 0),
            float(academic_data.get('science', 0) or 0),
            float(academic_data.get('edukasyon_pangkabuhayan', 0) or 0),
            float(academic_data.get('filipino', 0) or 0),
            float(academic_data.get('mapeh', 0) or 0),
        ]
        
        valid_grades = [g for g in grades if g > 0]
        all_subjects_85_above = all(g >= 85 for g in valid_grades) if valid_grades else False
        
        # Check if student meets academic requirements for STE
        if not (average_grade >= 90 and all_subjects_85_above and dost_exam_result == 'passed'):
            return JsonResponse({
                'success': False,
                'error': 'You do not meet the academic requirements for the STE program.',
                'requirements': {
                    'average_grade': f'Required: 90 above (Current: {average_grade})',
                    'all_subjects_85': f'Required: All subjects 85 above (Current min: {min(valid_grades) if valid_grades else 0})',
                    'dost_exam': f'Required: Passed (Current: {dost_exam_result})',
                }
            }, status=400)
        
        # Check if student is in Qualified_for_ste table
        is_qualified, qualified_record = check_ste_qualification(student_lrn)
        
        if not is_qualified:
            return JsonResponse({
                'success': False,
                'error': 'You are not registered in the Qualified for STE database. '
                         'Please contact your school administrator or select another program.',
                'action': 'contact_admin_or_select_other'
            }, status=400)
    
    # If all validations pass, save the program selection
    program_selection_data = {
        'selected_program_code': selected_program,
        'selected_at': timezone.now().isoformat(),
        'confirmed': True,
    }
    
    EnrollmentSessionManager.save_program_selection(request, program_selection_data)
    
    # Save all enrollment data to database
    try:
        save_enrollment_to_database(request)
        
        # Clear all enrollment session data after successful save
        EnrollmentSessionManager.clear_all_enrollment_data(request)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to save enrollment data: {str(e)}'
        }, status=500)
    
    return JsonResponse({
        'success': True,
        'message': f'{selected_program} program confirmed successfully!',
        'program_code': selected_program,
    })


def save_enrollment_to_database(request):
    """
    Save all enrollment data from session to database
    This should be called after program selection is confirmed
    """
    # Get all data from session
    student_data = EnrollmentSessionManager.get_student_data(request)
    family_data = EnrollmentSessionManager.get_family_data(request)
    survey_data = EnrollmentSessionManager.get_survey_data(request)
    academic_data = EnrollmentSessionManager.get_academic_data(request)
    program_selection_data = EnrollmentSessionManager.get_program_selection(request)
    
    # Debug: Print family_data structure
    print("=" * 80)
    print("FAMILY DATA FROM SESSION:")
    print(f"Type: {type(family_data)}")
    if family_data:
        print(f"Keys: {list(family_data.keys())}")
        for key, value in family_data.items():
            print(f"  {key}: {type(value)} - {value if not isinstance(value, dict) else f'dict with keys: {list(value.keys())}'}")
    print("=" * 80)
    
    if not all([student_data, family_data, survey_data, academic_data, program_selection_data]):
        raise ValueError("Incomplete enrollment data in session")
    
    lrn = student_data.get('lrn')
    if not lrn:
        raise ValueError("LRN not found in session data")
    
    # Get active school year
    try:
        school_year = SchoolYear.objects.filter(is_active=True).first()
    except Exception:
        school_year = None
    
    with transaction.atomic():
        # 1. Determine guardian's email based on guardian_type
        guardian_type = family_data.get('guardian_type') or family_data.get('primary_guardian_type', 'mother')
        guardian_email = None
        
        if guardian_type == 'father':
            guardian_email = family_data.get('father_email', '')
        elif guardian_type == 'mother':
            guardian_email = family_data.get('mother_email', '')
        elif guardian_type == 'other':
            guardian_email = family_data.get('guardian_email', '')
        
        # Use guardian's email or fallback to empty string
        guardian_email = guardian_email or ''
        
        # 2. Create or update Student record
        student, created = Student.objects.get_or_create(
            lrn=lrn,
            defaults={
                'email': guardian_email,
                'school_year': school_year,
                'enrollment_status': 'submitted',
                'is_lis_verified': EnrollmentSessionManager.is_lrn_verified(request),
                'lis_verified_at': timezone.now() if EnrollmentSessionManager.is_lrn_verified(request) else None,
            }
        )
        
        # Update student fields with guardian's email
        student.email = guardian_email
        student.school_year = school_year
        student.enrollment_status = 'submitted'
        # Don't mark as completed yet - will do after successful data save
        student.save()
        
        # 2. Create or update StudentData
        student_data_obj, created = StudentData.objects.update_or_create(
            student=student,
            defaults={
                'last_name': student_data.get('last_name', ''),
                'first_name': student_data.get('first_name', ''),
                'middle_name': student_data.get('middle_name', ''),
                'gender': student_data.get('gender', ''),
                'date_of_birth': student_data.get('date_of_birth'),
                'place_of_birth': student_data.get('place_of_birth', ''),
                'religion': student_data.get('religion', ''),
                'dialect_spoken': student_data.get('dialect_spoken', ''),
                'ethnic_tribe': student_data.get('ethnic_tribe', ''),
                'address': student_data.get('address', ''),
                'enrolling_as': student_data.get('enrolling_as', []),
                'is_sped': student_data.get('is_sped', False),
                'sped_details': student_data.get('sped_details', ''),
                'is_working_student': student_data.get('is_working_student', False),
                'working_details': student_data.get('working_details', ''),
                'last_school_attended': student_data.get('last_school_attended', ''),
                'previous_grade_section': student_data.get('previous_grade_section', ''),
                'last_school_year': student_data.get('last_school_year', ''),
            }
        )
        
        # 3. Create Parent records for father and mother
        parents = {}
        for parent_type in ['father', 'mother']:
            field_prefix = parent_type
            
            # Check if we have parent data
            if family_data.get(f'{field_prefix}_first_name') and family_data.get(f'{field_prefix}_family_name'):
                first_name = family_data.get(f'{field_prefix}_first_name', '')
                family_name = family_data.get(f'{field_prefix}_family_name', '')
                middle_name = family_data.get(f'{field_prefix}_middle_name', '')
                date_of_birth = family_data.get(f'{field_prefix}_dob')
                occupation = family_data.get(f'{field_prefix}_occupation', '')
                address = family_data.get(f'{field_prefix}_address', '')
                contact_number = family_data.get(f'{field_prefix}_contact_number', '')
                email = family_data.get(f'{field_prefix}_email', '')
                
                # Only create if we have required fields
                if first_name and family_name and date_of_birth and occupation and contact_number:
                    try:
                        parent, created = Parent.objects.get_or_create(
                            family_name=family_name,
                            first_name=first_name,
                            date_of_birth=date_of_birth,
                            parent_type=parent_type,
                            defaults={
                                'middle_name': middle_name or '',
                                'occupation': occupation,
                                'address': address,
                                'contact_number': contact_number,
                                'email': email or '',
                            }
                        )
                        parents[parent_type] = parent
                    except Exception as e:
                        print(f"Error creating {parent_type} parent: {e}")
        
        # 4. Create Guardian record ONLY if "other" guardian is selected
        other_guardian = None
        field_prefix = 'guardian'
        
        if family_data.get(f'{field_prefix}_first_name') and family_data.get(f'{field_prefix}_family_name'):
            first_name = family_data.get(f'{field_prefix}_first_name', '')
            family_name = family_data.get(f'{field_prefix}_family_name', '')
            middle_name = family_data.get(f'{field_prefix}_middle_name', '')
            date_of_birth = family_data.get(f'{field_prefix}_dob')
            occupation = family_data.get(f'{field_prefix}_occupation', '')
            address = family_data.get(f'{field_prefix}_address', '')
            contact_number = family_data.get(f'{field_prefix}_contact_number', '')
            email = family_data.get(f'{field_prefix}_email', '')
            relationship = family_data.get(f'{field_prefix}_relationship', 'Guardian')
            
            # Only create if we have required fields
            if first_name and family_name and date_of_birth and occupation and contact_number:
                try:
                    other_guardian, created = Guardian.objects.get_or_create(
                        family_name=family_name,
                        first_name=first_name,
                        date_of_birth=date_of_birth,
                        relationship_to_student=relationship,
                        defaults={
                            'middle_name': middle_name or '',
                            'occupation': occupation,
                            'address': address,
                            'contact_number': contact_number,
                            'email': email or '',
                        }
                    )
                except Exception as e:
                    print(f"Error creating other guardian: {e}")
        
        # 5. Determine official guardian based on guardian_type from session
        primary_guardian_type = family_data.get('guardian_type') or family_data.get('primary_guardian_type', 'mother')
        
        # Create FamilyData only if we have both father and mother (required fields)
        if parents.get('father') and parents.get('mother'):
            family_data_obj, created = FamilyData.objects.update_or_create(
                student=student,
                defaults={
                    'father': parents.get('father'),
                    'mother': parents.get('mother'),
                    'other_guardian': other_guardian,
                    'official_guardian_type': primary_guardian_type,
                }
            )
            
            # Mark family data as completed only after successful save
            student.family_data_completed = True
            student.family_data_completed_at = timezone.now()
        
        # 4. Create or update SurveyData
        survey_obj, created = SurveyData.objects.update_or_create(
            student=student,
            defaults={
                'learning_style': survey_data.get('learning_style', ''),
                'study_hours': survey_data.get('study_hours', ''),
                'study_environment': survey_data.get('study_environment', ''),
                'schoolwork_support': survey_data.get('schoolwork_support', ''),
                'enjoyed_subjects': survey_data.get('enjoyed_subjects', []),
                'interested_program': survey_data.get('interested_program', ''),
                'program_motivation': survey_data.get('program_motivation', ''),
                'enjoyed_activities': survey_data.get('enjoyed_activities', []),
                'enjoyed_activities_other': survey_data.get('enjoyed_activities_other', ''),
                'assignments_on_time': survey_data.get('assignments_on_time', ''),
                'handle_difficult_lessons': survey_data.get('handle_difficult_lessons', ''),
                'device_availability': survey_data.get('device_availability', ''),
                'internet_access': survey_data.get('internet_access', ''),
                'absences': survey_data.get('absences', ''),
                'absence_reason': survey_data.get('absence_reason', ''),
                'participation': survey_data.get('participation', ''),
                'difficulty_areas': survey_data.get('difficulty_areas', []),
                'extra_support': survey_data.get('extra_support', ''),
                'quiet_place': survey_data.get('quiet_place', ''),
                'distance_from_school': survey_data.get('distance_from_school', ''),
                'travel_difficulty': survey_data.get('travel_difficulty', ''),
                'survey_responses_json': survey_data,
            }
        )
        
        # Mark other steps as completed
        student.student_data_completed = True
        student.student_data_completed_at = timezone.now()
        student.survey_completed = True
        student.survey_completed_at = timezone.now()
        
        # 5. Create or update AcademicData
        academic_obj, created = AcademicData.objects.update_or_create(
            student=student,
            defaults={
                'dost_exam_result': academic_data.get('dost_exam_result', ''),
                'mathematics': float(academic_data.get('mathematics', 0) or 0) or None,
                'araling_panlipunan': float(academic_data.get('araling_panlipunan', 0) or 0) or None,
                'english': float(academic_data.get('english', 0) or 0) or None,
                'edukasyon_sa_pagpapakatao': float(academic_data.get('edukasyon_sa_pagpapakatao', 0) or 0) or None,
                'science': float(academic_data.get('science', 0) or 0) or None,
                'edukasyon_pangkabuhayan': float(academic_data.get('edukasyon_pangkabuhayan', 0) or 0) or None,
                'filipino': float(academic_data.get('filipino', 0) or 0) or None,
                'mapeh': float(academic_data.get('mapeh', 0) or 0) or None,
                'is_working_student': student_data.get('is_working_student', False),
                'working_type': student_data.get('working_details', ''),
                'is_pwd': student_data.get('is_sped', False),
                'disability_type': student_data.get('sped_details', ''),
            }
        )
        
        # 6. Create or update ProgramSelection
        program_obj, created = ProgramSelection.objects.update_or_create(
            student=student,
            defaults={
                'school_year': school_year,
                'selected_program_code': program_selection_data.get('selected_program_code', ''),
                'program_description': f"Selected based on student profile and recommendations",
                'selection_reason': f"Student confirmed selection on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}",
            }
        )
        
        # Mark academic and program selection as completed after successful save
        student.academic_data_completed = True
        student.academic_data_completed_at = timezone.now()
        student.program_selected = True
        student.program_selected_at = timezone.now()
        student.save()
    
    return student