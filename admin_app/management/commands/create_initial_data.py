from django.core.management.base import BaseCommand
from admin_app.models import Position, Department, Program

class Command(BaseCommand):
    help = 'Creates initial positions, departments, and programs'

    def handle(self, *args, **kwargs):
        # Create Positions
        self.stdout.write(self.style.WARNING('\n📋 Creating Positions...'))
        positions = [
            {'name': 'Teacher I', 'description': 'Entry-level teaching position'},
            {'name': 'Teacher II', 'description': 'Mid-level teaching position'},
            {'name': 'Teacher III', 'description': 'Senior teaching position'},
            {'name': 'Master Teacher I', 'description': 'Advanced teaching position'},
            {'name': 'Master Teacher II', 'description': 'Advanced teaching position'},
            {'name': 'Master Teacher III', 'description': 'Advanced teaching position'},
            {'name': 'Head Teacher I', 'description': 'Department head position'},
            {'name': 'Head Teacher II', 'description': 'Department head position'},
            {'name': 'Head Teacher III', 'description': 'Department head position'},
            {'name': 'Principal I', 'description': 'School principal'},
            {'name': 'Principal II', 'description': 'School principal'},
            {'name': 'Principal III', 'description': 'School principal'},
            {'name': 'School Head', 'description': 'School head administrator'},
        ]

        for pos_data in positions:
            pos, created = Position.objects.get_or_create(
                name=pos_data['name'],
                defaults={'description': pos_data['description']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created position: {pos.name}'))
            else:
                self.stdout.write(f'  - Position already exists: {pos.name}')

        # Create Departments
        self.stdout.write(self.style.WARNING('\n🏢 Creating Departments...'))
        departments = [
            {'name': 'English Department', 'description': 'Handles English language and literature education'},
            {'name': 'Science Department', 'description': 'Covers all science subjects'},
            {'name': 'Mathematics Department', 'description': 'Mathematics and related subjects'},
            {'name': 'Filipino Department', 'description': 'Filipino language and culture'},
            {'name': 'Values Department', 'description': 'Values education and character formation'},
            {'name': 'TLE Department', 'description': 'Technology and Livelihood Education'},
            {'name': 'History Department', 'description': 'History and social studies'},
            {'name': 'MAPEH Department', 'description': 'Music, Arts, Physical Education, and Health'},
        ]

        for dept_data in departments:
            dept, created = Department.objects.get_or_create(
                name=dept_data['name'],
                defaults={'description': dept_data['description']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created department: {dept.name}'))
            else:
                self.stdout.write(f'  - Department already exists: {dept.name}')

        # Create Programs
        self.stdout.write(self.style.WARNING('\n🎓 Creating Programs...'))
        programs = [
            {'code': 'STE', 'name': 'Science, Technology, and Engineering', 'description': 'Focus on science and technology education'},
            {'code': 'STEM', 'name': 'Science, Technology, Engineering, and Mathematics', 'description': 'Advanced science and math program'},
            {'code': 'SPFL', 'name': 'Special Program in Foreign Language', 'description': 'Language immersion program'},
            {'code': 'SPTVE', 'name': 'Special Program in Technical-Vocational Education', 'description': 'Technical and vocational skills'},
            {'code': 'TOP5', 'name': 'TOP 5 Program', 'description': 'Top performing students program'},
            {'code': 'HETERO', 'name': 'Heterogeneous', 'description': 'Mixed ability grouping'},
        ]

        for prog_data in programs:
            prog, created = Program.objects.get_or_create(
                code=prog_data['code'],
                defaults={
                    'name': prog_data['name'],
                    'description': prog_data['description']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created program: {prog.code} - {prog.name}'))
            else:
                self.stdout.write(f'  - Program already exists: {prog.code}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Initial data creation completed!\n'))