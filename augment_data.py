import os
import cv2
import random
import shutil
from albumentations import Compose, HorizontalFlip, RandomBrightnessContrast, Rotate

# ----- 1 COUNT CLASSES -----
label_dir = "data/train-img4/labels"
img_dir = "data/train-img4/images"

class0_files = []
class1_files = []

for file in os.listdir(label_dir):
    if not file.endswith(".txt"):
        continue
    path = os.path.join(label_dir, file)
    with open(path, "r") as f:
        lines = f.readlines()
        classes = {line.split()[0] for line in lines}
        if "0" in classes:
            class0_files.append(file)
        if "1" in classes:
            class1_files.append(file)

print(f"Class 0 images: {len(class0_files)}")
print(f"Class 1 images: {len(class1_files)}")

# ----- 2️  OVERSAMPLE MINORITY -----
augment = Compose([
    HorizontalFlip(p=0.5),
    RandomBrightnessContrast(p=0.5),
    Rotate(limit=10, p=0.5),
])

minority_files = class0_files
n_to_add = int(len(minority_files) * 0.15)
print(f"Oversampling {n_to_add} minority images...")

for i in range(n_to_add):
    fname = random.choice(minority_files)
    base = os.path.splitext(fname)[0]

    img_path = os.path.join(img_dir, f"{base}.jpg")
    label_path = os.path.join(label_dir, fname)

    if not os.path.exists(img_path):
        continue

    img = cv2.imread(img_path)
    aug_img = augment(image=img)["image"]

    new_name = f"{base}_aug{i}"
    cv2.imwrite(os.path.join(img_dir, f"{new_name}.jpg"), aug_img)
    shutil.copy(label_path, os.path.join(label_dir, f"{new_name}.txt"))

print("✅ Oversampling done.")


# ----- 2️  UNDERSAMPLE MAJORITY -----


n_to_remove = int(len(class1_files) * 0.15)
remove_files = random.sample(class1_files, n_to_remove)

print(f"Removing {n_to_remove} majority images...")

for fname in remove_files:
    base = os.path.splitext(fname)[0]
    img_path = os.path.join(img_dir, f"{base}.jpg")
    label_path = os.path.join(label_dir, fname)
    if os.path.exists(img_path):
        os.remove(img_path)
    if os.path.exists(label_path):
        os.remove(label_path)

print("✅ Undersampling done.")

# UNDO OVERSAMPLING
# import os

# img_dir = "data/train-img4/images"
# label_dir = "data/train-img4/labels"

# deleted_imgs = 0
# deleted_labels = 0

# for folder, count in [(img_dir, "image"), (label_dir, "label")]:
#     for f in os.listdir(folder):
#         if "_aug" in f:
#             os.remove(os.path.join(folder, f))
#             if folder == img_dir:
#                 deleted_imgs += 1
#             else:
#                 deleted_labels += 1

# print(f"✅ Deleted {deleted_imgs} oversampled images.")
# print(f"✅ Deleted {deleted_labels} oversampled labels.")
