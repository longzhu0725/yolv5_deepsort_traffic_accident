import time
from dataclasses import dataclass
import numpy as np


@dataclass
class AccidentEvent:
    involved_track_ids: list
    pixel_position: tuple
    score_total: float
    score_collision: float
    score_speed: float
    severity: str
    trigger_time: float


class AccidentDetector:
    def __init__(self, w_collision=0.5, w_speed=0.5, threshold=0.6,
                 collision_iou=0.3, collision_frames=3,
                 speed_drop_pct=0.7, speed_window=5,
                 cooldown_seconds=30, cooldown_distance=100):
        self.w_collision = w_collision
        self.w_speed = w_speed
        self.threshold = threshold
        self.collision_iou = collision_iou
        self.collision_frames = collision_frames
        self.speed_drop_pct = speed_drop_pct
        self.speed_window = speed_window
        self.cooldown_seconds = cooldown_seconds
        self.cooldown_distance = cooldown_distance

        self.collision_counter = {}
        self.recent_alerts = []

    def analyze(self, tracks):
        accidents = []

        for i in range(len(tracks)):
            for j in range(i + 1, len(tracks)):
                track_a = tracks[i]
                track_b = tracks[j]

                s_collision = self._check_collision(track_a, track_b)

                s_speed = max(
                    self._check_speed_anomaly(track_a),
                    self._check_speed_anomaly(track_b)
                )

                score = self.w_collision * s_collision + self.w_speed * s_speed

                if score >= self.threshold:
                    mid_x = (track_a.center[0] + track_b.center[0]) // 2
                    mid_y = (track_a.center[1] + track_b.center[1]) // 2

                    if not self._is_cooling(mid_x, mid_y):
                        severity = 'critical' if score >= 0.9 else 'serious' if score >= 0.75 else 'normal'
                        event = AccidentEvent(
                            involved_track_ids=[track_a.track_id, track_b.track_id],
                            pixel_position=(mid_x, mid_y),
                            score_total=round(score, 3),
                            score_collision=round(s_collision, 3),
                            score_speed=round(s_speed, 3),
                            severity=severity,
                            trigger_time=time.time()
                        )
                        accidents.append(event)
                        self.recent_alerts.append((time.time(), mid_x, mid_y))

        return accidents

    def _check_collision(self, track_a, track_b):
        iou = self._compute_iou(track_a.bbox, track_b.bbox)
        key = (min(track_a.track_id, track_b.track_id), max(track_a.track_id, track_b.track_id))

        if iou > self.collision_iou:
            self.collision_counter[key] = self.collision_counter.get(key, 0) + 1
            if self.collision_counter[key] >= self.collision_frames:
                return min(1.0, iou * 1.5)
        else:
            self.collision_counter[key] = 0

        return 0.0

    def _check_speed_anomaly(self, track):
        history = list(track.velocity_history)
        if len(history) < self.speed_window:
            return 0.0

        recent = history[-self.speed_window:]
        first_half = recent[:len(recent) // 2]
        second_half = recent[len(recent) // 2:]

        max_v = max(first_half) if first_half else 0
        min_v = min(second_half) if second_half else 0

        if max_v > 5.0:
            drop_ratio = (max_v - min_v) / max_v
            if drop_ratio >= self.speed_drop_pct:
                return min(1.0, drop_ratio)

        return 0.0

    def _is_cooling(self, x, y):
        now = time.time()
        self.recent_alerts = [(t, rx, ry) for t, rx, ry in self.recent_alerts
                              if now - t < self.cooldown_seconds]

        for t, rx, ry in self.recent_alerts:
            distance = np.sqrt((x - rx) ** 2 + (y - ry) ** 2)
            if distance < self.cooldown_distance:
                return True

        return False

    def _compute_iou(self, box_a, box_b):
        x1_a, y1_a, x2_a, y2_a = box_a
        x1_b, y1_b, x2_b, y2_b = box_b

        x1_inter = max(x1_a, x1_b)
        y1_inter = max(y1_a, y1_b)
        x2_inter = min(x2_a, x2_b)
        y2_inter = min(y2_a, y2_b)

        if x2_inter <= x1_inter or y2_inter <= y1_inter:
            return 0.0

        inter_area = (x2_inter - x1_inter) * (y2_inter - y1_inter)

        area_a = (x2_a - x1_a) * (y2_a - y1_a)
        area_b = (x2_b - x1_b) * (y2_b - y1_b)

        union_area = area_a + area_b - inter_area

        return inter_area / union_area if union_area > 0 else 0.0

    def reset(self):
        self.collision_counter = {}
        self.recent_alerts = []
