from django.shortcuts import render, redirect
from admin_app.models import SystemSettings, StaffMember

def landing_page(request):
    """
    Landing page with dynamic content from SystemSettings
    """
    # Fetch all settings
    try:
        settings_qs = SystemSettings.objects.all()
        settings = {}
        for setting in settings_qs:
            settings[setting.setting_type] = {
                'value': setting.setting_value,
                'image_url': setting.image.url if setting.image else None
            }
    except Exception as e:
        settings = {}
    
    # Fetch active staff members
    try:
        staff_members = StaffMember.objects.filter(is_active=True).order_by('display_order', 'name')
    except Exception:
        staff_members = []
    
    # Helper function to get setting value safely
    def get_setting(key, default=''):
        return settings.get(key, {}).get('value', default)
    
    def get_setting_image(key):
        return settings.get(key, {}).get('image_url', None)
    
    context = {
        # Header
        'header_logo_school': get_setting_image('header_logo_school'),
        'header_logo_region': get_setting_image('header_logo_region'),
        'header_logo_peninsula': get_setting_image('header_logo_peninsula'),
        'header_logo_matatag': get_setting_image('header_logo_matatag'),
        'header_caption': get_setting('header_caption', '''
            <h2 class="text-2xl font-bold mb-4">Welcome to Excellence in Education</h2>
            <p class="text-lg">Empowering students to achieve their dreams through quality education and innovative programs</p>
        '''),
        
        # Announcements
        'announcement_image': get_setting_image('announcement_image'),
        'announcement_caption': get_setting('announcement_caption', 'Stay updated with our latest announcements'),
        
        # Contact Information
        'contact_address': get_setting('contact_address', 'R.T. Lim Boulevard Zamboanga City, Philippines'),
        'contact_phone': get_setting('contact_phone', '+63 61 0086516'),
        'contact_email': get_setting('contact_email', 'nationalhighschoolwest@gmail.com'),
        'contact_facebook': get_setting('contact_facebook', 'https://web.facebook.com/znhs.west'),
        'contact_hours': get_setting('contact_hours', '''Monday to Friday: 7:00 AM - 5:00 PM
Saturday: 7:00 AM - 5:00 PM
Sunday: Closed'''),
        
        # Footer
        'footer_copyright': get_setting('footer_copyright', '© 2025 Zamboanga National High School West. All rights reserved.'),
        
        # Staff Members
        'staff_members': staff_members,
    }
    
    return render(request, 'enrollment_app/landing.html', context)

def clear_session(request):
    request.session.clear()
    return redirect('enrollment_app:landing')
