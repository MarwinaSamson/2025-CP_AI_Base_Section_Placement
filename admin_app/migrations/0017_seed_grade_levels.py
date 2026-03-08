"""
Data migration — seeds the four standard JHS grade level rows.
Uses get_or_create so it is safe to run on a database that already
has some or all of these rows (idempotent).
Reverse operation is intentionally a no-op: we never want to delete
grade levels automatically because other tables FK into them.
"""

from django.db import migrations


def seed_grade_levels(apps, schema_editor):
    GradeLevel = apps.get_model('admin_app', 'GradeLevel')
    grades = [
        ('G7',  'Grade 7'),
        ('G8',  'Grade 8'),
        ('G9',  'Grade 9'),
        ('G10', 'Grade 10'),
    ]
    for code, name in grades:
        GradeLevel.objects.get_or_create(
            code=code,
            defaults={
                'name':      name,
                'is_active': True,
            },
        )


def reverse_seed(apps, schema_editor):
    # Intentionally non-destructive — do not delete rows on rollback.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0016_lisstudent'),
    ]

    operations = [
        migrations.RunPython(seed_grade_levels, reverse_seed),
    ]
