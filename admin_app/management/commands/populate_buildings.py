from django.core.management.base import BaseCommand
from admin_app.models import Building, Room


class Command(BaseCommand):
    help = 'Populates the database with buildings and rooms'

    def handle(self, *args, **options):
        self.stdout.write('Populating buildings and rooms...')

        # Define buildings and their rooms
        buildings_data = {
            'Building 1': ['101', '102', '103', '104', '105'],
            'Building 2': ['201', '202', '203', '204', '205'],
            'Building 3': ['301', '302', '303', '304', '305'],
            'Building 4': ['Lab 1', 'Lab 2', 'Lab 3', 'Lecture 1', 'Lecture 2'],
            'Building 5': ['IT-101', 'IT-102', 'IT-201', 'IT-202', 'Server Room']
        }

        created_buildings = 0
        created_rooms = 0

        for building_name, room_numbers in buildings_data.items():
            # Get or create building
            building, building_created = Building.objects.get_or_create(name=building_name)
            if building_created:
                created_buildings += 1
                self.stdout.write(self.style.SUCCESS(f'Created building: {building_name}'))
            
            # Create rooms for this building
            for room_number in room_numbers:
                room, room_created = Room.objects.get_or_create(
                    building=building,
                    room_number=room_number
                )
                if room_created:
                    created_rooms += 1
                    self.stdout.write(f'  - Created room: {room_number}')

        self.stdout.write(self.style.SUCCESS(
            f'\nCompleted! Created {created_buildings} buildings and {created_rooms} rooms.'
        ))