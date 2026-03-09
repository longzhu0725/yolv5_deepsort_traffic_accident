def success(data=None, message='success', code=200):
    response = {
        'code': code,
        'message': message,
        'data': data
    }
    return response, code


def error(message='error', code=400):
    response = {
        'code': code,
        'message': message,
        'data': None
    }
    return response, code
