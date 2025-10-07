# changes in directories 

import os
import cv2

# Paths
TRAIN_VIDEOS = "data/train/Videos"
TRAIN_ANNOT = "data/train/Annotation_yolo_fixed"

IMAGES_DST = "data/images/train"
LABELS_DST = "data/labels/train"

# Create destination folders
os.makedirs(IMAGES_DST, exist_ok=True)
os.makedirs(LABELS_DST, exist_ok=True)

# Loop through all videos
for video_file in os.listdir(TRAIN_VIDEOS):
    if not video_file.endswith((".mp4", ".avi", ".mov")):
        continue

    video_path = os.path.join(TRAIN_VIDEOS, video_file)
    video_name = os.path.splitext(video_file)[0]

    # Corresponding annotation file
    ann_file = os.path.join(TRAIN_ANNOT, video_name + ".txt")
    if not os.path.exists(ann_file):
        print(f"No annotation for {video_file}, skipping...")
        continue

    # Read annotation lines (skip first 2 lines)
    with open(ann_file, "r") as f:
        lines = f.readlines()[2:]  # skip first two lines

    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Cannot open {video_file}")
        continue

    frame_count = 0
    saved_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1

        # Save frame as jpg
        frame_filename = f"{video_name}_frame_{frame_count:05d}.jpg"
        frame_path = os.path.join(IMAGES_DST, frame_filename)
        cv2.imwrite(frame_path, frame)

        # Get corresponding annotation line
        idx = frame_count - 1  # frame_count starts at 1
        if idx < len(lines):
            frame_label = lines[idx].strip()
        else:
            frame_label = ""  # no bbox for frames beyond annotation

        # Save YOLO label
        label_path = os.path.join(LABELS_DST, frame_filename.replace(".jpg", ".txt"))
        with open(label_path, "w") as f:
            if frame_label != "":
                f.write(frame_label)

        saved_count += 1

    cap.release()
    print(f"Processed {video_file}: extracted {saved_count} frames.")

print("Frame extraction and label linking complete!")
