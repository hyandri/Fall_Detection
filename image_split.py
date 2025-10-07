# import os
# import random
# import shutil

# IMAGES_SRC = "data/images/train"  # all extracted frames
# LABELS_SRC = "data/labels/train"

# IMAGES_DST_TRAIN = "data/images/train_final"
# IMAGES_DST_VAL = "data/images/val"
# LABELS_DST_TRAIN = "data/labels/train_final"
# LABELS_DST_VAL = "data/labels/val"

# os.makedirs(IMAGES_DST_TRAIN, exist_ok=True)
# os.makedirs(IMAGES_DST_VAL, exist_ok=True)
# os.makedirs(LABELS_DST_TRAIN, exist_ok=True)
# os.makedirs(LABELS_DST_VAL, exist_ok=True)

# # List all images
# images = [f for f in os.listdir(IMAGES_SRC) if f.endswith(".jpg")]
# random.shuffle(images)

# split_ratio = 0.8
# split_idx = int(len(images) * split_ratio)
# train_images = images[:split_idx]
# val_images = images[split_idx:]

# # Function to move files
# def move_files(img_list, img_dst, label_dst):
#     for img_file in img_list:
#         shutil.copy2(os.path.join(IMAGES_SRC, img_file), os.path.join(img_dst, img_file))
#         label_file = img_file.replace(".jpg", ".txt")
#         shutil.copy2(os.path.join(LABELS_SRC, label_file), os.path.join(label_dst, label_file))

# move_files(train_images, IMAGES_DST_TRAIN, LABELS_DST_TRAIN)
# move_files(val_images, IMAGES_DST_VAL, LABELS_DST_VAL)

# print(f"Train: {len(train_images)} images, Val: {len(val_images)} images")


import os
import random
import shutil

IMAGES_SRC = "data/images/train"  
LABELS_SRC = "data/labels/train"  



IMAGES_DST_TRAIN = "data/train-img4/images"
LABELS_DST_TRAIN = "data/train-img4/labels"

IMAGES_DST_VAL = "data/val4/images"
LABELS_DST_VAL = "data/val4/labels"


os.makedirs(IMAGES_DST_TRAIN, exist_ok=True)
os.makedirs(IMAGES_DST_VAL, exist_ok=True)
os.makedirs(LABELS_DST_TRAIN, exist_ok=True)
os.makedirs(LABELS_DST_VAL, exist_ok=True)

# List all images
images = [f for f in os.listdir(IMAGES_SRC) if f.endswith(".jpg")]
random.shuffle(images)


split_ratio = 0.8
split_idx = int(len(images) * split_ratio)
train_images = images[:split_idx]
val_images = images[split_idx:]

# Function to move files (Remains the same)
def move_files(img_list, img_dst, label_dst):
    for img_file in img_list:
        shutil.copy2(os.path.join(IMAGES_SRC, img_file), os.path.join(img_dst, img_file))
        label_file = img_file.replace(".jpg", ".txt")
        shutil.copy2(os.path.join(LABELS_SRC, label_file), os.path.join(label_dst, label_file))

move_files(train_images, IMAGES_DST_TRAIN, LABELS_DST_TRAIN)
move_files(val_images, IMAGES_DST_VAL, LABELS_DST_VAL)

print(f"Train: {len(train_images)} images, Val: {len(val_images)} images")

# import os
# import random
# import shutil

# IMAGES_SRC = "data/images/train" 
# LABELS_SRC = "data/labels/train" 

# IMAGES_DST_TRAIN = "data/train-img3/images"
# LABELS_DST_TRAIN = "data/train-img3/labels"

# IMAGES_DST_VAL = "data/val3/images"
# LABELS_DST_VAL = "data/val3/labels"

# os.makedirs(IMAGES_DST_TRAIN, exist_ok=True)
# os.makedirs(IMAGES_DST_VAL, exist_ok=True)
# os.makedirs(LABELS_DST_TRAIN, exist_ok=True)
# os.makedirs(LABELS_DST_VAL, exist_ok=True)

# # 1. Get unique video names from the frame files
# all_image_files = [f for f in os.listdir(IMAGES_SRC) if f.endswith(".jpg")]

# video_names = set()
# for f in all_image_files:
#     # Extracts 'video_name' from 'video_name_frame_00001.jpg'
#     prefix = f.rsplit('_frame_', 1)[0] 
#     video_names.add(prefix)

# video_list = list(video_names)
# random.shuffle(video_list)

# # 2. Split the video list (80/20 ratio applied to videos, not frames)
# split_ratio = 0.8
# split_idx = int(len(video_list) * split_ratio)
# train_videos = set(video_list[:split_idx])
# val_videos = set(video_list[split_idx:])

# print(f"Splitting {len(video_list)} unique videos: Train ({len(train_videos)}), Val ({len(val_videos)})")

# # 3. Compile the actual list of frames based on the split video names
# train_images = []
# val_images = []

# for f in all_image_files:
#     prefix = f.rsplit('_frame_', 1)[0]
    
#     if prefix in train_videos:
#         train_images.append(f)
#     elif prefix in val_videos:
#         val_images.append(f)

# # 4. Function to move files
# def move_files(img_list, img_dst, label_dst):
#     for img_file in img_list:
#         shutil.copy2(os.path.join(IMAGES_SRC, img_file), os.path.join(img_dst, img_file))
#         label_file = img_file.replace(".jpg", ".txt")
        
#         # Check if the label file exists before copying (it should if file 2 was run correctly)
#         label_src_path = os.path.join(LABELS_SRC, label_file)
#         if os.path.exists(label_src_path):
#             shutil.copy2(label_src_path, os.path.join(label_dst, label_file))

# move_files(train_images, IMAGES_DST_TRAIN, LABELS_DST_TRAIN)
# move_files(val_images, IMAGES_DST_VAL, LABELS_DST_VAL)

# print(f" Split complete. Train frames: {len(train_images)}, Val frames: {len(val_images)}")