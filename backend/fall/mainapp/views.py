from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse, StreamingHttpResponse
import cv2
import threading
import time
import base64
import numpy as np
from ultralytics import YOLO
import os
import io
import requests
import re
from dashboard.models import Contact

# Meta WhatsApp API setup (permanent token)
WHATSAPP_API_URL = "https://graph.facebook.com/v21.0/822663690935947/messages"
WHATSAPP_ACCESS_TOKEN = "EAAaxZA9x8v5gBPy6ZC4ZAkoWTrBaWRy8EdvzLko5TSSt4J5cZBY79Pg4f9eRbs55Dw0mweRXhJEyfqCs9UFT15SRn4oYSL9tffvV99hKPTh6bz2aMhyq2mVbDRoCqgzDM1ZAVXSuax6RXQ7hTURsbjtFNftYLrxqD0d058ItlzWTCZBRZA7tFYZCfM1WSyAOZBMdpsEoTNfZBX8RvuNY4QAwd1Yr1hrF4dbOsbothZBjr9P"


def home(request):
    return render(request, "home.html")


def format_phone_number(phone_number):
    """Format phone number for WhatsApp API (remove +, spaces, and special characters, keep only digits)
    
    Automatically adds Nepal country code (977) if:
    - Number is 10 digits (local format)
    - Number starts with Nepal mobile prefixes (98, 97, 96, 95, 94, 93, 92, 91)
    - Number doesn't already start with 977
    
    Examples:
    - 9866339977 → 9779866339977
    - +9779866339977 → 9779866339977
    - 9779866339977 → 9779866339977 (no change)
    """
    # Remove all non-digit characters
    cleaned = re.sub(r'\D', '', str(phone_number))
    
    # If number already starts with 977 (Nepal country code), return as is
    if cleaned.startswith('977'):
        return cleaned
    
    # Nepal mobile number prefixes
    nepal_prefixes = ['98', '97', '96', '95', '94', '93', '92', '91']
    
    # If number is 10 digits and starts with Nepal mobile prefix, add country code 977
    if len(cleaned) == 10 and any(cleaned.startswith(prefix) for prefix in nepal_prefixes):
        cleaned = '977' + cleaned
        print(f"ℹ️ Added country code 977 to phone number. Formatted: {cleaned}")
    
    # If number is 9 digits and starts with Nepal mobile prefix (without leading 0), add country code
    elif len(cleaned) == 9 and any(cleaned.startswith(prefix[1:]) for prefix in nepal_prefixes):
        cleaned = '977' + cleaned
        print(f"ℹ️ Added country code 977 to phone number. Formatted: {cleaned}")
    
    return cleaned


def send_whatsapp_message(phone_number, message_text):
    """Send WhatsApp message using Meta WhatsApp API"""
    try:
        # Format phone number (remove + and special characters)
        formatted_number = format_phone_number(phone_number)
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Prepare payload - using template message
        payload = {
            "messaging_product": "whatsapp",
            "to": formatted_number,
            "type": "template",
            "template": {
                "name": "fall_detection",
                "language": {"code": "en_US"}
            }
        }
        
        # Send message
        response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            return True, None
        else:
            # Parse error response for better error messages
            try:
                error_data = response.json()
                error_code = error_data.get('error', {}).get('code', '')
                error_message = error_data.get('error', {}).get('message', '')
                
                # Check if it's the "not in allowed list" error
                if error_code == 131030 or 'not in allowed list' in error_message.lower():
                    error_msg = f"⚠️ Phone number {formatted_number} is not in the allowed list. " \
                               f"Please add this number to your WhatsApp Business Account's test numbers list. " \
                               f"See instructions in the error log or Meta Business Manager."
                    return False, error_msg
                else:
                    error_msg = f"HTTP {response.status_code}: {error_message} (Code: {error_code})"
                    return False, error_msg
            except:
                # If JSON parsing fails, return raw response
                error_msg = f"HTTP {response.status_code}: {response.text}"
                return False, error_msg
            
    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        return False, error_msg


def send_alert(request):
    """Test function to send alerts - uses contacts from database"""
    # Fetch contacts from database where WhatsApp is enabled
    contacts = Contact.objects.filter(whatsapp_enabled=True)
    
    if not contacts.exists():
        print("⚠️ No contacts with WhatsApp enabled found in database")
        return redirect("home")
    
    # Send test message to each contact
    for contact in contacts:
        try:
            success, error = send_whatsapp_message(contact.phone_number, None)
            if success:
                print(f"✅ Test alert sent successfully to {contact.name} ({contact.phone_number})")
            else:
                print(f"❌ Failed to send test alert to {contact.name} ({contact.phone_number}): {error}")
        except Exception as e:
            print(f"❌ Exception sending test alert to {contact.name} ({contact.phone_number}): {e}")

    return redirect("home")


