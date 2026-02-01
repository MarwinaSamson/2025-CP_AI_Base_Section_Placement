#!/usr/bin/env python
"""
Diagnostic script to check section creation order for TOP5 track.
This will reveal why the sequential fill rule isn't working as expected.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'section_placement_system.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from admin_app.models import Section, SchoolYear

print("=" * 80)
print("SECTION ORDER DIAGNOSTIC - TOP5 TRACK")
print("=" * 80)

# Get active school year
school_year = SchoolYear.objects.filter(is_active=True).order_by('-start_date').first()
if not school_year:
    school_year = SchoolYear.objects.order_by('-start_date').first()

print(f"\nActive School Year: {school_year}")

# Get all TOP5 sections ordered by created_at (the way signals.py does it)
print("\n" + "-" * 80)
print("TOP5 SECTIONS - Ordered by created_at (sequential fill order):")
print("-" * 80)

top5_sections = Section.objects.filter(
    program__code='REGULAR',
    regular_track='TOP5',
    school_year=school_year
).order_by('created_at')

for i, section in enumerate(top5_sections, 1):
    actual_count = section.get_actual_count()
    print(f"{i}. {section.name}")
    print(f"   ID: {section.id}")
    print(f"   created_at: {section.created_at}")
    print(f"   Enrolled: {actual_count}/{section.max_students}")
    print(f"   Has space: {actual_count < section.max_students}")
    print()

# Also check HETERO for comparison
print("-" * 80)
print("HETERO SECTIONS - Ordered by created_at:")
print("-" * 80)

hetero_sections = Section.objects.filter(
    program__code='REGULAR',
    regular_track='HETERO',
    school_year=school_year
).order_by('created_at')

for i, section in enumerate(hetero_sections, 1):
    actual_count = section.get_actual_count()
    print(f"{i}. {section.name}")
    print(f"   ID: {section.id}")
    print(f"   created_at: {section.created_at}")
    print(f"   Enrolled: {actual_count}/{section.max_students}")
    print()

# Show what _get_next_available_section would return
print("=" * 80)
print("SIMULATING _get_next_available_section('REGULAR', school_year, 'TOP5'):")
print("=" * 80)

for section in top5_sections:
    actual_count = section.get_actual_count()
    if actual_count < section.max_students:
        print(f"\n>>> WOULD SELECT: {section.name} (ID: {section.id})")
        print(f"    Reason: First section in created_at order with available space")
        print(f"    Enrolled: {actual_count}/{section.max_students}")
        break
    else:
        print(f"Skipping {section.name} - FULL ({actual_count}/{section.max_students})")
else:
    print("\n>>> No available TOP5 sections found!")

print("\n" + "=" * 80)
