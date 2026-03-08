"""
Adds a nullable grade_level FK to DocumentRequirement.

Why nullable:
  - All existing requirement rows automatically get NULL, meaning they still
    apply to every grade level — zero change in current behaviour.
  - Admin can now optionally pin a requirement to a specific grade.
    e.g.  SF9 / Form 138 (Grade 6 card)  →  grade_level = G7
          SF9 / Form 138 (Grade 7 card)  →  grade_level = G8
    Requirements left NULL continue to apply to every grade.

View query pattern after this migration:
    from django.db.models import Q
    DocumentRequirement.objects.filter(
        school_year=active_sy,
        is_active=True,
    ).filter(
        Q(applies_to='all') | Q(applies_to=student.enrollee_type)
    ).filter(
        Q(grade_level__isnull=True) | Q(grade_level=student.grade_level)
    )
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0017_seed_grade_levels'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentrequirement',
            name='grade_level',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='document_requirements',
                to='admin_app.gradelevel',
                help_text=(
                    'If set, only students enrolling into this grade level see this requirement. '
                    'Leave blank (NULL) for requirements that apply to all grade levels.'
                ),
            ),
        ),
        migrations.AddIndex(
            model_name='documentrequirement',
            index=models.Index(fields=['grade_level'], name='doc_req_grade_level_idx'),
        ),
    ]
