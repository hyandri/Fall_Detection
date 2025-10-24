import os
import pandas as pd
import numpy as np

def normalize_keypoints(df):
    """Normalize coordinates to make them scale-independent."""
    keypoints = df.values
    mean = np.mean(keypoints, axis=0)
    std = np.std(keypoints, axis=0) + 1e-8
    normalized = (keypoints - mean) / std
    return normalized

def get_label_from_annotation(annot_file):
    """
    Read first two lines of annotation file to determine label.
    0 = fall
    1 = not fall
    """
    with open(annot_file, "r") as f:
        lines = f.readlines()
        bi = int(lines[0].strip())
        ei = int(lines[1].strip())
        if bi == 0 and ei == 0:
            return 1  # not fall
        else:
            return 0  # fall
            
def create_annotation_base_name(csv_file_name):
    """
    Handles the inconsistent naming:
    Input: video(1)_pose.csv
    Target Output: video (1)
    """
    # 1. Remove file extension and '_pose'
    base = os.path.splitext(csv_file_name)[0].replace("_pose", "")
    
    # 2. Add the missing space for filenames like 'video(1)' to match 'video (1)'
    # This targets the common naming pattern observed in your data.
    if base.startswith("video(") and base[5] == '(':
        # Replace the opening parenthesis with ' (' (space-parenthesis)
        base = base.replace('(', ' (', 1) 
    
    # Handle the 'fall' example you mentioned, assuming it also needs a space
    elif base.startswith("fall(") and base[4] == '(':
        base = base.replace('(', ' (', 1) 
        
    return base

def process_train_pose(input_csv_dir, annot_dir, output_file):
    """
    Reads all pose CSV files, normalizes the keypoints, retrieves labels 
    from annotations, and saves the result as a padded NumPy array.
    """
    data = []
    labels = []
    max_len = 0
    
    for csv_file in os.listdir(input_csv_dir):
        if not csv_file.endswith(".csv"):
            continue

        # *** CRITICAL FIX APPLIED HERE ***
        # Use the helper function to construct the correct annotation file name structure
        base_name = create_annotation_base_name(csv_file)
        annot_file = os.path.join(annot_dir, base_name + ".txt")
        
        if not os.path.exists(annot_file):
            # Print the expected path for any remaining debugging
            print(f"⚠️ Warning: Annotation file not found for {csv_file}. Expected: {annot_file}, skipping")
            continue

        # Get the label
        label = get_label_from_annotation(annot_file)
        
        # Read and preprocess the keypoints
        df = pd.read_csv(os.path.join(input_csv_dir, csv_file))
        df = df.select_dtypes(include=[np.number])
        normalized = normalize_keypoints(df)

        data.append(normalized)
        labels.append(label)
        
        if len(normalized) > max_len:
            max_len = len(normalized)

    if len(data) == 0:
        raise ValueError("❌ No valid data found — check filenames or annotation path!")

    # Pad or truncate to equal length
    num_samples = len(data)
    num_features = data[0].shape[1]
    X = np.zeros((num_samples, max_len, num_features), dtype=np.float32)

    for i, seq in enumerate(data):
        length = len(seq)
        X[i, :length, :] = seq[:max_len]

    y = np.array(labels, dtype=np.int32)
    
    np.savez(output_file, X=X, y=y)
    print(f"✅ Saved preprocessed train data (X shape: {X.shape}, y shape: {y.shape}) to {output_file}")


def get_absolute_paths():
    """Helper to get robust absolute paths for the directories."""
    # Using the relative paths provided in your original run, as the absolute path check seemed correct
    annot_dir = "dataset/train/Annotation_files"
    input_csv_dir = "pose_data/csvs_train"
    output_file = "pose_data/processed/train_pose_data.npz"
    
    print(f"INFO: Using CSV Directory: {input_csv_dir}")
    print(f"INFO: Using Annotation Directory: {os.path.abspath(annot_dir)}")

    return input_csv_dir, annot_dir, output_file

if __name__ == "__main__":
    input_csv_dir, annot_dir, output_file = get_absolute_paths()
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    process_train_pose(
        input_csv_dir=input_csv_dir,
        annot_dir=annot_dir,
        output_file=output_file
    )