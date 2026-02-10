from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from ..services.session_manager import EnrollmentSessionManager
from ..services.ocr_service import GeminiAPIKeyOCR
from ..services.recommendation_service import generate_academic_recommendations
from coordinator_app.models import Qualified_for_ste
from ..models import (
    Student, StudentData, Parent, Guardian, FamilyData, 
    SurveyData, AcademicData, ProgramSelection
)
from admin_app.models import SchoolYear, DocumentRequirement
import os
import uuid
import json
import shutil
from datetime import datetime


def academic_form(request):
    """
    Handle student academic data form with OCR grade extraction and name verification only.
    Auto-fills grades after successful name verification.
    Requires all previous forms to be completed.
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
    lrn = student_data.get('lrn') if student_data else None
    if lrn:
        try:
            db_sd = StudentData.objects.get(student__lrn=lrn)
            student_data['agreed_to_terms'] = db_sd.agreed_to_terms
        except StudentData.DoesNotExist:
            student_data['agreed_to_terms'] = False
    
    survey_data = EnrollmentSessionManager.get_survey_data(request)
    existing_academic_data = EnrollmentSessionManager.get_academic_data(request) or {}
    
    if request.method == 'POST':
        # ============================================================================
        # AJAX OCR EXTRACTION - Name Verification + Auto-fill Grades
        # ============================================================================
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.POST.get('ajax_extract') == '1':
            report_card = request.FILES.get('report_card')
            report_card_back = request.FILES.get('report_card_back')
            extracted_grades = {}
            name_verification = {}
            success = False
            error = None
            
            try:
                ocr_verifier = GeminiAPIKeyOCR()
                from concurrent.futures import ThreadPoolExecutor
                
                # Process both pages if available
                if report_card and report_card_back:
                    # Save both files to temp directory
                    temp_dir = os.path.join(settings.BASE_DIR, 'temp_uploads')
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    front_filename = f"{uuid.uuid4()}{os.path.splitext(report_card.name)[1]}"
                    front_path = os.path.join(temp_dir, front_filename)
                    with open(front_path, 'wb+') as destination:
                        for chunk in report_card.chunks():
                            destination.write(chunk)
                    
                    back_filename = f"{uuid.uuid4()}{os.path.splitext(report_card_back.name)[1]}"
                    back_path = os.path.join(temp_dir, back_filename)
                    with open(back_path, 'wb+') as destination:
                        for chunk in report_card_back.chunks():
                            destination.write(chunk)
                    
                    # Process both pages in parallel
                    with ThreadPoolExecutor() as executor:
                        future_front = executor.submit(ocr_verifier.extract_grades_and_name_from_image, front_path)
                        future_back = executor.submit(ocr_verifier.extract_grades_and_name_from_image, back_path)
                        front_result = future_front.result()
                        back_result = future_back.result()
                    
                    # Extract name from front page
                    extracted_name = front_result.get('student_name') or back_result.get('student_name')
                    
                    # Extract grades from back page
                    grades = back_result.get('grades') or {}
                    for subject, grade in grades.items():
                        if grade not in [None, '', 0]:
                            extracted_grades[subject] = grade
                    
                elif report_card:
                    # Single page processing
                    temp_dir = os.path.join(settings.BASE_DIR, 'temp_uploads')
                    os.makedirs(temp_dir, exist_ok=True)
                    unique_filename = f"{uuid.uuid4()}{os.path.splitext(report_card.name)[1]}"
                    temp_file_path = os.path.join(temp_dir, unique_filename)
                    with open(temp_file_path, 'wb+') as destination:
                        for chunk in report_card.chunks():
                            destination.write(chunk)
                    
                    result = ocr_verifier.extract_grades_and_name_from_image(temp_file_path)
                    extracted_name = result.get('student_name')
                    grades = result.get('grades') or {}
                    for subject, grade in grades.items():
                        if grade not in [None, '', 0]:
                            extracted_grades[subject] = grade
                
                # Get registered student name from session
                last_name = student_data.get('last_name', '').strip()
                first_name = student_data.get('first_name', '').strip()
                middle_name = student_data.get('middle_name', '').strip()
                
                name_parts = []
                if first_name:
                    name_parts.append(first_name)
                if middle_name:
                    name_parts.append(middle_name)
                
                if last_name and name_parts:
                    registered_name = f"{last_name}, {' '.join(name_parts)}"
                elif last_name:
                    registered_name = last_name
                elif name_parts:
                    registered_name = ' '.join(name_parts)
                else:
                    registered_name = ''
                
                # Verify name match (ONLY verification needed)
                name_verification = ocr_verifier.verify_student_name(extracted_name, registered_name)
                
                # Save verification results in session
                academic_data = EnrollmentSessionManager.get_academic_data(request) or {}
                academic_data['name_verified'] = name_verification['is_match']
                academic_data['extracted_name'] = name_verification['extracted']
                academic_data['registered_name'] = name_verification['registered']
                academic_data['name_similarity'] = name_verification['similarity']
                academic_data['name_verification_reason'] = name_verification['reason']
                academic_data['extracted_grades'] = extracted_grades

                # Store report card temp paths in session for later DB save
                if report_card and report_card_back:
                    academic_data['report_card_path'] = front_path
                    academic_data['report_card_name'] = report_card.name
                    academic_data['report_card_back_path'] = back_path
                    academic_data['report_card_back_name'] = report_card_back.name
                elif report_card:
                    academic_data['report_card_path'] = temp_file_path
                    academic_data['report_card_name'] = report_card.name

                EnrollmentSessionManager.save_academic_data(request, academic_data)
                
                success = True
                
            except Exception as e:
                error = str(e)
                print(f"OCR Error: {error}")
            
            return JsonResponse({
                'success': success,
                'extracted_grades': extracted_grades,
                'name_verification': name_verification,
                'error': error,
            })
        
        # ============================================================================
        # FORM SUBMISSION - Save Academic Data
        # ============================================================================
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
        
        # Preserve existing data
        academic_data['report_card_path'] = existing_academic_data.get('report_card_path', '')
        academic_data['report_card_name'] = existing_academic_data.get('report_card_name', '')
        academic_data['report_card_back_path'] = existing_academic_data.get('report_card_back_path', '')
        academic_data['report_card_back_name'] = existing_academic_data.get('report_card_back_name', '')
        academic_data['name_verified'] = existing_academic_data.get('name_verified', None)
        academic_data['extracted_name'] = existing_academic_data.get('extracted_name', '')
        academic_data['registered_name'] = existing_academic_data.get('registered_name', '')
        academic_data['extracted_grades'] = existing_academic_data.get('extracted_grades', {})
        
        # Handle report card uploads
        if 'report_card' in request.FILES:
            report_card = request.FILES['report_card']
            report_card_back = request.FILES.get('report_card_back')
            
            # Validate file
            if not report_card:
                messages.error(request, 'Please select a valid report card file.')
                return redirect('enrollment_app:academic')
            
            # Check file size (max 10MB)
            if report_card.size > 10 * 1024 * 1024:
                messages.error(request, 'Report card file is too large. Maximum size is 10MB.')
                return redirect('enrollment_app:academic')
            
            # Check file type
            allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'pdf', 'bmp', 'webp'}
            file_extension = os.path.splitext(report_card.name)[1].lower().lstrip('.')
            if file_extension not in allowed_extensions:
                messages.error(request, f'Invalid file type. Allowed types: {", ".join(allowed_extensions)}')
                return redirect('enrollment_app:academic')
            
            # Create temp directory
            temp_dir = os.path.join(settings.BASE_DIR, 'temp_uploads')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Save front page
            unique_filename = f"{uuid.uuid4()}{os.path.splitext(report_card.name)[1]}"
            temp_file_path = os.path.join(temp_dir, unique_filename)
            with open(temp_file_path, 'wb+') as destination:
                for chunk in report_card.chunks():
                    destination.write(chunk)
            
            academic_data['report_card_path'] = temp_file_path
            academic_data['report_card_name'] = report_card.name
            
            # Save back page if provided
            if report_card_back:
                if report_card_back.size > 10 * 1024 * 1024:
                    messages.error(request, 'Back page file is too large. Maximum size is 10MB.')
                    return redirect('enrollment_app:academic')
                
                back_extension = os.path.splitext(report_card_back.name)[1].lower().lstrip('.')
                if back_extension not in allowed_extensions:
                    messages.error(request, f'Invalid file type for back page. Allowed types: {", ".join(allowed_extensions)}')
                    return redirect('enrollment_app:academic')
                
                back_unique_filename = f"{uuid.uuid4()}{os.path.splitext(report_card_back.name)[1]}"
                back_temp_file_path = os.path.join(temp_dir, back_unique_filename)
                with open(back_temp_file_path, 'wb+') as destination:
                    for chunk in report_card_back.chunks():
                        destination.write(chunk)
                
                academic_data['report_card_back_path'] = back_temp_file_path
                academic_data['report_card_back_name'] = report_card_back.name
        
        # ============================================================================
        # HANDLE DOCUMENT UPLOADS
        # ============================================================================
        document_submissions = existing_academic_data.get('document_submissions', {})
        
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
        
        academic_data['document_submissions'] = document_submissions
        
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
        overall_average = round(sum(valid_grades) / len(valid_grades), 2) if valid_grades else 0
        academic_data['overall_average'] = overall_average
        # Also save as grade_6_final_average for ML compatibility
        academic_data['grade_6_final_average'] = overall_average

        # ============================================================================
        # OCR GRADE VERIFICATION - Compare extracted grades with submitted grades
        # Uses inline comparison (3-point tolerance) to avoid API dependency
        # ============================================================================
        extracted_grades = academic_data.get('extracted_grades') or existing_academic_data.get('extracted_grades', {})
        if extracted_grades:
            subject_key_map = {
                'filipino': 'Filipino',
                'english': 'English',
                'mathematics': 'Mathematics',
                'science': 'Science',
                'araling_panlipunan': 'ArPan',
                'edukasyon_sa_pagpapakatao': 'EsP',
                'edukasyon_pangkabuhayan': 'EPP/TLE',
                'mapeh': 'MAPEH',
            }
            manual_grades = {}
            for form_key, ocr_key in subject_key_map.items():
                value = academic_data.get(form_key)
                manual_grades[ocr_key] = float(value) if value else None

            # Inline grade comparison with 3-point tolerance
            TOLERANCE = 3.0
            mismatches = []
            matched = 0
            total_subjects = 0

            for subject, extracted_val in extracted_grades.items():
                manual_val = manual_grades.get(subject)
                if extracted_val is None or manual_val is None:
                    continue
                total_subjects += 1
                try:
                    ext = float(extracted_val)
                    man = float(manual_val)
                    if abs(ext - man) > TOLERANCE:
                        mismatches.append({
                            'subject': subject,
                            'expected': man,
                            'actual': ext,
                            'reason': f'Difference of {abs(ext - man):.1f} exceeds tolerance of {TOLERANCE}'
                        })
                    else:
                        matched += 1
                except (ValueError, TypeError):
                    continue

            is_match = len(mismatches) == 0 and total_subjects > 0
            confidence = round((matched / total_subjects * 100), 1) if total_subjects > 0 else 0

            academic_data['ocr_verified'] = is_match
            academic_data['ocr_mismatches'] = mismatches
            academic_data['extracted_grades'] = extracted_grades
            academic_data['ocr_confidence'] = confidence

            print(f"OCR Grade Verification: is_match={is_match}, confidence={confidence}%, mismatches={len(mismatches)}")
        # ============================================================================
        # END OCR GRADE VERIFICATION
        # ============================================================================

        # Save to session
        EnrollmentSessionManager.save_academic_data(request, academic_data)

        messages.success(request, 'Academic data saved successfully!')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'ocr_verified': academic_data.get('ocr_verified', None),
                'mismatches': academic_data.get('ocr_mismatches', []),
            })

        return redirect('enrollment_app:academic')
    
    # GET request - prepare context
    active_school_year = SchoolYear.objects.filter(is_active=True).first()
    
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
        'requirements': requirements,
    }
    
    return render(request, 'enrollment_app/studentAcademic.html', context)


def verify_grades_ajax(request):
    """
    AJAX endpoint to verify grades and generate program recommendations.
    Checks both name verification AND OCR grade verification before proceeding.
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
    # DUAL VERIFICATION GATE: Both name AND grade verification must pass
    # ============================================================================
    if (
        academic_data.get('name_verified') is not True or
        academic_data.get('ocr_verified') is not True
    ):
        # Handle name verification failures
        if academic_data.get('name_verified') is None:
            name_error = academic_data.get('name_error', 'Unknown name verification error occurred')
            return JsonResponse({
                'error': f'Name verification failed: {name_error}',
                'verified': False,
                'success': False,
                'message': f'Name verification failed: {name_error}'
            }, status=400)

        if academic_data.get('name_verified') is False:
            name_mismatch_reason = academic_data.get('name_verification_reason', 'Name mismatch')
            return JsonResponse({
                'success': False,
                'verified': False,
                'message': f'Name Verification Failed: {name_mismatch_reason}',
                'name_verification': {
                    'is_match': False,
                    'extracted': academic_data.get('extracted_name'),
                    'registered': academic_data.get('registered_name'),
                    'similarity': academic_data.get('name_similarity', 0),
                    'reason': name_mismatch_reason
                }
            })

        # Handle OCR grade verification failures
        if academic_data.get('ocr_verified') is None:
            ocr_error = academic_data.get('ocr_error', 'Unknown OCR error occurred')
            return JsonResponse({
                'error': f'Grade verification failed: {ocr_error}',
                'verified': False,
                'success': False,
                'message': f'Grade verification failed: {ocr_error}'
            }, status=400)

        if academic_data.get('ocr_verified') is False:
            mismatches = academic_data.get('ocr_mismatches', [])
            mismatch_details = []
            for mismatch in mismatches:
                subject_display = mismatch['subject'].replace('_', ' ').title()
                expected = mismatch.get('expected')
                actual = mismatch.get('actual')
                difference = round(abs(expected - actual), 2) if expected is not None and actual is not None else None
                mismatch_details.append({
                    'subject': subject_display,
                    'subject_key': mismatch['subject'],
                    'manual': expected,
                    'extracted': actual,
                    'difference': difference,
                    'reason': mismatch.get('reason', 'unknown')
                })
            return JsonResponse({
                'success': False,
                'verified': False,
                'message': 'There is a mismatch found in your inputted grades and uploaded report card. Please review and correct the mismatched grades.',
                'mismatches': mismatch_details
            })

    # ============================================================================
    # VERIFICATION PASSED - Generate recommendations
    # ============================================================================

    # Check if recommendations are already in session and valid
    session_recommendations = EnrollmentSessionManager.get_recommendations(request)
    if session_recommendations and session_recommendations.get('status') == 'success':
        formatted_recommendations = []
        for rec in session_recommendations['recommendations']:
            special_checks = []
            if rec['program_code'] == 'STE':
                is_qualified, qualified_record = check_ste_qualification(student_data.get('lrn', ''))
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
                'regular_track': rec.get('regular_track', None),
            })
        return JsonResponse({
            'success': True,
            'verified': True,
            'message': 'Grades verified successfully! Here are your program recommendations:',
            'overall_average': academic_data.get('overall_average', 0),
            'recommendations': formatted_recommendations,
            'dost_exam_result': academic_data.get('dost_exam_result', 'unknown'),
        })

    # Generate new recommendations
    student_lrn = student_data.get('lrn', '')
    try:
        recommendation_result = generate_academic_recommendations(
            student_lrn=student_lrn,
            academic_data=academic_data,
            survey_data=survey_data,
            student_data=student_data
        )
        formatted_recommendations = []
        if recommendation_result['status'] == 'success':
            for rec in recommendation_result['recommendations']:
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
                    'regular_track': rec.get('regular_track', None),
                })
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
    """Check if a student is qualified for STE program"""
    try:
        qualified_record = Qualified_for_ste.objects.filter(student_lrn=student_lrn).order_by('-updated_at').first()
        if qualified_record:
            is_qualified = qualified_record.status == 'qualified'
            return is_qualified, qualified_record
        return False, None
    except Exception as e:
        print(f"Error checking STE qualification: {str(e)}")
        return False, None


