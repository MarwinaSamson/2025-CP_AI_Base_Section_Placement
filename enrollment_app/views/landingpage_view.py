from django.shortcuts import render, redirect

def landing_page(request):
    return render(request, 'enrollment_app/landing.html')

def clear_session(request):
    request.session.clear()
    return redirect('enrollment_app:landing')
