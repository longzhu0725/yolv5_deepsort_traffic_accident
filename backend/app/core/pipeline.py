import os
import time
import json
import threading
import cv2
from datetime import datetime

from ..config import Config
from ..extensions import db
from ..models.camera import Camera
from ..models.accident import Accident
from .tracker import DeepSORTTracker
from .accident_detector import AccidentDetector
from .coordinate_mapper import CoordinateMapper
from .annotator import FrameAnnotator


class ProcessingPipeline:
    def __init__(self, camera_id, camera_config, detector, socketio, app, frame_buffer, buffer_lock):
        self.camera_id = camera_id
        self.camera_config = camera_config
        self.detector = detector
        self.socketio = socketio
        self.app = app
        self.frame_buffer = frame_buffer
        self.buffer_lock = buffer_lock

        self.tracker = DeepSORTTracker(
            reid_weights=Config.DEEPSORT_WEIGHTS,
            max_age=Config.DEEPSORT_MAX_AGE,
            n_init=Config.DEEPSORT_N_INIT,
            max_cosine_distance=Config.DEEPSORT_MAX_COSINE_DIST
        )

        self.accident_detector = AccidentDetector(
            w_collision=Config.ACCIDENT_WEIGHT_COLLISION,
            w_speed=Config.ACCIDENT_WEIGHT_SPEED,
            threshold=Config.ACCIDENT_THRESHOLD,
            collision_iou=Config.ACCIDENT_COLLISION_IOU,
            collision_frames=Config.ACCIDENT_COLLISION_FRAMES,
            speed_drop_pct=Config.ACCIDENT_SPEED_DROP,
            speed_window=Config.ACCIDENT_SPEED_WINDOW,
            cooldown_seconds=Config.ACCIDENT_COOLDOWN_SECONDS,
            cooldown_distance=Config.ACCIDENT_COOLDOWN_DISTANCE
        )

        self.coordinate_mapper = None
        if camera_config.get('homography_data'):
            self.coordinate_mapper = CoordinateMapper.from_json_string(
                camera_config['homography_data']
            )

        self.is_running = False
        self.thread = None
        self.fps = 0.0
        self.cap = None

    def start(self):
        print(f'[Pipeline-{self.camera_id}] start()被调用', flush=True)
        self.is_running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(f'[Pipeline-{self.camera_id}] 线程已启动', flush=True)

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        if self.cap:
            self.cap.release()

    def _run(self):
        print(f'[Pipeline-{self.camera_id}] _run()开始执行', flush=True)
        print(f'[Pipeline-{self.camera_id}] 尝试打开视频源: {self.camera_config["stream_url"]}', flush=True)
        self.cap = cv2.VideoCapture(self.camera_config['stream_url'])
        if not self.cap.isOpened():
            self._set_camera_status('error')
            print(f'[Pipeline-{self.camera_id}] 无法打开视频源: {self.camera_config["stream_url"]}', flush=True)
            return

        print(f'[Pipeline-{self.camera_id}] 视频源已打开', flush=True)
        self._set_camera_status('online')
        frame_count = 0
        fps_timer = time.time()

        print(f'[Pipeline-{self.camera_id}] 开始处理视频流')

        while self.is_running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue

                bboxes, confs, cls_ids = self.detector.detect_for_tracker(frame)

                tracks = self.tracker.update(bboxes, confs, cls_ids, frame, Config.TARGET_CLASSES)

                accidents = self.accident_detector.analyze(tracks)

                for acc in accidents:
                    self._handle_accident(acc, frame)

                annotated = FrameAnnotator.annotate(
                    frame, tracks, accidents,
                    self.fps, len(tracks), self.camera_config['name']
                )

                with self.buffer_lock:
                    self.frame_buffer[self.camera_id] = annotated

                frame_count += 1
                if frame_count % 30 == 0:
                    elapsed = time.time() - fps_timer
                    self.fps = round(30.0 / elapsed, 1) if elapsed > 0 else 0
                    fps_timer = time.time()

            except Exception as e:
                print(f'[Pipeline-{self.camera_id}] Error: {e}')
                import traceback
                traceback.print_exc()
                continue

        if self.cap:
            self.cap.release()
        self._set_camera_status('offline')
        print(f'[Pipeline-{self.camera_id}] 停止处理')

    def _handle_accident(self, accident, frame):
        with self.app.app_context():
            filename = f'acc_{self.camera_id}_{int(accident.trigger_time)}.jpg'
            filepath = os.path.join(Config.SNAPSHOT_FOLDER, filename)

            annotated = FrameAnnotator.draw_accident_marker(frame.copy(), accident)
            cv2.imwrite(filepath, annotated)

            geo_lat, geo_lng, address = None, None, None
            
            if self.coordinate_mapper:
                result = self.coordinate_mapper.pixel_to_geo(
                    accident.pixel_position[0], accident.pixel_position[1])
                if result:
                    geo_lng, geo_lat = result
                    address = f'{geo_lng:.5f}, {geo_lat:.5f}'
            
            if geo_lat is None or geo_lng is None:
                geo_lat = self.camera_config.get('location_lat')
                geo_lng = self.camera_config.get('location_lng')
                if geo_lat and geo_lng:
                    address = self.camera_config.get('location_desc') or f'{geo_lng:.5f}, {geo_lat:.5f}'

            today = datetime.now().strftime('%Y%m%d')
            count = Accident.query.filter(
                Accident.accident_no.like(f'ACC-{today}-%')
            ).count()
            accident_no = f'ACC-{today}-{count + 1:03d}'

            involved_count = len(accident.involved_track_ids)
            if involved_count >= 3:
                accident_type = 'multi_vehicle'
            elif accident.score_collision > 0.7:
                accident_type = 'collision'
            else:
                accident_type = 'unknown'

            record = Accident(
                accident_no=accident_no,
                camera_id=self.camera_id,
                trigger_time=datetime.fromtimestamp(accident.trigger_time),
                pixel_x=accident.pixel_position[0],
                pixel_y=accident.pixel_position[1],
                geo_lat=geo_lat,
                geo_lng=geo_lng,
                address=address,
                severity=accident.severity,
                accident_type=accident_type,
                score_total=accident.score_total,
                score_collision=accident.score_collision,
                score_speed=accident.score_speed,
                involved_ids=json.dumps(accident.involved_track_ids),
                involved_count=involved_count,
                snapshot_path=f'snapshots/{filename}',
                status='pending'
            )
            db.session.add(record)
            db.session.commit()

            from ..models.accident import ACCIDENT_TYPES, SEVERITY_DESC
            type_desc = ACCIDENT_TYPES.get(accident_type, '交通事故')
            severity_desc = SEVERITY_DESC.get(accident.severity, '事故')

            self.socketio.emit('accident_alert', {
                'accident_id': record.id,
                'accident_no': record.accident_no,
                'camera_id': self.camera_id,
                'camera_name': self.camera_config['name'],
                'trigger_time': record.trigger_time.strftime('%Y-%m-%d %H:%M:%S'),
                'severity': accident.severity,
                'severity_desc': severity_desc,
                'accident_type': accident_type,
                'accident_type_desc': type_desc,
                'score_total': accident.score_total,
                'geo_lat': geo_lat,
                'geo_lng': geo_lng,
                'address': address,
                'snapshot_url': f'/static/snapshots/{filename}',
                'message': f'检测到{severity_desc}：{type_desc}'
            })

            print(f'[Pipeline-{self.camera_id}] 检测到事故: {accident_no}, 类型: {type_desc}, 严重程度: {severity_desc}')

    def _set_camera_status(self, status):
        with self.app.app_context():
            camera = db.session.get(Camera, self.camera_id)
            if camera:
                camera.status = status
                db.session.commit()
