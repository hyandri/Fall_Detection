from ultralytics import YOLO

# Load model
model = YOLO("models/runs/detect/fall_detection_v22/weights/best.pt")

# Run detection on one video 
results = model.predict(
    source="data/test/video (23).avi",  # path to a test video
    save=True,       # save output video
    conf=0.4,        # confidence threshold
    show=True       # shows video while processing
)
