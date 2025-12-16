from flask import jsonify


def success(message: str = "ok", data=None, status: int = 200):
    return jsonify({
        'success': True,
        'message': message,
        'data': data
    }), status


def error(message: str = "error", errors=None, status: int = 400, data=None):
    return jsonify({
        'success': False,
        'message': message,
        'errors': errors or {},
        'data': data
    }), status


















