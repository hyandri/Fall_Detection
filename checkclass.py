import os

label_dir = "data/train-img4/labels"

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
