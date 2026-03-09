import jwt
from datetime import datetime, timedelta
from flask import Blueprint, request
from ..config import Config
from ..utils.response import success, error
from ..models.user import User
from ..extensions import db

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return error('请求数据不能为空', 400)

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return error('用户名和密码不能为空', 400)

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return error('用户名或密码错误', 401)

    expire_time = datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRE_HOURS)
    token = jwt.encode(
        {'user_id': user.id, 'exp': expire_time},
        Config.JWT_SECRET,
        algorithm='HS256'
    )

    return success({
        'token': token,
        'user': user.to_dict()
    }, '登录成功')


@auth_bp.route('/logout', methods=['POST'])
def logout():
    return success(message='登出成功')
