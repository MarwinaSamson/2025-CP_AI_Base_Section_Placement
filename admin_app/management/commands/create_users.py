from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from admin_app.models import UserProfile, Program

class Command(BaseCommand):
    help = 'Creates initial admin and coordinator users along with their profiles'

    def handle(self, *args, **kwargs):
        # Create admin user
        self.stdout.write(self.style.WARNING('Creating admin user...'))
        admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            first_name='Admin',
            last_name='User',
            email='admin@znhswest.edu'
        )
        UserProfile.objects.create(
            user=admin_user,
            user_type='admin'
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created admin user: {admin_user.username}'))

        # Create coordinator user
        self.stdout.write(self.style.WARNING('Creating coordinator user...'))
        # Ensure the program exists (you would probably have this already)
        program, created = Program.objects.get_or_create(
            code='STEM',
            defaults={'name': 'Science, Technology, Engineering, and Mathematics', 'description': 'Advanced science and math program'}
        )

        coord_user = User.objects.create_user(
            username='stem_coord',
            password='stem123',
            first_name='Juan',
            last_name='Garcia',
            email='juan.garcia@znhswest.edu'
        )
        
        # Create UserProfile for the coordinator
        UserProfile.objects.create(
            user=coord_user,
            user_type='coordinator',
            program=program,
            employee_id='COORD123'  # Assign a unique employee ID
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created coordinator user: {coord_user.username}'))

        self.stdout.write(self.style.SUCCESS('\n✅ Initial users creation completed!\n'))