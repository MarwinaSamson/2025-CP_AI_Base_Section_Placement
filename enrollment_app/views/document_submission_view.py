"""
Document Submission Views
Allows students to view required documents and submit them during enrollment
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.utils import timezone
import os

from ..models import Student, StudentDocumentSubmission
from admin_app.models import DocumentRequirement, SchoolYear


def get_student_from_session(request):
    """
    Get student object from session data
    Student LRN should be stored in session during enrollment
    """
    lrn = request.session.get('student_lrn')
    if not lrn:
        return None
    
    try:
        return Student.objects.get(lrn=lrn)
    except Student.DoesNotExist:
        return None


def document_submission_page(request):
    """
    Display document submission page for student
    Shows required documents and submission status
    """
    student = get_student_from_session(request)
    
    if not student:
        messages.error(request, "Please start your enrollment first")
        return redirect('enrollment_app:landing')
    
    # Get school year from StudentEnrollment (backward compat with Student.current_school_year property)
    school_year = student.current_school_year
    if not school_year:
        messages.error(request, "School year not assigned. Please contact support.")
        return redirect('enrollment_app:landing')
    
    # Get active requirements for student's school year
    requirements = DocumentRequirement.objects.filter(
        school_year=school_year,
        is_active=True
    ).order_by('order', 'name')
    
    # Get student's submissions
    submissions = StudentDocumentSubmission.objects.filter(
        student=student
    ).select_related('requirement')
    
    # Build submission map for easy lookup
    submission_map = {sub.requirement_id: sub for sub in submissions}
    
    # Add submission status to each requirement
    requirements_with_status = []
    for req in requirements:
        sub = submission_map.get(req.id)
        requirements_with_status.append({
            'requirement': req,
            'submission': sub,
            'is_submitted': sub is not None,
            'submission_status': sub.status if sub else None,
        })
    
    context = {
        'student': student,
        'requirements_with_status': requirements_with_status,
        'total_requirements': len(requirements),
        'submitted_count': sum(1 for r in requirements_with_status if r['is_submitted']),
        'school_year': school_year,
    }
    
    return render(request, 'enrollment_app/documentSubmission.html', context)


@require_http_methods(["POST"])
def upload_document(request, requirement_id):
    """
    Handle document upload for a specific requirement
    API endpoint called via AJAX
    """
    student = get_student_from_session(request)
    
    if not student:
        return JsonResponse({
            'success': False,
            'error': 'Student session not found. Please restart enrollment.'
        }, status=401)
    
    # Get the requirement
    school_year = student.current_school_year
    if not school_year:
        return JsonResponse({
            'success': False,
            'error': 'No active enrollment found. Please contact support.'
        }, status=400)
    
    requirement = get_object_or_404(
        DocumentRequirement,
        id=requirement_id,
        school_year=school_year,
        is_active=True
    )
    
    # Check if file is provided
    if 'document_file' not in request.FILES:
        return JsonResponse({
            'success': False,
            'error': 'No file provided'
        }, status=400)
    
    file_obj = request.FILES['document_file']
    
    # Validate file
    validation_errors = validate_file(file_obj, requirement)
    if validation_errors:
        return JsonResponse({
            'success': False,
            'error': validation_errors
        }, status=400)
    
    try:
        # Get or create submission
        submission, created = StudentDocumentSubmission.objects.update_or_create(
            student=student,
            requirement=requirement,
            defaults={
                'document_file': file_obj,
                'file_name': file_obj.name,
                'file_size': file_obj.size,
                'file_format': get_file_extension(file_obj.name),
                'status': 'pending',
                'reviewed_by': None,
                'review_notes': None,
                'reviewed_at': None,
            }
        )
        
        # Validate submission
        submission.clean()
        submission.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Document uploaded successfully',
            'status': submission.status,
            'action': 'created' if created else 'updated',
            'submission_id': submission.id,
        })
    
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': str(e.message) if hasattr(e, 'message') else str(e)
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error uploading document: {str(e)}'
        }, status=500)


@require_http_methods(["DELETE"])
def delete_document(request, requirement_id):
    """
    Delete a submitted document
    """
    student = get_student_from_session(request)
    
    if not student:
        return JsonResponse({
            'success': False,
            'error': 'Student session not found'
        }, status=401)
    
    # Get the submission
    submission = get_object_or_404(
        StudentDocumentSubmission,
        student=student,
        requirement_id=requirement_id
    )
    
    # Only allow deletion if status is pending or resubmit
    if submission.status not in ['pending', 'resubmit']:
        return JsonResponse({
            'success': False,
            'error': f'Cannot delete {submission.status} submission'
        }, status=400)
    
    try:
        # Delete the file from storage
        if submission.document_file:
            submission.document_file.delete(save=False)
        
        # Delete the submission record
        submission.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Document deleted successfully'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error deleting document: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def get_requirements_api(request):
    """
    API endpoint to get all active requirements for student's school year
    """
    student = get_student_from_session(request)
    
    if not student:
        return JsonResponse({
            'success': False,
            'error': 'Student session not found'
        }, status=401)
    
    school_year = student.current_school_year
    if not school_year:
        return JsonResponse({
            'success': False,
            'error': 'No active enrollment found. Please contact support.'
        }, status=400)
    
    requirements = DocumentRequirement.objects.filter(
        school_year=school_year,
        is_active=True
    ).order_by('order', 'name')
    
    # Get submissions
    submissions = StudentDocumentSubmission.objects.filter(
        student=student
    ).values('requirement_id', 'status', 'submitted_at', 'review_notes')
    
    submission_map = {sub['requirement_id']: sub for sub in submissions}
    
    requirements_data = []
    for req in requirements:
        sub = submission_map.get(req.id)
        requirements_data.append({
            'id': req.id,
            'name': req.name,
            'description': req.description,
            'requirement_type': req.requirement_type,
            'file_format': req.file_format,
            'max_file_size_mb': req.max_file_size_mb,
            'order': req.order,
            'allowed_extensions': req.get_allowed_extensions(),
            'is_submitted': sub is not None,
            'submission_status': sub['status'] if sub else None,
            'submitted_at': sub['submitted_at'].isoformat() if sub and sub['submitted_at'] else None,
            'review_notes': sub['review_notes'] if sub else None,
        })
    
    return JsonResponse({
        'success': True,
        'requirements': requirements_data,
        'total': len(requirements_data),
        'submitted': sum(1 for r in requirements_data if r['is_submitted']),
    })


def validate_file(file_obj, requirement):
    """
    Validate uploaded file against requirement specifications
    Returns error message if validation fails, None if valid
    """
    if not file_obj:
        return "No file provided"
    
    # Check file size
    max_size_bytes = requirement.max_file_size_mb * 1024 * 1024
    if file_obj.size > max_size_bytes:
        return f"File size exceeds maximum allowed size of {requirement.max_file_size_mb}MB"
    
    # Check file format
    file_ext = get_file_extension(file_obj.name)
    allowed_extensions = requirement.get_allowed_extensions()
    
    if file_ext.lower() not in allowed_extensions:
        return f"File format '.{file_ext}' is not allowed. Allowed formats: {', '.join(allowed_extensions)}"
    
    return None


def get_file_extension(filename):
    """Extract file extension from filename"""
    if not filename:
        return ""
    return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ""


def download_document(request, submission_id):
    """
    Download submitted document (for staff viewing)
    """
    # This would be restricted to staff/admin only
    submission = get_object_or_404(StudentDocumentSubmission, id=submission_id)
    
    if not submission.document_file:
        messages.error(request, "Document file not found")
        return redirect('enrollment_app:landing')
    
    # Return file for download
    from django.http import FileResponse
    response = FileResponse(submission.document_file.open('rb'))
    response['Content-Disposition'] = f'attachment; filename="{submission.file_name}"'
    return response
