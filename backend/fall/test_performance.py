#!/usr/bin/env python3
"""
Comprehensive performance testing script for fall detection system
Run this script to test and optimize system performance
"""

import requests
import time
import json
import threading
import statistics
from datetime import datetime

class PerformanceTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        self.running = False
        
    def test_system_startup(self):
        """Test system startup performance"""
        print("🚀 Testing System Startup Performance")
        print("-" * 40)
        
        start_time = time.time()
        
        try:
            # Test webcam startup
            response = requests.post(f"{self.base_url}/webcam/start/")
            webcam_time = time.time() - start_time
            
            if response.status_code == 200:
                print(f"✅ Webcam startup: {webcam_time:.2f}s")
            else:
                print(f"❌ Webcam startup failed: {response.status_code}")
                return False
            
            # Test detection enable
            response = requests.post(f"{self.base_url}/detection/enable/")
            detection_time = time.time() - start_time - webcam_time
            
            if response.status_code == 200:
                print(f"✅ Detection enable: {detection_time:.2f}s")
            else:
                print(f"❌ Detection enable failed: {response.status_code}")
                return False
            
            total_startup = time.time() - start_time
            print(f"✅ Total startup time: {total_startup:.2f}s")
            
            return total_startup < 10  # Should start within 10 seconds
            
        except Exception as e:
            print(f"❌ Startup test failed: {e}")
            return False
    
    def test_detection_performance(self, duration=30):
        """Test detection performance over time"""
        print(f"\n🔍 Testing Detection Performance ({duration}s)")
        print("-" * 40)
        
        fps_samples = []
        detection_times = []
        memory_usage = []
        
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                # Get performance stats
                response = requests.get(f"{self.base_url}/performance/stats/")
                if response.status_code == 200:
                    data = response.json()
                    performance = data['performance']
                    
                    fps_samples.append(performance['fps'])
                    detection_times.append(performance['detection_time'])
                    memory_usage.append(performance['memory_usage'])
                    
                    print(f"FPS: {performance['fps']:.1f} | "
                          f"Detection: {performance['detection_time']:.3f}s | "
                          f"Memory: {performance['memory_usage']:.1f}MB")
                
                time.sleep(1)  # Sample every second
                
            except Exception as e:
                print(f"❌ Performance test error: {e}")
                break
        
        # Calculate statistics
        if fps_samples:
            avg_fps = statistics.mean(fps_samples)
            min_fps = min(fps_samples)
            max_fps = max(fps_samples)
            
            avg_detection = statistics.mean(detection_times) if detection_times else 0
            avg_memory = statistics.mean(memory_usage) if memory_usage else 0
            
            print(f"\n📊 Performance Summary:")
            print(f"   Average FPS: {avg_fps:.1f}")
            print(f"   Min FPS: {min_fps:.1f}")
            print(f"   Max FPS: {max_fps:.1f}")
            print(f"   Average Detection Time: {avg_detection:.3f}s")
            print(f"   Average Memory Usage: {avg_memory:.1f}MB")
            
            # Performance rating
            if avg_fps >= 15:
                rating = "Excellent"
            elif avg_fps >= 10:
                rating = "Good"
            elif avg_fps >= 5:
                rating = "Fair"
            else:
                rating = "Poor"
            
            print(f"   Performance Rating: {rating}")
            
            return {
                'avg_fps': avg_fps,
                'min_fps': min_fps,
                'max_fps': max_fps,
                'avg_detection_time': avg_detection,
                'avg_memory': avg_memory,
                'rating': rating
            }
        
        return None
    
    def test_alert_performance(self):
        """Test alert system performance"""
        print(f"\n🚨 Testing Alert System Performance")
        print("-" * 40)
        
        try:
            # Test alert status
            start_time = time.time()
            response = requests.get(f"{self.base_url}/alerts/status/")
            alert_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Alert status response: {alert_time:.3f}s")
                print(f"   Alerts enabled: {data['alert_enabled']}")
                print(f"   Total alerts: {data['alert_count']}")
                print(f"   Cooldown remaining: {data['cooldown_remaining']:.1f}s")
            else:
                print(f"❌ Alert status failed: {response.status_code}")
                return False
            
            # Test alert toggle
            start_time = time.time()
            response = requests.post(f"{self.base_url}/alerts/toggle/")
            toggle_time = time.time() - start_time
            
            if response.status_code == 200:
                print(f"✅ Alert toggle response: {toggle_time:.3f}s")
            else:
                print(f"❌ Alert toggle failed: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Alert performance test failed: {e}")
            return False
    
    def test_optimization_suggestions(self):
        """Test optimization suggestions"""
        print(f"\n⚡ Testing Optimization Suggestions")
        print("-" * 40)
        
        try:
            response = requests.get(f"{self.base_url}/performance/optimize/")
            if response.status_code == 200:
                data = response.json()
                optimizations = data.get('optimizations', [])
                
                if optimizations:
                    print("🔧 Optimization suggestions found:")
                    for opt in optimizations:
                        print(f"   Type: {opt['type']}")
                        print(f"   Message: {opt['message']}")
                        print(f"   Suggestions: {', '.join(opt['suggestions'])}")
                        print()
                else:
                    print("✅ No optimizations needed - system running efficiently!")
                
                return True
            else:
                print(f"❌ Optimization test failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Optimization test error: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run comprehensive performance test"""
        print("🧪 Fall Detection - Comprehensive Performance Test")
        print("=" * 60)
        
        results = {
            'startup_test': False,
            'performance_test': None,
            'alert_test': False,
            'optimization_test': False,
            'overall_rating': 'Unknown'
        }
        
        # Test 1: System Startup
        results['startup_test'] = self.test_system_startup()
        
        if not results['startup_test']:
            print("❌ System startup failed - cannot continue tests")
            return results
        
        # Test 2: Detection Performance
        results['performance_test'] = self.test_detection_performance(30)
        
        # Test 3: Alert Performance
        results['alert_test'] = self.test_alert_performance()
        
        # Test 4: Optimization Suggestions
        results['optimization_test'] = self.test_optimization_suggestions()
        
        # Overall rating
        if results['performance_test']:
            rating = results['performance_test']['rating']
            results['overall_rating'] = rating
            
            print(f"\n🎯 Overall Performance Rating: {rating}")
            
            if rating in ['Excellent', 'Good']:
                print("✅ System is performing well!")
            elif rating == 'Fair':
                print("⚠️  System performance is acceptable but could be improved")
            else:
                print("❌ System performance needs optimization")
        
        return results
    
    def cleanup(self):
        """Cleanup after testing"""
        try:
            print(f"\n🧹 Cleaning up...")
            requests.post(f"{self.base_url}/webcam/stop/")
            print("✅ Cleanup completed")
        except:
            print("⚠️  Cleanup failed - manual cleanup may be needed")

def main():
    tester = PerformanceTester()
    
    try:
        results = tester.run_comprehensive_test()
        
        print(f"\n📋 Test Results Summary:")
        print(f"   Startup Test: {'✅ Pass' if results['startup_test'] else '❌ Fail'}")
        print(f"   Performance Test: {'✅ Pass' if results['performance_test'] else '❌ Fail'}")
        print(f"   Alert Test: {'✅ Pass' if results['alert_test'] else '❌ Fail'}")
        print(f"   Optimization Test: {'✅ Pass' if results['optimization_test'] else '❌ Fail'}")
        print(f"   Overall Rating: {results['overall_rating']}")
        
        if all([results['startup_test'], results['performance_test'], results['alert_test'], results['optimization_test']]):
            print("\n🎉 All tests passed! System is ready for production.")
        else:
            print("\n⚠️  Some tests failed. Please review the results.")
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main()
