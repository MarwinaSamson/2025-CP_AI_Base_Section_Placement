"""
LRN Verification Service
Verifies student LRN against LIS database
"""

from django.conf import settings
from django.core.exceptions import ValidationError


class LRNVerificationService:
    """
    Service to verify LRN against LIS database
    """

    @staticmethod
    def _is_lis_available():
        """Check if LIS database connection is configured."""
        return 'lis' in settings.DATABASES

    @staticmethod
    def _normalize_name(name):
        """Normalize a name for comparison (trim, collapse spaces, lowercase)."""
        if not name:
            return ''
        return ' '.join(name.strip().split()).lower()

    @staticmethod
    def verify_lrn(lrn, first_name=None, last_name=None):
        """
        Verify if LRN exists in LIS database and ensure name matches LIS record.

        Args:
            lrn (str): The LRN to verify (12 digits)
            first_name (str, optional): Submitted first name (required for match check)
            last_name (str, optional): Submitted last name (required for match check)

        Returns:
            dict: {
                'is_valid': bool,
                'student_data': dict or None,
        """
        # Validate LRN format
        if not lrn or not lrn.isdigit() or len(lrn) != 12:
            return {
                'is_valid': False,
                'student_data': None,
                'message': 'Invalid LRN format. LRN must be exactly 12 digits.'
            }

        # Check if LIS database is available
        if not LRNVerificationService._is_lis_available():
            # LIS not configured - skip verification and allow enrollment
            return {
                'is_valid': True,
                'student_data': None,
                'message': 'LRN format validated. LIS verification skipped (not available).',
                'lis_skipped': True
            }

        import logging
        try:
            # Import from admin_app instead of lis
            from admin_app.models import LISStudent
            # Query database using default connection
            lis_student = LISStudent.objects.get(lrn=lrn)

            lis_first = LRNVerificationService._normalize_name(lis_student.first_name)
            lis_last = LRNVerificationService._normalize_name(lis_student.last_name)
            form_first = LRNVerificationService._normalize_name(first_name)
            form_last = LRNVerificationService._normalize_name(last_name)

            if not form_first or not form_last:
                return {
                    'is_valid': False,
                    'student_data': None,
                    'message': 'Please provide both first and last name to verify LRN against LIS.'
                }

            if form_first != lis_first or form_last != lis_last:
                return {
                    'is_valid': False,
                    'student_data': None,
                    'message': 'The inputted name does not match the owner of the LRN in the LIS. Please re-enter the exact first and last name.'
                }

            return {
                'is_valid': True,
                'student_data': {
                    'lrn': lis_student.lrn,
                    'first_name': lis_student.first_name,
                    'last_name': lis_student.last_name,
                    'birth_date': lis_student.birth_date.isoformat(),
                    'last_school': lis_student.last_school,
                },
                'message': 'LRN verified successfully.'
            }

        except Exception as e:
            logging.error("LRN verification error", exc_info=True)
            error_message = str(e)
            if 'DoesNotExist' in type(e).__name__ or 'matching query does not exist' in error_message.lower():
                return {
                    'is_valid': False,
                    'student_data': None,
                    'message': 'The LRN you entered is not listed in the LIS. Please try contacting your previous school.'
                }
            return {
                'is_valid': False,
                'student_data': None,
                'message': f'Error verifying LRN: {e}'
            }

    @staticmethod
    def get_student_info(lrn):
        """
        Get full student information from LIS

        Args:
            lrn (str): Student's LRN

        Returns:
            LISStudent object or None
        """
        # if not LRNVerificationService._is_lis_available():
        #     return None
        try:
            from lis.models import LISStudent
            return LISStudent.objects.get(lrn=lrn)
        except:
            return None

    @staticmethod
    def check_lrn_exists(lrn):
        """
        Quick check if LRN exists in LIS

        Args:
            lrn (str): Student's LRN

        Returns:
            bool: True if exists, False otherwise
        """
        try:
            from lis.models import LISStudent
            return LISStudent.objects.filter(lrn=lrn).exists()
        except:
            return False