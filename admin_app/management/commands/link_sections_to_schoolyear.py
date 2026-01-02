"""
Management command to link existing sections to the current active school year
Usage: python manage.py link_sections_to_schoolyear
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from admin_app.models import Section, SchoolYear


class Command(BaseCommand):
    help = 'Links all existing sections without a school year to the current active school year'

    def add_arguments(self, parser):
        parser.add_argument(
            '--school-year',
            type=str,
            help='School year label (e.g., 2025-2026) to link sections to. If not provided, uses the active school year.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating',
        )

    def handle(self, *args, **options):
        school_year_label = options.get('school_year')
        dry_run = options.get('dry_run')

        try:
            # Get the target school year
            if school_year_label:
                school_year = SchoolYear.objects.get(year_label=school_year_label)
                self.stdout.write(self.style.SUCCESS(f'Using school year: {school_year.year_label}'))
            else:
                school_year = SchoolYear.objects.filter(is_active=True).first()
                if not school_year:
                    self.stdout.write(self.style.ERROR('No active school year found. Please create one first or specify --school-year'))
                    return
                self.stdout.write(self.style.SUCCESS(f'Using active school year: {school_year.year_label}'))

            # Get sections without a school year
            sections_without_year = Section.objects.filter(school_year__isnull=True)
            count = sections_without_year.count()

            if count == 0:
                self.stdout.write(self.style.WARNING('No sections found without a school year. All sections are already linked!'))
                return

            self.stdout.write(f'\nFound {count} section(s) without a school year:')
            self.stdout.write('=' * 80)
            
            for section in sections_without_year:
                self.stdout.write(f'  - {section.program.code} - {section.name} (Adviser: {section.adviser or "None"})')

            if dry_run:
                self.stdout.write('\n' + '=' * 80)
                self.stdout.write(self.style.WARNING('DRY RUN: No changes were made. Remove --dry-run to apply changes.'))
                return

            # Confirm before proceeding
            self.stdout.write('\n' + '=' * 80)
            confirm = input(f'\nLink these {count} section(s) to school year "{school_year.year_label}"? (yes/no): ')
            
            if confirm.lower() not in ['yes', 'y']:
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return

            # Update sections
            with transaction.atomic():
                updated_count = sections_without_year.update(school_year=school_year)
                
                self.stdout.write('\n' + '=' * 80)
                self.stdout.write(self.style.SUCCESS(f'✓ Successfully linked {updated_count} section(s) to school year "{school_year.year_label}"'))
                
                # Show summary
                self.stdout.write('\nSummary by Program:')
                programs = sections_without_year.values_list('program__code', flat=True).distinct()
                for program_code in programs:
                    program_count = Section.objects.filter(
                        school_year=school_year, 
                        program__code=program_code
                    ).count()
                    self.stdout.write(f'  - {program_code}: {program_count} section(s)')

        except SchoolYear.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'School year "{school_year_label}" not found.'))
            self.stdout.write('Available school years:')
            for sy in SchoolYear.objects.all():
                active_marker = ' (ACTIVE)' if sy.is_active else ''
                self.stdout.write(f'  - {sy.year_label}{active_marker}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