# Global variables for alert system
alert_history = []
alert_lock = threading.Lock()
alert_enabled = True
alert_count = 0
last_alert_time = 0
ALERT_COOLDOWN = 30  # 30 seconds cooldown between alerts


def send_fall_alert(detection_info=None):
    """Enhanced fall alert system with logging and error handling"""
    global alert_history, alert_lock, alert_count, last_alert_time
    
    if not alert_enabled:
        return False
    
    current_time = time.time()
    
    # Check cooldown
    if current_time - last_alert_time < ALERT_COOLDOWN:
        return False
    
    try:
        # Fetch contacts from database where WhatsApp is enabled
        contacts = Contact.objects.filter(whatsapp_enabled=True)
        
        if not contacts.exists():
            print("⚠️ No contacts with WhatsApp enabled found in database")
            return False
        
        # Prepare alert message details
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        message_details = {
            'timestamp': timestamp,
            'location': 'Fall Detection System',
            'status': 'IMMEDIATE ATTENTION REQUIRED',
            'confidence': detection_info.get('confidence', 'N/A') if detection_info else 'N/A',
            'bbox': detection_info.get('bbox', 'N/A') if detection_info else 'N/A'
        }
        
        # Send messages to each contact individually
        success_count = 0
        failed_contacts = []
        
        for contact in contacts:
            try:
                # Send WhatsApp message to this contact
                success, error = send_whatsapp_message(contact.phone_number, message_details)
                
                if success:
                    success_count += 1
                    print(f"✅ Alert sent successfully to {contact.name} ({contact.phone_number})")
                else:
                    failed_contacts.append({
                        'name': contact.name,
                        'phone': contact.phone_number,
                        'error': error
                    })
                    print(f"❌ Failed to send alert to {contact.name} ({contact.phone_number}): {error}")
                    
                    # Provide helpful instructions if phone number is not in allowed list
                    if 'not in allowed list' in str(error).lower() or '131030' in str(error):
                        formatted_phone = format_phone_number(contact.phone_number)
                        print(f"\n📋 INSTRUCTIONS TO ADD PHONE NUMBER TO ALLOWED LIST:")
                        print(f"   1. Go to https://business.facebook.com/")
                        print(f"   2. Navigate to Business Settings > WhatsApp Accounts")
                        print(f"   3. Select your WhatsApp Business Account")
                        print(f"   4. Go to Settings > Phone Numbers")
                        print(f"   5. Add phone number: +{formatted_phone} to Test Numbers list")
                        print(f"   6. Save and wait a few minutes for changes to take effect")
                        print(f"   7. The number should be in international format: +{formatted_phone}\n")
                    
            except Exception as e:
                failed_contacts.append({
                    'name': contact.name,
                    'phone': contact.phone_number,
                    'error': str(e)
                })
                print(f"❌ Exception sending alert to {contact.name} ({contact.phone_number}): {e}")
        
        # Log the alert
        alert_record = {
            'timestamp': current_time,
            'success_count': success_count,
            'total_recipients': contacts.count(),
            'failed_contacts': failed_contacts,
            'detection_info': detection_info,
            'message_details': message_details
        }
        
        with alert_lock:
            alert_history.append(alert_record)
            alert_count += 1
            last_alert_time = current_time
            
            # Keep only last 50 alerts
            if len(alert_history) > 50:
                alert_history.pop(0)
        
        print(f"🚨 Fall alert sent! Success: {success_count}/{contacts.count()}")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Critical error in alert system: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_alert_status(request):
    """Get alert system status and history"""
    global alert_enabled, alert_count, last_alert_time, alert_history, alert_lock
    
    with alert_lock:
        recent_alerts = alert_history[-10:] if alert_history else []
    
    return JsonResponse({
        'alert_enabled': alert_enabled,
        'alert_count': alert_count,
        'last_alert_time': last_alert_time,
        'cooldown_remaining': max(0, ALERT_COOLDOWN - (time.time() - last_alert_time)),
        'recent_alerts': recent_alerts
    })


def toggle_alerts(request):
    """Toggle alert system on/off"""
    global alert_enabled
    
    alert_enabled = not alert_enabled
    status = "enabled" if alert_enabled else "disabled"
    
    return JsonResponse({
        'status': 'success',
        'message': f'Alert system {status}',
        'alert_enabled': alert_enabled
    })  
