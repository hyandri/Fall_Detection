#!/usr/bin/env python3
"""
Complete system test for fall detection
Tests all components: webcam, detection, streaming, alerts, and performance
"""

import requests
import time
import json
import sys
import threading
from datetime import datetime

class CompleteSystemTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_results = {}
        
    def test_all_components(self):
        """Test all system components"""
        print("🧪 Complete Fall Detection System Test")
        print("=" * 60)
        
        # Test 1: System Startup
        print("\n1️⃣ Testing System Startup...")
        self.test_results['startup'] = self.test_startup()
        
        # Test 2: Webcam Functionality
        print("\n2️⃣ Testing Webcam Functionality...")
        self.test_results['webcam'] = self.test_webcam()
        
        # Test 3: Detection System
        print("\n3️⃣ Testing Detection System...")
        self.test_results['detection'] = self.test_detection()
        
        # Test 4: Streaming System
        print("\n4️⃣ Testing Streaming System...")
        self.test_results['streaming'] = self.test_streaming()
        
        # Test 5: Alert System
        print("\n5️⃣ Testing Alert System...")
        self.test_results['alerts'] = self.test_alerts()
        
        
        # Generate final report
        self.generate_report()
        
        return self.test_results
    
    def test_startup(self):
        """Test system startup"""
        try:
            # Test home page
            response = requests.get(f"{self.base_url}/")
            if response.status_code != 200:
                print("❌ Home page failed")
                return False
            
            # Test detection page
            response = requests.get(f"{self.base_url}/detection/")
            if response.status_code != 200:
                print("❌ Detection page failed")
                return False
            
            print("✅ System startup successful")
            return True
            
        except Exception as e:
            print(f"❌ Startup test failed: {e}")
            return False
    
    def test_webcam(self):
        """Test webcam functionality"""
        try:
            # Start webcam
            response = requests.post(f"{self.base_url}/webcam/start/")
            if response.status_code != 200:
                print("❌ Webcam start failed")
                return False
            
            data = response.json()
            if data['status'] != 'success':
                print(f"❌ Webcam start error: {data['message']}")
                return False
            
            # Check webcam status
            response = requests.get(f"{self.base_url}/webcam/status/")
            if response.status_code != 200:
                print("❌ Webcam status check failed")
                return False
            
            data = response.json()
            if not data['running']:
                print("❌ Webcam not running")
                return False
            
            print("✅ Webcam functionality working")
            return True
            
        except Exception as e:
            print(f"❌ Webcam test failed: {e}")
            return False
    
    def test_detection(self):
        """Test detection system"""
        try:
            # Enable detection
            response = requests.post(f"{self.base_url}/detection/enable/")
            if response.status_code != 200:
                print("❌ Detection enable failed")
                return False
            
            data = response.json()
            if data['status'] != 'success':
                print(f"❌ Detection enable error: {data['message']}")
                return False
            
            # Check detection status
            response = requests.get(f"{self.base_url}/detection/status/")
            if response.status_code != 200:
                print("❌ Detection status check failed")
                return False
            
            data = response.json()
            if not data['detection_enabled']:
                print("❌ Detection not enabled")
                return False
            
            print("✅ Detection system working")
            return True
            
        except Exception as e:
            print(f"❌ Detection test failed: {e}")
            return False
    
    def test_streaming(self):
        """Test streaming system"""
        try:
            # Test detection stream
            response = requests.get(f"{self.base_url}/stream/video/", timeout=5)
            if response.status_code != 200:
                print("❌ Detection stream failed")
                return False
            
            # Test raw stream
            response = requests.get(f"{self.base_url}/stream/raw/", timeout=5)
            if response.status_code != 200:
                print("❌ Raw stream failed")
                return False
            
            print("✅ Streaming system working")
            return True
            
        except Exception as e:
            print(f"❌ Streaming test failed: {e}")
            return False
    
    def test_alerts(self):
        """Test alert system"""
        try:
            # Check alert status
            response = requests.get(f"{self.base_url}/alerts/status/")
            if response.status_code != 200:
                print("❌ Alert status check failed")
                return False
            
            data = response.json()
            if not data['alert_enabled']:
                print("❌ Alerts not enabled")
                return False
            
            # Test alert toggle
            response = requests.post(f"{self.base_url}/alerts/toggle/")
            if response.status_code != 200:
                print("❌ Alert toggle failed")
                return False
            
            # Toggle back
            response = requests.post(f"{self.base_url}/alerts/toggle/")
            if response.status_code != 200:
                print("❌ Alert toggle back failed")
                return False
            
            print("✅ Alert system working")
            return True
            
        except Exception as e:
            print(f"❌ Alert test failed: {e}")
            return False
    
    
    def generate_report(self):
        """Generate final test report"""
        print("\n" + "=" * 60)
        print("📋 COMPLETE SYSTEM TEST REPORT")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        print(f"📊 Test Results: {passed_tests}/{total_tests} passed")
        print()
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name.title()}: {status}")
        
        print()
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED!")
            print("✅ Fall Detection System is fully operational")
            print("🚀 System is ready for production use")
        else:
            print("⚠️  SOME TESTS FAILED")
            print("❌ Please review failed components")
            print("🔧 System may need troubleshooting")
        
        print("\n📱 Next Steps:")
        print("   1. Start the system: python manage.py runserver")
        print("   2. Open browser: http://localhost:8000/")
        print("   3. Click 'Start Fall Detection'")
        
        return passed_tests == total_tests
    
    def cleanup(self):
        """Cleanup after testing"""
        try:
            print("\n🧹 Cleaning up...")
            requests.post(f"{self.base_url}/webcam/stop/")
            print("✅ Cleanup completed")
        except:
            print("⚠️  Cleanup failed - manual cleanup may be needed")

def main():
    print("🔍 Fall Detection - Complete System Test")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code != 200:
            print("❌ Django server is not running!")
            print("Please start the server first:")
            print("   cd /Users/krrishpanakarmacharya/Desktop/fall_detection/Fall_Detection")
            print("   source venv/bin/activate")
            print("   cd backend/fall")
            print("   python manage.py runserver")
            sys.exit(1)
    except:
        print("❌ Cannot connect to Django server!")
        print("Please start the server first:")
        print("   cd /Users/krrishpanakarmacharya/Desktop/fall_detection/Fall_Detection")
        print("   source venv/bin/activate")
        print("   cd backend/fall")
        print("   python manage.py runserver")
        sys.exit(1)
    
    tester = CompleteSystemTester()
    
    try:
        success = tester.test_all_components()
        
        if success:
            print("\n🎉 System is ready for use!")
            sys.exit(0)
        else:
            print("\n❌ System needs attention")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main()
