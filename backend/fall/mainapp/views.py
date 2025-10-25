from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse, StreamingHttpResponse
from twilio.rest import Client
import cv2
import threading
import time
import base64
import numpy as np
from ultralytics import YOLO
import os
import io

# Twilio setup (keep these in settings.py ideally)
TWILIO_SID = "ACe174d93e3b036d70b94f2a016ef06b2f"
TWILIO_AUTH_TOKEN = "892b9f668d276b80ef6a5b75b66b40ff"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"  # Twilio sandbox or business number

client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)


def home(request):
    return render(request, "home.html")


def send_alert(request):
    guardians = ["+9779841985769","+9779843385807"]  
    for number in guardians:
        client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body="⚠️ Fall detected! Please check immediately.",
            to=f"whatsapp:{number}"
        )

    return redirect("home")


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
        # Prepare alert message
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        message = f"🚨 FALL DETECTION ALERT 🚨\n"
        message += f"Time: {timestamp}\n"
        message += f"Location: Fall Detection System\n"
        message += f"Status: IMMEDIATE ATTENTION REQUIRED\n\n"
        message += f"Please check the person immediately!\n"
        message += f"System is monitoring and will send updates."
        
        if detection_info:
            message += f"\n\nDetection Details:\n"
            message += f"Confidence: {detection_info.get('confidence', 'N/A'):.2f}\n"
            message += f"Location: {detection_info.get('bbox', 'N/A')}\n"
        
        # Send to all guardians
        guardians = ["+9779841985769", "+9779843385807"]
        success_count = 0
        
        for number in guardians:
            try:
                client.messages.create(
                    from_=TWILIO_WHATSAPP_NUMBER,
                    body=message,
                    to=f"whatsapp:{number}"
                )
                success_count += 1
                print(f"✅ Alert sent successfully to {number}")
            except Exception as e:
                print(f"❌ Failed to send alert to {number}: {e}")
        
        # Log the alert
        alert_record = {
            'timestamp': current_time,
            'success_count': success_count,
            'total_recipients': len(guardians),
            'detection_info': detection_info,
            'message': message
        }
        
        with alert_lock:
            alert_history.append(alert_record)
            alert_count += 1
            last_alert_time = current_time
            
            # Keep only last 50 alerts
            if len(alert_history) > 50:
                alert_history.pop(0)
        
        print(f"🚨 Fall alert sent! Success: {success_count}/{len(guardians)}")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Critical error in alert system: {e}")
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
                        
                        # Update latest detections
                        with detection_lock:
                            latest_detections = detections
                        
                        # Draw bounding boxes on frame
                        annotated_frame = frame.copy()
                        for detection in detections:
                            x1, y1, x2, y2 = detection['bbox']
                            confidence = detection['confidence']
                            class_name = detection['class_name']
                            
                            # Draw bounding box
                            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            
                            # Draw label
                            label = f"{class_name}: {confidence:.2f}"
                            cv2.putText(annotated_frame, label, (x1, y1 - 10), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        
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
                # Process frame for detection if enabled
                if detection_enabled and fall_detection_model is not None:
                    try:
                        # Run YOLO detection
                        results = fall_detection_model(frame, conf=0.4, verbose=False)
                        
                        # Extract detections
                        detections = []
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
                        
                        # Update latest detections
                        with detection_lock:
                            latest_detections = detections
                        
                        # Draw bounding boxes
                        for detection in detections:
                            x1, y1, x2, y2 = detection['bbox']
                            confidence = detection['confidence']
                            class_name = detection['class_name']
                            
                            # Choose color based on class
                            color = (0, 0, 255) if 'fall' in class_name.lower() else (0, 255, 0)
                            
                            # Draw bounding box
                            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                            
                            # Draw label with background
                            label = f"{class_name}: {confidence:.2f}"
                            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                            cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), 
                                         (x1 + label_size[0], y1), color, -1)
                            cv2.putText(frame, label, (x1, y1 - 5), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                        
                        # Add detection status text
                        status_text = f"Detections: {len(detections)} | Detection: {'ON' if detection_enabled else 'OFF'}"
                        cv2.putText(frame, status_text, (10, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                        cv2.putText(frame, status_text, (10, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
                        
                    except Exception as e:
                        print(f"Error in streaming detection: {e}")
                
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
    """Enable fall detection"""
    global detection_enabled
    
    if not webcam_running:
        return JsonResponse({'status': 'error', 'message': 'Webcam is not running'})
    
    if fall_detection_model is None:
        return JsonResponse({'status': 'error', 'message': 'YOLO model not loaded'})
    
    detection_enabled = True
    return JsonResponse({'status': 'success', 'message': 'Fall detection enabled'})


def disable_detection(request):
    """Disable fall detection"""
    global detection_enabled
    
    detection_enabled = False
    return JsonResponse({'status': 'success', 'message': 'Fall detection disabled'})


def get_detection_status(request):
    """Get current detection status and results"""
    global detection_enabled, latest_detections, detection_lock, last_alert_time
    
    with detection_lock:
        detections = latest_detections.copy()
    
    # Check for fall detections and trigger alerts
    fall_detected = False
    for detection in detections:
        if 'fall' in detection['class_name'].lower():
            fall_detected = True
            break
    
    # Trigger enhanced alert if fall detected
    if fall_detected:
        # Find the fall detection with highest confidence
        fall_detection = None
        for detection in detections:
            if 'fall' in detection['class_name'].lower():
                if fall_detection is None or detection['confidence'] > fall_detection['confidence']:
                    fall_detection = detection
        
        # Send enhanced alert
        send_fall_alert(fall_detection)
    
    return JsonResponse({
        'detection_enabled': detection_enabled,
        'detections': detections,
        'fall_detected': fall_detected,
        'detection_count': len(detections)
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