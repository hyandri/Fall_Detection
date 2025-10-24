#!/usr/bin/env python3
"""
Test script for the enhanced alert system
Run this script to test alert functionality
"""

import requests
import time
import json

def test_alert_system():
    """Test the alert system endpoints"""
    base_url = "http://localhost:8000"
    
    print("🔔 Testing Alert System")
    print("=" * 40)
    
    try:
        # Test alert status
        print("📊 Checking alert status...")
        response = requests.get(f"{base_url}/alerts/status/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Alert system enabled: {data['alert_enabled']}")
            print(f"📈 Total alerts sent: {data['alert_count']}")
            print(f"⏰ Last alert time: {data['last_alert_time']}")
            print(f"🕐 Cooldown remaining: {data['cooldown_remaining']:.1f}s")
        else:
            print(f"❌ Failed to get alert status: {response.status_code}")
            return False
        
        # Test alert toggle
        print("\n🔄 Testing alert toggle...")
        response = requests.post(f"{base_url}/alerts/toggle/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Alert system toggled: {data['alert_enabled']}")
        else:
            print(f"❌ Failed to toggle alerts: {response.status_code}")
        
        # Test manual alert
        print("\n🚨 Testing manual alert...")
        response = requests.post(f"{base_url}/send-alert/")
        if response.status_code == 200:
            print("✅ Manual alert sent successfully")
        else:
            print(f"❌ Failed to send manual alert: {response.status_code}")
        
        print("\n✅ Alert system test completed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to Django server")
        print("Make sure the server is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_detection_integration():
    """Test detection and alert integration"""
    base_url = "http://localhost:8000"
    
    print("\n🔍 Testing Detection Integration")
    print("=" * 40)
    
    try:
        # Check if webcam is running
        response = requests.get(f"{base_url}/webcam/status/")
        if response.status_code == 200:
            data = response.json()
            print(f"📹 Webcam running: {data['running']}")
            print(f"📊 Frame available: {data['frame_available']}")
        else:
            print("❌ Could not check webcam status")
            return False
        
        # Check detection status
        response = requests.get(f"{base_url}/detection/status/")
        if response.status_code == 200:
            data = response.json()
            print(f"🤖 Detection enabled: {data['detection_enabled']}")
            print(f"📈 Detection count: {data['detection_count']}")
            print(f"🚨 Fall detected: {data['fall_detected']}")
        else:
            print("❌ Could not check detection status")
            return False
        
        print("✅ Detection integration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔔 Fall Detection - Alert System Test")
    print("=" * 50)
    
    try:
        # Test alert system
        alert_success = test_alert_system()
        
        # Test detection integration
        detection_success = test_detection_integration()
        
        if alert_success and detection_success:
            print("\n🎉 All tests passed! Alert system is working correctly.")
            print("\n📱 Check your WhatsApp for test alerts!")
        else:
            print("\n❌ Some tests failed. Please check the system.")
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
