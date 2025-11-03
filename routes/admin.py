from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from core.responses import success, error
from core.db import get_conn
from core.user_profile_service import user_profile_service
import os
import shutil
import sqlite3

from .utils.auth import current_user_id, ensure_admin_for_json, ensure_admin_view

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin')
def admin():
    # 강화??관리자 권한 ?�인
    response = ensure_admin_view()
    if response:
        return response

    # 관리자 본인?��? ?�인
    admin_user_id = current_user_id()
    with get_conn() as conn:
        admin_user = conn.execute("SELECT username, is_admin FROM users WHERE id = ?", (admin_user_id,)).fetchone()
        if not admin_user or not admin_user['is_admin']:
            return redirect(url_for('home.login'))

    return render_template('admin.html')


# ---- Admin APIs (simple skeleton) ----
@admin_bp.route('/admin/api/users', methods=['GET'])
def users_list():
    # ?�버�? ?�션 ?�보 출력
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


@admin_bp.route('/admin/api/users/<int:user_id>/tokens/grant', methods=['POST'])
def users_tokens_grant(user_id: int):
    # 강화??관리자 권한 ?�인
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    # 관리자 본인?��? ?�인
    conn = get_conn()
    admin_user = conn.execute("SELECT username, is_admin FROM users WHERE id = ?", (admin_user_id,)).fetchone()
    if not admin_user or not admin_user['is_admin']:
        return error('invalid admin', status=403)
    
    data = request.get_json(silent=True) or {}
    amount = int(data.get('amount', 0))
    if amount <= 0:
        return error('amount must be > 0', status=400)
    
    # ?�???�용??존재 ?�인
    target_user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    if not target_user:
        return error('user not found', status=404)
    
    # 로그 기록
    print(f"ADMIN TOKEN GRANT: Admin {admin_user['username']} (ID:{admin_user_id}) granting {amount} tokens to {target_user['username']} (ID:{user_id})")
    
    # ?�큰 지�?
    conn.execute("UPDATE users SET token_balance = COALESCE(token_balance,0) + ? WHERE id = ?", (amount, user_id))
    
    # ?�력 기록
    conn.execute(
        "INSERT INTO token_history (user_id, changed_by, amount, change_type, created_at) VALUES (?, ?, ?, 'grant', datetime('now'))",
        (user_id, admin_user_id, amount)
    )
    
    conn.commit()
    
    # 결과 ?�인
    new_balance = conn.execute("SELECT token_balance FROM users WHERE id = ?", (user_id,)).fetchone()
    print(f"TOKEN GRANT RESULT: {target_user['username']} now has {new_balance['token_balance']} tokens")
    
    return success('granted')


@admin_bp.route('/admin/api/users/<int:user_id>/tokens/reset', methods=['POST'])
def users_tokens_reset(user_id: int):
    # 강화??관리자 권한 ?�인
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    # 관리자 본인?��? ?�인
    conn = get_conn()
    admin_user = conn.execute("SELECT username, is_admin FROM users WHERE id = ?", (admin_user_id,)).fetchone()
    if not admin_user or not admin_user['is_admin']:
        return error('invalid admin', status=403)
    
    # ?�???�용??존재 ?�인
    target_user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    if not target_user:
        return error('user not found', status=404)
    
    # 로그 기록
    print(f"ADMIN TOKEN RESET: Admin {admin_user['username']} (ID:{admin_user_id}) resetting tokens for {target_user['username']} (ID:{user_id})")
    
    # ?�큰 초기??(지급량�??�용??모두 초기??
    conn.execute("UPDATE users SET token_balance = 0, tokens_used = 0 WHERE id = ?", (user_id,))
    
    # ?�력 기록
    conn.execute(
        "INSERT INTO token_history (user_id, changed_by, amount, change_type, created_at) VALUES (?, ?, 0, 'reset', datetime('now'))",
        (user_id, admin_user_id)
    )
    
    conn.commit()
    
    # 결과 ?�인
    new_balance = conn.execute("SELECT token_balance FROM users WHERE id = ?", (user_id,)).fetchone()
    print(f"TOKEN RESET RESULT: {target_user['username']} now has {new_balance['token_balance']} tokens")
    
    return success('reset')


