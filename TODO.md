# TODO Steps for Fixing "SchoolYear.students" Error

## Plan Status: Approved ✅

**Status: ✅ COMPLETED - Both fixes applied**

**Task Completed ✅**\n\nThe "Error loading school years: 'SchoolYear' object has no attribute 'students'" is fixed.\n\n**Changes:**\n1. ✅ Fixed `_school_year_to_dict()` - Now uses `get_total_students()` instead of non-existent `students.count()`\n2. ✅ Fixed `delete_school_year()` - Now uses `get_total_students() > 0` for check and count\n\n**Verification:** Reload the settings page - School years now load correctly with proper student counts.

**Breakdown:**
1. Fix `_school_year_to_dict()` → use `get_total_students()`
2. Fix `delete_school_year()` → check `get_total_students() > 0`

