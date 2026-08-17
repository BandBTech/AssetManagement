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

    # Keep only 1 object with the highest confidence score
    if detected:
        detected = max(detected, key=lambda x: x["confidence"])
    else:
        detected = None

    _, buffer = cv2.imencode(".jpg", annotated)
    content_file = ContentFile(buffer.tobytes(), name=f"{uuid.uuid4()}.jpg")

    return content_file, detected


import math
from .models import Asset


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Returns distance in meters between two lat/lng coordinates.
    """
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return R * c


def find_or_create_asset_within_radius(coordinates: dict, label_val: str, defaults: dict, radius_meters: float = 1.0):
    """
    Looks for an existing asset with matching label within radius_meters of coordinates.
    Returns (asset, created_boolean).
    """
    try:
        target_lat = float(coordinates.get("lat"))
        target_lng = float(coordinates.get("lng"))
    except (TypeError, ValueError):
        target_lat, target_lng = None, None

    if target_lat is not None and target_lng is not None and label_val:
        candidates = Asset.objects.filter(label=label_val)
        closest_asset = None
        min_distance = float("inf")

        for candidate in candidates:
            cand_coords = candidate.coordinates or {}
            try:
                cand_lat = float(cand_coords.get("lat"))
                cand_lng = float(cand_coords.get("lng"))
                dist = haversine_distance(target_lat, target_lng, cand_lat, cand_lng)
                if dist <= radius_meters and dist < min_distance:
                    min_distance = dist
                    closest_asset = candidate
            except (TypeError, ValueError):
                continue

        if closest_asset:
            return closest_asset, False

    new_asset = Asset.objects.create(
        coordinates=coordinates,
        label=label_val,
        **defaults
    )
    return new_asset, True

