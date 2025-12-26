"""
Enrollment Session Manager
Manages enrollment form data storage in Django sessions
"""

from django.utils import timezone


class EnrollmentSessionManager:
    """
    Manages enrollment form data in session until all forms are completed
    """
    
    SESSION_KEY_PREFIX = 'enrollment_'
    
    # Session keys
    KEY_LRN = f'{SESSION_KEY_PREFIX}lrn'
    KEY_LRN_VERIFIED = f'{SESSION_KEY_PREFIX}lrn_verified'
    KEY_STUDENT_DATA = f'{SESSION_KEY_PREFIX}student_data'
    KEY_FAMILY_DATA = f'{SESSION_KEY_PREFIX}family_data'
    KEY_SURVEY_DATA = f'{SESSION_KEY_PREFIX}survey_data'
    KEY_ACADEMIC_DATA = f'{SESSION_KEY_PREFIX}academic_data'
    KEY_PROGRAM_SELECTION = f'{SESSION_KEY_PREFIX}program_selection'
    
    @staticmethod
    def save_student_data(request, data):
        """
        Save student data form to session
        
        Args:
            request: Django request object
            data (dict): Student data dictionary
        """
        request.session[EnrollmentSessionManager.KEY_STUDENT_DATA] = data
        request.session[EnrollmentSessionManager.KEY_LRN] = data.get('lrn')
        request.session.modified = True
    
    @staticmethod
    def save_family_data(request, data):
        """Save family data form to session"""
        request.session[EnrollmentSessionManager.KEY_FAMILY_DATA] = data
        request.session.modified = True
    
    @staticmethod
    def save_survey_data(request, data):
        """Save survey data to session"""
        request.session[EnrollmentSessionManager.KEY_SURVEY_DATA] = data
        request.session.modified = True
    
    @staticmethod
    def save_academic_data(request, data):
        """Save academic data to session"""
        request.session[EnrollmentSessionManager.KEY_ACADEMIC_DATA] = data
        request.session.modified = True
    
    @staticmethod
    def save_program_selection(request, data):
        """Save program selection to session"""
        request.session[EnrollmentSessionManager.KEY_PROGRAM_SELECTION] = data
        request.session.modified = True
    
    @staticmethod
    def get_student_data(request):
        """Retrieve student data from session"""
        return request.session.get(EnrollmentSessionManager.KEY_STUDENT_DATA)
    
    @staticmethod
    def get_family_data(request):
        """Retrieve family data from session"""
        return request.session.get(EnrollmentSessionManager.KEY_FAMILY_DATA)
    
    @staticmethod
    def get_survey_data(request):
        """Retrieve survey data from session"""
        return request.session.get(EnrollmentSessionManager.KEY_SURVEY_DATA)
    
    @staticmethod
    def get_academic_data(request):
        """Retrieve academic data from session"""
        return request.session.get(EnrollmentSessionManager.KEY_ACADEMIC_DATA)
    
    @staticmethod
    def get_program_selection(request):
        """Retrieve program selection from session"""
        return request.session.get(EnrollmentSessionManager.KEY_PROGRAM_SELECTION)
    
    @staticmethod
    def get_lrn(request):
        """Get LRN from session"""
        return request.session.get(EnrollmentSessionManager.KEY_LRN)
    
    @staticmethod
    def get_all_session_data(request):
        """
        Retrieve all enrollment data from session
        
        Returns:
            dict: All session data
        """
        return {
            'lrn': request.session.get(EnrollmentSessionManager.KEY_LRN),
            'student_data': request.session.get(EnrollmentSessionManager.KEY_STUDENT_DATA),
            'family_data': request.session.get(EnrollmentSessionManager.KEY_FAMILY_DATA),
            'survey_data': request.session.get(EnrollmentSessionManager.KEY_SURVEY_DATA),
            'academic_data': request.session.get(EnrollmentSessionManager.KEY_ACADEMIC_DATA),
            'program_selection': request.session.get(EnrollmentSessionManager.KEY_PROGRAM_SELECTION),
        }
    
    @staticmethod
    def clear_session_data(request):
        """Clear all enrollment data from session"""
        keys_to_delete = [
            key for key in request.session.keys() 
            if key.startswith(EnrollmentSessionManager.SESSION_KEY_PREFIX)
        ]
        for key in keys_to_delete:
            del request.session[key]
        request.session.modified = True
    
    @staticmethod
    def is_lrn_verified(request):
        """Check if LRN has been verified"""
        return request.session.get(EnrollmentSessionManager.KEY_LRN_VERIFIED, False)
    
    @staticmethod
    def set_lrn_verified(request, verified=True):
        """Mark LRN as verified in session"""
        request.session[EnrollmentSessionManager.KEY_LRN_VERIFIED] = verified
        if verified:
            request.session[f'{EnrollmentSessionManager.SESSION_KEY_PREFIX}verified_at'] = timezone.now().isoformat()
        request.session.modified = True
    
    @staticmethod
    def is_all_forms_complete(request):
        """
        Check if all required forms are completed
        
        Returns:
            bool: True if all forms completed
        """
        return all([
            request.session.get(EnrollmentSessionManager.KEY_STUDENT_DATA),
            request.session.get(EnrollmentSessionManager.KEY_FAMILY_DATA),
            request.session.get(EnrollmentSessionManager.KEY_SURVEY_DATA),
            request.session.get(EnrollmentSessionManager.KEY_ACADEMIC_DATA),
            request.session.get(EnrollmentSessionManager.KEY_PROGRAM_SELECTION),
        ])
    
    @staticmethod
    def get_completion_status(request):
        """
        Get form completion status
        
        Returns:
            dict: Status of each form
        """
        return {
            'lrn_verified': EnrollmentSessionManager.is_lrn_verified(request),
            'student_data_complete': bool(request.session.get(EnrollmentSessionManager.KEY_STUDENT_DATA)),
            'family_data_complete': bool(request.session.get(EnrollmentSessionManager.KEY_FAMILY_DATA)),
            'survey_data_complete': bool(request.session.get(EnrollmentSessionManager.KEY_SURVEY_DATA)),
            'academic_data_complete': bool(request.session.get(EnrollmentSessionManager.KEY_ACADEMIC_DATA)),
            'program_selection_complete': bool(request.session.get(EnrollmentSessionManager.KEY_PROGRAM_SELECTION)),
            'all_complete': EnrollmentSessionManager.is_all_forms_complete(request)
        }
        
# Add these methods to your existing EnrollmentSessionManager class

    @staticmethod
    def save_academic_data(request, academic_data):
        """
        Save academic data to session
        
        Args:
            request: Django request object
            academic_data: Dictionary containing academic information
        """
        request.session['academic_data'] = academic_data
        request.session.modified = True

    @staticmethod
    def get_academic_data(request):
        """
        Retrieve academic data from session
        
        Args:
            request: Django request object
            
        Returns:
            Dictionary containing academic data or None
        """
        return request.session.get('academic_data', None)

    @staticmethod
    def clear_academic_data(request):
        """Clear academic data from session"""
        if 'academic_data' in request.session:
            del request.session['academic_data']
            request.session.modified = True