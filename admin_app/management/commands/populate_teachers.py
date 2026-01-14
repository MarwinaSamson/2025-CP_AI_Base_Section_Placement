from django.core.management.base import BaseCommand
from admin_app.models import Teacher, Position, Department


class Command(BaseCommand):
    help = 'Populate the database with 10 sample teachers'

    def handle(self, *args, **kwargs):
        # Get or create positions
        position_t1, _ = Position.objects.get_or_create(
            name='Teacher I',
            defaults={'description': 'Entry-level teaching position'}
        )
        position_t2, _ = Position.objects.get_or_create(
            name='Teacher II',
            defaults={'description': 'Intermediate teaching position'}
        )
        position_t3, _ = Position.objects.get_or_create(
            name='Teacher III',
            defaults={'description': 'Advanced teaching position'}
        )
        position_mt1, _ = Position.objects.get_or_create(
            name='Master Teacher I',
            defaults={'description': 'Master teaching position'}
        )

        # Get or create departments
        dept_math, _ = Department.objects.get_or_create(
            name='Mathematics Department',
            defaults={'description': 'Department of Mathematics'}
        )
        dept_science, _ = Department.objects.get_or_create(
            name='Science Department',
            defaults={'description': 'Department of Science'}
        )
        dept_english, _ = Department.objects.get_or_create(
            name='English Department',
            defaults={'description': 'Department of English'}
        )
        dept_filipino, _ = Department.objects.get_or_create(
            name='Filipino Department',
            defaults={'description': 'Department of Filipino'}
        )
        dept_social, _ = Department.objects.get_or_create(
            name='Social Studies Department',
            defaults={'description': 'Department of Social Studies'}
        )

        # Sample teacher data
        teachers_data = [
            {
                'first_name': 'Maria',
                'middle_name': 'Santos',
                'last_name': 'Cruz',
                'email': 'maria.cruz@znhswest.edu.ph',
                'position': position_t3,
                'department': dept_math,
                'address': '123 Zamboanga City',
            },
            {
                'first_name': 'Juan',
                'middle_name': 'Dela',
                'last_name': 'Reyes',
                'email': 'juan.reyes@znhswest.edu.ph',
                'position': position_mt1,
                'department': dept_science,
                'address': '456 Zamboanga City',
            },
            {
                'first_name': 'Ana',
                'middle_name': 'Lopez',
                'last_name': 'Garcia',
                'email': 'ana.garcia@znhswest.edu.ph',
                'position': position_t2,
                'department': dept_english,
                'address': '789 Zamboanga City',
            },
            {
                'first_name': 'Pedro',
                'middle_name': 'Ramos',
                'last_name': 'Aquino',
                'email': 'pedro.aquino@znhswest.edu.ph',
                'position': position_t1,
                'department': dept_filipino,
                'address': '321 Zamboanga City',
            },
            {
                'first_name': 'Rosa',
                'middle_name': 'Mendoza',
                'last_name': 'Torres',
                'email': 'rosa.torres@znhswest.edu.ph',
                'position': position_t3,
                'department': dept_social,
                'address': '654 Zamboanga City',
            },
            {
                'first_name': 'Carlos',
                'middle_name': 'Flores',
                'last_name': 'Bautista',
                'email': 'carlos.bautista@znhswest.edu.ph',
                'position': position_t2,
                'department': dept_math,
                'address': '987 Zamboanga City',
            },
            {
                'first_name': 'Elena',
                'middle_name': 'Santiago',
                'last_name': 'Villanueva',
                'email': 'elena.villanueva@znhswest.edu.ph',
                'position': position_t1,
                'department': dept_science,
                'address': '147 Zamboanga City',
            },
            {
                'first_name': 'Roberto',
                'middle_name': 'Castro',
                'last_name': 'Fernandez',
                'email': 'roberto.fernandez@znhswest.edu.ph',
                'position': position_t3,
                'department': dept_english,
                'address': '258 Zamboanga City',
            },
            {
                'first_name': 'Carmen',
                'middle_name': 'Rivera',
                'last_name': 'Morales',
                'email': 'carmen.morales@znhswest.edu.ph',
                'position': position_mt1,
                'department': dept_filipino,
                'address': '369 Zamboanga City',
            },
            {
                'first_name': 'Miguel',
                'middle_name': 'Hernandez',
                'last_name': 'Pascual',
                'email': 'miguel.pascual@znhswest.edu.ph',
                'position': position_t2,
                'department': dept_social,
                'address': '741 Zamboanga City',
            },
        ]

        created_count = 0
        skipped_count = 0

        for teacher_data in teachers_data:
            # Check if teacher with this email already exists
            if Teacher.objects.filter(email=teacher_data['email']).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipped: {teacher_data['first_name']} {teacher_data['last_name']} (email already exists)"
                    )
                )
                skipped_count += 1
                continue

            # Create teacher
            teacher = Teacher.objects.create(**teacher_data)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created: {teacher.get_full_name()} - {teacher.position.name} ({teacher.department.name})"
                )
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Successfully created {created_count} teacher(s)'
            )
        )
        if skipped_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠ Skipped {skipped_count} teacher(s) (already exist)'
                )
            )
