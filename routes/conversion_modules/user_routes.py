"""
사용자 정보 라우트 모듈
사용자 정보 조회 등의 사용자 관련 기능
"""

from flask import Blueprint, session, jsonify
from core.db import get_conn_optimized as get_conn
from core.responses import success, error
from core.utils import row_value
from core.token_service import calculate_available_tokens
from ..utils.auth import ensure_login_for_json
import logging

user_bp = Blueprint('user', __name__)
logger = logging.getLogger(__name__)


@user_bp.route('/api/user-info', methods=['GET'])
def user_info():
    """현재 로그인한 사용자 정보 조회 API"""
    try:
        user_id, guard_response = ensure_login_for_json()
        if guard_response is not None:
            logger.warning("로그인되지 않은 사용자")
            return guard_response

        logger.info(f"유저정보 요청 - 세션 ID: {user_id}")
        
        # 사용자 정보 조회 (기존 방식으로 복원)
        with get_conn() as conn:
            user = conn.execute(
                """SELECT id, username, email, company_name, business_number,
                          representative_name, phone, address, business_type, business_category,
                          plan_type, monthly_limit, used_count, is_active, is_admin,
                          token_balance, tokens_used, created_at
                   FROM users WHERE id = ?""",
                (user_id,)
            ).fetchone()
            
            if not user:
                logger.warning(f"사용자 ID {user_id}를 찾을 수 없음")
                return error('사용자를 찾을 수 없습니다', status=404)
            
            logger.info(f"사용자 정보 조회 성공: {user['username']}")
            
            # 민감한 정보는 제외하고 필요한 정보만 반환
            safe_user_data = {
                'id': row_value(user, 'id'),
                'username': row_value(user, 'username', ''),
                'email': row_value(user, 'email', ''),
                'company_name': row_value(user, 'company_name', ''),
                'business_number': row_value(user, 'business_number', ''),
                'representative_name': row_value(user, 'representative_name', ''),
                'phone': row_value(user, 'phone', ''),
                'address': row_value(user, 'address', ''),
                'business_type': row_value(user, 'business_type', ''),
                'business_category': row_value(user, 'business_category', ''),
                'plan_type': row_value(user, 'plan_type', ''),
                'monthly_limit': row_value(user, 'monthly_limit', 0),
                'used_count': row_value(user, 'used_count', 0),
                'is_active': bool(row_value(user, 'is_active', 0)),
                'is_admin': bool(row_value(user, 'is_admin', 0)),
                'token_balance': row_value(user, 'token_balance', 0) or 0,
                'tokens_used': row_value(user, 'tokens_used', 0) or 0,
                'created_at': row_value(user, 'created_at', '')
            }
            
            return success('사용자 정보 조회 성공', data={'user': safe_user_data})
            
    except Exception as e:
        logger.error(f"사용자 정보 조회 중 오류가 발생했습니다: {str(e)}")
        return error(f"사용자 정보 조회 중 오류가 발생했습니다: {str(e)}", status=500)
            
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
                available_tokens = calculate_available_tokens(user['token_balance'], user['tokens_used'])
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
