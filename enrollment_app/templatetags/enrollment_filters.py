"""
Custom template filters for enrollment_app
"""
from django import template

register = template.Library()


@register.filter
def to_accept_format(file_format):
    """
    Convert file format string to HTML accept attribute format.
    Input: "pdf,jpg,jpeg,png" or "pdf, jpg, jpeg, png"
    Output: ".pdf,.jpg,.jpeg,.png"
    """
    if not file_format:
        return ""

    # Split by comma, strip whitespace, add dots, rejoin
    extensions = [ext.strip() for ext in file_format.split(',')]
    return ','.join(f'.{ext}' if not ext.startswith('.') else ext for ext in extensions)
