from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse, StreamingHttpResponse
from django.contrib.auth.decorators import login_required
from twilio.rest import Client
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
import datetime
import random
import json
from django.contrib.auth.models import User
from dashboard.models import Contact, FallAlert, ViewerProfile



# Twilio setup (keep these in settings.py ideally)

# Meta WhatsApp API setup (permanent token)
WHATSAPP_API_URL = "https://graph.facebook.com/v21.0/822663690935947/messages"
WHATSAPP_ACCESS_TOKEN = "EAAaxZA9x8v5gBPy6ZC4ZAkoWTrBaWRy8EdvzLko5TSSt4J5cZBY79Pg4f9eRbs55Dw0mweRXhJEyfqCs9UFT15SRn4oYSL9tffvV99hKPTh6bz2aMhyq2mVbDRoCqgzDM1ZAVXSuax6RXQ7hTURsbjtFNftYLrxqD0d058ItlzWTCZBRZA7tFYZCfM1WSyAOZBMdpsEoTNfZBX8RvuNY4QAwd1Yr1hrF4dbOsbothZBjr9P"



def home(request):
    # If user is authenticated, redirect to appropriate dashboard based on user type
    if request.user.is_authenticated:
        # If user has a profile and is a viewer, send to viewer dashboard
        if hasattr(request.user, 'userprofile') and getattr(request.user.userprofile, 'user_type', 'setup') == 'viewer':
            return redirect('viewer_dashboard')
        # Default: setup/admin users go to main dashboard
        return redirect('dashboard')
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
        print(f"ℹ Added country code 977 to phone number. Formatted: {cleaned}")
    
    # If number is 9 digits and starts with Nepal mobile prefix (without leading 0), add country code
    elif len(cleaned) == 9 and any(cleaned.startswith(prefix[1:]) for prefix in nepal_prefixes):
        cleaned = '977' + cleaned
        print(f"ℹ Added country code 977 to phone number. Formatted: {cleaned}")
    
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
        
        # Log the full response for debugging
        print(f"📤 WhatsApp API Response Status: {response.status_code}")
        print(f"📤 WhatsApp API Response Body: {response.text}")
        
        if response.status_code == 200:
            # Check if response contains error even with 200 status
            try:
                response_data = response.json()
                if 'error' in response_data:
                    error_code = response_data.get('error', {}).get('code', '')
                    error_message = response_data.get('error', {}).get('message', '')
                    error_msg = f"API returned error: {error_message} (Code: {error_code})"
                    print(f"❌ {error_msg}")
                    return False, error_msg
                else:
                    # Success - log message ID if available
                    message_id = response_data.get('messages', [{}])[0].get('id', 'N/A')
                    print(f"✅ WhatsApp message sent successfully. Message ID: {message_id}")
                    return True, None
            except:
                # If JSON parsing fails but status is 200, assume success
                print(f"✅ WhatsApp message sent (status 200, couldn't parse response)")
                return True, None
        else:
            # Parse error response for better error messages
            try:
                error_data = response.json()
                error_code = error_data.get('error', {}).get('code', '')
                error_message = error_data.get('error', {}).get('message', '')
                
                # Check if it's the "not in allowed list" error
                if error_code == 131030 or 'not in allowed list' in error_message.lower():
                    error_msg = f"⚠ Phone number {formatted_number} is not in the allowed list. " \
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
        print(f"❌ Exception in send_whatsapp_message: {error_msg}")
        return False, error_msg


def send_alert(request):
    """Test function to send alerts - uses contacts from database"""
    # Fetch contacts from database where WhatsApp is enabled
    contacts = Contact.objects.filter(whatsapp_enabled=True)
    
    if not contacts.exists():
        print("⚠ No contacts with WhatsApp enabled found in database")
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


