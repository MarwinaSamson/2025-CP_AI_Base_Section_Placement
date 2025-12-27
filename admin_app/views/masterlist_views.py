from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def masterlist(request):
    return render(request, 'admin_app/masterlist.html')

@login_required
def masterlist_by_section(request, section_id):
    return render(request, 'admin_app/masterlist.html', {'section_id': section_id})