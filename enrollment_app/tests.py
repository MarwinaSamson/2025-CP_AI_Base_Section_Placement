from django.test import TestCase
from django.utils import timezone
from datetime import date

from enrollment_app.models import (
	Student, StudentEnrollment, StudentDocumentSubmission,
)
from admin_app.models import SchoolYear, GradeLevel, DocumentRequirement
from django.contrib.auth.models import User
from django.urls import reverse


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


class TransfereeEnrollmentTest(TestCase):
	def setUp(self):
		from admin_app.models import SchoolYear, GradeLevel, DocumentRequirement
		from enrollment_app.services.transferee_service import create_transferee_enrollment

		self.SchoolYear = SchoolYear
		self.GradeLevel = GradeLevel
		self.DocumentRequirement = DocumentRequirement
		self.create_service = create_transferee_enrollment

		self.sy = SchoolYear.objects.create(year_label='2026-2027', start_date=date(2026,6,1), end_date=date(2027,3,31), is_active=True)
		self.g8, _ = GradeLevel.objects.get_or_create(code='G8', defaults={'name': 'Grade 8'})

		self.student = Student.objects.create(lrn='TSTTRANS001', email='trans@test.example')

		# Document requirement that applies to transferees for this grade
		self.req = DocumentRequirement.objects.create(
			school_year=self.sy,
			name='SF9 / Form 138',
			applies_to='transferee',
			grade_level=self.g8,
		)

	def test_create_transferee_enrollment_without_docs(self):
		enrollment = self.create_service(self.student.lrn, self.sy, self.g8, last_school_attended='Other School')
		self.assertIsNotNone(enrollment)
		self.assertEqual(enrollment.enrollee_type, 'transferee')
		self.assertFalse(enrollment.documents_completed)

	def test_transferee_documents_approval_marks_enrollment(self):
		enrollment = self.create_service(self.student.lrn, self.sy, self.g8, last_school_attended='Other School')
		# Upload required document (pending)
		sub = StudentDocumentSubmission.objects.create(
			student=self.student,
			requirement=self.req,
			school_year=self.sy,
			document_file='sf9.pdf',
			file_name='sf9.pdf',
			file_size=100,
			file_format='pdf',
			status='pending',
		)

		# Approve it — save should mark enrollment.documents_completed
		sub.status = 'approved'
		sub.save()

		se = StudentEnrollment.objects.get(student=self.student, school_year=self.sy)
		self.assertTrue(se.documents_completed)


class DocumentReviewEndpointTest(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='coordinator', password='pass')
		self.sy = SchoolYear.objects.create(year_label='2027-2028', start_date=date(2027,6,1), end_date=date(2028,3,31), is_active=True)
		self.g8, _ = GradeLevel.objects.get_or_create(code='G8', defaults={'name': 'Grade 8'})
		self.student = Student.objects.create(lrn='TSTDOC001', email='doc@test.example')
		self.enrollment = StudentEnrollment.objects.create(
			student=self.student,
			school_year=self.sy,
			grade_level=self.g8,
			enrollee_type='transferee',
			enrollment_status='draft',
			documents_completed=False,
		)
		self.req = DocumentRequirement.objects.create(
			school_year=self.sy,
			name='Transferee Doc',
			applies_to='transferee',
			grade_level=self.g8,
		)
		self.sub = StudentDocumentSubmission.objects.create(
			student=self.student,
			requirement=self.req,
			school_year=self.sy,
			document_file='trans.doc',
			file_name='trans.doc',
			file_size=10,
			file_format='doc',
			status='pending',
		)

	def test_review_endpoint_approve_marks_enrollment(self):
		self.client.login(username='coordinator', password='pass')
		url = reverse('coordinator:api_review_document', args=[self.student.lrn, self.sub.id])
		resp = self.client.post(url, data={'action': 'approve', 'review_notes': 'OK'}, content_type='application/json')
		self.assertEqual(resp.status_code, 200)
		self.sub.refresh_from_db()
		self.assertEqual(self.sub.status, 'approved')
		se = StudentEnrollment.objects.get(student=self.student, school_year=self.sy)
		self.assertTrue(se.documents_completed)

