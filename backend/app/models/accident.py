import json
from datetime import datetime
from ..extensions import db


ACCIDENT_TYPES = {
    'collision': '车辆碰撞',
    'rear_end': '追尾事故',
    'side_impact': '侧面碰撞',
    'rollover': '翻车事故',
    'multi_vehicle': '多车事故',
    'unknown': '交通事故'
}

SEVERITY_DESC = {
    'normal': '一般事故',
    'serious': '严重事故',
    'critical': '重大事故'
}


class Accident(db.Model):
    __tablename__ = 'accidents'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    accident_no = db.Column(db.String(50), nullable=False, unique=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False)

    trigger_time = db.Column(db.DateTime, nullable=False)

    pixel_x = db.Column(db.Integer, default=None)
    pixel_y = db.Column(db.Integer, default=None)
    geo_lat = db.Column(db.Float, default=None)
    geo_lng = db.Column(db.Float, default=None)
    address = db.Column(db.String(300), default=None)

    severity = db.Column(db.String(20), default='normal')
    accident_type = db.Column(db.String(50), default='unknown')
    score_total = db.Column(db.Float, default=0)
    score_collision = db.Column(db.Float, default=0)
    score_speed = db.Column(db.Float, default=0)

    involved_ids = db.Column(db.Text, default=None)
    involved_count = db.Column(db.Integer, default=0)

    snapshot_path = db.Column(db.String(500), default=None)

    status = db.Column(db.String(20), default='pending')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    camera = db.relationship('Camera', backref=db.backref('accidents', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'accident_no': self.accident_no,
            'camera_id': self.camera_id,
            'camera_name': self.camera.name if self.camera else None,
            'trigger_time': self.trigger_time.strftime('%Y-%m-%d %H:%M:%S') if self.trigger_time else None,
            'severity': self.severity,
            'severity_desc': SEVERITY_DESC.get(self.severity, '未知'),
            'accident_type': self.accident_type,
            'accident_type_desc': ACCIDENT_TYPES.get(self.accident_type, '交通事故'),
            'score_total': self.score_total,
            'involved_count': self.involved_count,
            'status': self.status,
            'snapshot_url': f'/static/{self.snapshot_path}' if self.snapshot_path else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def to_detail_dict(self):
        result = self.to_dict()
        result.update({
            'pixel_x': self.pixel_x,
            'pixel_y': self.pixel_y,
            'geo_lat': self.geo_lat,
            'geo_lng': self.geo_lng,
            'address': self.address,
            'score_collision': self.score_collision,
            'score_speed': self.score_speed,
            'involved_ids': json.loads(self.involved_ids) if self.involved_ids else []
        })
        return result
