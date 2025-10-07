# import os


# ANNOT_SRC = "data/train/Annotation_files"  # your copied raw annotations
# YOLO_DST = "data/train/Annotation_yolo(2)"  # output YOLO labels

# # Original video resolution
# IMG_W, IMG_H = 320, 240

# os.makedirs(YOLO_DST, exist_ok=True)

# # Function to convert one annotation line to YOLO format
# def convert_line(line):
#     parts = line.strip().split(",")
#     if len(parts) != 6:
#         return None
    
#     frame_num, y_t, x1, y1, x2, y2 = parts
#     y_t = int(y_t)
    
#     # Skip frames without bbox
#     if int(x1) == 0 and int(y1) == 0 and int(x2) == 0 and int(y2) == 0:
#         return None
    
#     # Map yt → class_id
#     if y_t == 1:
#         cls = 1  # Non-Fall
#     else:
#         cls = 0
    
#     x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))
    
#     # Convert to YOLO normalized format
#     x_center = ((x1 + x2) / 2) / IMG_W
#     y_center = ((y1 + y2) / 2) / IMG_H
#     width = (x2 - x1) / IMG_W
#     height = (y2 - y1) / IMG_H
    
#     return f"{cls} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"

# # Process each file
# def process_file(src_file, dst_file):
#     with open(src_file, "r") as f:
#         lines = f.readlines()
    
#     # Skip first 2 lines (fall start/end)
#     lines = lines[2:]
    
#     yolo_lines = []
#     for line in lines:
#         converted = convert_line(line)
#         if converted:
#             yolo_lines.append(converted)
    
#     # Write YOLO file if any bbox exists
#     if yolo_lines:
#         with open(dst_file, "w") as f:
#             f.write("\n".join(yolo_lines))

# # Loop through all annotation files
# count = 0
# for fname in os.listdir(ANNOT_SRC):
#     if fname.endswith(".txt"):
#         src_path = os.path.join(ANNOT_SRC, fname)
#         dst_path = os.path.join(YOLO_DST, fname)
#         process_file(src_path, dst_path)
#         count += 1

# print(f"Converted {count} annotation files to YOLO format in: {YOLO_DST}")

import os

ANNOT_SRC = "data/train/Annotation_files"
YOLO_DST = "data/train/Annotation_yolo_fixed"
IMG_W, IMG_H = 320, 240

os.makedirs(YOLO_DST, exist_ok=True)

def convert_line(line):
    parts = line.strip().split(",")
    if len(parts) != 6:
        return None

    frame_num, y_t, x1, y1, x2, y2 = parts
    y_t = int(y_t)
    x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))

    # --- Class mapping ---
    # Adjust according to your dataset: e.g., y_t==1: non-fall, y_t==2: fall
    if y_t == 1:
        cls = 1  # Non-Fall
    else:
        cls = 0  # Fall

    # --- Handle empty bbox for fall ---
    if x1 == 0 and y1 == 0 and x2 == 0 and y2 == 0:
        # if fall frame, give approximate full-frame box
        if cls == 0:
            x1, y1, x2, y2 = 0, 0, IMG_W, IMG_H
        else:
            return None  # still skip empty non-fall

    # --- Convert to YOLO format ---
    x_center = ((x1 + x2) / 2) / IMG_W
    y_center = ((y1 + y2) / 2) / IMG_H
    width = (x2 - x1) / IMG_W
    height = (y2 - y1) / IMG_H

    return f"{cls} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"

def process_file(src_file, dst_file):
    with open(src_file, "r") as f:
        lines = f.readlines()

    lines = lines[2:]
    yolo_lines = []
    for line in lines:
        converted = convert_line(line)
        if converted:
            yolo_lines.append(converted)

    if yolo_lines:
        with open(dst_file, "w") as f:
            f.write("\n".join(yolo_lines))

count = 0
for fname in os.listdir(ANNOT_SRC):
    if fname.endswith(".txt"):
        process_file(os.path.join(ANNOT_SRC, fname),
                     os.path.join(YOLO_DST, fname))
        count += 1

print(f"✅ Converted {count} annotation files to YOLO format (including fall frames).")
