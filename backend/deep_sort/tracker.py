import numpy as np
from .kalman_filter import KalmanFilter
from .track import Track
from .linear_assignment import linear_assignment, iou_distance, min_cost_distance


class Tracker:
    def __init__(self, max_iou_distance=0.7, max_age=30, n_init=3, nn_budget=100):
        self.max_iou_distance = max_iou_distance
        self.max_age = max_age
        self.n_init = n_init
        self.nn_budget = nn_budget
        
        self.kalman = KalmanFilter()
        self.tracks = []
        self._next_id = 1
        self._max_id_used = 0  # 记录已使用的最大ID
    
    def predict(self):
        for track in self.tracks:
            track.predict(self.kalman)
    
    def increment_ages(self):
        for track in self.tracks:
            track.increment_age()
            track.mark_missed()
    
    def update(self, detections):
        matches, unmatched_tracks, unmatched_detections = self._match(detections)
        
        for track_idx, detection_idx in matches:
            self.tracks[track_idx].update(self.kalman, detections[detection_idx])
        
        for track_idx in unmatched_tracks:
            self.tracks[track_idx].mark_missed()
        
        for detection_idx in unmatched_detections:
            self._init_track(detections[detection_idx])
        
        self.tracks = [t for t in self.tracks if not t.is_deleted()]
    
    def _match(self, detections):
        if len(self.tracks) == 0:
            return [], [], list(range(len(detections)))
        
        confirmed_tracks = [i for i, t in enumerate(self.tracks) if t.is_confirmed()]
        unconfirmed_tracks = [i for i, t in enumerate(self.tracks) if not t.is_confirmed()]
        
        matches_a, unmatched_tracks_a, unmatched_detections = self._match_by_iou(
            confirmed_tracks, detections
        )
        
        matches_b, unmatched_tracks_b, unmatched_detections = self._match_by_iou(
            unconfirmed_tracks, detections, unmatched_detections, iou_threshold=0.3
        )
        
        matches = matches_a + matches_b
        unmatched_tracks = unmatched_tracks_a + unmatched_tracks_b
        
        return matches, unmatched_tracks, unmatched_detections
    
    def _match_by_iou(self, track_indices, detections, detection_indices=None, iou_threshold=None):
        if detection_indices is None:
            detection_indices = list(range(len(detections)))
        
        if len(track_indices) == 0 or len(detection_indices) == 0:
            return [], track_indices, detection_indices
        
        cost_matrix = iou_distance(
            [self.tracks[i] for i in track_indices],
            [detections[i] for i in detection_indices]
        )
        
        threshold = iou_threshold if iou_threshold is not None else self.max_iou_distance
        indices = linear_assignment(cost_matrix, threshold)
        
        matches = []
        unmatched_tracks = list(track_indices)
        unmatched_detections = list(detection_indices)
        
        for row, col in indices:
            track_idx = track_indices[row]
            detection_idx = detection_indices[col]
            if cost_matrix[row, col] <= threshold:
                matches.append((track_idx, detection_idx))
                unmatched_tracks.remove(track_idx)
                unmatched_detections.remove(detection_idx)
        
        return matches, unmatched_tracks, unmatched_detections
    
    def _init_track(self, detection):
        mean, covariance = self.kalman.initiate(detection.to_xyah())
        self._next_id = self._max_id_used + 1  # 从最大 ID+1 开始
        self.tracks.append(Track(
            mean, covariance, self._next_id, self.n_init, self.max_age,
            detection.class_id, detection.confidence
        ))
        self._max_id_used = max(self._max_id_used, self._next_id)
        self._next_id += 1
