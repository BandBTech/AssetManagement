import cv2
import numpy as np
from django.core.files.base import ContentFile
import uuid

# Lazy load YOLO to avoid import issues during migration
yolo_main_model = None
yolo_pipe_model = None


def _get_models():
    global yolo_main_model, yolo_pipe_model
    from ultralytics import YOLO
    if yolo_main_model is None:
        yolo_main_model = YOLO("model/best.pt")
    if yolo_pipe_model is None:
        yolo_pipe_model = YOLO("model/pipes_best.pt")
    return yolo_main_model, yolo_pipe_model


def run_yolo_and_annotate(image_file):
    """
    Takes Django InMemoryUploadedFile.
    Returns (annotated_image_as_ContentFile, detected_objects_list)
    """
    yolo_model, pipe_model = _get_models()

    image_bytes = np.frombuffer(image_file.read(), np.uint8)
    image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Could not decode image. Check file format.")

    # Find the class ID for 'pipe' in the first model to exclude it
    pipe_class_id = None
    for k, v in yolo_model.names.items():
        if v.lower() == 'pipe':
            pipe_class_id = k
            break
            
    classes_to_detect = None
    if pipe_class_id is not None:
        classes_to_detect = [k for k in yolo_model.names.keys() if k != pipe_class_id]

    # Run inference, excluding 'pipe' from the first model
    results = yolo_model(image, conf=0.6, classes=classes_to_detect)
    results_pipe = pipe_model(image, conf=0.6)
    
    # Plot both results on the same image
    annotated = results[0].plot()
    try:
        annotated = results_pipe[0].plot(im=annotated)
    except TypeError:
        try:
            annotated = results_pipe[0].plot(img=annotated)
        except TypeError:
            pass # Fallback if neither works, we just return the first plot

    detected = []
    # Collect detections from first model
    for box in results[0].boxes:
        detected.append(
            {
                "label": yolo_model.names[int(box.cls)],
                "confidence": round(float(box.conf), 2),
            }
        )
        
    # Collect detections from pipe model
    for box in results_pipe[0].boxes:
        detected.append(
            {
                "label": pipe_model.names[int(box.cls)],
                "confidence": round(float(box.conf), 2),
            }
        )

    _, buffer = cv2.imencode(".jpg", annotated)
    content_file = ContentFile(buffer.tobytes(), name=f"{uuid.uuid4()}.jpg")

    return content_file, detected
