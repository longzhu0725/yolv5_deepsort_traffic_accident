from datetime import datetime, timedelta
from flask import Blueprint, request
from sqlalchemy import func
from ..utils.response import success, error
from ..utils.auth_decorator import login_required
from ..models.accident import Accident, ACCIDENT_TYPES, SEVERITY_DESC
from ..models.camera import Camera
from ..extensions import db

accidents_bp = Blueprint('accidents', __name__, url_prefix='/api/accidents')


@accidents_bp.route('', methods=['GET'])
@login_required
def get_accidents():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    camera_id = request.args.get('camera_id', type=int)
    severity = request.args.get('severity')
    status = request.args.get('status')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    query = Accident.query

    if camera_id:
        query = query.filter(Accident.camera_id == camera_id)
    if severity:
        query = query.filter(Accident.severity == severity)
    if status:
        query = query.filter(Accident.status == status)
    if start_time:
        try:
            start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            start_dt = datetime.strptime(start_time, '%Y-%m-%d')
        query = query.filter(Accident.trigger_time >= start_dt)
    if end_time:
        try:
            end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            end_dt = datetime.strptime(end_time, '%Y-%m-%d')
        query = query.filter(Accident.trigger_time <= end_dt)

    query = query.order_by(Accident.trigger_time.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    items = [acc.to_dict() for acc in pagination.items]

    return success({
        'items': items,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


@accidents_bp.route('/<int:accident_id>', methods=['GET'])
@login_required
def get_accident(accident_id):
    accident = db.session.get(Accident, accident_id)
    if not accident:
        return error('事故记录不存在', 404)

    return success(accident.to_detail_dict())


@accidents_bp.route('/<int:accident_id>/status', methods=['PUT'])
@login_required
def update_accident_status(accident_id):
    accident = db.session.get(Accident, accident_id)
    if not accident:
        return error('事故记录不存在', 404)

    data = request.get_json()
    if not data:
        return error('请求数据不能为空', 400)

    new_status = data.get('status')
    if not new_status:
        return error('状态不能为空', 400)

    valid_transitions = {
        'pending': ['acknowledged'],
        'acknowledged': ['resolved'],
        'resolved': ['closed'],
        'closed': []
    }

    if new_status not in valid_transitions.get(accident.status, []):
        return error(f'无法从 {accident.status} 状态转换到 {new_status}', 400)

    accident.status = new_status
    db.session.commit()

    return success(message='状态更新成功')


@accidents_bp.route('/<int:accident_id>', methods=['PUT'])
@login_required
def update_accident(accident_id):
    accident = db.session.get(Accident, accident_id)
    if not accident:
        return error('事故记录不存在', 404)

    data = request.get_json()
    if not data:
        return error('请求数据不能为空', 400)

    if 'severity' in data:
        if data['severity'] not in ['normal', 'serious', 'critical']:
            return error('无效的严重程度', 400)
        accident.severity = data['severity']

    if 'accident_type' in data:
        if data['accident_type'] not in ACCIDENT_TYPES:
            return error('无效的事故类型', 400)
        accident.accident_type = data['accident_type']

    if 'address' in data:
        accident.address = data['address'][:300] if data['address'] else None

    if 'geo_lat' in data:
        accident.geo_lat = data['geo_lat']

    if 'geo_lng' in data:
        accident.geo_lng = data['geo_lng']

    if 'status' in data:
        valid_status = ['pending', 'acknowledged', 'resolved', 'closed']
        if data['status'] not in valid_status:
            return error('无效的状态', 400)
        accident.status = data['status']

    db.session.commit()
    return success(accident.to_detail_dict(), message='更新成功')


@accidents_bp.route('/<int:accident_id>', methods=['DELETE'])
@login_required
def delete_accident(accident_id):
    accident = db.session.get(Accident, accident_id)
    if not accident:
        return error('事故记录不存在', 404)

    import os
    if accident.snapshot_path:
        snapshot_full_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'static',
            accident.snapshot_path
        )
        if os.path.exists(snapshot_full_path):
            try:
                os.remove(snapshot_full_path)
            except Exception as e:
                print(f'删除截图文件失败: {e}')

    db.session.delete(accident)
    db.session.commit()

    return success(message='删除成功')