@admin_bp.route('/admin/api/users/<int:user_id>/approve', methods=['POST'])
def users_approve(user_id: int):
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET approval_status = 'approved', is_active = 1 WHERE id = ?",
            (user_id,)
        )
        conn.commit()
    
    return success('?�용?��? ?�인?�었?�니??)

@admin_bp.route('/admin/api/users/<int:user_id>/reject', methods=['POST'])
def users_reject(user_id: int):
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET approval_status = 'rejected' WHERE id = ?",
            (user_id,)
        )
        conn.commit()
    
    return success('?�용?��? 거�??�었?�니??)

@admin_bp.route('/admin/api/users/<int:user_id>', methods=['DELETE'])
def users_delete(user_id: int):
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    with get_conn() as conn:
        # ?�프????���?변�?
        conn.execute(
            "UPDATE users SET is_deleted = 1, deleted_at = datetime('now') WHERE id = ?",
            (user_id,)
        )
        conn.commit()
    
    return success('?�용???�태가 변경되?�습?�다')

@admin_bp.route('/admin/api/users/<int:user_id>/restore', methods=['POST'])
def users_restore(user_id: int):
    """??��/비활??미승???�태??계정??즉시 복구"""
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    with get_conn() as conn:
        row = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return error('user not found', status=404)
        conn.execute(
            "UPDATE users SET is_deleted = 0, is_active = 1, approval_status = 'approved' WHERE id = ?",
            (user_id,)
        )
        conn.commit()
    return success('?�용?��? 복구?�었?�니??)


# 즉시 ?�전??��: DB 물리??�� + user_data ?�더 ?�거
@admin_bp.route('/admin/api/users/<int:user_id>/purge', methods=['POST'])
def users_purge(user_id: int):
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    # ?�일 경로
    base_users_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'user_data')
    user_dir = os.path.join(base_users_dir, str(user_id))

    with get_conn() as conn:
        # 존재 ?�인
        u = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not u:
            return error('user not found', status=404)

        # ?��? ?�이???�거 (존재 ??
        try:
            conn.execute("DELETE FROM token_history WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM usage_logs WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM conversion_logs WHERE user_id = ?", (user_id,))
        except Exception:
            pass

        # ?�용???�코??물리 ??��
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()

    # ?�일 ?�스???�리
    try:
        if os.path.isdir(user_dir):
            shutil.rmtree(user_dir)
    except Exception as e:
        # ?�일 ?�리 ?�패?�도 DB ??��???�료?�었?��?�?경고�?반환
        return success(f'?�용????�� ?�료(?�일 ?��? ?�리 ?�패: {str(e)})')

    return success('?�용?��? 관???�일???�전 ??��?�었?�니??)


# ?�괄 ?�전??��: ?�정 관리자(keep_username) ?�외?�고 모두 ??��
@admin_bp.route('/admin/api/users/purge-all', methods=['POST'])
def users_purge_all():
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    data = request.get_json(silent=True) or {}
    keep_username = data.get('keep_username') or 'kweon4309'

    base_users_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'user_data')

    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        # 보존 ?�???�인
        keeper = conn.execute("SELECT id FROM users WHERE username = ? AND COALESCE(is_deleted,0)=0", (keep_username,)).fetchone()
        if not keeper:
            return error('keeper not found', status=404)
        keep_id = keeper['id']

        # ??�� ?�??ID 목록 ?�집 (관리자 ?�함 ?��? 무�?, ??보존???�외)
        rows = conn.execute("SELECT id FROM users WHERE id != ?", (keep_id,)).fetchall()
        target_ids = [r['id'] for r in rows]

        # ?��? ?�이????��
        for uid in target_ids:
            try:
                conn.execute("DELETE FROM token_history WHERE user_id = ?", (uid,))
                conn.execute("DELETE FROM usage_logs WHERE user_id = ?", (uid,))
                conn.execute("DELETE FROM conversion_logs WHERE user_id = ?", (uid,))
            except Exception:
                pass
        # ?�용????��
        conn.execute("DELETE FROM users WHERE id != ?", (keep_id,))
        conn.commit()

    # ?�일 ?�스???�리
    try:
        if os.path.isdir(base_users_dir):
            for name in os.listdir(base_users_dir):
                # ?�더명이 ?�용??id?�고 가??
                if name.isdigit() and int(name) != keep_id:
                    shutil.rmtree(os.path.join(base_users_dir, name), ignore_errors=True)
    except Exception:
        pass

    return success('보존 ?�???�외 모든 ?�용???�일 ?�전 ??�� ?�료')


@admin_bp.route('/admin/api/token-history', methods=['GET'])
def token_history():
    # 강화??관리자 권한 ?�인
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    # 관리자 본인?��? ?�인
    admin_user_id = current_user_id()
    with get_conn() as conn:
        admin_user = conn.execute("SELECT username, is_admin FROM users WHERE id = ?", (admin_user_id,)).fetchone()
        if not admin_user or not admin_user['is_admin']:
            return error('invalid admin', status=403)
        
        # ?�큰 ?�력 조회
        rows = conn.execute("""
            SELECT th.id,
                   th.change_type AS action,
                   th.amount,
                   -- UTC ISO8601 for stable client-side TZ formatting
                   strftime('%Y-%m-%dT%H:%M:%SZ', th.created_at) AS timestamp_utc,
                   admin.username as admin_username,
                   target.username as target_username
            FROM token_history th
            JOIN users admin ON th.changed_by = admin.id
            JOIN users target ON th.user_id = target.id
            ORDER BY th.created_at DESC
            LIMIT 50
        """).fetchall()
        
        history = [dict(r) for r in rows]
        return success('ok', data={'history': history})


# ?�큰 ?�력 ?�택 ??�� API
@admin_bp.route('/admin/api/token-history/delete', methods=['POST'])
def delete_token_history():
    # 관리자 권한 ?�인
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    data = request.get_json(silent=True) or {}
    ids = data.get('ids') or []

    # ?�력 검�?
    if not isinstance(ids, list) or len(ids) == 0:
        return error('??��????��???�습?�다', status=400)

    # ?�수 캐스??�??�효??검??
    try:
        id_list = [int(i) for i in ids]
    except Exception:
        return error('?�효?��? ?��? ID 목록?�니??, status=400)

    admin_user_id = current_user_id()
    with get_conn() as conn:
        admin_user = conn.execute("SELECT username, is_admin FROM users WHERE id = ?", (admin_user_id,)).fetchone()
        if not admin_user or not admin_user['is_admin']:
            return error('invalid admin', status=403)

        # ??�� (?�전?�게 ?�레?�스?�??구성)
        placeholders = ','.join(['?'] * len(id_list))
        conn.execute(f"DELETE FROM token_history WHERE id IN ({placeholders})", id_list)
        conn.commit()

    return success('?�택???�큰 ?�력????��?�었?�니??)


# ?�메???�증 ?�정 API
@admin_bp.route('/admin/api/email-settings', methods=['GET'])
def get_email_settings():
    """?�메???�증 ?�정 조회 API"""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    try:
        from core.email_verification_manager import EmailVerificationManager
        
        email_manager = EmailVerificationManager()
        stats = email_manager.get_verification_stats()
        
        # ?�재 ?�정 조회
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            settings = conn.execute(
                """
                SELECT key, value FROM settings 
                WHERE key LIKE 'email_verification_%'
                ORDER BY key
                """
            ).fetchall()
        
        settings_dict = {setting['key']: setting['value'] for setting in settings}
        
        return success('ok', data={
            'stats': stats,
            'settings': settings_dict
        })
        
    except Exception as e:
        return error(f'?�정 조회 �??�류가 발생?�습?�다: {str(e)}', status=500)


@admin_bp.route('/admin/api/email-settings/update', methods=['POST'])
def update_email_settings():
    """?�메???�증 ?�정 ?�데?�트 API"""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    try:
        data = request.get_json(silent=True) or {}
        
        # ?�정�??�데?�트
        settings_to_update = [
            'email_verification_enabled',
            'email_verification_expiry_hours',
            'email_verification_max_attempts',
            'email_verification_lockout_hours'
        ]
        
        with get_conn() as conn:
            for setting_key in settings_to_update:
                value = data.get(setting_key)
                if value is not None:
                    conn.execute(
                        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                        (setting_key, str(value))
                    )
            
            conn.commit()
        
        return success('?�메???�증 ?�정???�데?�트?�었?�니??)
        
    except Exception as e:
        return error(f'?�정 ?�데?�트 �??�류가 발생?�습?�다: {str(e)}', status=500)


# ?�로??API ?�드?�인?�들 (?�합???�?�보?�용)
@admin_bp.route('/admin/api/grant-tokens', methods=['POST'])
def grant_tokens():
    """?�큰 지�?API (?�로???�드?�인??"""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    amount = data.get('amount')
    
    if not user_id or not amount:
        return error('?�용??ID?� ?�큰 ?�량???�요?�니??, status=400)
    
    try:
        amount = int(amount)
        if amount <= 0:
            return error('?�큰 ?�량?� 0보다 커야 ?�니??, status=400)
    except ValueError:
        return error('?�효?��? ?��? ?�큰 ?�량?�니??, status=400)
    
    admin_user_id = current_user_id()
    with get_conn() as conn:
        # 관리자 ?�인
        admin_user = conn.execute("SELECT username FROM users WHERE id = ? AND is_admin = 1", (admin_user_id,)).fetchone()
        if not admin_user:
            return error('관리자 권한???�습?�다', status=403)
        
        # ?�???�용???�인
        target_user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        if not target_user:
            return error('?�용?��? 찾을 ???�습?�다', status=404)
        
        # ?�큰 지�?
        conn.execute("UPDATE users SET token_balance = COALESCE(token_balance, 0) + ? WHERE id = ?", (amount, user_id))
        
        # ?�력 기록
        conn.execute(
            "INSERT INTO token_history (user_id, changed_by, amount, change_type, created_at) VALUES (?, ?, ?, 'grant', datetime('now'))",
            (user_id, admin_user_id, amount)
        )
        
        conn.commit()
        
        return success('?�큰???�공?�으�?지급되?�습?�다')


@admin_bp.route('/admin/api/reset-tokens', methods=['POST'])
def reset_tokens():
    """?�큰 초기??API (?�로???�드?�인??"""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return error('?�용??ID가 ?�요?�니??, status=400)
    
    admin_user_id = current_user_id()
    with get_conn() as conn:
        # 관리자 ?�인
        admin_user = conn.execute("SELECT username FROM users WHERE id = ? AND is_admin = 1", (admin_user_id,)).fetchone()
        if not admin_user:
            return error('관리자 권한???�습?�다', status=403)
        
        # ?�???�용???�인
        target_user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        if not target_user:
            return error('?�용?��? 찾을 ???�습?�다', status=404)
        
        # ?�큰 초기??(보유 ?�큰�??�용 ?�큰 모두 초기??
        conn.execute("UPDATE users SET token_balance = 0, tokens_used = 0 WHERE id = ?", (user_id,))
        
        # ?�력 기록
        conn.execute(
            "INSERT INTO token_history (user_id, changed_by, amount, change_type, created_at) VALUES (?, ?, 0, 'reset', datetime('now'))",
            (user_id, admin_user_id)
        )
        
        conn.commit()
        
        return success('?�큰???�전??초기?�되?�습?�다 (보유 ?�큰: 0, ?�용 ?�큰: 0)')


@admin_bp.route('/admin/api/approve-user', methods=['POST'])
def approve_user():
    """?�용???�인 API (?�로???�드?�인??"""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return error('?�용??ID가 ?�요?�니??, status=400)
    
    with get_conn() as conn:
        # ?�???�용???�인
        target_user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        if not target_user:
            return error('?�용?��? 찾을 ???�습?�다', status=404)
        
        # ?�용???�인
        conn.execute(
            "UPDATE users SET approval_status = 'approved', is_active = 1 WHERE id = ?",
            (user_id,)
        )
        
        conn.commit()
        
        return success('?�용?��? ?�인?�었?�니??)


@admin_bp.route('/admin/api/delete-user', methods=['POST'])
def delete_user():
    """?�용????�� API (?�로???�드?�인??"""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return error('?�용??ID가 ?�요?�니??, status=400)
    
    with get_conn() as conn:
        # ?�???�용???�인
        target_user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        if not target_user:
            return error('?�용?��? 찾을 ???�습?�다', status=404)
        
        # ?�프????��
        conn.execute(
            "UPDATE users SET is_deleted = 1, deleted_at = datetime('now') WHERE id = ?",
            (user_id,)
        )
        
        conn.commit()
        
        return success('?�용?��? ??��?�었?�니??)


@admin_bp.route('/admin/api/user-conversions/<int:user_id>', methods=['GET'])
def user_conversions(user_id):
    """?�정 ?�용?�의 변???�력 조회"""
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


@admin_bp.route('/admin/api/users/<int:user_id>/change-plan', methods=['POST'])
@admin_bp.route('/admin/api/users/<int:user_id>/update-plan', methods=['POST'])
def update_user_plan(user_id):
    """?�용??VIP ?�급 변�?API"""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    data = request.get_json(silent=True) or {}
    plan_type = data.get('plan_type')
    
    # ?�효??plan_type 체크
    valid_plan_types = ['free', 'vip', 'premium-vip', 'gold-vip']
    if not plan_type or plan_type not in valid_plan_types:
        return error(f'?�효?��? ?��? ?�랜 ?�?�입?�다. 가?�한 �? {", ".join(valid_plan_types)}', status=400)
    
    admin_user_id = current_user_id()
    conn = get_conn()
    try:
        conn.row_factory = sqlite3.Row
        
        # 관리자 ?�인
        admin_user = conn.execute("SELECT username FROM users WHERE id = ? AND is_admin = 1", (admin_user_id,)).fetchone()
        if not admin_user:
            return error('관리자 권한???�습?�다', status=403)
        
        # ?�???�용???�인
        target_user = conn.execute("SELECT username, plan_type FROM users WHERE id = ?", (user_id,)).fetchone()
        if not target_user:
            return error('?�용?��? 찾을 ???�습?�다', status=404)
        
        old_plan = target_user['plan_type']
        
        # plan_type ?�데?�트
        conn.execute("UPDATE users SET plan_type = ? WHERE id = ?", (plan_type, user_id))
        
        # ?�력 기록
        conn.execute(
            "INSERT INTO token_history (user_id, changed_by, amount, change_type, meta, created_at) VALUES (?, ?, 0, 'plan_change', ?, datetime('now'))",
            (user_id, admin_user_id, f'plan:{old_plan}->{plan_type}')
        )
        
        conn.commit()
        
        print(f"VIP ?�급 변�? ?�용??{target_user['username']} (ID:{user_id}) ?�랜 변�?{old_plan} -> {plan_type}")
        
        return success(f'?�용???�랜??{plan_type}?�로 변경되?�습?�다 (?�전: {old_plan})')
    finally:
        conn.close()


