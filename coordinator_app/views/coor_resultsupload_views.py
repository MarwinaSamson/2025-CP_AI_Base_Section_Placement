from django.shortcuts import render

def results_upload(request):
    return render(request, 'coordinator_app/resultsUpload.html')