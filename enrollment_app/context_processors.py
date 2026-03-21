import json
from admin_app.models import SystemSettings, StaffMember

def content_settings(request):
    try:
        smap = {s.setting_type: s for s in SystemSettings.objects.all()}

        def val(key, default=''):
            s = smap.get(key)
            return s.setting_value if s else default

        def img(key):
            s = smap.get(key)
            return s.image.url if s and s.image else None

        try:
            footer_links = json.loads(val('footer_links', '{}'))
        except (json.JSONDecodeError, TypeError):
            footer_links = {}

        try:
            footer_social = json.loads(val('footer_social', '{}'))
        except (json.JSONDecodeError, TypeError):
            footer_social = {}

        staff_list = []
        for member in StaffMember.objects.filter(is_active=True).order_by('display_order', 'name'):
            staff_list.append({
                'id': member.id,
                'name': member.name,
                'position': member.position,
                'photo_url': member.photo.url if member.photo else None,
            })

        return {
            'header_caption': val('header_caption'),
            'mission': val('mission'),
            'vision': val('vision'),
            'school_admin_name': val('school_admin_name', 'Zandro G. Sepe, MS'),
            'school_admin_title': val('school_admin_title', 'School Principal'),
            'announcement_caption': val('announcement_caption'),
            'contact_address': val('contact_address', 'R.T. Lim Boulevard Zamboanga City, Philippines'),
            'contact_phone': val('contact_phone', '+63 61 0086516'),
            'contact_email': val('contact_email', 'nationalhighschoolwest@gmail.com'),
            'contact_facebook': val('contact_facebook', 'https://web.facebook.com/znhs.west'),
            'contact_hours': val('contact_hours', 'Monday to Friday: 7:00 AM - 5:00 PM\nSaturday: 7:00 AM - 5:00 PM\nSunday: Closed'),
            'logo_school': img('header_logo_school'),
            'logo_region_ix': img('header_logo_region'),
            'logo_zamboanga_peninsula': img('header_logo_peninsula'),
            'logo_matatag': img('header_logo_matatag'),
            'announcement_image': img('announcement_image'),
            'footer_copyright': val('footer_copyright', '© 2025 Zamboanga National High School West. All rights reserved.'),
            'footer_links': footer_links,
            'footer_social': footer_social,
            'staff_members': staff_list,
        }
    except Exception:
        return {}