import json
import numpy as np
import cv2


class CoordinateMapper:
    def __init__(self, calibration_data):
        src = np.float32(calibration_data['src_points'])
        dst = np.float32(calibration_data['dst_points'])
        self.H, _ = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)

    @classmethod
    def from_json_string(cls, json_str):
        if not json_str:
            return None
        try:
            calibration_data = json.loads(json_str)
            if 'src_points' not in calibration_data or 'dst_points' not in calibration_data:
                return None
            return cls(calibration_data)
        except (json.JSONDecodeError, KeyError):
            return None

    def pixel_to_geo(self, px, py):
        if self.H is None:
            return None

        point = np.array([[[px, py]]], dtype=np.float32)
        result = cv2.perspectiveTransform(point, self.H)
        lng, lat = result[0][0]
        return (round(lng, 7), round(lat, 7))
