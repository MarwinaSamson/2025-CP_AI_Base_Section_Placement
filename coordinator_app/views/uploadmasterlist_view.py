from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from coordinator_app.models import SectionMasterlist
from coordinator_app.forms import SectionMasterlistUploadForm

@login_required
@user_passes_test(lambda u: u.is_staff)
def upload_section_masterlist(request):
    if request.method == 'POST':
        form = SectionMasterlistUploadForm(request.POST, request.FILES)
        if form.is_valid():
            masterlist = form.save(commit=False)
            masterlist.uploaded_by = request.user
            masterlist.save()
            messages.success(request, 'Section masterlist uploaded successfully!')
            return redirect('coordinator:section_management')
    else:
        form = SectionMasterlistUploadForm()
    return render(request, 'coordinator_app/upload_section_masterlist.html', {'form': form})
