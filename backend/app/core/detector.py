import os
import sys
import numpy as np
import torch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
YOlOV5_PATH = os.path.join(BASE_DIR, 'yolov5')
if os.path.exists(YOlOV5_PATH):
    sys.path.insert(0, YOlOV5_PATH)


class YOLOv5Detector:
    def __init__(self, weights_path, conf=0.5, iou=0.45, img_size=640, device='', target_classes=None):
        self.weights_path = weights_path
        self.conf = conf
        self.iou = iou
        self.img_size = img_size
        self.device = device
        self.target_classes = target_classes

        cache_path = os.path.join(os.path.expanduser('~'), '.cache', 'torch', 'hub', 'ultralytics_yolov5_master')
        
        try:
            if os.path.exists(YOlOV5_PATH):
                self.model = torch.hub.load(YOlOV5_PATH, 'custom', path=weights_path, source='local', _verbose=False)
            elif os.path.exists(cache_path):
                sys.path.insert(0, cache_path)
                from models.experimental import attempt_load
                from models.common import AutoShape
                self.model = AutoShape(attempt_load(weights_path, device=device if device else ('cuda' if torch.cuda.is_available() else 'cpu')))
            else:
                self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=weights_path, source='local', _verbose=False)
        except Exception as e:
            print(f'加载模型失败，尝试备用方法: {e}')
            try:
                self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=weights_path, source='local', _verbose=False, skip_validation=True)
            except Exception as e2:
                print(f'备用方法也失败: {e2}')
                raise e

        self.model.conf = conf
        self.model.iou = iou

        if target_classes:
            self.model.classes = list(target_classes.keys())

        dummy_image = np.zeros((img_size, img_size, 3), dtype=np.uint8)
        self.model(dummy_image, size=img_size)

        print(f'YOLOv5模型加载完成: {weights_path}')

    def detect(self, frame):
        results = self.model(frame, size=self.img_size)
        preds = results.xyxy[0].cpu().numpy()

        detections = []
        for pred in preds:
            x1, y1, x2, y2, confidence, class_id = pred
            class_id = int(class_id)
            class_name = self.target_classes.get(class_id, str(class_id)) if self.target_classes else str(class_id)

            detections.append({
                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                'confidence': float(confidence),
                'class_id': class_id,
                'class_name': class_name
            })

        return detections

    def detect_for_tracker(self, frame):
        detections = self.detect(frame)

        if not detections:
            return np.array([]), np.array([]), np.array([])

        bboxes = np.array([d['bbox'] for d in detections])
        confidences = np.array([d['confidence'] for d in detections])
        class_ids = np.array([d['class_id'] for d in detections])

        return bboxes, confidences, class_ids
