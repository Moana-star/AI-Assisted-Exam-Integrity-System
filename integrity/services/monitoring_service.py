"""Computer-vision adapters for observable examination events.

YOLO is optional in the academic prototype. When it is not installed or a
model path is not configured, the service returns an explicit unavailable
status so callers can route the event to manual review.
"""
import cv2
import numpy as np


def detect_faces(image_bytes):
    image = cv2.imdecode(np.frombuffer(image_bytes or b'', dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    if image is None:
        return {'status': 'inconclusive', 'face_count': 0, 'message': 'Image is not readable.'}
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = detector.detectMultiScale(image, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
    count = len(faces)
    return {'status': 'ok' if count == 1 else 'review', 'face_count': count, 'message': 'One face detected.' if count == 1 else ('No face detected.' if count == 0 else 'Multiple faces detected.')}


def detect_objects(image_bytes, model_path=None, classes=None):
    if not model_path:
        return {'status': 'unavailable', 'detections': [], 'message': 'No YOLO model is configured; manual monitoring remains available.'}
    try:
        from ultralytics import YOLO
        image = cv2.imdecode(np.frombuffer(image_bytes or b'', dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None: return {'status': 'inconclusive', 'detections': [], 'message': 'Image is not readable.'}
        result = YOLO(model_path)(image, verbose=False)[0]
        detections = []
        for box in result.boxes:
            label = result.names[int(box.cls[0])]
            confidence = float(box.conf[0])
            if not classes or label in classes: detections.append({'class': label, 'confidence': confidence})
        return {'status': 'ok', 'detections': detections, 'message': f'{len(detections)} configured object(s) detected.'}
    except ImportError:
        return {'status': 'unavailable', 'detections': [], 'message': 'Install ultralytics and configure a YOLO model to enable object detection.'}
