"""
Management command: generate_academic_statuses
Generates StudentAcademicYearStatus records for all approved students
from a given school year based on their AcademicPerformance final grades.

Usage:
    python manage.py generate_academic_statuses
    python manage.py generate_academic_statuses --school_year 2025-2026
    python manage.py generate_academic_statuses --school_year 2025-2026 --dry_run
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from admin_app.models import SchoolYear
from enrollment_app.models import (
    Student, StudentEnrollment, StudentAcademicYearStatus
)
from coordinator_app.models import AcademicPerformance

PASSING_GRADE = 75  # DepEd standard


class Command(BaseCommand):
    help = 'Generate StudentAcademicYearStatus records based on final grades'

    def add_arguments(self, parser):
        parser.add_argument(
            '--school_year',
            type=str,
            default=None,
            help='School year label (e.g. 2025-2026). Defaults to most recent non-active SY.',
        )
        parser.add_argument(
            '--dry_run',
            action='store_true',
            help='Preview what would be created without saving.',
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing records.',
        )

    def handle(self, *args, **options):
        dry_run  = options['dry_run']
        overwrite = options['overwrite']

        # Resolve target school year
        if options['school_year']:
            try:
                school_year = SchoolYear.objects.get(
                    year_label=options['school_year']
                )
            except SchoolYear.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(
                        f"School year '{options['school_year']}' not found."
                    )
                )
                return
        else:
            # Default: most recently deactivated (previous) school year
            school_year = (
                SchoolYear.objects.filter(is_active=False)
                .order_by('-year_label')
                .first()
            )
            if not school_year:
                self.stderr.write(
                    self.style.ERROR('No inactive school year found.')
                )
                return

        self.stdout.write(
            self.style.NOTICE(
                f"\n{'[DRY RUN] ' if dry_run else ''}Generating statuses for "
                f"School Year: {school_year.year_label}\n"
            )
        )

        # Get all approved enrollments for this school year
        enrollments = StudentEnrollment.objects.filter(
            school_year=school_year,
            enrollment_status='approved',
        ).select_related('student', 'grade_level')

        total     = enrollments.count()
        created   = 0
        skipped   = 0
        promoted  = 0
        retained  = 0
        no_grades = 0

        self.stdout.write(f"Found {total} approved enrollment(s) to process.\n")

        for enrollment in enrollments:
            student    = enrollment.student
            grade_level = enrollment.grade_level

            # Skip if already exists and not overwriting
            existing = StudentAcademicYearStatus.objects.filter(
                student=student,
                school_year=school_year,
            ).first()

            if existing and not overwrite:
                skipped += 1
                continue

            # Get the assigned section from ProgramSelection
            section = None
            try:
                ps = student.program_selection
                if ps.assigned_section and ps.school_year == school_year:
                    section = ps.assigned_section
            except Exception:
                pass

            # Fetch Final Grade (quarter=5) AcademicPerformance records
            final_grades = AcademicPerformance.objects.filter(
                student=student,
                school_year=school_year,
                quarter=5,  # Final Grade
            )

            if not final_grades.exists():
                # Try Q4 grades as fallback
                final_grades = AcademicPerformance.objects.filter(
                    student=student,
                    school_year=school_year,
                    quarter=4,
                )

            if not final_grades.exists():
                # No grades at all — set as pending
                final_status  = 'pending'
                overall_grade = None
                no_grades    += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"  {student.lrn}: No grades found — setting 'pending'"
                    )
                )
            else:
                grades      = [float(ap.grade) for ap in final_grades]
                avg         = round(sum(grades) / len(grades), 2)
                overall_grade = avg
                min_grade    = min(grades)

                # Promotion rule: ALL subjects must be >= 75
                if min_grade >= PASSING_GRADE:
                    final_status = 'promoted'
                    promoted    += 1
                else:
                    final_status = 'retained'
                    retained    += 1

                self.stdout.write(
                    f"  {student.lrn} | Grade {grade_level} | "
                    f"Avg: {avg} | Min: {min_grade} | "
                    f"→ {self.style.SUCCESS(final_status) if final_status == 'promoted' else self.style.ERROR(final_status)}"
                )

            if not dry_run:
                with transaction.atomic():
                    if existing and overwrite:
                        existing.final_status  = final_status
                        existing.overall_grade = overall_grade
                        existing.grade_level   = grade_level
                        existing.section       = section
                        existing.save()
                    else:
                        StudentAcademicYearStatus.objects.create(
                            student=student,
                            school_year=school_year,
                            grade_level=grade_level,
                            section=section,
                            final_status=final_status,
                            overall_grade=overall_grade,
                            remarks=(
                                f'Auto-generated by system. '
                                f'Based on {"Final Grade" if final_grades.filter(quarter=5).exists() else "Q4"} records.'
                            ),
                        )
                created += 1

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f"{'[DRY RUN] ' if dry_run else ''}Done!\n"
                f"  Processed : {total}\n"
                f"  Created   : {created}\n"
                f"  Skipped   : {skipped} (already exist)\n"
                f"  Promoted  : {promoted}\n"
                f"  Retained  : {retained}\n"
                f"  No grades : {no_grades} (set to pending)\n"
            )
        )