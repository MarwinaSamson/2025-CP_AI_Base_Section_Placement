#!/usr/bin/env python
"""Test the API endpoints"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'section_placement_system.settings')
django.setup()

from django.contrib.auth.models import User
from admin_app.models import UserProfile

# Check if users exist
print("=" * 50)
print("CHECKING DATABASE USERS")
print("=" * 50)

users = User.objects.all()
print(f"\nTotal users in database: {users.count()}")

for user in users[:5]:  # Show first 5 users
    try:
        profile = user.profile
        print(f"\nUser: {user.username}")
        print(f"  - Name: {user.first_name} {user.last_name}")
        print(f"  - Email: {user.email}")
        print(f"  - Type: {profile.user_type}")
        print(f"  - Position: {profile.get_position_name()}")
        print(f"  - Department: {profile.get_department_name()}")
        print(f"  - Active: {user.is_active}")
    except UserProfile.DoesNotExist:
        print(f"\nUser: {user.username} - NO PROFILE!")
        print(f"  - Name: {user.first_name} {user.last_name}")
        print(f"  - Email: {user.email}")

print("\n" + "=" * 50)
print("TEST COMPLETE")
print("=" * 50)
