import os
from flask import Flask
from flask_cors import CORS
from .config import Config
from .extensions import db, socketio
from .models.user import User
from .models.camera import Camera
from .models.accident import Accident


def create_app():
    static_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static')
    app = Flask(__name__, static_folder=static_folder)
    app.config.from_object(Config)

    CORS(app)

    db.init_app(app)
    socketio.init_app(app)

    from .api.auth import auth_bp
    from .api.cameras import cameras_bp
    from .api.accidents import accidents_bp
    from .api.statistics import stats_bp
    from .api.video import video_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(cameras_bp)
    app.register_blueprint(accidents_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(video_bp)

    from .sockets.events import register_socket_events
    register_socket_events(socketio)

    snapshot_folder = Config.SNAPSHOT_FOLDER
    if not os.path.exists(snapshot_folder):
        os.makedirs(snapshot_folder)

    with app.app_context():
        db.create_all()

    return app
