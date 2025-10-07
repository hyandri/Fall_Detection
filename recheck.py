import os

label_dir = "data/train/Annotation_yolo_fixed"
counts = [0, 0]  

for file in os.listdir(label_dir):
    with open(os.path.join(label_dir, file)) as f:
        for line in f:
            cls = int(line.split()[0])
            counts[cls] += 1

print("Labels per class:", counts)
