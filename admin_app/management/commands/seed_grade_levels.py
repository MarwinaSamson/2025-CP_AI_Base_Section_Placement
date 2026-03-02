from django.core.management.base import BaseCommand
from admin_app.models import GradeLevel

class Command(BaseCommand):
    help = 'Seed Grade 7-10 into GradeLevel table'

    def handle(self, *args, **kwargs):
        grades = [
            {'code': 'G7',  'name': 'Grade 7'},
            {'code': 'G8',  'name': 'Grade 8'},
            {'code': 'G9',  'name': 'Grade 9'},
            {'code': 'G10', 'name': 'Grade 10'},
        ]
        for g in grades:
            obj, created = GradeLevel.objects.get_or_create(
                code=g['code'],
                defaults={'name': g['name'], 'is_active': True}
            )
            status = 'Created' if created else 'Already exists'
            self.stdout.write(f"{status}: {obj.name}")
        self.stdout.write(self.style.SUCCESS('Done!'))