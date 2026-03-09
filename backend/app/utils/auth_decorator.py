import functools
import jwt
from flask import request, g
from ..config import Config
from ..utils.response import error
from ..models.user import User
from ..extensions import db


def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return error('缺少认证令牌', 401)

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return error('令牌格式错误', 401)

        token = parts[1]
        try:
            payload = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
            user_id = payload.get('user_id')
            if not user_id:
                return error('无效的令牌', 401)

            user = db.session.get(User, user_id)
            if not user:
                return error('用户不存在', 401)

            g.current_user = user
        except jwt.ExpiredSignatureError:
            return error('令牌已过期', 401)
        except jwt.InvalidTokenError:
            return error('无效的令牌', 401)

        return f(*args, **kwargs)

    return decorated_function
