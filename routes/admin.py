from flask import request, session
from core.responses import success, error
from core.db import get_conn
from core.user_profile_service import user_profile_service
import sqlite3

from .admin import admin_bp
from .utils.auth import current_user_id, ensure_admin_for_json


# ---- Admin APIs (simple skeleton) ----
@admin_bp.route('/admin/api/users', methods=['GET'])
def users_list():
    # ?버? ?션 ?보 출력
    print(f"DEBUG: Session data - user_id: {current_user_id()}, is_admin: {session.get('is_admin')}")
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        print("DEBUG: Failed admin check - missing session data")
        return guard_response

    # 관리자 본인?��? ?�인
    with get_conn() as conn:
        admin_user = conn.execute("SELECT username, is_admin FROM users WHERE id = ?", (admin_user_id,)).fetchone()
        if not admin_user or not admin_user['is_admin']:
            return error('invalid admin', status=403)
        
        # 로그 기록
        print(f"ADMIN USERS LIST: Admin {admin_user['username']} (ID:{admin_user_id}) accessing users list")
        
        # ?�로???�비?��? ?�용?�여 최근 24?�간 변??건수�??�함???�용??목록 조회
        # ?�반 ?�용?�만 조회 (관리자 ?�외)
        users = user_profile_service.get_all_users_with_recent_usage()
        # 관리자 계정 ?�외
        general_users = [user for user in users if not user.get('is_admin', False)]
        return success('ok', data={'users': general_users})


@admin_bp.route('/admin/api/admin-users', methods=['GET'])
def admin_users_list():
    """관리자 계정 목록 조회"""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    with get_conn() as conn:
        admin_user = conn.execute("SELECT username FROM users WHERE id = ?", (admin_user_id,)).fetchone()
        if not admin_user:
            return error('invalid admin', status=403)
        
        # 관리자 계정�?조회
        admin_users = conn.execute("""
            SELECT id, username, email, company_name, business_number, representative_name, 
                   phone, address, plan_type, monthly_limit, used_count, is_active, 
                   created_at, COALESCE(token_balance, 0) AS token_balance, 
                   COALESCE(tokens_used, 0) AS tokens_used, 
                   COALESCE(approval_status, 'pending') AS approval_status
            FROM users 
            WHERE COALESCE(is_deleted, 0) = 0 AND is_admin = 1
            ORDER BY created_at ASC
        """).fetchall()
        
        admin_users_data = [dict(user) for user in admin_users]
        return success('ok', data={'admin_users': admin_users_data})


@admin_bp.route('/admin/api/admin-dashboard-stats', methods=['GET'])
def admin_dashboard_stats():
    """관리자 ?�?�보???�계 조회"""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    with get_conn() as conn:
        admin_user = conn.execute("SELECT username FROM users WHERE id = ?", (admin_user_id,)).fetchone()
        if not admin_user:
            return error('invalid admin', status=403)
        
        # �?발급 ?�큰
        total_issued_tokens = conn.execute("""
            SELECT COALESCE(SUM(token_balance), 0) as total_issued 
            FROM users 
            WHERE COALESCE(is_deleted, 0) = 0
        """).fetchone()['total_issued']
        
        # ?�재 ?�성 ?�용??(?�반 ?�용?�만)
        active_users_count = conn.execute("""
            SELECT COUNT(*) as active_count 
            FROM users 
            WHERE COALESCE(is_deleted, 0) = 0 AND is_active = 1 AND COALESCE(is_admin, 0) = 0
        """).fetchone()['active_count']
        
        # ?�스???�러??(가?�치 - ?�제로는 로그?�서 계산)
        system_error_rate = 0.1  # 0.1% 가?�치
        
        # ?�스??가?�률 (가?�치)
        system_uptime = 99.9  # 99.9% 가?�치
        
        stats = {
            'total_issued_tokens': total_issued_tokens,
            'active_users_count': active_users_count,
            'system_error_rate': system_error_rate,
            'system_uptime': system_uptime
        }
        
        return success('ok', data=stats)


@admin_bp.route('/admin/api/users/<int:user_id>', methods=['PUT'])
def users_update(user_id: int):
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    if not email:
        return error('email required', status=400)
    conn = get_conn()
    conn.execute("UPDATE users SET email = ? WHERE id = ?", (email, user_id))
    conn.commit()
    return success('updated')


@admin_bp.route('/admin/api/user-conversions/<int:user_id>', methods=['GET'])
def user_conversions(user_id):
    """?정 ?용?의 변???력 조회"""
    # 관리자 권한 ?�인
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        
        # ?�용??존재 ?�인
        user = conn.execute("SELECT id, username FROM users WHERE id = ? AND is_deleted = 0", (user_id,)).fetchone()
        if not user:
            return error('user not found', status=404)
        
        # 변???�력 조회
        conversions = conn.execute("""
            SELECT id, original_filename, created_at, status, tokens_used, file_size
            FROM conversion_logs 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 20
        """, (user_id,)).fetchall()
        
        conversions_list = []
        for conv in conversions:
            conversions_list.append({
                'id': conv['id'],
                'original_filename': conv['original_filename'],
                'created_at': conv['created_at'],
                'status': conv['status'],
                'tokens_used': conv['tokens_used'],
                'file_size': conv['file_size']
            })
        
        return success(data={'conversions': conversions_list})


