# pose_extraction/extract_pose.py

import cv2
import mediapipe as mp
import pandas as pd
import os
from tqdm import tqdm

# Paths
video_dir = "data/test"  # path to folder containing videos
output_dir = "pose_data/csvs_test"
os.makedirs(output_dir, exist_ok=True)

# Initialize Mediapipe Pose model
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

for video_file in tqdm(os.listdir(video_dir)):
    if not video_file.endswith((".mp4", ".avi", ".mov")):
        continue

    video_path = os.path.join(video_dir, video_file)
    cap = cv2.VideoCapture(video_path)

    frame_num = 0
    all_keypoints = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_num += 1
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        # Collect keypoints
        if results.pose_landmarks:
            keypoints = []
            for lm in results.pose_landmarks.landmark:
                keypoints.extend([lm.x, lm.y, lm.z, lm.visibility])
            all_keypoints.append([frame_num] + keypoints)

    cap.release()

    # Convert to DataFrame and save
    df = pd.DataFrame(all_keypoints)
    df.to_csv(os.path.join(output_dir, f"{os.path.splitext(video_file)[0]}_pose.csv"),
              index=False, header=False)

print("✅ Pose extraction completed. CSVs saved in:", output_dir)
