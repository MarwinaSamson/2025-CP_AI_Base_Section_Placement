from django.test import TestCase
from django.utils import timezone
from datetime import date

from enrollment_app.models import (
	Student, StudentEnrollment, StudentDocumentSubmission,
)
from admin_app.models import SchoolYear, GradeLevel, DocumentRequirement


# Existing tests (placeholder) and new carry-over test
class CarryOverDocumentsTest(TestCase):
	def setUp(self):
		# Create school years
		self.sy_from = SchoolYear.objects.create(
			year_label='2024-2025', start_date=date(2024,6,1), end_date=date(2025,3,31), is_active=False
		)
		self.sy_to = SchoolYear.objects.create(
			year_label='2025-2026', start_date=date(2025,6,1), end_date=date(2026,3,31), is_active=True
		)

		# Create or get grade levels (migrations may have seeded these)
		self.g7, _ = GradeLevel.objects.get_or_create(code='G7', defaults={'name': 'Grade 7'})
		self.g8, _ = GradeLevel.objects.get_or_create(code='G8', defaults={'name': 'Grade 8'})

		# Create a student
		self.student = Student.objects.create(lrn='TSTCARRY001', email='carry@test.example')

		# Create a document requirement for the prior year
		self.req = DocumentRequirement.objects.create(
			school_year=self.sy_from,
			name='Test Document',
			applies_to='all',
		)

		# Create an approved StudentDocumentSubmission in prior year
		self.original_submission = StudentDocumentSubmission.objects.create(
			student=self.student,
			requirement=self.req,
			school_year=self.sy_from,
			document_file='dummy.txt',
			file_name='dummy.txt',
			file_size=123,
			file_format='txt',
			status='approved',
		)

		# Create a draft StudentEnrollment for the target year (continuing)
		self.enrollment_to = StudentEnrollment.objects.create(
			student=self.student,
			school_year=self.sy_to,
			grade_level=self.g8,
			enrollee_type='continuing',
			enrollment_status='draft',
			documents_completed=False,
		)

	def test_carry_over_marks_enrollment_documents_completed(self):
		# Precondition: enrollment documents_completed is False
		self.assertFalse(self.enrollment_to.documents_completed)

		carried = StudentDocumentSubmission.carry_over_for_student(self.student, self.sy_to)

		# Ensure a carried-over submission was created
		self.assertTrue(len(carried) >= 1)
		new_sub = StudentDocumentSubmission.objects.filter(student=self.student, school_year=self.sy_to).first()
		self.assertIsNotNone(new_sub)
		self.assertTrue(new_sub.is_carried_over)

		# Enrollment for the new year should be marked documents_completed
		se = StudentEnrollment.objects.get(pk=self.enrollment_to.pk)
		self.assertTrue(se.documents_completed)
		self.assertIsNotNone(se.documents_completed_at)

