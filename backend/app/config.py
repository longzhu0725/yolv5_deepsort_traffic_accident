import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    SECRET_KEY = 'traffic-accident-secret-key-2025'
    JWT_SECRET = 'jwt-secret-key-2025'
    JWT_EXPIRE_HOURS = 8

    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "traffic_accident.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SNAPSHOT_FOLDER = os.path.join(BASE_DIR, 'static', 'snapshots')

    YOLO_WEIGHTS = os.path.join(BASE_DIR, 'weights', 'yolov5s.pt')
    YOLO_CONF = 0.5
    YOLO_IOU = 0.45
    YOLO_IMG_SIZE = 640
    YOLO_DEVICE = ''

    DEEPSORT_WEIGHTS = os.path.join(BASE_DIR, 'weights', 'ckpt.t7') if os.path.exists(os.path.join(BASE_DIR, 'weights', 'ckpt.t7')) else None
    DEEPSORT_MAX_AGE = 50
    DEEPSORT_N_INIT = 1
    DEEPSORT_MAX_COSINE_DIST = 0.7

    ACCIDENT_WEIGHT_COLLISION = 0.5
    ACCIDENT_WEIGHT_SPEED = 0.5
    ACCIDENT_THRESHOLD = 0.6
    ACCIDENT_COLLISION_IOU = 0.3
    ACCIDENT_COLLISION_FRAMES = 3
    ACCIDENT_SPEED_DROP = 0.7
    ACCIDENT_SPEED_WINDOW = 5
    ACCIDENT_COOLDOWN_SECONDS = 30
    ACCIDENT_COOLDOWN_DISTANCE = 100

    TARGET_CLASSES = {0: 'person', 1: 'bicycle', 2: 'car',
                      3: 'motorcycle', 5: 'bus', 7: 'truck'}
