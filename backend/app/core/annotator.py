import cv2
import numpy as np
from datetime import datetime


class FrameAnnotator:
    @staticmethod
    def draw_tracks(frame, tracks):
        result = frame.copy()
        for track in tracks:
            color = FrameAnnotator.get_color_by_id(track.track_id)

            x1, y1, x2, y2 = [int(v) for v in track.bbox]
            cv2.rectangle(result, (x1, y1), (x2, y2), color, 2)

            label = f"ID:{track.track_id} {track.class_name} {track.confidence:.2f}"
            cv2.putText(result, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            if len(track.trajectory) > 1:
                points = np.array(list(track.trajectory), dtype=np.int32)
                cv2.polylines(result, [points], False, color, 1)

        return result

    @staticmethod
    def draw_accident_marker(frame, accident):
        result = frame.copy()
        x, y = [int(v) for v in accident.pixel_position]

        cv2.circle(result, (x, y), 30, (0, 0, 255), 3)
        cv2.circle(result, (x, y), 5, (0, 0, 255), -1)

        overlay = result.copy()
        cv2.rectangle(overlay, (x - 80, y - 60), (x + 80, y - 20), (0, 0, 200), -1)
        cv2.addWeighted(overlay, 0.6, result, 0.4, 0, result)

        severity_text = {'normal': '一般', 'serious': '较重', 'critical': '严重'}
        text = f"ACCIDENT {severity_text.get(accident.severity, accident.severity)}"
        cv2.putText(result, text, (x - 75, y - 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        return result

    @staticmethod
    def draw_info(frame, fps, track_count, camera_name):
        result = frame.copy()

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        info_text = f"FPS: {fps:.1f} | Tracks: {track_count} | {camera_name} | {now}"

        cv2.rectangle(result, (0, 0), (len(info_text) * 10 + 20, 30), (0, 0, 0), -1)
        cv2.putText(result, info_text, (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        return result

    @staticmethod
    def annotate(frame, tracks, accidents, fps, track_count, camera_name):
        result = frame.copy()
        result = FrameAnnotator.draw_tracks(result, tracks)
        for acc in accidents:
            result = FrameAnnotator.draw_accident_marker(result, acc)
        result = FrameAnnotator.draw_info(result, fps, track_count, camera_name)
        return result

    @staticmethod
    def get_color_by_id(track_id):
        hue = (track_id * 37) % 180
        hsv = np.array([[[hue, 255, 255]]], dtype=np.uint8)
        bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        return tuple(map(int, bgr[0][0]))
