"""
사용자 정보 라우트 모듈
사용자 정보 조회 등의 사용자 관련 기능
"""

from flask import Blueprint, session, jsonify
from core.db import get_conn_optimized as get_conn
from core.responses import success, error
from core.utils import row_value

user_bp = Blueprint('user', __name__)


@user_bp.route('/api/user-info', methods=['GET'])
def user_info():
    """현재 로그인한 사용자 정보 조회 API"""
    if not session.get('user_id'):
        return error("로그인이 필요합니다", 401)
    
    try:
        with get_conn() as conn:
            user = conn.execute(
                "SELECT id, username, email, token_balance, COALESCE(tokens_used, 0) as tokens_used, created_at FROM users WHERE id = ?", 
                (session['user_id'],)
            ).fetchone()
            
            if not user:
                return error("사용자를 찾을 수 없습니다", 404)
            
            available_tokens = (user['token_balance'] or 0) - (user['tokens_used'] or 0)

            # 호환성을 위해 평탄/중첩 구조를 동시에 반환
            payload = {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "available_tokens": available_tokens,
                "total_tokens": user['token_balance'] or 0,
                "used_tokens": user['tokens_used'] or 0,
                "created_at": user['created_at']
            }
            return success({
                **payload,
                "user": payload,
            })
            
@user_bp.route('/api/admin/users', methods=['GET'])
def admin_users():
    """관리자용 사용자 목록 조회 API"""
    if not session.get('user_id') or not session.get('is_admin'):
        return error("관리자 권한이 필요합니다", 403)
    
    try:
        with get_conn() as conn:
            users = conn.execute(
                """
                SELECT id, username, email, company_name, business_number,
                       representative_name, phone, address, business_type, business_category,
                       token_balance, COALESCE(tokens_used, 0) as tokens_used, 
                       created_at, is_active, is_admin
                FROM users 
                ORDER BY created_at DESC
                """
            ).fetchall()
            
            users_data = []
            for user in users:
                available_tokens = (user['token_balance'] or 0) - (user['tokens_used'] or 0)
                users_data.append({
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'company_name': user['company_name'],
                    'business_number': user['business_number'],
                    'representative_name': user['representative_name'],
                    'phone': user['phone'],
                    'address': user['address'],
                    'business_type': user['business_type'],
                    'business_category': user['business_category'],
                    'token_balance': user['token_balance'] or 0,
                    'tokens_used': user['tokens_used'] or 0,
                    'available_tokens': available_tokens,
                    'created_at': user['created_at'],
                    'is_active': bool(user['is_active']),
                    'is_admin': bool(user['is_admin'])
                })
            
            return success('사용자 목록 조회 성공', data={'users': users_data})
            
    except Exception as e:
        return error(f"사용자 목록 조회 중 오류가 발생했습니다: {str(e)}", 500)
