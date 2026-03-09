from datetime import datetime
from ..extensions import db


class Camera(db.Model):
    __tablename__ = 'cameras'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    camera_code = db.Column(db.String(50), nullable=False, unique=True)
    stream_url = db.Column(db.String(500), nullable=False)
    stream_type = db.Column(db.String(20), default='file')
    location_lat = db.Column(db.Float, default=None)
    location_lng = db.Column(db.Float, default=None)
    location_desc = db.Column(db.String(200), default=None)
    homography_data = db.Column(db.Text, default=None)
    status = db.Column(db.String(20), default='offline')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'camera_code': self.camera_code,
            'stream_url': self.stream_url,
            'stream_type': self.stream_type,
            'location_lat': self.location_lat,
            'location_lng': self.location_lng,
            'location_desc': self.location_desc,
            'homography_data': self.homography_data,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def to_detail_dict(self):
        result = self.to_dict()
        result['has_calibration'] = self.homography_data is not None and len(self.homography_data) > 0
        return result
