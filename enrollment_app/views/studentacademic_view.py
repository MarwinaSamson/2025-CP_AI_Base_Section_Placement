from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from ..services.session_manager import EnrollmentSessionManager
from ..services.ocr_service import OCRGradeVerifier
import os
import uuid


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
            
            # Perform OCR verification
            try:
                ocr_verifier = OCRGradeVerifier()
                
                # Extract grades from uploaded image
                extracted_grades = ocr_verifier.extract_grades_from_image(temp_file_path)
                
                # Prepare manual grades for comparison
                manual_grades = {
                    'filipino': float(academic_data['filipino']) if academic_data['filipino'] else None,
                    'english': float(academic_data['english']) if academic_data['english'] else None,
                    'mathematics': float(academic_data['mathematics']) if academic_data['mathematics'] else None,
                    'science': float(academic_data['science']) if academic_data['science'] else None,
                    'araling_panlipunan': float(academic_data['araling_panlipunan']) if academic_data['araling_panlipunan'] else None,
                    'edukasyon_sa_pagpapakatao': float(academic_data['edukasyon_sa_pagpapakatao']) if academic_data['edukasyon_sa_pagpapakatao'] else None,
                    'edukasyon_pangkabuhayan': float(academic_data['edukasyon_pangkabuhayan']) if academic_data['edukasyon_pangkabuhayan'] else None,
                    'mapeh': float(academic_data['mapeh']) if academic_data['mapeh'] else None,
                }
                
                # Compare grades
                verification_result = ocr_verifier.verify_grades(extracted_grades, manual_grades)
                
                # Store verification results
                academic_data['ocr_verified'] = verification_result['is_match']
                academic_data['ocr_mismatches'] = verification_result['mismatches']
                academic_data['extracted_grades'] = extracted_grades
                
            except Exception as e:
                # If OCR fails, log error but don't block submission
                print(f"OCR Error: {str(e)}")
                academic_data['ocr_verified'] = None
                academic_data['ocr_error'] = str(e)
        
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
        
        return redirect('enrollment_app:student_academic')
    
    # GET request - prepare context
    context = {
        'student_data': student_data,
        'academic_data': existing_academic_data,
        'lrn': student_data.get('lrn', ''),
        'is_working_student': 'Yes' if student_data.get('is_working_student') else 'No',
        'working_type': student_data.get('working_details', 'None'),
        'is_pwd': 'Yes' if student_data.get('is_sped') else 'No',
        'disability_type': student_data.get('sped_details', 'None'),
    }
    
    return render(request, 'enrollment_app/studentAcademic.html', context)


def verify_grades_ajax(request):
    """
    AJAX endpoint to verify grades without full form submission
    Used when "See Recommended Program" button is clicked
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    # Get academic data from session
    academic_data = EnrollmentSessionManager.get_academic_data(request)
    
    if not academic_data:
        return JsonResponse({
            'error': 'No academic data found. Please save your grades first.'
        }, status=400)
    
    # Check if OCR verification was performed
    if 'ocr_verified' not in academic_data:
        return JsonResponse({
            'error': 'Please upload your report card for verification.'
        }, status=400)
    
    # Check verification status
    if academic_data.get('ocr_verified') is False:
        mismatches = academic_data.get('ocr_mismatches', [])
        mismatch_details = []
        
        for mismatch in mismatches:
            subject_display = mismatch['subject'].replace('_', ' ').title()
            mismatch_details.append({
                'subject': subject_display,
                'subject_key': mismatch['subject'],  # Keep original key for field highlighting
                'manual': mismatch['manual_grade'],
                'extracted': mismatch['extracted_grade'],
                'difference': mismatch.get('difference', 0)
            })
        
        return JsonResponse({
            'success': False,
            'verified': False,
            'message': 'There is a mismatch found in your inputted grades and uploaded report card.',
            'mismatches': mismatch_details
        })
    
    # Grades verified successfully
    return JsonResponse({
        'success': True,
        'verified': True,
        'message': 'Grades verified successfully!',
        'overall_average': academic_data.get('overall_average', 0)
    })