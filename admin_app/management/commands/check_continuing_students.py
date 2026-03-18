"""
Management command: check_continuing_students
=============================================
Checks which students from SY 2025-2026 are eligible to enroll
as continuing (old) students in SY 2026-2027.

Usage:
    python manage.py check_continuing_students
    python manage.py check_continuing_students --export csv
    python manage.py check_continuing_students --status promoted
    python manage.py check_continuing_students --verbose

Place this file in:
    any_app/management/commands/check_continuing_students.py
    (e.g. admin_app/management/commands/check_continuing_students.py)
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from admin_app.models import SchoolYear
from enrollment_app.models import Student, StudentEnrollment, StudentAcademicYearStatus, ProgramSelection
import csv
import sys


class Command(BaseCommand):
    help = 'Check students eligible to continue enrollment in 2026-2027'

    def add_arguments(self, parser):
        parser.add_argument(
            '--export',
            type=str,
            choices=['csv'],
            help='Export results to CSV (prints to stdout)',
        )
        parser.add_argument(
            '--status',
            type=str,
            choices=['promoted', 'retained', 'pending', 'all'],
            default='all',
            help='Filter by academic year status (default: all)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed info per student',
        )

    def handle(self, *args, **options):
        # ── Get the two school years ─────────────────────────────────
        try:
            sy_2025 = SchoolYear.objects.get(year_label='2025-2026')
        except SchoolYear.DoesNotExist:
            self.stderr.write(self.style.ERROR('School year 2025-2026 not found.'))
            return

        try:
            sy_2026 = SchoolYear.objects.get(year_label='2026-2027')
        except SchoolYear.DoesNotExist:
            self.stderr.write(self.style.ERROR('School year 2026-2027 not found.'))
            return

        self.stdout.write(self.style.NOTICE(
            f'\n{"="*70}\n'
            f'  Continuing Student Eligibility Check\n'
            f'  From: {sy_2025.year_label}  →  To: {sy_2026.year_label}\n'
            f'{"="*70}\n'
        ))

        # ── Step 1: Get all approved enrollments from 2025-2026 ──────
        approved_enrollments_2025 = StudentEnrollment.objects.filter(
            school_year=sy_2025,
            enrollment_status='approved',
        ).select_related('student', 'grade_level', 'student__student_data')

        total_approved = approved_enrollments_2025.count()
        self.stdout.write(f'Total approved enrollments in 2025-2026: {total_approved}')

        # ── Step 2: Build eligibility data ───────────────────────────
        eligible   = []   # promoted — definitely can continue
        check_list = []   # no academic year status yet — needs review
        ineligible = []   # retained, dropped, transferred, etc.
        already_enrolled = []  # already have a 2026-2027 enrollment

        for enrollment in approved_enrollments_2025:
            student = enrollment.student

            # Check if already enrolled in 2026-2027
            existing_2026 = StudentEnrollment.objects.filter(
                student=student,
                school_year=sy_2026,
            ).first()

            if existing_2026:
                already_enrolled.append({
                    'lrn': student.lrn,
                    'name': self._get_name(student),
                    'grade_2025': enrollment.grade_level.name if enrollment.grade_level else 'N/A',
                    'status_2026': existing_2026.enrollment_status,
                    'enrollee_type_2026': existing_2026.enrollee_type,
                })
                continue

            # Check StudentAcademicYearStatus for 2025-2026
            academic_status = StudentAcademicYearStatus.objects.filter(
                student=student,
                school_year=sy_2025,
            ).first()

            # Get their program/section info
            program_info = self._get_program_info(student, sy_2025)

            row = {
                'lrn': student.lrn,
                'name': self._get_name(student),
                'grade_2025': enrollment.grade_level.name if enrollment.grade_level else 'N/A',
                'next_grade': self._next_grade(enrollment.grade_level),
                'program': program_info['program'],
                'section': program_info['section'],
                'final_status': academic_status.final_status if academic_status else 'NO RECORD',
                'overall_grade': str(academic_status.overall_grade) if academic_status and academic_status.overall_grade else 'N/A',
                'remarks': academic_status.remarks if academic_status else '',
                'has_probation': self._check_probation(student),
            }

            if academic_status:
                if academic_status.final_status == 'promoted':
                    eligible.append(row)
                else:
                    ineligible.append(row)
            else:
                # No academic year status recorded yet
                check_list.append(row)

        # ── Apply --status filter ─────────────────────────────────────
        status_filter = options['status']

        # ── Display Results ───────────────────────────────────────────
        if options['export'] == 'csv':
            self._export_csv(eligible, check_list, ineligible, already_enrolled)
            return

        # ── Summary ───────────────────────────────────────────────────
        self.stdout.write('\n' + '─'*70)
        self.stdout.write(self.style.SUCCESS(
            f'  ✅  ELIGIBLE (Promoted)          : {len(eligible)}'
        ))
        self.stdout.write(self.style.WARNING(
            f'  ⚠️   NEEDS REVIEW (No status yet) : {len(check_list)}'
        ))
        self.stdout.write(self.style.ERROR(
            f'  ❌  INELIGIBLE (Not promoted)    : {len(ineligible)}'
        ))
        self.stdout.write(
            f'  ℹ️   ALREADY IN 2026-2027         : {len(already_enrolled)}'
        )
        self.stdout.write('─'*70 + '\n')

        # ── Eligible Students ─────────────────────────────────────────
        if status_filter in ('all', 'promoted') and eligible:
            self.stdout.write(self.style.SUCCESS(
                f'\n✅  ELIGIBLE FOR CONTINUING ENROLLMENT ({len(eligible)} students)\n'
            ))
            self._print_table(eligible, options['verbose'])

        # ── Needs Review ─────────────────────────────────────────────
        if status_filter in ('all', 'pending') and check_list:
            self.stdout.write(self.style.WARNING(
                f'\n⚠️   NO ACADEMIC STATUS RECORDED — NEEDS REVIEW ({len(check_list)} students)\n'
            ))
            self.stdout.write(
                '  These students were approved in 2025-2026 but have no\n'
                '  StudentAcademicYearStatus record. They CANNOT be marked\n'
                '  as continuing until a status is recorded by their adviser.\n'
            )
            self._print_table(check_list, options['verbose'])

        # ── Ineligible ────────────────────────────────────────────────
        if status_filter in ('all', 'retained') and ineligible:
            self.stdout.write(self.style.ERROR(
                f'\n❌  NOT ELIGIBLE FOR CONTINUING ({len(ineligible)} students)\n'
            ))
            self._print_table(ineligible, options['verbose'])

        # ── Already enrolled ─────────────────────────────────────────
        if already_enrolled:
            self.stdout.write(
                f'\nℹ️   ALREADY ENROLLED IN 2026-2027 ({len(already_enrolled)} students)\n'
            )
            if options['verbose']:
                for s in already_enrolled:
                    self.stdout.write(
                        f"  {s['lrn']}  {s['name']:<30}  "
                        f"Status: {s['status_2026']}  Type: {s['enrollee_type_2026']}"
                    )

        self.stdout.write('\n' + '='*70 + '\n')
        self.stdout.write(self.style.SUCCESS(
            'Run with --export csv to get a downloadable spreadsheet.\n'
            'Run with --verbose to see section and program details.\n'
            'Run with --status promoted|retained|pending to filter.\n'
        ))

    # ── Helpers ───────────────────────────────────────────────────────

    def _get_name(self, student):
        try:
            sd = student.student_data
            return f"{sd.last_name}, {sd.first_name}"
        except Exception:
            return 'N/A'

    def _get_program_info(self, student, school_year):
        try:
            ps = ProgramSelection.objects.filter(
                student=student,
                school_year=school_year,
                admin_approved=True,
            ).select_related('assigned_section').first()
            if ps:
                return {
                    'program': ps.selected_program_code or 'N/A',
                    'section': ps.assigned_section.name if ps.assigned_section else 'Unassigned',
                }
        except Exception:
            pass
        return {'program': 'N/A', 'section': 'N/A'}

    def _next_grade(self, grade_level):
        if not grade_level:
            return 'N/A'
        mapping = {
            'G7': 'Grade 8',
            'G8': 'Grade 9',
            'G9': 'Grade 10',
            'G10': 'Graduated',
        }
        return mapping.get(grade_level.code, f'After {grade_level.name}')

    def _check_probation(self, student):
        try:
            from coordinator_app.models import ProbationRecord
            return ProbationRecord.objects.filter(student=student, is_active=True).exists()
        except Exception:
            return False

    def _print_table(self, rows, verbose=False):
        if not rows:
            return
        header = f"  {'LRN':<14} {'Name':<30} {'Grade':<10} {'Next Grade':<12} {'Final Status':<15} {'Grade':<8}"
        if verbose:
            header += f" {'Program':<10} {'Section':<15} {'Probation':<10} {'Remarks'}"
        self.stdout.write(header)
        self.stdout.write('  ' + '-'*100)
        for r in rows:
            line = (
                f"  {r['lrn']:<14} {r['name']:<30} {r['grade_2025']:<10} "
                f"{r['next_grade']:<12} {r['final_status']:<15} {r['overall_grade']:<8}"
            )
            if verbose:
                probation = '⚠️ YES' if r['has_probation'] else 'No'
                line += f" {r['program']:<10} {r['section']:<15} {probation:<10} {r.get('remarks','')}"
            self.stdout.write(line)

    def _export_csv(self, eligible, check_list, ineligible, already_enrolled):
        writer = csv.writer(sys.stdout)
        writer.writerow([
            'LRN', 'Name', 'Grade 2025-2026', 'Next Grade',
            'Program', 'Section', 'Final Status', 'Overall Grade',
            'Has Probation', 'Eligible for Continuing', 'Remarks',
        ])
        for r in eligible:
            writer.writerow([
                r['lrn'], r['name'], r['grade_2025'], r['next_grade'],
                r['program'], r['section'], r['final_status'], r['overall_grade'],
                'Yes' if r['has_probation'] else 'No',
                'YES - PROMOTED',
                r.get('remarks', ''),
            ])
        for r in check_list:
            writer.writerow([
                r['lrn'], r['name'], r['grade_2025'], r['next_grade'],
                r['program'], r['section'], 'NO STATUS RECORDED', r['overall_grade'],
                'Yes' if r['has_probation'] else 'No',
                'NEEDS REVIEW',
                r.get('remarks', ''),
            ])
        for r in ineligible:
            writer.writerow([
                r['lrn'], r['name'], r['grade_2025'], r['next_grade'],
                r['program'], r['section'], r['final_status'], r['overall_grade'],
                'Yes' if r['has_probation'] else 'No',
                'NO - NOT PROMOTED',
                r.get('remarks', ''),
            ])
        for r in already_enrolled:
            writer.writerow([
                r['lrn'], r['name'], r['grade_2025'], 'N/A',
                'N/A', 'N/A', r['status_2026'], 'N/A',
                'N/A',
                f'ALREADY IN 2026-2027 ({r["enrollee_type_2026"]})',
                '',
            ])