from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from twilio.rest import Client
import json

# Twilio configuration
TWILIO_SID = "ACe174d93e3b036d70b94f2a016ef06b2f"
TWILIO_AUTH_TOKEN = "892b9f668d276b80ef6a5b75b66b40ff"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"

# Initialize Twilio client
client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# Public views
def home(request):
    return render(request, "home.html")

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Validation
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('signup')

        if not email.endswith('@gmail.com'):
            messages.error(request, 'Please use a valid Gmail account.')
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username is taken.')
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email is taken.')
            return redirect('signup')

        # Create user and auto-login
        user = User.objects.create_user(username=username, password=password, email=email)
        user.save()
        
        # Authenticate and login
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
        
    return render(request, "signup.html")

def loginout(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Logged in successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('login')
    else:
        return render(request, "loginout.html")

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('home')

# Protected views (require login)
@login_required
def dashboard(request):
    return render(request, "dashboard.html")

@login_required
def admin_dashboard(request):
    return render(request, "admin_dashboard.html")

@login_required
def contacts(request):
    return render(request, "contacts.html")

@login_required
def alerts_list(request):
    return render(request, "alerts.html")

@login_required
def profile(request):
    return render(request, 'profile.html')

@login_required
def settings(request):
    return render(request, 'settings.html')

# API endpoints
def send_alert(request):
    if request.method == 'POST':
        try:
            # Send WhatsApp alerts to guardians
            guardians = ["+9779841985769", "+9779843385807"]  
            
            for number in guardians:
                client.messages.create(
                    from_=TWILIO_WHATSAPP_NUMBER,
                    body="⚠️ Fall detected! Please check immediately.",
                    to=f"whatsapp:{number}"
                )
            
            messages.success(request, 'Alert sent successfully to all guardians!')
            return JsonResponse({'status': 'success', 'message': 'Alert sent successfully!'})
            
        except Exception as e:
            messages.error(request, f'Failed to send alert: {str(e)}')
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def detect_fall(request):
    if request.method == 'POST':
        try:
            # Add your fall detection logic here
            # Process video/image data for fall detection
            
            fall_detected = True  # Replace with actual detection logic
            confidence = 0.95     # Replace with actual confidence score
            
            if fall_detected:
                # Automatically trigger alert when fall is detected
                send_alert(request)
            
            return JsonResponse({
                'fall_detected': fall_detected, 
                'confidence': confidence,
                'message': 'Fall detected! Alert sent.' if fall_detected else 'No fall detected'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)})
    
    return JsonResponse({'error': 'Invalid request method'})

def get_alerts(request):
    if request.method == 'GET':
        try:
            # Return list of recent alerts (replace with your actual data)
            alerts = [
                {
                    'id': 1, 
                    'message': 'Test alert sent successfully', 
                    'timestamp': '2025-10-26 14:45:00', 
                    'type': 'success'
                },
                {
                    'id': 2, 
                    'message': 'Fall detected in Room A', 
                    'timestamp': '2025-10-26 14:30:00', 
                    'type': 'warning'
                },
            ]
            return JsonResponse({'alerts': alerts})
            
        except Exception as e:
            return JsonResponse({'error': str(e)})
    
    return JsonResponse({'error': 'Invalid request method'})