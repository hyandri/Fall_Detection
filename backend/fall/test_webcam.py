#!/usr/bin/env python3
"""
Simple test script to verify webcam functionality
Run this script to test if your webcam is working properly
"""

import cv2
import sys
import time

def test_webcam():
    """Test webcam capture functionality"""
    print("Testing webcam capture...")
    
    # Try to initialize webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Error: Could not open webcam (index 0)")
        # Try alternative camera indices
        for i in range(1, 5):
            print(f"Trying camera index {i}...")
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                print(f"✅ Successfully opened webcam at index {i}")
                break
        else:
            print("❌ Error: Could not find any working webcam")
            return False
    
    # Set webcam properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    print("✅ Webcam initialized successfully")
    print("📹 Capturing frames for 5 seconds...")
    print("Press 'q' to quit early")
    
    frame_count = 0
    start_time = time.time()
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("❌ Error: Failed to read frame from webcam")
            break
        
        frame_count += 1
        
        # Display frame info every 30 frames
        if frame_count % 30 == 0:
            elapsed = time.time() - start_time
            fps = frame_count / elapsed
            print(f"📊 Frames captured: {frame_count}, FPS: {fps:.1f}")
        
        # Show frame (optional - comment out if running headless)
        cv2.imshow('Webcam Test', frame)
        
        # Check for quit key or timeout
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("🛑 Quit key pressed")
            break
        
        # Stop after 5 seconds
        if time.time() - start_time > 5:
            print("⏰ 5 seconds elapsed")
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    elapsed = time.time() - start_time
    avg_fps = frame_count / elapsed if elapsed > 0 else 0
    
    print(f"✅ Test completed successfully!")
    print(f"📊 Total frames: {frame_count}")
    print(f"⏱️  Total time: {elapsed:.2f} seconds")
    print(f"🚀 Average FPS: {avg_fps:.1f}")
    
    if avg_fps >= 15:
        print("✅ Performance: Good (FPS >= 15)")
    elif avg_fps >= 10:
        print("⚠️  Performance: Acceptable (FPS >= 10)")
    else:
        print("❌ Performance: Poor (FPS < 10)")
    
    return True

if __name__ == "__main__":
    print("🔍 Fall Detection - Webcam Test")
    print("=" * 40)
    
    try:
        success = test_webcam()
        if success:
            print("\n✅ Webcam test passed! Your webcam is ready for fall detection.")
            sys.exit(0)
        else:
            print("\n❌ Webcam test failed! Please check your webcam connection.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