def confirm_program_selection_ajax(request):
    """AJAX endpoint to confirm program selection"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    selected_program = data.get('program_code', '').upper().strip()
    student_lrn = data.get('student_lrn', '')
    regular_track = (data.get('regular_track') or '').upper().strip() or None
    program_name = data.get('program_name', '')
    
    # Handle TOP5/HETERO as Regular tracks
    if selected_program in ['TOP5', 'TOP 5', 'HETERO']:
        regular_track = 'TOP5' if 'TOP' in selected_program else 'HETERO'
        selected_program = 'REGULAR'
    elif selected_program == 'REGULAR' and regular_track in ['TOP5', 'TOP 5', 'HETERO']:
        regular_track = 'TOP5' if 'TOP' in regular_track else 'HETERO'
    
    # Fallback: extract track from program_name
    if selected_program == 'REGULAR' and not regular_track:
        name_lower = program_name.lower() if program_name else ''
        if 'top' in name_lower or 'top-5' in name_lower or 'top 5' in name_lower:
            regular_track = 'TOP5'
        elif 'hetero' in name_lower:
            regular_track = 'HETERO'
        
        if not regular_track:
            try:
                program_selection = EnrollmentSessionManager.get_program_selection(request)
                if program_selection:
                    stored_track = program_selection.get('regular_track')
                    if stored_track:
                        regular_track = stored_track.upper()
            except Exception:
                pass
    
    if not selected_program or not student_lrn:
        return JsonResponse({'error': 'Missing program code or student LRN'}, status=400)
    
    academic_data = EnrollmentSessionManager.get_academic_data(request)
    if not academic_data:
        return JsonResponse({'error': 'Academic data not found in session'}, status=400)
    
    # Special validation for STE
    if selected_program == 'STE':
        average_grade = float(academic_data.get('overall_average', 0))
        dost_exam_result = academic_data.get('dost_exam_result', '').lower().strip()
        
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
        
        is_qualified, qualified_record = check_ste_qualification(student_lrn)
        if not is_qualified:
            return JsonResponse({
                'success': False,
                'error': 'You are not registered in the Qualified for STE database. '
                         'Please contact your school administrator or select another program.',
                'action': 'contact_admin_or_select_other'
            }, status=400)
    
    # Save program selection
    program_selection_data = {
        'selected_program_code': selected_program,
        'regular_track': regular_track,
        'selected_at': timezone.now().isoformat(),
        'confirmed': True,
    }
    
    EnrollmentSessionManager.save_program_selection(request, program_selection_data)
    
    # Save to database
    try:
        save_enrollment_to_database(request)
        EnrollmentSessionManager.clear_all_enrollment_data(request)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Failed to save enrollment data: {str(e)}'
        }, status=500)
    
    return JsonResponse({
        'success': True,
        'message': f"{selected_program} program confirmed successfully{f' (Regular track: {regular_track})' if regular_track else ''}!",
        'program_code': selected_program,
        'regular_track': regular_track,
    })


def save_enrollment_to_database(request):
    """Save all enrollment data from session to database"""
    student_data = EnrollmentSessionManager.get_student_data(request)
    family_data = EnrollmentSessionManager.get_family_data(request)
    survey_data = EnrollmentSessionManager.get_survey_data(request)
    academic_data = EnrollmentSessionManager.get_academic_data(request)
    program_selection_data = EnrollmentSessionManager.get_program_selection(request)
    
    if not all([student_data, family_data, survey_data, academic_data, program_selection_data]):
        raise ValueError("Incomplete enrollment data in session")
    
    lrn = student_data.get('lrn')
    if not lrn:
        raise ValueError("LRN not found in session data")
    
    try:
        school_year = SchoolYear.objects.filter(is_active=True).first()
    except Exception:
        school_year = None
    
    with transaction.atomic():
        # Determine guardian email
        guardian_type = family_data.get('guardian_type') or family_data.get('primary_guardian_type', 'mother')
        guardian_email = None
        
        if guardian_type == 'father':
            guardian_email = family_data.get('father_email', '')
        elif guardian_type == 'mother':
            guardian_email = family_data.get('mother_email', '')
        elif guardian_type == 'other':
            guardian_email = family_data.get('guardian_email', '')
        
        guardian_email = guardian_email or ''
        
        # Create/update Student
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
        
        student.email = guardian_email
        student.school_year = school_year
        student.enrollment_status = 'submitted'
        student.save()
        
        # Create/update StudentData
        date_of_birth_value = student_data.get('date_of_birth')
        if isinstance(date_of_birth_value, str):
            from datetime import datetime
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

        student_data_obj, created = StudentData.objects.update_or_create(
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
                'student_photo': student_photo_file if student_photo_file else student_data_obj.student_photo if not created else '',
            }
        )
        
        # Create Parent records
        parents = {}
        for parent_type in ['father', 'mother']:
            field_prefix = parent_type
            
            if family_data.get(f'{field_prefix}_first_name') and family_data.get(f'{field_prefix}_family_name'):
                first_name = family_data.get(f'{field_prefix}_first_name', '')
                family_name = family_data.get(f'{field_prefix}_family_name', '')
                middle_name = family_data.get(f'{field_prefix}_middle_name', '')
                date_of_birth = family_data.get(f'{field_prefix}_dob')
                
                if isinstance(date_of_birth, str):
                    from datetime import datetime
                    try:
                        date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        date_of_birth = None
                
                occupation = family_data.get(f'{field_prefix}_occupation', '')
                address = family_data.get(f'{field_prefix}_address', '')
                contact_number = family_data.get(f'{field_prefix}_contact_number', '')
                email = family_data.get(f'{field_prefix}_email', '')
                
                contact_number = contact_number.strip()[:20]
                
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
        
        # Create Guardian (if "other")
        other_guardian = None
        field_prefix = 'guardian'
        
        if family_data.get(f'{field_prefix}_first_name') and family_data.get(f'{field_prefix}_family_name'):
            first_name = family_data.get(f'{field_prefix}_first_name', '')
            family_name = family_data.get(f'{field_prefix}_family_name', '')
            middle_name = family_data.get(f'{field_prefix}_middle_name', '')
            date_of_birth = family_data.get(f'{field_prefix}_dob')
            
            if isinstance(date_of_birth, str):
                from datetime import datetime
                try:
                    date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    date_of_birth = None
            
            occupation = family_data.get(f'{field_prefix}_occupation', '')
            address = family_data.get(f'{field_prefix}_address', '')
            contact_number = family_data.get(f'{field_prefix}_contact_number', '')
            email = family_data.get(f'{field_prefix}_email', '')
            relationship = family_data.get(f'{field_prefix}_relationship', 'Guardian')
            
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
        
        # Create FamilyData
        primary_guardian_type = family_data.get('guardian_type') or family_data.get('primary_guardian_type', 'mother')
        guardian_record = None
        if primary_guardian_type == 'father':
            guardian_record = parents.get('father')
        elif primary_guardian_type == 'mother':
            guardian_record = parents.get('mother')
        elif primary_guardian_type == 'other':
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

            family_data_obj, created = FamilyData.objects.update_or_create(
                student=student,
                defaults={
                    'father': parents.get('father'),
                    'mother': parents.get('mother'),
                    'other_guardian': other_guardian if primary_guardian_type == 'other' else None,
                    'official_guardian_type': primary_guardian_type,
                    'parent_photo': parent_photo_file if parent_photo_file else (family_data_obj.parent_photo if not created and hasattr(family_data_obj, 'parent_photo') else ''),
                }
            )
            
            student.family_data_completed = True
            student.family_data_completed_at = timezone.now()
        
        # Create SurveyData
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
        
        student.student_data_completed = True
        student.student_data_completed_at = timezone.now()
        student.survey_completed = True
        student.survey_completed_at = timezone.now()
        
        # Create AcademicData
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

        # Save report card to AcademicData.report_card FileField
        # This is CRITICAL for AI auto-processing: _has_report_card() checks this field
        report_card_path = academic_data.get('report_card_path', '')
        if report_card_path and os.path.exists(report_card_path):
            from django.core.files import File as DjangoFile
            report_card_name = academic_data.get('report_card_name', os.path.basename(report_card_path))
            with open(report_card_path, 'rb') as rc_file:
                academic_obj.report_card.save(report_card_name, DjangoFile(rc_file), save=True)

        # Save Document Submissions
        document_submissions = academic_data.get('document_submissions', {})
        if document_submissions:
            from ..models import StudentDocumentSubmission
            from django.core.files import File

            for req_id, doc_info in document_submissions.items():
                try:
                    requirement = DocumentRequirement.objects.get(id=req_id)
                    temp_file_path = doc_info['file_path']
                    if os.path.exists(temp_file_path):
                        with open(temp_file_path, 'rb') as temp_file:
                            submission, created = StudentDocumentSubmission.objects.update_or_create(
                                student=student,
                                requirement=requirement,
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
                            print(f"Warning: Could not delete temp file {temp_file_path}: {e}")
                except DocumentRequirement.DoesNotExist:
                    print(f"Warning: DocumentRequirement with ID {req_id} not found")
                except Exception as e:
                    print(f"Error saving document submission for requirement {req_id}: {e}")

        # Mark completion flags
        student.academic_data_completed = True
        student.academic_data_completed_at = timezone.now()
        student.program_selected = True
        student.program_selected_at = timezone.now()
        student.save()

        # Create ProgramSelection
        regular_track = (program_selection_data.get('regular_track') or '').upper() or None
        selected_program_code = program_selection_data.get('selected_program_code', '')

        if selected_program_code == 'REGULAR' and not regular_track:
            program_name = program_selection_data.get('program_name', '')
            if program_name:
                name_lower = program_name.lower()
                if 'top' in name_lower:
                    regular_track = 'TOP5'
                elif 'hetero' in name_lower:
                    regular_track = 'HETERO'

            if not regular_track:
                try:
                    from enrollment_app.services.recommendation_service import generate_academic_recommendations
                    rec_result = generate_academic_recommendations(
                        student.lrn,
                        EnrollmentSessionManager.get_academic_data(request) or {},
                        EnrollmentSessionManager.get_survey_data(request) or {},
                        EnrollmentSessionManager.get_student_data(request) or {}
                    )
                    if rec_result and rec_result.get('recommendations'):
                        for rec in rec_result['recommendations']:
                            if rec.get('program_code') == 'REGULAR' and rec.get('regular_track'):
                                regular_track = rec['regular_track'].upper()
                                break
                except Exception as e:
                    print(f"DEBUG: ML fallback failed: {e}")

            if not regular_track:
                regular_track = 'HETERO'

        track_note = f" (Regular track: {regular_track})" if regular_track else ''

        program_obj, created = ProgramSelection.objects.update_or_create(
            student=student,
            defaults={
                'school_year': school_year,
                'selected_program_code': program_selection_data.get('selected_program_code', ''),
                'regular_track': regular_track,
                'program_description': f"Selected based on student profile and recommendations{track_note}",
                'selection_reason': f"Student confirmed selection on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}{track_note}",
            }
        )
    
    return student