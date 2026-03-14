"""
management/commands/promote_continuing_students.py

Promotes all approved students from a completed school year into the next
school year as continuing enrollees.

Usage:
    # Dry run first — shows what WOULD happen, changes nothing
    python manage.py promote_continuing_students --dry-run

    # Specify school years explicitly
    python manage.py promote_continuing_students --from-sy 2025-2026 --to-sy 2026-2027

    # Auto-detect: uses the currently active SY as source, prompts for target
    python manage.py promote_continuing_students

What it does per student:
    1. Maps their grade to the next (G7→G8, G8→G9, G9→G10).
       Grade 10 graduates are skipped and reported separately.
    2. Checks for an active ProbationRecord — if found, forces REGULAR program.
    3. Updates the Student record for the new school year:
       - school_year, grade_level, enrollee_type = 'continuing'
       - enrollment_status reset to 'draft'
       - completion flags reset (student must re-fill application form)
       - documents_completed stays True (carry-over handled below)
    4. Updates the ProgramSelection for the new school year.
    5. Calls StudentDocumentSubmission.carry_over_for_student() so the student
       does NOT need to upload documents again — the coordinator hands them over
       physically, and the system marks documents as on-file.

Safety:
    - --dry-run shows a full preview with no database writes.
    - Non-approved students (draft, under_review, rejected) are untouched.
    - G10 graduates are listed but NOT modified.
    - Already-promoted students (already in the target SY) are skipped safely.
    - A confirmation prompt is shown before any writes unless --yes is passed.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from admin_app.models import GradeLevel, SchoolYear
from coordinator_app.models import ProbationRecord
from enrollment_app.models import (
    ProgramSelection,
    Student,
    StudentEnrollment,
    StudentDocumentSubmission,
)


# Grade progression order — code must match what's in the GradeLevel table
GRADE_NEXT = {
    'G7':  'G8',
    'G8':  'G9',
    'G9':  'G10',
    'G10': None,   # None = graduate, do not promote
}


class Command(BaseCommand):
    help = (
        'Promotes all approved students to the next grade level for a new school year. '
        'Checks probation records and carries over documents automatically.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--from-sy',
            dest='from_sy',
            default=None,
            help='Source school year label (e.g. 2025-2026). Defaults to the currently active SY.',
        )
        parser.add_argument(
            '--to-sy',
            dest='to_sy',
            default=None,
            help='Target school year label (e.g. 2026-2027). Must already exist in the SchoolYear table.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help='Preview what would happen without making any changes.',
        )
        parser.add_argument(
            '--yes',
            action='store_true',
            dest='yes',
            help='Skip the confirmation prompt and proceed immediately.',
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_school_year(self, label, active_fallback=False):
        if label:
            try:
                return SchoolYear.objects.get(year_label=label)
            except SchoolYear.DoesNotExist:
                raise CommandError(
                    f"School year '{label}' not found. "
                    f"Available: {list(SchoolYear.objects.values_list('year_label', flat=True))}"
                )
        if active_fallback:
            sy = SchoolYear.objects.filter(is_active=True).first()
            if not sy:
                raise CommandError(
                    'No active school year found. '
                    'Set one as active in the admin or pass --from-sy explicitly.'
                )
            return sy
        return None

    def _next_grade(self, grade_level):
        """Returns the next GradeLevel object or None if G10 (graduate)."""
        if not grade_level:
            return None
        next_code = GRADE_NEXT.get(grade_level.code)
        if next_code is None:
            return None   # G10 → graduate
        try:
            return GradeLevel.objects.get(code=next_code)
        except GradeLevel.DoesNotExist:
            raise CommandError(
                f"Next grade '{next_code}' not found in GradeLevel table. "
                f"Run the seed migration first: python manage.py migrate"
            )

    # ------------------------------------------------------------------
    # Main handler
    # ------------------------------------------------------------------

    def handle(self, *args, **options):
        dry_run  = options['dry_run']
        skip_confirm = options['yes']

        # ── Resolve school years ──────────────────────────────────────
        from_sy = self._get_school_year(options['from_sy'], active_fallback=True)

        if options['to_sy']:
            to_sy = self._get_school_year(options['to_sy'])
        else:
            # List available years and ask which one to promote into
            years = SchoolYear.objects.exclude(pk=from_sy.pk).order_by('-year_label')
            if not years.exists():
                raise CommandError(
                    'No other school years exist to promote into. '
                    'Create the next school year in the admin first, then re-run.'
                )
            self.stdout.write('\nAvailable target school years:')
            for i, sy in enumerate(years, 1):
                self.stdout.write(f'  {i}. {sy.year_label}')
            choice = input('\nEnter the NUMBER of the target school year: ').strip()
            try:
                to_sy = list(years)[int(choice) - 1]
            except (ValueError, IndexError):
                raise CommandError('Invalid selection. Aborted.')

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f'\n{"DRY RUN — " if dry_run else ""}Promoting: '
                f'{from_sy.year_label}  →  {to_sy.year_label}\n'
            )
        )

        # ── Fetch approved students in the source SY ──────────────────
        students = (
            Student.objects
            .filter(school_year=from_sy, enrollment_status='approved')
            .select_related('grade_level', 'program_selection')
            .order_by('grade_level__code')
        )

        if not students.exists():
            self.stdout.write(self.style.WARNING(
                f'No approved students found in {from_sy.year_label}. Nothing to do.'
            ))
            return

        # ── Preview ───────────────────────────────────────────────────
        promote_list  = []   # (student, next_grade, program_code, probation_record)
        graduate_list = []   # students finishing G10
        skip_list     = []   # already in target SY

        for student in students:
            # Skip students already promoted into this SY
            if student.school_year_id == to_sy.pk:
                skip_list.append(student)
                continue

            grade = student.grade_level
            next_grade = self._next_grade(grade)

            if next_grade is None:
                graduate_list.append(student)
                continue

            # Get current program from ProgramSelection
            ps = getattr(student, 'program_selection', None)
            current_program = ps.selected_program_code if ps else None

            # Check for active probation
            probation = ProbationRecord.get_active_for_student(student)
            if probation:
                final_program = 'REGULAR'
            else:
                final_program = current_program  # stays the same

            promote_list.append((student, next_grade, final_program, probation))

        # ── Print summary ─────────────────────────────────────────────
        self.stdout.write(f'  Students to promote : {len(promote_list)}')
        self.stdout.write(f'  Graduates (G10)     : {len(graduate_list)}')
        self.stdout.write(f'  Already in target SY: {len(skip_list)}')
        self.stdout.write('')

        if promote_list:
            self.stdout.write(self.style.MIGRATE_HEADING('Promotion details:'))
            for student, next_grade, program, probation in promote_list:
                sd = getattr(student, 'student_data', None)
                name = sd.full_name if sd else student.lrn
                current_grade = student.grade_level.code if student.grade_level else '?'
                probation_note = (
                    f'  ⚠  PROBATED ({probation.previous_program} → REGULAR)'
                    if probation else ''
                )
                self.stdout.write(
                    f'  {name:<35} {current_grade} → {next_grade.code:<4} '
                    f'| program: {program or "—"}{probation_note}'
                )

        if graduate_list:
            self.stdout.write('')
            self.stdout.write(self.style.MIGRATE_HEADING('Graduates (will NOT be promoted):'))
            for student in graduate_list:
                sd = getattr(student, 'student_data', None)
                name = sd.full_name if sd else student.lrn
                self.stdout.write(f'  {name} — G10 graduate')

        if dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                'DRY RUN complete — no changes were made. '
                'Remove --dry-run to apply.'
            ))
            return

        if not promote_list:
            self.stdout.write(self.style.SUCCESS('\nNothing to promote.'))
            return

        # ── Confirmation ──────────────────────────────────────────────
        if not skip_confirm:
            answer = input(
                f'\nProceed with promoting {len(promote_list)} student(s)? (yes/no): '
            ).strip().lower()
            if answer != 'yes':
                self.stdout.write(self.style.WARNING('Aborted.'))
                return

        # ── Apply changes ─────────────────────────────────────────────
        promoted  = 0
        errored   = 0
        now       = timezone.now()

        for student, next_grade, final_program, probation in promote_list:
            try:
                with transaction.atomic():
                    # 1. Create NEW StudentEnrollment for the target year
                    # (Do NOT update Student — it's stable, LRN-based)
                    enrollment, created = StudentEnrollment.objects.get_or_create(
                        student=student,
                        school_year=to_sy,
                        defaults={
                            'grade_level': next_grade,
                            'enrollee_type': 'continuing',
                            'enrollment_status': 'draft',
                            'is_locked': False,
                            # All form_completed start as False for continuing students
                            'student_data_completed': False,
                            'family_data_completed': False,
                            'survey_completed': False,
                            'academic_data_completed': False,
                            'program_selected': False,
                            'documents_completed': False,
                        }
                    )

                    # 2. Update or create ProgramSelection for the target year
                    ps, ps_created = ProgramSelection.objects.get_or_create(
                        student=student,
                        school_year=to_sy,
                        defaults={
                            'selected_program_code': final_program,
                            'requires_program_selection': False,
                            'selection_reason': (
                                f'Promoted from {from_sy.year_label}. '
                                + (f'Probated: moved from {probation.previous_program} to REGULAR.'
                                   if probation else 'Program retained.')
                            ),
                        }
                    )

                    if not ps_created:
                        # Update existing ProgramSelection
                        ps.selected_program_code = final_program
                        ps.requires_program_selection = False
                        ps.admin_approved = False
                        ps.admin_rejected = False
                        ps.admin_notes = None
                        ps.approved_by = None
                        ps.approved_at = None
                        ps.rejected_by = None
                        ps.rejected_at = None
                        ps.rejection_reason = None
                        ps.assigned_section = None
                        ps.section_assigned_at = None
                        ps.regular_track = None
                        ps.program_description = None
                        ps.selection_reason = (
                            f'Promoted from {from_sy.year_label}. '
                            + (f'Probated: moved from {probation.previous_program} to REGULAR.'
                               if probation else 'Program retained.')
                        )
                        ps.save()

                    # 3. Carry over documents (marks documents_completed=True automatically)
                    StudentDocumentSubmission.carry_over_for_student(student, to_sy)

                promoted += 1

            except Exception as exc:
                errored += 1
                sd = getattr(student, 'student_data', None)
                name = sd.full_name if sd else student.lrn
                self.stdout.write(self.style.ERROR(
                    f'  ERROR promoting {name} ({student.lrn}): {exc}'
                ))

        # ── Final report ──────────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done.  Promoted: {promoted}  |  Errors: {errored}  |  '
            f'Graduates skipped: {len(graduate_list)}'
        ))

        if errored:
            self.stdout.write(self.style.WARNING(
                'Some students failed — check the errors above and re-run for those students.'
            ))
