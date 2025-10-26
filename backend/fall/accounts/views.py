from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
import json

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
    if request.method=="POST":
        username=request.POST['username']
        password=request.POST['password']

        user=auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('home')  
        else:
            messages.info(request,'invalid credintials')
            return redirect('loginout')
    else:
        return render(request, 'loginout.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('home')

def home(request):
    return render(request, 'home.html')

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

@login_required
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')

@login_required
def contacts(request):
    return render(request, 'contacts.html')

@login_required
def alerts_list(request):
    return render(request, 'alert.html')

def send_alert(request):
    if request.method == 'POST':
        try:
            # Add your alert sending logic here
            # This could integrate with Twilio, email, or other services
            
            # Example: Send WhatsApp alert
            # twilio_client.messages.create(...)
            
            messages.success(request, 'Alert sent successfully!')
            return JsonResponse({'status': 'success', 'message': 'Alert sent successfully!'})
        except Exception as e:
            messages.error(request, f'Failed to send alert: {str(e)}')
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def detect_fall(request):
    if request.method == 'POST':
        try:
            # Add your fall detection logic here
            # This could process video frames, sensor data, etc.
            
            # Example fall detection logic
            data = json.loads(request.body)
            # Process the data for fall detection
            
            fall_detected = True  # Replace with actual detection logic
            confidence = 0.95     # Replace with actual confidence score
            
            if fall_detected:
                # Trigger alert automatically
                messages.warning(request, 'Fall detected! Sending alerts...')
            
            return JsonResponse({
                'fall_detected': fall_detected, 
                'confidence': confidence,
                'message': 'Fall detected!' if fall_detected else 'No fall detected'
            })
        except Exception as e:
            return JsonResponse({'error': str(e)})
    
    return JsonResponse({'error': 'Invalid request method'})

def get_alerts(request):
    if request.method == 'GET':
        try:
            # Return list of recent alerts
            # This could come from your database
            alerts = [
                {'id': 1, 'message': 'Test alert 1', 'timestamp': '2025-10-26 13:45:00', 'type': 'info'},
                {'id': 2, 'message': 'Fall detected in Room A', 'timestamp': '2025-10-26 13:30:00', 'type': 'warning'},
            ]
            return JsonResponse({'alerts': alerts})
        except Exception as e:
            return JsonResponse({'error': str(e)})
    
    return JsonResponse({'error': 'Invalid request method'})

# Additional utility views
def profile(request):
    if not request.user.is_authenticated:
        return redirect('loginout')
    return render(request, 'profile.html')

def settings(request):
    if not request.user.is_authenticated:
        return redirect('loginout')
    return render(request, 'settings.html')