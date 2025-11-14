from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import auth
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from mainapp.views import stop_webcam, disable_detection

def signup(request):
    if request.method=='POST':
        username=request.POST.get('username')
        email=request.POST.get('email')
        password=request.POST.get('password')

        if len(password) < 8:
            messages.info(request, 'Password must be at least 8 characters long.')
            return redirect('signup')

        if not email.endswith('@gmail.com'):
            messages.info(request, 'Please use a valid Gmail account.')
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.info(request, 'Username is taken.')
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.info(request, 'Email is taken.')
            return redirect('signup')

        # Create user
        user = User.objects.create_user(username=username, password=password, email=email)
        user.save()
        messages.success(request, 'Account created successfully! You can now log in.')
        return redirect('loginout')

    return render(request, 'signup.html')

def loginout(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            # Prefer a POST 'next' then GET 'next', default to 'dashboard'
            next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard'
            return redirect(next_url)
        else:
            messages.info(request, 'invalid credentials')
            return redirect('loginout')
    return render(request, 'loginout.html')
def logout(request):
    # Stop detection and webcam before logging out
    try:
        disable_detection(request)
    except Exception as e:
        # Ignore errors if detection isn't running
        pass
    
    try:
        stop_webcam(request)
    except Exception as e:
        # Ignore errors if webcam isn't running
        pass
    
    auth_logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('home')
