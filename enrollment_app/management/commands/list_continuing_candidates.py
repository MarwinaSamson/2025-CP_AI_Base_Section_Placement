"""
Management command: list_continuing_candidates

Lists students from a source school year who have `final_status='promoted'`
and therefore are eligible to enroll as `continuing` in a target school year.

Usage:
  python manage.py list_continuing_candidates --from "2025-2026" --to "2026-2027"
  python manage.py list_continuing_candidates --from "2025-2026" --to "2026-2027" --csv out.csv
  python manage.py list_continuing_candidates --from "2025-2026" --to "2026-2027" --only-not-enrolled

If both `--from` and `--to` are omitted the command will attempt to auto-detect
the most recent inactive school year as source and the active school year as target.
"""

import csv
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'List students eligible to re-enroll as continuing based on promoted statuses'

    def add_arguments(self, parser):
        parser.add_argument('--from', dest='from_sy', help='Source school year label (e.g. 2025-2026)')
        parser.add_argument('--to', dest='to_sy', help='Target (next) school year label (e.g. 2026-2027)')
        parser.add_argument('--csv', dest='csv_path', help='Write results to CSV file')
        parser.add_argument('--only-not-enrolled', dest='only_not_enrolled', action='store_true',
                            help='Only include students who are NOT already enrolled in the target year')

    def handle(self, *args, **options):
        from admin_app.models import SchoolYear
        from enrollment_app.models import (
            StudentAcademicYearStatus, StudentEnrollment
        )

        from_label = options.get('from_sy')
        to_label = options.get('to_sy')

        # Resolve school years
        if from_label:
            try:
                from_sy = SchoolYear.objects.get(year_label=from_label)
            except SchoolYear.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Source school year '{from_label}' not found."))
                return
        else:
            # pick most recent inactive as source
            from_sy = SchoolYear.objects.filter(is_active=False).order_by('-year_label').first()
            if not from_sy:
                self.stderr.write(self.style.ERROR('No inactive school year found to use as source.'))
                return

        if to_label:
            try:
                to_sy = SchoolYear.objects.get(year_label=to_label)
            except SchoolYear.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Target school year '{to_label}' not found."))
                return
        else:
            to_sy = SchoolYear.objects.filter(is_active=True).first()
            if not to_sy:
                self.stderr.write(self.style.ERROR('No active school year found to use as target.'))
                return

        self.stdout.write(self.style.NOTICE(f"Checking promoted students from {from_sy.year_label} → {to_sy.year_label}\n"))

        # Query promoted statuses
        statuses = StudentAcademicYearStatus.objects.filter(
            school_year=from_sy,
            final_status='promoted'
        ).select_related('student', 'grade_level', 'section')

        rows = []
        for st in statuses:
            student = st.student
            enrolled_qs = StudentEnrollment.objects.filter(student=student, school_year=to_sy)
            enrolled = enrolled_qs.exists()
            enrollee_type = None
            if enrolled:
                en = enrolled_qs.first()
                enrollee_type = en.enrollee_type

            # Build name safely
            sd = getattr(student, 'student_data', None)
            name = ''
            if sd:
                first = getattr(sd, 'first_name', '') or ''
                last = getattr(sd, 'last_name', '') or ''
                name = f"{first} {last}".strip()

            row = {
                'lrn': str(student.lrn),
                'name': name,
                'grade_level': st.grade_level.name if st.grade_level else '',
                'section': st.section.name if st.section else '',
                'overall_grade': str(st.overall_grade) if st.overall_grade is not None else '',
                'final_status': st.final_status,
                'already_enrolled': 'yes' if enrolled else 'no',
                'enrollee_type': enrollee_type or '',
            }

            if options.get('only_not_enrolled') and enrolled:
                continue

            rows.append(row)

        # Output
        if options.get('csv_path'):
            path = options.get('csv_path')
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['lrn','name','grade_level','section','overall_grade','final_status','already_enrolled','enrollee_type'])
                writer.writeheader()
                for r in rows:
                    writer.writerow(r)
            self.stdout.write(self.style.SUCCESS(f'Wrote {len(rows)} rows to {path}'))
        else:
            if not rows:
                self.stdout.write('No promoted students found (or filtered out).')
                return
            fmt = '{:<14} {:<30} {:<12} {:<12} {:<8} {:<10} {:<14} {:<12}'
            self.stdout.write(fmt.format('LRN','Name','Grade','Section','Avg','Status','Already Enrolled','Type'))
            self.stdout.write('-'*120)
            for r in rows:
                self.stdout.write(fmt.format(r['lrn'], r['name'][:30], r['grade_level'][:12], r['section'][:12], r['overall_grade'][:8], r['final_status'][:10], r['already_enrolled'][:14], r['enrollee_type'][:12]))
