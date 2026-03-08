"""
Management command: set_grade7

Sets grade_level = Grade 7 for ALL existing students and sections
that currently have no grade level (or optionally all of them).

Usage:
  python manage.py set_grade7
  python manage.py set_grade7 --force          # overwrite even if already set
  python manage.py set_grade7 --dry-run        # preview without saving
"""

from django.core.management.base import BaseCommand
from admin_app.models import GradeLevel, Section
from enrollment_app.models import Student


class Command(BaseCommand):
    help = 'Set grade_level = Grade 7 for all existing students and sections'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite grade_level even if already set (default: only update NULL entries)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview how many records will be updated without saving anything',
        )

    def handle(self, *args, **options):
        force   = options['force']
        dry_run = options['dry_run']

        # ── 1. Find Grade 7 ───────────────────────────────────────────────────
        grade7 = GradeLevel.objects.filter(code='G7').first()
        if not grade7:
            # Try by name if code is different
            grade7 = GradeLevel.objects.filter(name__icontains='grade 7').first()

        if not grade7:
            self.stderr.write(self.style.ERROR(
                'Grade 7 not found in GradeLevel table.\n'
                'Please add it first via Admin → Settings → Others → Grade Level.'
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f'Found Grade 7 → id={grade7.id}, code="{grade7.code}", name="{grade7.name}"'
        ))

        # ── 2. Update Sections ────────────────────────────────────────────────
        if force:
            section_qs = Section.objects.all()
        else:
            section_qs = Section.objects.filter(grade_level__isnull=True)

        section_count = section_qs.count()

        if dry_run:
            self.stdout.write(f'[DRY RUN] Sections to update: {section_count}')
        else:
            updated = section_qs.update(grade_level=grade7)
            self.stdout.write(self.style.SUCCESS(
                f'✔ Sections updated: {updated}'
            ))

        # ── 3. Update Students ────────────────────────────────────────────────
        if force:
            student_qs = Student.objects.all()
        else:
            student_qs = Student.objects.filter(grade_level__isnull=True)

        student_count = student_qs.count()

        if dry_run:
            self.stdout.write(f'[DRY RUN] Students to update: {student_count}')
            self.stdout.write(self.style.WARNING(
                '\nDry run complete. No changes saved. Remove --dry-run to apply.'
            ))
        else:
            updated = student_qs.update(grade_level=grade7)
            self.stdout.write(self.style.SUCCESS(
                f'✔ Students updated: {updated}'
            ))
            self.stdout.write(self.style.SUCCESS(
                '\nDone! All targeted records now have Grade 7 assigned.'
            ))
