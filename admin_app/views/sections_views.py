from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def sections_list(request):
    return render(request, 'admin_app/sections.html')

@login_required
def sections_by_program(request, program):
    return render(request, 'admin_app/sections.html', {'program': program})

@login_required
def section_detail(request, program, section_id):
    return render(request, 'admin_app/sections.html', {
        'program': program,
        'section_id': section_id
    })