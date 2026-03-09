from datetime import datetime, timedelta
import random
from flask import Blueprint, request
from sqlalchemy import func
from ..utils.response import success
from ..utils.auth_decorator import login_required
from ..models.accident import Accident, ACCIDENT_TYPES
from ..models.camera import Camera
from ..extensions import db

stats_bp = Blueprint('stats', __name__, url_prefix='/api/statistics')


@stats_bp.route('/overview', methods=['GET'])
@login_required
def get_overview():
    today = datetime.now().date()

    today_count = Accident.query.filter(
        func.date(Accident.trigger_time) == today
    ).count()

    total_count = Accident.query.count()

    pending_count = Accident.query.filter(
        Accident.status.in_(['pending', 'acknowledged'])
    ).count()

    online_cameras = Camera.query.filter_by(status='online').count()
    total_cameras = Camera.query.count()

    return success({
        'today_count': today_count,
        'total_count': total_count,
        'pending_count': pending_count,
        'online_cameras': online_cameras,
        'total_cameras': total_cameras
    })


@stats_bp.route('/trend', methods=['GET'])
@login_required
def get_trend():
    days = request.args.get('days', 7, type=int)

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days - 1)

    results = db.session.query(
        func.date(Accident.trigger_time).label('date'),
        func.count(Accident.id).label('count')
    ).filter(
        func.date(Accident.trigger_time) >= start_date
    ).group_by(
        func.date(Accident.trigger_time)
    ).all()

    date_counts = {}
    for r in results:
        if r.date:
            date_str = r.date.strftime('%Y-%m-%d') if hasattr(r.date, 'strftime') else str(r.date)
            date_counts[date_str] = r.count

    labels = []
    values = []
    current_date = start_date
    while current_date <= end_date:
        labels.append(current_date.strftime('%m-%d'))
        date_str = current_date.strftime('%Y-%m-%d')
        values.append(date_counts.get(date_str, 0))
        current_date += timedelta(days=1)

    return success({
        'labels': labels,
        'values': values
    })


@stats_bp.route('/severity', methods=['GET'])
@login_required
def get_severity():
    results = db.session.query(
        Accident.severity,
        func.count(Accident.id).label('count')
    ).group_by(
        Accident.severity
    ).all()

    severity_names = {
        'normal': '一般',
        'serious': '较重',
        'critical': '严重'
    }

    data = []
    for r in results:
        data.append({
            'name': severity_names.get(r.severity, r.severity),
            'value': r.count
        })

    for severity in ['normal', 'serious', 'critical']:
        if not any(d['name'] == severity_names[severity] for d in data):
            data.append({
                'name': severity_names[severity],
                'value': 0
            })

    return success(data)


@stats_bp.route('/accident-types', methods=['GET'])
@login_required
def get_accident_types():
    results = db.session.query(
        Accident.accident_type,
        func.count(Accident.id).label('count')
    ).group_by(
        Accident.accident_type
    ).all()

    data = []
    for r in results:
        type_name = ACCIDENT_TYPES.get(r.accident_type, r.accident_type)
        data.append({
            'name': type_name,
            'value': r.count
        })

    for type_key, type_name in ACCIDENT_TYPES.items():
        if not any(d['name'] == type_name for d in data):
            data.append({
                'name': type_name,
                'value': 0
            })

    return success(data)


@stats_bp.route('/traffic-flow', methods=['GET'])
@login_required
def get_traffic_flow():
    hours = request.args.get('hours', 24, type=int)
    
    now = datetime.now()
    labels = []
    values = []
    
    for i in range(hours - 1, -1, -1):
        hour_time = now - timedelta(hours=i)
        labels.append(hour_time.strftime('%H:00'))
        base_flow = random.randint(50, 150)
        hour = hour_time.hour
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            base_flow = int(base_flow * 1.8)
        elif 0 <= hour <= 5:
            base_flow = int(base_flow * 0.3)
        values.append(base_flow)
    
    return success({
        'labels': labels,
        'values': values
    })


@stats_bp.route('/vehicle-types', methods=['GET'])
@login_required
def get_vehicle_types():
    data = [
        {'name': '小型车辆', 'value': random.randint(200, 500)},
        {'name': '中型车辆', 'value': random.randint(50, 150)},
        {'name': '大型车辆', 'value': random.randint(20, 80)},
        {'name': '摩托车', 'value': random.randint(10, 50)},
        {'name': '行人', 'value': random.randint(5, 30)}
    ]
    return success(data)


@stats_bp.route('/hourly-accidents', methods=['GET'])
@login_required
def get_hourly_accidents():
    results = db.session.query(
        func.strftime('%H', Accident.trigger_time).label('hour'),
        func.count(Accident.id).label('count')
    ).group_by(
        func.strftime('%H', Accident.trigger_time)
    ).all()
    
    hour_counts = {int(r.hour): r.count for r in results if r.hour}
    
    labels = []
    values = []
    for h in range(24):
        labels.append(f'{h:02d}:00')
        values.append(hour_counts.get(h, 0))
    
    return success({
        'labels': labels,
        'values': values
    })
