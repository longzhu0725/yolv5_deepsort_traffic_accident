import time
import threading
import cv2
from flask import Flask, current_app

from ..config import Config
from ..extensions import db
from ..models.camera import Camera
from .detector import YOLOv5Detector
from .pipeline import ProcessingPipeline


class PipelineManager:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if PipelineManager._initialized:
            return
        PipelineManager._initialized = True
        
        self.detector = None
        self.pipelines = {}
        self.frame_buffer = {}
        self.buffer_lock = threading.Lock()
        self.app = None
        self.socketio = None

    @classmethod
    def get_instance(cls):
        return cls()

    def init_app(self, app, socketio):
        self.app = app
        self.socketio = socketio

        with app.app_context():
            Camera.query.update({'status': 'offline'})
            db.session.commit()
            print('已重置所有摄像头状态为离线')

        if self.detector is None:
            self.detector = YOLOv5Detector(
                weights_path=app.config['YOLO_WEIGHTS'],
                conf=app.config['YOLO_CONF'],
                iou=app.config['YOLO_IOU'],
                img_size=app.config['YOLO_IMG_SIZE'],
                device=app.config['YOLO_DEVICE'],
                target_classes=app.config['TARGET_CLASSES']
            )
            print(f'模型加载完成')

    def start_camera(self, camera_id):
        print(f'[PipelineManager] 尝试启动摄像头 {camera_id}', flush=True)
        print(f'[PipelineManager] 当前pipelines: {list(self.pipelines.keys())}', flush=True)
        
        if camera_id in self.pipelines:
            return False, "摄像头已在运行"

        if self.app is None:
            return False, "系统未初始化，请重启服务"

        with self.app.app_context():
            camera = db.session.get(Camera, camera_id)
            if not camera:
                return False, "摄像头不存在"

            camera_config = camera.to_dict()
            print(f'[PipelineManager] 摄像头配置: {camera_config}', flush=True)

        print(f'[PipelineManager] 创建ProcessingPipeline...', flush=True)
        pipeline = ProcessingPipeline(
            camera_id=camera_id,
            camera_config=camera_config,
            detector=self.detector,
            socketio=self.socketio,
            app=self.app,
            frame_buffer=self.frame_buffer,
            buffer_lock=self.buffer_lock
        )

        print(f'[PipelineManager] 启动Pipeline...', flush=True)
        pipeline.start()
        self.pipelines[camera_id] = pipeline
        print(f'[PipelineManager] 摄像头 {camera_id} 已添加到pipelines', flush=True)

        return True, "启动成功"

    def stop_camera(self, camera_id):
        if camera_id in self.pipelines:
            pipeline = self.pipelines[camera_id]
            pipeline.stop()
            del self.pipelines[camera_id]

            with self.buffer_lock:
                if camera_id in self.frame_buffer:
                    del self.frame_buffer[camera_id]

        if self.app:
            with self.app.app_context():
                camera = db.session.get(Camera, camera_id)
                if camera:
                    camera.status = 'offline'
                    db.session.commit()

        return True, "停止成功"

    def generate_mjpeg(self, camera_id):
        while True:
            with self.buffer_lock:
                frame = self.frame_buffer.get(camera_id)

            if frame is not None:
                _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' +
                       jpeg.tobytes() + b'\r\n')

            time.sleep(0.03)

    def get_camera_status(self, camera_id):
        if camera_id not in self.pipelines:
            return None

        pipeline = self.pipelines[camera_id]
        return {
            'is_running': pipeline.is_running,
            'fps': pipeline.fps
        }

    def stop_all(self):
        for camera_id in list(self.pipelines.keys()):
            self.stop_camera(camera_id)
