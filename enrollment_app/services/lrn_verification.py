"""
LRN Verification Service
Verifies student LRN against LIS database
"""

from lis.models import LISStudent
from django.core.exceptions import ValidationError


class LRNVerificationService:
    """
    Service to verify LRN against LIS database
    """
    
    @staticmethod
    def verify_lrn(lrn):
        """
        Verify if LRN exists in LIS database
        
        Args:
            lrn (str): The LRN to verify (12 digits)
            
        Returns:
            dict: {
                'is_valid': bool,
                'student_data': dict or None,
                'message': str
            }
        """
        # Validate LRN format
        if not lrn or len(lrn) != 12 or not lrn.isdigit():
            return {
                'is_valid': False,
                'student_data': None,
                'message': 'Invalid LRN format. LRN must be exactly 12 digits.'
            }
        
        try:
            # Query LIS database using 'lis' connection
            lis_student = LISStudent.objects.using('lis').get(lrn=lrn)
            
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
            
        except LISStudent.DoesNotExist:
            return {
                'is_valid': False,
                'student_data': None,
                'message': 'The LRN you entered is not listed in the LIS. Please try contacting your previous school.'
            }
        except Exception as e:
            return {
                'is_valid': False,
                'student_data': None,
                'message': f'Error verifying LRN: {str(e)}'
            }
    
    @staticmethod
    def get_lis_student_info(lrn):
        """
        Get full student information from LIS
        
        Args:
            lrn (str): Student's LRN
            
        Returns:
            LISStudent object or None
        """
        try:
            return LISStudent.objects.using('lis').get(lrn=lrn)
        except LISStudent.DoesNotExist:
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
        return LISStudent.objects.using('lis').filter(lrn=lrn).exists()