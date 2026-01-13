# Setup Instructions for Section Assignment Module Fixes

## Step 1: Install Required Dependencies

```bash
pip install reportlab python-docx
```

## Step 2: Apply Database Migration

```bash
python manage.py migrate coordinator_app
```

## Step 3: Verify Model Registration in Admin (Optional)

If you want to manage AI preferences through Django admin, add to `coordinator_app/admin.py`:

```python
from coordinator_app.models import AIAssistantPreference
from django.contrib import admin

@admin.register(AIAssistantPreference)
class AIAssistantPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'program', 'ai_enabled', 'updated_at')
    list_filter = ('program', 'ai_enabled', 'updated_at')
    search_fields = ('user__username', 'program__code')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Coordinator & Program', {
            'fields': ('user', 'program')
        }),
        ('Settings', {
            'fields': ('ai_enabled',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
```

## Step 4: Verify Changes

### Test Dynamic User Info

1. Log in as a coordinator
2. Navigate to Section Assignment page
3. Verify:
   - Your full name appears (from Django user first_name and last_name)
   - Your user type appears (from UserProfile)
   - Your profile photo appears OR your initials appear with background color
   - Your program code appears and is read-only

### Test AI Toggle (Per Program)

1. Log in as a coordinator (e.g., STEM coordinator)
2. Toggle AI Assistant OFF
3. Refresh the page - it should remain OFF
4. Log out and log in as different coordinator in different program
5. AI toggle should be ON in their program (independent setting)
6. Log back in as first coordinator - AI should still be OFF for them

### Test Export

1. Click "Export" button
2. Choose format: "pdf" or "docx"
3. File downloads with proper formatting
4. Verify:
   - Filename includes program code and date
   - Headers have coordinator name and date
   - Table has all student data properly formatted
   - Colors/styling is applied (PDF/DOCX specific)

## Troubleshooting

### Export not working?

- Ensure reportlab and python-docx are installed: `pip list | grep -E "reportlab|python-docx"`
- Check Django logs for error messages
- Verify CSRF token is being sent: Check browser DevTools Network tab

### AI toggle not persisting?

- Check browser console for JavaScript errors (F12 → Console)
- Verify database migration was applied: `python manage.py showmigrations coordinator_app`
- Check that user has a UserProfile with a Program assigned

### User info not showing?

- Verify Django User model has first_name and last_name filled
- Verify UserProfile exists for the user
- Check that UserProfile.program is set

## API Endpoints

### AI Toggle

```
POST /coordinator/api/section-assignment/ai-toggle/
Content-Type: application/json
X-CSRFToken: [token]

{
  "enabled": true/false
}

Response:
{
  "success": true,
  "message": "AI Assistant enabled for STEM program",
  "ai_enabled": true,
  "program": "STEM",
  "user_id": 1
}
```

### Export Assignments

```
POST /coordinator/api/section-assignment/export/
Content-Type: application/json
X-CSRFToken: [token]

{
  "format": "pdf"  // or "docx"
}

Response: Binary file (PDF or DOCX)
```

## Notes

- All settings are scoped to the logged-in user and their program
- AI preferences are stored in database (not localStorage)
- Export function retrieves live data from database
- CSRF protection is enabled on all API endpoints
- User must be logged in and have a coordinator profile
