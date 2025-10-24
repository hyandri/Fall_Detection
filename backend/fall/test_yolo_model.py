#!/usr/bin/env python3
"""
Test script to verify YOLO model loading and basic functionality
Run this script to test if your YOLO model is working properly
"""

import os
import sys
import cv2
import numpy as np
from ultralytics import YOLO

def test_yolo_model():
    """Test YOLO model loading and basic functionality"""
    print("🔍 Testing YOLO Fall Detection Model")
    print("=" * 50)
    
    # Get the model path
    model_path = os.path.join('..', '..', 'models', 'runs', 'detect', 'fall_detection_v22', 'weights', 'best.pt')
    model_path = os.path.abspath(model_path)
    
    print(f"📁 Looking for model at: {model_path}")
    
    if not os.path.exists(model_path):
        print(f"❌ Error: Model file not found at {model_path}")
        print("Please check if the model file exists and the path is correct.")
        return False
    
    print("✅ Model file found!")
    
    try:
        print("🔄 Loading YOLO model...")
        model = YOLO(model_path)
        print("✅ YOLO model loaded successfully!")
        
        # Print model information
        print(f"📊 Model classes: {model.names}")
        print(f"📊 Number of classes: {len(model.names)}")
        
        # Test with a dummy image
        print("🧪 Testing model with dummy image...")
        dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        try:
            results = model(dummy_image, conf=0.4, verbose=False)
            print("✅ Model inference test passed!")
            
            # Test with webcam if available
            print("📹 Testing with webcam (if available)...")
            cap = cv2.VideoCapture(0)
            
            if cap.isOpened():
                print("✅ Webcam detected!")
                ret, frame = cap.read()
                
                if ret:
                    print("🔄 Running detection on webcam frame...")
                    results = model(frame, conf=0.4, verbose=False)
                    print("✅ Webcam detection test passed!")
                    
                    # Show detection results
                    detection_count = 0
                    for result in results:
                        if result.boxes is not None:
                            detection_count += len(result.boxes)
                    
                    print(f"📊 Detections found: {detection_count}")
                    
                    if detection_count > 0:
                        print("🎯 Detection results:")
                        for result in results:
                            if result.boxes is not None:
                                for i, box in enumerate(result.boxes):
                                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                                    confidence = box.conf[0].cpu().numpy()
                                    class_id = int(box.cls[0].cpu().numpy())
                                    class_name = model.names[class_id]
                                    
                                    print(f"  Detection {i+1}: {class_name} (confidence: {confidence:.2f})")
                else:
                    print("⚠️  Could not read frame from webcam")
                
                cap.release()
            else:
                print("⚠️  No webcam detected, skipping webcam test")
            
            print("\n✅ All tests passed! Your YOLO model is ready for fall detection.")
            return True
            
        except Exception as e:
            print(f"❌ Error during model inference: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error loading YOLO model: {e}")
        return False

def test_model_performance():
    """Test model performance with timing"""
    print("\n🚀 Performance Test")
    print("-" * 30)
    
    model_path = os.path.join('..', '..', 'models', 'runs', 'detect', 'fall_detection_v22', 'weights', 'best.pt')
    model_path = os.path.abspath(model_path)
    
    if not os.path.exists(model_path):
        print("❌ Model not found for performance test")
        return
    
    try:
        import time
        model = YOLO(model_path)
        
        # Create test images of different sizes
        test_sizes = [(640, 480), (1280, 720), (1920, 1080)]
        
        for width, height in test_sizes:
            print(f"📏 Testing with {width}x{height} image...")
            
            # Create dummy image
            dummy_image = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
            
            # Time the inference
            start_time = time.time()
            results = model(dummy_image, conf=0.4, verbose=False)
            end_time = time.time()
            
            inference_time = end_time - start_time
            fps = 1.0 / inference_time if inference_time > 0 else 0
            
            print(f"⏱️  Inference time: {inference_time:.3f}s")
            print(f"🚀 FPS: {fps:.1f}")
            
            if fps >= 10:
                print("✅ Performance: Good")
            elif fps >= 5:
                print("⚠️  Performance: Acceptable")
            else:
                print("❌ Performance: Poor")
            print()

    except Exception as e:
        print(f"❌ Performance test failed: {e}")

if __name__ == "__main__":
    print("🔍 Fall Detection - YOLO Model Test")
    print("=" * 50)
    
    try:
        success = test_yolo_model()
        if success:
            test_model_performance()
            print("\n🎉 Model test completed successfully!")
            print("Your YOLO model is ready for integration with the Django backend.")
            sys.exit(0)
        else:
            print("\n❌ Model test failed!")
            print("Please check your model file and try again.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