def save_fall_image(frame, setup_user_id, detection_info=None):
    """
    Save fall detection frame as an image file.
    
    Args:
        frame: OpenCV frame (numpy array) to save
        setup_user_id: ID of the setup user who owns this detection
        detection_info: Optional dictionary containing detection information
        
    Returns:
        str: Relative path to saved image (for database storage), or None if failed
    """
    try:
        # Create fall_alerts directory if it doesn't exist
        fall_alerts_dir = os.path.join(settings.MEDIA_ROOT, 'fall_alerts')
        os.makedirs(fall_alerts_dir, exist_ok=True)
        
        # Generate filename: {timestamp}_{setup_user_id}_{random}.jpg
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        random_suffix = random.randint(1000, 9999)
        filename = f"{timestamp}_{setup_user_id}_{random_suffix}.jpg"
        filepath = os.path.join(fall_alerts_dir, filename)
        
        # Save image using cv2.imwrite()
        # Note: Using frame_lock might not be necessary here since we're copying the frame
        # but we'll ensure the directory creation and file writing are atomic operations
        success = cv2.imwrite(filepath, frame)
        
        if not success:
            print(f"❌ Failed to save fall image to {filepath}")
            return None
        
        # Return relative path for database storage (MEDIA_URL + relative path)
        # Format: fall_alerts/{filename}
        relative_path = os.path.join('fall_alerts', filename).replace('\\', '/')
        print(f"✅ Fall image saved: {relative_path}")
        return relative_path
        
    except Exception as e:
        print(f"❌ Error saving fall image: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


# Global variables for alert system
alert_history = []
alert_lock = threading.Lock()
alert_enabled = True
alert_count = 0
last_alert_time = 0
ALERT_COOLDOWN = 30  # 30 seconds cooldown between alerts


def send_fall_alert(detection_info=None, image_path=None, setup_user_id=None):
    """Enhanced fall alert system with logging and error handling
    
    Args:
        detection_info: Dictionary containing detection details (confidence, bbox, class_name, etc.)
        image_path: Relative path to saved fall image (optional)
        setup_user_id: ID of the setup user who owns this detection (optional)
    """
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
            print("⚠ No contacts with WhatsApp enabled found in database")
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
        
        # Create FallAlert records in database if setup_user_id is provided
        whatsapp_sent = success_count > 0
        fall_alerts_created = []
        
        if setup_user_id:
            try:
                # Get setup_user object
                try:
                    setup_user = User.objects.get(id=setup_user_id)
                except User.DoesNotExist:
                    print(f"⚠️ Setup user with ID {setup_user_id} not found - skipping FallAlert creation")
                    setup_user = None
                
                if setup_user:
                    # Get all active viewers linked to this setup user
                    active_viewers = ViewerProfile.objects.filter(
                        setup_user=setup_user,
                        is_active=True
                    )
                    
                    # Prepare detection_info as JSON string
                    # Convert numpy types to native Python types for JSON serialization
                    if detection_info:
                        # Create a copy to avoid modifying original
                        detection_info_serializable = {}
                        for key, value in detection_info.items():
                            # Convert numpy types to Python types
                            if isinstance(value, np.ndarray):
                                detection_info_serializable[key] = value.tolist()
                            elif isinstance(value, (np.integer, np.floating)):
                                detection_info_serializable[key] = value.item()
                            else:
                                detection_info_serializable[key] = value
                        detection_info_json = json.dumps(detection_info_serializable)
                    else:
                        detection_info_json = ''
                    
                    # Get consecutive_frames and confidence from detection_info
                    consecutive_frames = detection_info.get('consecutive_frames', 0) if detection_info else 0
                    confidence = detection_info.get('confidence') if detection_info else None
                    
                    if active_viewers.exists():
                        # Create FallAlert for each active viewer
                        for viewer in active_viewers:
                            fall_alert = FallAlert.objects.create(
                                setup_user=setup_user,
                                viewer=viewer,
                                status='pending',
                                confidence=confidence,
                                consecutive_frames=consecutive_frames,
                                snapshot_path=image_path or '',
                                detection_info=detection_info_json,
                                whatsapp_sent=whatsapp_sent
                            )
                            fall_alerts_created.append(fall_alert)
                            print(f"✅ FallAlert created for viewer: {viewer.name} (Alert ID: {fall_alert.id})")
                    else:
                        # No viewers linked, create one general alert without viewer assignment
                        fall_alert = FallAlert.objects.create(
                            setup_user=setup_user,
                            viewer=None,
                            status='pending',
                            confidence=confidence,
                            consecutive_frames=consecutive_frames,
                            snapshot_path=image_path or '',
                            detection_info=detection_info_json,
                            whatsapp_sent=whatsapp_sent
                        )
                        fall_alerts_created.append(fall_alert)
                        print(f"✅ FallAlert created for setup user: {setup_user.username} (Alert ID: {fall_alert.id}) - No viewers linked")
                        
            except Exception as e:
                print(f"❌ Error creating FallAlert records: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print("⚠️ No setup_user_id provided - skipping FallAlert creation")
        
        # Log the alert
        alert_record = {
            'timestamp': current_time,
            'success_count': success_count,
            'total_recipients': contacts.count(),
            'failed_contacts': failed_contacts,
            'detection_info': detection_info,
            'message_details': message_details,
            'fall_alerts_created': len(fall_alerts_created)
        }
        
        with alert_lock:
            alert_history.append(alert_record)
            alert_count += 1
            last_alert_time = current_time
            
            # Keep only last 50 alerts
            if len(alert_history) > 50:
                alert_history.pop(0)
        
        print(f"🚨 Fall alert sent! Success: {success_count}/{contacts.count()}, FallAlerts created: {len(fall_alerts_created)}")
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







# Global variables for webcam management
webcam_capture = None
webcam_thread = None
webcam_running = False
latest_frame = None
frame_lock = threading.Lock()

# Global variables for fall detection
fall_detection_model = None
detection_enabled = False
latest_detections = []
detection_lock = threading.Lock()
last_alert_time = 0
ALERT_COOLDOWN = 30  # 30 seconds cooldown between alerts

# Alert system variables
alert_history = []
alert_lock = threading.Lock()
alert_enabled = True
alert_count = 0

# Alert aggregation variables
consecutive_fall_frames = 0
FALL_THRESHOLD = 5  # Number of consecutive frames with fall detection required before alert

# Current setup user context (who started detection)
current_setup_user_id = None



def initialize_webcam():
    """Initialize webcam capture"""
    global webcam_capture
    try:
        webcam_capture = cv2.VideoCapture(0)
        if not webcam_capture.isOpened():
            # Try alternative camera indices
            for i in range(1, 5):
                webcam_capture = cv2.VideoCapture(i)
                if webcam_capture.isOpened():
                    break
        
        if webcam_capture.isOpened():
            # Set webcam properties for better performance
            webcam_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            webcam_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            webcam_capture.set(cv2.CAP_PROP_FPS, 30)
            return True
        else:
            return False
    except Exception as e:
        print(f"Error initializing webcam: {e}")
        return False


def initialize_fall_detection_model():
    """Initialize the YOLO fall detection model"""
    global fall_detection_model
    try:
        # Get the absolute path to the model
        model_path = os.path.join(settings.BASE_DIR, '..', '..', 'models', 'runs', 'detect', 'fall_detection_v22', 'weights', 'best.pt')
        model_path = os.path.abspath(model_path)
        
        if not os.path.exists(model_path):
            print(f"Model file not found at: {model_path}")
            return False
        
        print(f"Loading YOLO model from: {model_path}")
        fall_detection_model = YOLO(model_path)
        print("✅ YOLO model loaded successfully")
        return True
    except Exception as e:
        print(f"Error loading YOLO model: {e}")
        return False


def webcam_capture_loop():
    """Continuous webcam capture loop running in a separate thread"""
    global webcam_capture, webcam_running, latest_frame, frame_lock, fall_detection_model, detection_enabled, latest_detections, detection_lock
    
    while webcam_running:
        if webcam_capture and webcam_capture.isOpened():
            ret, frame = webcam_capture.read()
            if ret:
                # Process frame for fall detection if enabled
                if detection_enabled and fall_detection_model is not None:
                    try:
                        # Start performance timing
                        detection_start = time.time()
                        
                        # Run YOLO detection on the frame
                        results = fall_detection_model(frame, conf=0.4, verbose=False)
                        
                        # Extract detection information
                        detections = []
                        annotated_frame = frame.copy()
                        for result in results:
                            if result.boxes is not None:
                                for box in result.boxes:
                                    # Get bounding box coordinates and confidence
                                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                                    confidence = box.conf[0].cpu().numpy()
                                    class_id = int(box.cls[0].cpu().numpy())
                                    
                                    # Get class name
                                    class_name = fall_detection_model.names[class_id]
                                    
                                    detections.append({
                                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                        'confidence': float(confidence),
                                        'class_id': class_id,
                                        'class_name': class_name
                                    })

                        # If the YOLO result already contains rendered annotations, reuse them
                        if results:
                            try:
                                annotated_frame = results[0].plot()
                            except Exception:
                                # Fallback to the original frame if plotting fails
                                annotated_frame = frame.copy()
                        
                        # Update latest detections
                        with detection_lock:
                            latest_detections = detections
                        
                        with frame_lock:
                            latest_frame = annotated_frame
                        
                            
                    except Exception as e:
                        print(f"Error in fall detection: {e}")
                        with frame_lock:
                            latest_frame = frame.copy()
                else:
                    with frame_lock:
                        latest_frame = frame.copy()
            else:
                print("Failed to read frame from webcam")
                time.sleep(0.1)
        else:
            print("Webcam not available")
            time.sleep(0.1)


def start_webcam(request):
    """Start webcam capture"""
    global webcam_capture, webcam_thread, webcam_running, fall_detection_model
    
    if webcam_running:
        return JsonResponse({'status': 'already_running', 'message': 'Webcam is already running'})
    
    if initialize_webcam():
        # Initialize YOLO model if not already loaded
        if fall_detection_model is None:
            if not initialize_fall_detection_model():
                return JsonResponse({'status': 'error', 'message': 'Failed to load YOLO model'})
        
        webcam_running = True
        webcam_thread = threading.Thread(target=webcam_capture_loop, daemon=True)
        webcam_thread.start()
        return JsonResponse({'status': 'success', 'message': 'Webcam started successfully'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Failed to initialize webcam'})


def stop_webcam(request):
    """Stop webcam capture"""
    global webcam_capture, webcam_thread, webcam_running
    
    webcam_running = False
    
    if webcam_thread:
        webcam_thread.join(timeout=2)
    
    if webcam_capture:
        webcam_capture.release()
        webcam_capture = None
    
    return JsonResponse({'status': 'success', 'message': 'Webcam stopped successfully'})


def get_webcam_status(request):
    """Get current webcam status"""
    global webcam_running, latest_frame, frame_lock
    
    status = {
        'running': webcam_running,
        'frame_available': False
    }
    
    if webcam_running and latest_frame is not None:
        with frame_lock:
            if latest_frame is not None:
                status['frame_available'] = True
                status['frame_shape'] = latest_frame.shape
    
    return JsonResponse(status)


def get_latest_frame(request):
    """Get the latest captured frame as base64 encoded image"""
    global latest_frame, frame_lock, webcam_running
    
    if not webcam_running or latest_frame is None:
        return JsonResponse({'status': 'error', 'message': 'No frame available'})
    
    try:
        with frame_lock:
            if latest_frame is not None:
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', latest_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                    return JsonResponse({
                        'status': 'success',
                        'frame': frame_base64,
                        'timestamp': time.time()
                    })
                else:
                    return JsonResponse({'status': 'error', 'message': 'Failed to encode frame'})
            else:
                return JsonResponse({'status': 'error', 'message': 'No frame available'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error processing frame: {str(e)}'})


def webcam_test(request):
    """Render webcam test page"""
    return render(request, "webcam_test.html")


def fall_detection_test(request):
    """Render fall detection test page"""
    return render(request, "fall_detection_test.html")


def streaming_test(request):
    """Render streaming test page"""
    return render(request, "streaming_test.html")


@login_required(login_url='loginout')
def fall_detection(request):
    """Render main fall detection page"""
    return render(request, "fall_detection.html")




def generate_frames():
    """Generate video frames for streaming"""
    global webcam_capture, webcam_running, latest_frame, frame_lock, detection_enabled, latest_detections, detection_lock
    
    while webcam_running:
        if webcam_capture and webcam_capture.isOpened():
            ret, frame = webcam_capture.read()
            if ret:
                annotated_frame = frame.copy()
                # Process frame for detection if enabled
                if detection_enabled and fall_detection_model is not None:
                    try:
                        # Run YOLO detection
                        results = fall_detection_model(frame, conf=0.4, verbose=False)
                        
                        # Extract detections
                        detections = []
                        annotated_frame = frame.copy()
                        for result in results:
                            if result.boxes is not None:
                                for box in result.boxes:
                                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                                    confidence = box.conf[0].cpu().numpy()
                                    class_id = int(box.cls[0].cpu().numpy())
                                    class_name = fall_detection_model.names[class_id]
                                    
                                    detections.append({
                                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                        'confidence': float(confidence),
                                        'class_id': class_id,
                                        'class_name': class_name
                                    })

                        # Prefer the model-rendered frame if available
                        if results:
                            try:
                                annotated_frame = results[0].plot()
                            except Exception:
                                annotated_frame = frame.copy()

                        # Update latest detections
                        with detection_lock:
                            latest_detections = detections
                        
                        # Add detection status text
                        status_text = f"Detections: {len(detections)} | Detection: {'ON' if detection_enabled else 'OFF'}"
                        cv2.putText(annotated_frame, status_text, (10, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                        cv2.putText(annotated_frame, status_text, (10, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
                        
                    except Exception as e:
                        print(f"Error in streaming detection: {e}")
                
                # Encode frame as JPEG (prefer annotated frame when available)
                ret, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                else:
                    time.sleep(0.1)
            else:
                time.sleep(0.1)
        else:
            time.sleep(0.1)


def video_stream(request):
    """Stream video feed with detection overlays"""
    if not webcam_running:
        return JsonResponse({'error': 'Webcam is not running'}, status=400)
    
    return StreamingHttpResponse(
        generate_frames(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )


def video_stream_raw(request):
    """Stream raw video feed without detection overlays"""
    if not webcam_running:
        return JsonResponse({'error': 'Webcam is not running'}, status=400)
    
    def generate_raw_frames():
        global webcam_capture, webcam_running
        
        while webcam_running:
            if webcam_capture and webcam_capture.isOpened():
                ret, frame = webcam_capture.read()
                if ret:
                    # Encode frame as JPEG
                    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    if ret:
                        frame_bytes = buffer.tobytes()
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    else:
                        time.sleep(0.1)
                else:
                    time.sleep(0.1)
            else:
                time.sleep(0.1)
    
    return StreamingHttpResponse(
        generate_raw_frames(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )


def enable_detection(request):
    """Enable fall detection for the current setup user"""
    global detection_enabled, current_setup_user_id
    
    if not webcam_running:
        return JsonResponse({'status': 'error', 'message': 'Webcam is not running'})
    
    if fall_detection_model is None:
        return JsonResponse({'status': 'error', 'message': 'YOLO model not loaded'})
    
    # Require authenticated setup user to start detection context
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'You must be logged in as a setup user to start detection.'})
    
    # If UserProfile exists, ensure this is a setup user
    if hasattr(request.user, 'userprofile') and request.user.userprofile.user_type != 'setup':
        return JsonResponse({'status': 'error', 'message': 'Only setup users can start fall detection.'})
    
    # Store current setup user ID for use when alerts are generated
    current_setup_user_id = request.user.id
    detection_enabled = True
    print(f"✅ Fall detection enabled by setup user ID {current_setup_user_id}")
    return JsonResponse({'status': 'success', 'message': 'Fall detection enabled', 'setup_user_id': current_setup_user_id})


def disable_detection(request):
    """Disable fall detection"""
    global detection_enabled
    
    detection_enabled = False
    return JsonResponse({'status': 'success', 'message': 'Fall detection disabled'})


def get_detection_status(request):
    """Get current detection status and results"""
    global detection_enabled, latest_detections, detection_lock, last_alert_time, ALERT_COOLDOWN
    global consecutive_fall_frames, FALL_THRESHOLD, latest_frame, frame_lock, current_setup_user_id
    
    with detection_lock:
        detections = latest_detections.copy()
    
    # Check for fall detections and trigger alerts
    fall_detected = False
    for detection in detections:
        if 'fall' in detection['class_name'].lower():
            fall_detected = True
            break
    
    # Alert aggregation logic: require consecutive fall detections
    with detection_lock:
        if fall_detected:
            # Increment consecutive fall frame counter (cap at threshold to prevent overflow)
            if consecutive_fall_frames < FALL_THRESHOLD:
                consecutive_fall_frames += 1
            print(f"📊 Fall detected - Consecutive frames: {consecutive_fall_frames}/{FALL_THRESHOLD}")
            
            # Only send alert if threshold reached
            if consecutive_fall_frames >= FALL_THRESHOLD:
                # Find the fall detection with highest confidence
                fall_detection = None
                for detection in detections:
                    if 'fall' in detection['class_name'].lower():
                        if fall_detection is None or detection['confidence'] > fall_detection['confidence']:
                            fall_detection = detection
                
                # Ensure we have a detection_info dict (create empty one if fall_detection is None)
                if fall_detection is None:
                    fall_detection = {'class_name': 'fall', 'confidence': 0.0}
                
                # Add consecutive_frames to detection_info
                fall_detection['consecutive_frames'] = consecutive_fall_frames
                
                # Capture current frame for alert
                image_path = None
                setup_user_id = current_setup_user_id
                
                # Fallback: if no setup user was stored, use current authenticated user (for backward compatibility)
                if setup_user_id is None and request.user.is_authenticated:
                    setup_user_id = request.user.id
                
                if setup_user_id is not None:
                    # Get current frame with thread-safe lock
                    current_frame = None
                    with frame_lock:
                        if latest_frame is not None:
                            # Make a copy to avoid reference issues
                            current_frame = latest_frame.copy()
                    
                    # Save the fall image if frame is available
                    if current_frame is not None:
                        image_path = save_fall_image(current_frame, setup_user_id, fall_detection)
                        if image_path:
                            print(f"📸 Fall image captured and saved: {image_path}")
                        else:
                            print(f"⚠️ Failed to save fall image")
                    else:
                        print(f"⚠️ No frame available to capture")
                else:
                    print(f"⚠️ No setup_user_id available - cannot associate alert with a setup user")
                
                # Send enhanced alert with image path (rate limiting is handled inside send_fall_alert)
                alert_sent = send_fall_alert(detection_info=fall_detection, image_path=image_path, setup_user_id=setup_user_id)
            
            # Only reset counter if alert was successfully sent
            # If rate limited, keep counter at threshold so we can send once cooldown expires
            if alert_sent:
                consecutive_fall_frames = 0
                print(f"✅ Alert sent after {FALL_THRESHOLD} consecutive fall detections")
            else:
                # Keep counter at threshold (don't increment further, but don't reset)
                consecutive_fall_frames = FALL_THRESHOLD
                # Calculate remaining cooldown time
                current_time = time.time()
                cooldown_remaining = max(0, ALERT_COOLDOWN - (current_time - last_alert_time))
                print(f"⏸️ Alert rate limited - Cooldown remaining: {cooldown_remaining:.1f}s - Will retry when cooldown expires")
        else:
            # Reset counter when no fall detected
            if consecutive_fall_frames > 0:
                print(f"🔄 No fall detected - Resetting consecutive frame counter (was at {consecutive_fall_frames})")
            consecutive_fall_frames = 0
    
    return JsonResponse({
        'detection_enabled': detection_enabled,
        'detections': detections,
        'fall_detected': fall_detected,
        'detection_count': len(detections),
        'consecutive_fall_frames': consecutive_fall_frames,
        'fall_threshold': FALL_THRESHOLD
    })


def get_detection_frame(request):
    """Get the latest frame with detection overlays"""
    global latest_frame, frame_lock, webcam_running, detection_enabled
    
    if not webcam_running or latest_frame is None:
        return JsonResponse({'status': 'error', 'message': 'No frame available'})
    
    try:
        with frame_lock:
            if latest_frame is not None:
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', latest_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                    return JsonResponse({
                        'status': 'success',
                        'frame': frame_base64,
                        'timestamp': time.time(),
                        'detection_enabled': detection_enabled
                    })
                else:
                    return JsonResponse({'status': 'error', 'message': 'Failed to encode frame'})
            else:
                return JsonResponse({'status': 'error', 'message': 'No frame available'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error processing frame: {str(e)}'})  