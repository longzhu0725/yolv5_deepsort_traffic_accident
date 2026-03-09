import os
import sys
from dataclasses import dataclass, field
from collections import deque
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


@dataclass
class TrackInfo:
    track_id: int
    bbox: list
    center: tuple
    class_id: int
    class_name: str
    confidence: float
    trajectory: deque = field(default_factory=lambda: deque(maxlen=50))
    velocity: float = 0.0
    velocity_history: deque = field(default_factory=lambda: deque(maxlen=30))


class DeepSORTTracker:
    def __init__(self, reid_weights, max_age=30, n_init=3, max_cosine_distance=0.2, nn_budget=100):
        self.reid_weights = reid_weights
        self.max_age = max_age
        self.n_init = n_init
        self.max_cosine_distance = max_cosine_distance
        self.nn_budget = nn_budget

        self.tracker = None
        self.tracks_info = {}
        self._simple_next_id = 1
        self._simple_missed = {}
        self._simple_iou_threshold = 0.3

        self._init_tracker()

    def _init_tracker(self):
        try:
            from deep_sort.deep_sort import DeepSort
            self.tracker = DeepSort(
                model_path=self.reid_weights,
                max_age=self.max_age,
                n_init=self.n_init,
                max_iou_distance=self.max_cosine_distance
            )
            print(f'DeepSORT跟踪器初始化完成')
        except ImportError as e:
            print(f'DeepSORT模块导入失败: {e}')
            print('使用简化跟踪器（仅基于IoU匹配）')
            self.tracker = None
        except Exception as e:
            print(f'DeepSORT初始化异常: {e}')
            print('使用简化跟踪器')
            self.tracker = None

    def update(self, bboxes, confidences, class_ids, frame, class_names=None):
        if self.tracker is not None:
            if len(bboxes) == 0:
                self._cleanup_tracks([])
                return []
            return self._update_with_deepsort(bboxes, confidences, class_ids, frame, class_names)
        else:
            return self._update_simple(bboxes, confidences, class_ids, class_names)

    def _update_with_deepsort(self, bboxes, confidences, class_ids, frame, class_names):
        tlwhs = self._bbox_xyxy_to_tlwh(bboxes)

        outputs = self.tracker.update(tlwhs, confidences, class_ids, frame)

        active_ids = []
        tracks = []

        for output in outputs:
            x1, y1, x2, y2, track_id, class_id, conf = output
            track_id = int(track_id)
            class_id = int(class_id)
            active_ids.append(track_id)

            center = ((x1 + x2) // 2, (y1 + y2) // 2)

            if track_id not in self.tracks_info:
                class_name = class_names.get(class_id, str(class_id)) if class_names else str(class_id)
                self.tracks_info[track_id] = TrackInfo(
                    track_id=track_id,
                    bbox=[x1, y1, x2, y2],
                    center=center,
                    class_id=class_id,
                    class_name=class_name,
                    confidence=conf
                )
            else:
                prev_center = self.tracks_info[track_id].center
                velocity = np.sqrt((center[0] - prev_center[0]) ** 2 + (center[1] - prev_center[1]) ** 2)

                self.tracks_info[track_id].bbox = [x1, y1, x2, y2]
                self.tracks_info[track_id].center = center
                self.tracks_info[track_id].confidence = conf
                self.tracks_info[track_id].velocity = velocity
                self.tracks_info[track_id].velocity_history.append(velocity)

            self.tracks_info[track_id].trajectory.append(center)
            tracks.append(self.tracks_info[track_id])

        self._cleanup_tracks(active_ids)
        return tracks

    def _update_simple(self, bboxes, confidences, class_ids, class_names):
        bboxes = np.asarray(bboxes)
        confidences = np.asarray(confidences)
        class_ids = np.asarray(class_ids)

        if len(bboxes) == 0:
            for tid in list(self._simple_missed.keys()):
                self._simple_missed[tid] = self._simple_missed.get(tid, 0) + 1
                if self._simple_missed[tid] > self.max_age:
                    self._simple_missed.pop(tid, None)
                    self.tracks_info.pop(tid, None)
            return []

        det_to_track = {}
        candidate_pairs = []

        for det_idx, (bbox, cls_id) in enumerate(zip(bboxes, class_ids)):
            cls_id = int(cls_id)
            for tid, track in self.tracks_info.items():
                if int(track.class_id) != cls_id:
                    continue
                iou = self._compute_iou_xyxy(track.bbox, bbox)
                if iou >= self._simple_iou_threshold:
                    candidate_pairs.append((iou, tid, det_idx))

        candidate_pairs.sort(key=lambda x: x[0], reverse=True)

        used_tracks = set()
        used_dets = set()
        for _, tid, det_idx in candidate_pairs:
            if tid in used_tracks or det_idx in used_dets:
                continue
            det_to_track[det_idx] = tid
            used_tracks.add(tid)
            used_dets.add(det_idx)

        tracks = []

        for i, (bbox, conf, cls_id) in enumerate(zip(bboxes, confidences, class_ids)):
            x1, y1, x2, y2 = bbox
            center = ((x1 + x2) // 2, (y1 + y2) // 2)
            cls_id = int(cls_id)

            if i in det_to_track:
                track_id = det_to_track[i]
            else:
                track_id = self._simple_next_id
                self._simple_next_id += 1

            class_name = class_names.get(cls_id, str(cls_id)) if class_names else str(cls_id)

            if track_id not in self.tracks_info:
                track_info = TrackInfo(
                    track_id=track_id,
                    bbox=[x1, y1, x2, y2],
                    center=center,
                    class_id=cls_id,
                    class_name=class_name,
                    confidence=float(conf)
                )
                track_info.trajectory.append(center)
                self.tracks_info[track_id] = track_info
            else:
                track_info = self.tracks_info[track_id]
                prev_center = track_info.center
                velocity = np.sqrt((center[0] - prev_center[0]) ** 2 + (center[1] - prev_center[1]) ** 2)
                track_info.bbox = [x1, y1, x2, y2]
                track_info.center = center
                track_info.class_id = cls_id
                track_info.class_name = class_name
                track_info.confidence = float(conf)
                track_info.velocity = velocity
                track_info.velocity_history.append(velocity)
                track_info.trajectory.append(center)

            self._simple_missed[track_id] = 0
            tracks.append(track_info)

        active_track_ids = set(det_to_track.values()) | {t.track_id for t in tracks}
        for tid in list(self.tracks_info.keys()):
            if tid in active_track_ids:
                continue
            self._simple_missed[tid] = self._simple_missed.get(tid, 0) + 1
            if self._simple_missed[tid] > self.max_age:
                self._simple_missed.pop(tid, None)
                self.tracks_info.pop(tid, None)

        return tracks

    def _cleanup_tracks(self, active_ids):
        inactive_ids = [tid for tid in self.tracks_info.keys() if tid not in active_ids]
        for tid in inactive_ids:
            del self.tracks_info[tid]

    def _bbox_xyxy_to_tlwh(self, bboxes):
        if len(bboxes) == 0:
            return np.array([])

        tlwh = np.zeros_like(bboxes, dtype=np.float32)
        tlwh[:, 0] = bboxes[:, 0]
        tlwh[:, 1] = bboxes[:, 1]
        tlwh[:, 2] = np.maximum(1.0, bboxes[:, 2] - bboxes[:, 0])
        tlwh[:, 3] = np.maximum(1.0, bboxes[:, 3] - bboxes[:, 1])
        return tlwh

    def _compute_iou_xyxy(self, box_a, box_b):
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b

        inter_x1 = max(ax1, bx1)
        inter_y1 = max(ay1, by1)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)

        if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
            return 0.0

        inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
        area_a = (ax2 - ax1) * (ay2 - ay1)
        area_b = (bx2 - bx1) * (by2 - by1)
        union = area_a + area_b - inter_area
        if union <= 0:
            return 0.0
        return float(inter_area / union)

    def reset(self):
        self.tracks_info = {}
        self._simple_missed = {}
        self._simple_next_id = 1
        if self.tracker is not None:
            self._init_tracker()
