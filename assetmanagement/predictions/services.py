import cv2
import numpy as np
from django.core.files.base import ContentFile
import uuid

# Lazy load YOLO to avoid import issues during migration
model = None


def _get_model():
    global model
    if model is None:
        from ultralytics import YOLO

        model = YOLO("best.pt")
    return model


def run_yolo_and_annotate(image_file):
    """
    Takes Django InMemoryUploadedFile.
    Returns (annotated_image_as_ContentFile, detected_objects_list)
    """
    yolo_model = _get_model()

    image_bytes = np.frombuffer(image_file.read(), np.uint8)
    image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Could not decode image. Check file format.")  # ← add this

    results = yolo_model(image, conf=0.6)
    annotated = results[0].plot()

    detected = []
    for box in results[0].boxes:
        detected.append(
            {
                "label": yolo_model.names[int(box.cls)],
                "confidence": round(float(box.conf), 2),
            }
        )

    _, buffer = cv2.imencode(".jpg", annotated)
    content_file = ContentFile(buffer.tobytes(), name=f"{uuid.uuid4()}.jpg")

    return content_file, detected
