from flask import Blueprint
from flask import Response
from ..core.pipeline_manager import PipelineManager

video_bp = Blueprint('video', __name__, url_prefix='/api/video')


@video_bp.route('/stream/<int:camera_id>')
def stream(camera_id):
    manager = PipelineManager.get_instance()
    return Response(
        manager.generate_mjpeg(camera_id),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )
