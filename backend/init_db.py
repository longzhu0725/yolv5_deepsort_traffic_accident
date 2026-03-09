import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.camera import Camera
from werkzeug.security import generate_password_hash


def init_database():
    app = create_app()

    with app.app_context():
        db.create_all()

        if User.query.count() == 0:
            admin = User(username='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            print('创建管理员账户: admin / admin123')

        if Camera.query.count() == 0:
            camera1 = Camera(
                name='测试路口A',
                camera_code='CAM-001',
                stream_url='./data/test_videos/accident1.mp4',
                stream_type='file',
                location_lat=39.9042,
                location_lng=116.4074,
                location_desc='模拟路口A',
                status='offline'
            )
            camera2 = Camera(
                name='测试路口B',
                camera_code='CAM-002',
                stream_url='./data/test_videos/normal_traffic.mp4',
                stream_type='file',
                location_lat=39.9142,
                location_lng=116.4174,
                location_desc='模拟路口B',
                status='offline'
            )
            db.session.add(camera1)
            db.session.add(camera2)
            print('创建测试摄像头: CAM-001, CAM-002')

        db.session.commit()
        print('数据库初始化完成')


if __name__ == '__main__':
    init_database()
