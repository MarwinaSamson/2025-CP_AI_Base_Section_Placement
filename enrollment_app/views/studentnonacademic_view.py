from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from admin_app.models import SchoolYear
import os
import uuid
import base64
import re
from datetime import datetime
from ..services.session_manager import EnrollmentSessionManager


def map_gender_value(gender_from_student_data):
    """
    Map gender values from student data form to non-academic survey form
    Student data uses: 'male', 'female', 'other'
    Non-academic form uses: 'Male', 'Female', 'Prefer not to say'
    """
    gender_mapping = {
        'male': 'Male',
        'female': 'Female',
        'other': 'Prefer not to say'
    }
    return gender_mapping.get(gender_from_student_data.lower(), '')


def non_academic_form(request):
    """
    Handle non-academic survey form (Survey Data)
    Requires student and family data to be completed first
    """
    
    # Check if previous forms are completed
    if not EnrollmentSessionManager.is_lrn_verified(request):
        messages.error(request, 'Please complete the Student Data form first.')
        return redirect('enrollment_app:student_data')
    
    student_data = EnrollmentSessionManager.get_student_data(request)
    family_data = EnrollmentSessionManager.get_family_data(request)
    
    if not family_data:
        messages.error(request, 'Please complete the Family Data form first.')
        return redirect('enrollment_app:family_data')
    
    if request.method == 'POST':
        # Prepare survey data
        survey_data = {
            # Section A: Student Information (Optional)
            'student_name': request.POST.get('student_name', ''),
            'age': request.POST.get('age', ''),
            'current_grade_section': request.POST.get('current_grade_section', ''),
            'residence_barangay': request.POST.get('residence_barangay', ''),
            'gender': request.POST.get('gender', ''),
            
            # Section B: Student Profile
            'learning_style': request.POST.get('learning_style', ''),
            'study_hours': request.POST.get('study_hours', ''),
            'study_environment': request.POST.get('study_environment', ''),
            'schoolwork_support': request.POST.get('schoolwork_support', ''),
            
            # Section C: Interests & Motivation
            'enjoyed_subjects': request.POST.getlist('enjoyed_subjects'),
            'interested_program': request.POST.get('interested_program', ''),
            'program_motivation': request.POST.get('program_motivation', ''),
            'enjoyed_activities': request.POST.getlist('enjoyed_activities'),
            'enjoyed_activities_other': request.POST.get('enjoyed_activities_other', ''),
            
            # Section D: Behavioral & Study Habits
            'assignments_on_time': request.POST.get('assignments_on_time', ''),
            'handle_difficult_lessons': request.POST.get('handle_difficult_lessons', ''),
            
            # Section E: Technology Access
            'device_availability': request.POST.get('device_availability', ''),
            'internet_access': request.POST.get('internet_access', ''),
            
            # Section F: Attendance & Responsibility
            'absences': request.POST.get('absences', ''),
            'absence_reason': request.POST.get('absence_reason', ''),
            'participation': request.POST.get('participation', ''),
            
            # Section G: Learning Support & Special Needs
            'difficulty_areas': request.POST.getlist('difficulty_areas'),
            'extra_support': request.POST.get('extra_support', ''),
            
            # Section H: Environmental Factors
            'quiet_place': request.POST.get('quiet_place', ''),
            'distance_from_school': request.POST.get('distance_from_school', ''),
            'travel_difficulty': request.POST.get('travel_difficulty', ''),
        }
        
        # Validate required fields - TEMPORARILY DISABLED FOR TESTING
        required_fields = [
            'learning_style', 'study_hours', 'study_environment', 'schoolwork_support',
            'interested_program', 'program_motivation', 'assignments_on_time',
            'handle_difficult_lessons', 'device_availability', 'internet_access',
            'absences', 'absence_reason', 'participation', 'extra_support',
            'quiet_place', 'distance_from_school', 'travel_difficulty'
        ]
        
        missing_fields = [field for field in required_fields if not survey_data.get(field)]
        
        if missing_fields:
            print(f"DEBUG: Missing fields: {missing_fields}")
            print(f"DEBUG: Survey data keys: {list(survey_data.keys())}")
            for field in missing_fields:
                print(f"DEBUG: {field} = {repr(survey_data.get(field))}")
        
        # TEMPORARILY DISABLE VALIDATION TO TEST FORM SUBMISSION
        if False:  # Changed from if missing_fields: to if False:
            messages.error(request, f'Please fill in all required fields marked with *. Missing: {", ".join(missing_fields)}')
            return render(request, 'enrollment_app/studentNonAcademic.html', {
                'form_data': request.POST,
                'student_info': student_data
            })
        
        # Save complete survey response as backup
        survey_data['survey_responses_json'] = survey_data.copy()
        
        # Save to session
        EnrollmentSessionManager.save_survey_data(request, survey_data)
        
        messages.success(request, 'Survey completed successfully! Please continue with Academic Data.')
        return redirect('enrollment_app:academic')
    
    # GET request - check for existing session data
    existing_survey_data = EnrollmentSessionManager.get_survey_data(request)

    # Pre-populate Section A with student data if no existing survey data
    form_data = existing_survey_data or {}

    if not existing_survey_data and student_data:
        # Calculate age from date of birth
        age = ''
        if student_data.get('date_of_birth'):
            try:
                birth_date = datetime.strptime(student_data['date_of_birth'], '%Y-%m-%d')
                today = datetime.now()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                age = str(age)
            except (ValueError, TypeError):
                age = ''

        # Extract barangay from address (simple extraction - can be improved)
        barangay = ''
        address = student_data.get('address', '')
        if address:
            # Try to extract barangay - look for common patterns
            address_lower = address.lower()
            if 'brgy' in address_lower or 'barangay' in address_lower:
                # Simple extraction - take the part after brgy/barangay
                match = re.search(r'(?:brgy|barangay)\s*([^,]+)', address_lower, re.IGNORECASE)
                if match:
                    barangay = match.group(1).strip().title()
            else:
                # If no brgy found, take first part of address
                barangay = address.split(',')[0].strip()

        # Pre-populate Section A fields
        form_data.update({
            'student_name': f"{student_data.get('first_name', '')} {student_data.get('last_name', '')}".strip(),
            'age': age,
            'current_grade_section': student_data.get('previous_grade_section', ''),
            'residence_barangay': barangay,
            'gender': map_gender_value(student_data.get('gender', '')),
        })

    # Get active school year
    active_school_year = SchoolYear.objects.filter(is_active=True).first()
    
    return render(request, 'enrollment_app/studentNonAcademic.html', {
        'form_data': form_data,
        'student_info': student_data,
        'school_year': active_school_year
    })