"""
Management command to clear all data from Qualified_for_ste table
and reset the auto-increment ID
"""

from django.core.management.base import BaseCommand
from django.db import connection
from coordinator_app.models import Qualified_for_ste


class Command(BaseCommand):
    help = 'Delete all records from Qualified_for_ste table and reset auto-increment'

    def handle(self, *args, **options):
        # Confirm before deleting
        confirm = input('Are you sure you want to delete ALL Qualified_for_ste records? (yes/no): ')
        
        if confirm.lower() != 'yes':
            self.stdout.write(self.style.WARNING('Operation cancelled.'))
            return
        
        # Count records before deletion
        count = Qualified_for_ste.objects.count()
        
        # Delete all records
        Qualified_for_ste.objects.all().delete()
        
        # Reset auto-increment (for MySQL/MariaDB)
        with connection.cursor() as cursor:
            try:
                cursor.execute("ALTER TABLE qualified_for_ste AUTO_INCREMENT = 1")
                self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} records from Qualified_for_ste'))
                self.stdout.write(self.style.SUCCESS('Auto-increment ID reset to 1'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Records deleted but could not reset auto-increment: {str(e)}'))
                self.stdout.write(self.style.WARNING('This is normal for SQLite databases'))
