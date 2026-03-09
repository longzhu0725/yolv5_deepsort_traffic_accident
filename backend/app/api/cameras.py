from flask import Blueprint, request
from flask import Response
from ..utils.response import success, error
from ..utils.auth_decorator import login_required
from ..models.camera import Camera
from ..extensions import db
from ..core.pipeline_manager import PipelineManager
import sys

cameras_bp = Blueprint('cameras', __name__, url_prefix='/api/cameras')


@cameras_bp.route('', methods=['GET'])
@login_required
def get_cameras():
    cameras = Camera.query.all()
    return success([c.to_detail_dict() for c in cameras])


@cameras_bp.route('', methods=['POST'])
@login_required
def create_camera():
    data = request.get_json()
    if not data:
        return error('请求数据不能为空', 400)

    name = data.get('name')
    camera_code = data.get('camera_code')
    stream_url = data.get('stream_url')

    if not name or not camera_code or not stream_url:
        return error('名称、编号和视频源不能为空', 400)

    existing = Camera.query.filter_by(camera_code=camera_code).first()
    if existing:
        return error('摄像头编号已存在', 400)

    camera = Camera(
        name=name,
        camera_code=camera_code,
        stream_url=stream_url,
        stream_type=data.get('stream_type', 'file'),
        location_lat=data.get('location_lat'),
        location_lng=data.get('location_lng'),
        location_desc=data.get('location_desc'),
        homography_data=data.get('homography_data')
    )

    db.session.add(camera)
    db.session.commit()

    return success({'id': camera.id}, '创建成功', 201)


@cameras_bp.route('/<int:camera_id>', methods=['PUT'])
@login_required
def update_camera(camera_id):
    camera = db.session.get(Camera, camera_id)
    if not camera:
        return error('摄像头不存在', 404)

    data = request.get_json()
    if not data:
        return error('请求数据不能为空', 400)

    if 'name' in data:
        camera.name = data['name']
    if 'camera_code' in data:
        existing = Camera.query.filter(
            Camera.camera_code == data['camera_code'],
            Camera.id != camera_id
        ).first()
        if existing:
            return error('摄像头编号已存在', 400)
        camera.camera_code = data['camera_code']
    if 'stream_url' in data:
        camera.stream_url = data['stream_url']
    if 'stream_type' in data:
        camera.stream_type = data['stream_type']
    if 'location_lat' in data:
        camera.location_lat = data['location_lat']
    if 'location_lng' in data:
        camera.location_lng = data['location_lng']
    if 'location_desc' in data:
        camera.location_desc = data['location_desc']
    if 'homography_data' in data:
        camera.homography_data = data['homography_data']

    db.session.commit()
    return success(message='更新成功')


@cameras_bp.route('/<int:camera_id>', methods=['DELETE'])
@login_required
def delete_camera(camera_id):
    camera = db.session.get(Camera, camera_id)
    if not camera:
        return error('摄像头不存在', 404)

    manager = PipelineManager.get_instance()
    if camera_id in manager.pipelines:
        manager.stop_camera(camera_id)

    db.session.delete(camera)
    db.session.commit()

    return success(message='删除成功')


@cameras_bp.route('/<int:camera_id>/start', methods=['POST'])
@login_required
def start_camera(camera_id):
    print(f'[API] ========== 开始启动摄像头 {camera_id} ==========', flush=True)
    camera = db.session.get(Camera, camera_id)
    if not camera:
        return error('摄像头不存在', 404)

    manager = PipelineManager.get_instance()
    print(f'[API] PipelineManager实例ID: {id(manager)}', flush=True)
    print(f'[API] manager.app: {manager.app}', flush=True)
    print(f'[API] manager.detector: {manager.detector}', flush=True)
    print(f'[API] manager.pipelines: {manager.pipelines}', flush=True)
    print(f'[API] _initialized: {PipelineManager._initialized}', flush=True)
    success_flag, message = manager.start_camera(camera_id)
    print(f'[API] 启动结果: success_flag={success_flag}, message={message}', flush=True)

    if success_flag:
        return success(message=message)
    else:
        return error(message, 400)


@cameras_bp.route('/<int:camera_id>/stop', methods=['POST'])
@login_required
def stop_camera(camera_id):
    manager = PipelineManager.get_instance()
    success_flag, message = manager.stop_camera(camera_id)

    if success_flag:
        return success(message=message)
    else:
        return error(message, 400)
