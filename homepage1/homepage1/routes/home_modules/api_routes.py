from flask import Blueprint, jsonify, request
from core.db import get_conn_optimized as get_conn

home_api_bp = Blueprint('home_api', __name__)


# ====== AJAX duplicate checks (non-deleted accounts only) ======
@home_api_bp.route('/api/check-username')
def api_check_username():
    username = (request.args.get('username') or '').strip()
    if not username:
        return jsonify({"success": False, "available": False, "error": "username_required"})
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE username = ? AND COALESCE(is_deleted,0) = 0 LIMIT 1",
            (username,)
        ).fetchone()
    return jsonify({"success": True, "available": row is None})


@home_api_bp.route('/api/check-business-number')
def api_check_business_number():
    business_number = (request.args.get('business_number') or '').strip()
    if not business_number:
        return jsonify({"success": False, "available": False, "error": "business_number_required"})
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE business_number = ? AND COALESCE(is_deleted,0) = 0 LIMIT 1",
            (business_number,)
        ).fetchone()
    return jsonify({"success": True, "available": row is None})


@home_api_bp.route('/api/check-email')
def api_check_email():
    email = (request.args.get('email') or '').strip()
    if not email:
        return jsonify({"success": False, "available": False, "error": "email_required"})
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE email = ? AND COALESCE(is_deleted,0) = 0 LIMIT 1",
            (email,)
        ).fetchone()
    return jsonify({"success": True, "available": row is None})

