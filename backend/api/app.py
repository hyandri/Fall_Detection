from flask import Flask, request, jsonify
from flask_cors import CORS
from auth import create_token, verify_token, verify_password, hash_password
from models import db, User, Alert
from whatsapp_integration import send_whatsapp_alert
import os
from dotenv import load_dotenv

load_dotenv()

# Optional integrations from krrishpana branch (import safely)
try:
    from backend.detection.fall_detector import FallDetector
    from backend.alert_service import send_whatsapp_alert as send_whatsapp_from_krr
    from backend.auth import login_required
except Exception:
    # If those modules aren't present, provide safe fallbacks so the API still runs
    FallDetector = None
    send_whatsapp_from_krr = None
    def login_required(f):
        return f

app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///fall_detection.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 400
        
    user = User(
        name=data['name'],
        email=data['email'],
        password=hash_password(data['password']),
        phone=data['phone']
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    
    if user and verify_password(data['password'], user.password):
        token = create_token(user.id)
        return jsonify({'token': token, 'user': user.to_dict()}), 200
    
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/send-alert', methods=['POST'])
def send_alert():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({'message': 'No token provided'}), 401
        
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': 'Invalid token'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    try:
        # Send WhatsApp alert
        message = "⚠️ Fall Detected! Emergency assistance may be needed."
        send_whatsapp_alert(user.phone, message)
        
        # Record alert in database
        alert = Alert(user_id=user.id, type='fall_detected', status='sent')
        db.session.add(alert)
        db.session.commit()
        
        return jsonify({'message': 'Alert sent successfully'}), 200
    except Exception as e:
        return jsonify({'message': f'Error sending alert: {str(e)}'}), 500

@app.route('/alerts', methods=['GET'])
def get_alerts():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({'message': 'No token provided'}), 401
        
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': 'Invalid token'}), 401
    
    alerts = Alert.query.filter_by(user_id=user_id).order_by(Alert.timestamp.desc()).all()
    return jsonify([alert.to_dict() for alert in alerts]), 200


# Basic health route
@app.route('/', methods=['GET'])
def index():
    return jsonify({'status': 'ok', 'message': 'Fall Detection API is healthy'}), 200


# Simple health check (explicit path)
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200


# Test endpoint to send a WhatsApp message using configured Twilio credentials.
# POST JSON: {"to": "+1555...", "message": "text"}
# If 'to' is omitted it falls back to the WHATSAPP_PHONE_NUMBER in the environment (.env)
@app.route('/test-whatsapp', methods=['POST'])
def test_whatsapp():
    data = request.json or {}
    to_number = data.get('to') or os.getenv('WHATSAPP_PHONE_NUMBER')
    message_text = data.get('message', 'Test message from Fall Detection API')

    if not to_number:
        return jsonify({'message': 'No destination number provided and WHATSAPP_PHONE_NUMBER not set'}), 400

    success, info = send_whatsapp_alert(to_number, message_text)
    if success:
        return jsonify({'message': 'Test WhatsApp sent', 'sid': info}), 200
    else:
        return jsonify({'message': 'Failed to send test WhatsApp', 'error': info}), 500


# Routes to integrate krrishpana detection system (if available)
@app.route('/api/start-detection', methods=['POST'])
@login_required
def start_detection():
    if FallDetector is None:
        return jsonify({'message': 'Detection module not available'}), 501
    try:
        detector = FallDetector()
        detector.start()
        return jsonify({'status': 'Detection started'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/fall-detected', methods=['POST'])
def fall_detected_webhook():
    # Endpoint for krrishpana detection to POST fall events
    data = request.json or {}
    fall_data = data.get('fall_data', {})
    contacts = data.get('contacts')

    message_text = f"🚨 FALL DETECTED! Confidence: {fall_data.get('confidence') or 'unknown'}"
    try:
        # prefer local send_whatsapp_alert if available
        if contacts:
            for c in contacts:
                send_whatsapp_alert(c, message_text)
        else:
            # fallback to environment-configured number
            to_num = os.getenv('WHATSAPP_PHONE_NUMBER')
            send_whatsapp_alert(to_num, message_text)

        # also call krrishpana alert service if present
        if send_whatsapp_from_krr:
            try:
                send_whatsapp_from_krr(os.getenv('WHATSAPP_PHONE_NUMBER'), message_text)
            except Exception:
                pass

        return jsonify({'status': 'Alert sent'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)