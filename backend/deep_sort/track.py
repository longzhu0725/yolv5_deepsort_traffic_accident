import numpy as np
from .kalman_filter import KalmanFilter


class TrackState:
    Tentative = 1
    Confirmed = 2
    Deleted = 3


class Track:
    def __init__(self, mean, covariance, track_id, n_init, max_age, class_id=-1, confidence=0.0):
        self.mean = mean
        self.covariance = covariance
        self.track_id = track_id
        self.hits = 1
        self.age = 1
        self.time_since_update = 0
        self.state = TrackState.Tentative
        self.n_init = n_init
        self.max_age = max_age
        self.class_id = class_id
        self.confidence = confidence
        self.features = []
    
    def to_tlwh(self):
        ret = self.mean[:4].copy()
        ret[2] *= ret[3]
        ret[:2] -= ret[2:] / 2
        return ret
    
    def to_tlbr(self):
        ret = self.to_tlwh()
        ret[2:] += ret[:2]
        return ret
    
    def predict(self, kalman):
        self.mean, self.covariance = kalman.predict(self.mean, self.covariance)
        self.age += 1
        self.time_since_update += 1
    
    def update(self, kalman, detection):
        self.mean, self.covariance = kalman.update(
            self.mean, self.covariance, detection.to_xyah()
        )
        self.hits += 1
        self.time_since_update = 0
        self.confidence = detection.confidence
        if self.state == TrackState.Tentative and self.hits >= self.n_init:
            self.state = TrackState.Confirmed
    
    def mark_missed(self):
        if self.state == TrackState.Tentative and self.time_since_update > 3:
            self.state = TrackState.Deleted
        elif self.state == TrackState.Confirmed and self.time_since_update > self.max_age:
            self.state = TrackState.Deleted
    
    def is_tentative(self):
        return self.state == TrackState.Tentative
    
    def is_confirmed(self):
        return self.state == TrackState.Confirmed
    
    def is_deleted(self):
        return self.state == TrackState.Deleted
    
    def increment_age(self):
        self.age += 1
