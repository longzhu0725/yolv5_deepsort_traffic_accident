import numpy as np
import torch

from .detection import Detection
from .tracker import Tracker


class DeepSort:
    def __init__(self, model_path, max_dist=0.2, min_confidence=0.3, 
                 nms_max_overlap=1.0, max_iou_distance=0.7, 
                 max_age=70, n_init=3, nn_budget=100, use_cuda=True):
        self.min_confidence = min_confidence
        self.nms_max_overlap = nms_max_overlap
        
        self.extractor = None
        self.use_cuda = use_cuda and torch.cuda.is_available()
        self.device = torch.device('cuda' if self.use_cuda else 'cpu')
        
        try:
            from .deep.reid import Extractor
            self.extractor = Extractor(model_path, use_cuda=self.use_cuda)
            print(f'DeepSORT ReID模型加载完成: {model_path}')
        except Exception as e:
            print(f'DeepSORT ReID模型加载失败: {e}')
            print('将使用仅外观特征匹配模式')
        
        self.tracker = Tracker(
            max_iou_distance=max_iou_distance,
            max_age=max_age,
            n_init=n_init,
            nn_budget=nn_budget
        )
    
    def update(self, bbox_xywh, confidences, classes, img):
        self.tracker.predict()
        
        if len(bbox_xywh) == 0:
            self.tracker.update([])
            return []
        
        detections = []
        
        if self.extractor is not None:
            features = self._get_features(bbox_xywh, img)
            for i, (bbox, conf, cls, feat) in enumerate(zip(bbox_xywh, confidences, classes, features)):
                if conf >= self.min_confidence:
                    det = Detection(bbox, conf, feat, cls)
                    detections.append(det)
        else:
            for i, (bbox, conf, cls) in enumerate(zip(bbox_xywh, confidences, classes)):
                if conf >= self.min_confidence:
                    det = Detection(bbox, conf, None, cls)
                    detections.append(det)
        
        self.tracker.update(detections)
        
        outputs = []
        for track in self.tracker.tracks:
            if track.time_since_update > 1:
                continue
            
            bbox = track.to_tlbr()
            outputs.append([
                bbox[0], bbox[1], bbox[2], bbox[3],
                track.track_id, track.class_id, track.confidence
            ])
        
        return np.array(outputs) if outputs else np.empty((0, 7))
    
    def _get_features(self, bbox_xywh, img):
        if self.extractor is None:
            return np.zeros((len(bbox_xywh), 128))
        
        crops = []
        for box in bbox_xywh:
            x, y, w, h = box.astype(int)
            x1 = max(0, x - w // 2)
            y1 = max(0, y - h // 2)
            x2 = min(img.shape[1], x + w // 2)
            y2 = min(img.shape[0], y + h // 2)
            crop = img[y1:y2, x1:x2]
            if crop.size > 0:
                crops.append(crop)
            else:
                crops.append(np.zeros((64, 64, 3), dtype=np.uint8))
        
        features = self.extractor(crops)
        return features
    
    def increment_ages(self):
        self.tracker.increment_ages()
