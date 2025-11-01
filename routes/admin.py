from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from core.responses import success, error
from core.db import get_conn
from core.user_profile_service import user_profile_service
import os
import shutil
import sqlite3

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin')
def admin():
    # 강화된 관리자 권한 확인
    if not session.get('is_admin') or not session.get('user_id'):
        return redirect(url_for('home.login'))
    
    # 관리자 본인인지 확인
    admin_user_id = session.get('user_id')
    with get_conn() as conn:
        admin_user = conn.execute("SELECT username, is_admin FROM users WHERE id = ?", (admin_user_id,)).fetchone()
        if not admin_user or not admin_user['is_admin']:
            return redirect(url_for('home.login'))

    return render_template('admin.html')


# ---- Admin APIs (simple skeleton) ----
@admin_bp.route('/admin/api/users', methods=['GET'])
def users_list():
    # 디버깅: 세션 정보 출력
    print(f"DEBUG: Session data - user_id: {session.get('user_id')}, is_admin: {session.get('is_admin')}")
    
    # 강화된 관리자 권한 확인
    if not session.get('is_admin') or not session.get('user_id'):
        print("DEBUG: Failed admin check - missing session data")
        return error('forbidden', status=403)
    
    # 관리자 본인인지 확인
    admin_user_id = session.get('user_id')
    with get_conn() as conn:
        admin_user = conn.execute("SELECT username, is_admin FROM users WHERE id = ?", (admin_user_id,)).fetchone()
        if not admin_user or not admin_user['is_admin']:
            return error('invalid admin', status=403)
        
        # 로그 기록
        print(f"ADMIN USERS LIST: Admin {admin_user['username']} (ID:{admin_user_id}) accessing users list")
        
        # 새로운 서비스를 사용하여 최근 24시간 변환 건수를 포함한 사용자 목록 조회
        # 일반 사용자만 조회 (관리자 제외)
        users = user_profile_service.get_all_users_with_recent_usage()
        # 관리자 계정 제외
        general_users = [user for user in users if not user.get('is_admin', False)]
        return success('ok', data={'users': general_users})


@admin_bp.route('/admin/api/admin-users', methods=['GET'])
def admin_users_list():
    """관리자 계정 목록 조회"""
    if not session.get('is_admin') or not session.get('user_id'):
        return error('forbidden', status=403)
    
    admin_user_id = session.get('user_id')
    with get_conn() as conn:
        admin_user = conn.execute("SELECT username FROM users WHERE id = ?", (admin_user_id,)).fetchone()
        if not admin_user:
            return error('invalid admin', status=403)
        
        # 관리자 계정만 조회
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
    """관리자 대시보드 통계 조회"""
    if not session.get('is_admin') or not session.get('user_id'):
        return error('forbidden', status=403)
    
    admin_user_id = session.get('user_id')
    with get_conn() as conn:
        admin_user = conn.execute("SELECT username FROM users WHERE id = ?", (admin_user_id,)).fetchone()
        if not admin_user:
            return error('invalid admin', status=403)
        
        # 총 발급 토큰
        total_issued_tokens = conn.execute("""
            SELECT COALESCE(SUM(token_balance), 0) as total_issued 
            FROM users 
            WHERE COALESCE(is_deleted, 0) = 0
        """).fetchone()['total_issued']
        
        # 현재 활성 사용자 (일반 사용자만)
        active_users_count = conn.execute("""
            SELECT COUNT(*) as active_count 
            FROM users 
            WHERE COALESCE(is_deleted, 0) = 0 AND is_active = 1 AND COALESCE(is_admin, 0) = 0
        """).fetchone()['active_count']
        
        # 시스템 에러율 (가정치 - 실제로는 로그에서 계산)
        system_error_rate = 0.1  # 0.1% 가정치
        
        # 시스템 가동률 (가정치)
        system_uptime = 99.9  # 99.9% 가정치
        
        stats = {
            'total_issued_tokens': total_issued_tokens,
            'active_users_count': active_users_count,
            'system_error_rate': system_error_rate,
            'system_uptime': system_uptime
        }
        
        return success('ok', data=stats)


@admin_bp.route('/admin/api/users/<int:user_id>', methods=['PUT'])
def users_update(user_id: int):
    if not session.get('is_admin'):
        return error('forbidden', status=403)
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
    # 강화된 관리자 권한 확인
    if not session.get('is_admin') or not session.get('user_id'):
        return error('forbidden', status=403)
    
    # 관리자 본인인지 확인
    admin_user_id = session.get('user_id')
    conn = get_conn()
    admin_user = conn.execute("SELECT username, is_admin FROM users WHERE id = ?", (admin_user_id,)).fetchone()
    if not admin_user or not admin_user['is_admin']:
        return error('invalid admin', status=403)
    
    data = request.get_json(silent=True) or {}
    amount = int(data.get('amount', 0))
    if amount <= 0:
        return error('amount must be > 0', status=400)
    
    # 대상 사용자 존재 확인
    target_user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    if not target_user:
        return error('user not found', status=404)
    
    # 로그 기록
    print(f"ADMIN TOKEN GRANT: Admin {admin_user['username']} (ID:{admin_user_id}) granting {amount} tokens to {target_user['username']} (ID:{user_id})")
    
    # 토큰 지급
    conn.execute("UPDATE users SET token_balance = COALESCE(token_balance,0) + ? WHERE id = ?", (amount, user_id))
    
    # 이력 기록
    conn.execute(
        "INSERT INTO token_history (user_id, changed_by, amount, change_type, created_at) VALUES (?, ?, ?, 'grant', datetime('now'))",
        (user_id, admin_user_id, amount)
    )
    
    conn.commit()
    
    # 결과 확인
    new_balance = conn.execute("SELECT token_balance FROM users WHERE id = ?", (user_id,)).fetchone()
    print(f"TOKEN GRANT RESULT: {target_user['username']} now has {new_balance['token_balance']} tokens")
    
    return success('granted')


@admin_bp.route('/admin/api/users/<int:user_id>/tokens/reset', methods=['POST'])
def users_tokens_reset(user_id: int):
    # 강화된 관리자 권한 확인
    if not session.get('is_admin') or not session.get('user_id'):
        return error('forbidden', status=403)
    
    # 관리자 본인인지 확인
    admin_user_id = session.get('user_id')
    conn = get_conn()
    admin_user = conn.execute("SELECT username, is_admin FROM users WHERE id = ?", (admin_user_id,)).fetchone()
    if not admin_user or not admin_user['is_admin']:
        return error('invalid admin', status=403)
    
    # 대상 사용자 존재 확인
    target_user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    if not target_user:
        return error('user not found', status=404)
    
    # 로그 기록
    print(f"ADMIN TOKEN RESET: Admin {admin_user['username']} (ID:{admin_user_id}) resetting tokens for {target_user['username']} (ID:{user_id})")
    
    # 토큰 초기화 (지급량과 사용량 모두 초기화)
    conn.execute("UPDATE users SET token_balance = 0, tokens_used = 0 WHERE id = ?", (user_id,))
    
    # 이력 기록
    conn.execute(
        "INSERT INTO token_history (user_id, changed_by, amount, change_type, created_at) VALUES (?, ?, 0, 'reset', datetime('now'))",
        (user_id, admin_user_id)
    )
    
    conn.commit()
    
    # 결과 확인
    new_balance = conn.execute("SELECT token_balance FROM users WHERE id = ?", (user_id,)).fetchone()
    print(f"TOKEN RESET RESULT: {target_user['username']} now has {new_balance['token_balance']} tokens")
    
    return success('reset')


@admin_bp.route('/admin/api/users/<int:user_id>/approve', methods=['POST'])
def users_approve(user_id: int):
    if not session.get('is_admin'):
        return error('forbidden', status=403)
    
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET approval_status = 'approved', is_active = 1 WHERE id = ?",
            (user_id,)
        )
        conn.commit()
    
    return success('사용자가 승인되었습니다')

@admin_bp.route('/admin/api/users/<int:user_id>/reject', methods=['POST'])
def users_reject(user_id: int):
    if not session.get('is_admin'):
        return error('forbidden', status=403)
    
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET approval_status = 'rejected' WHERE id = ?",
            (user_id,)
        )
        conn.commit()
    
    return success('사용자가 거부되었습니다')

@admin_bp.route('/admin/api/users/<int:user_id>', methods=['DELETE'])
def users_delete(user_id: int):
    if not session.get('is_admin'):
        return error('forbidden', status=403)
    
    with get_conn() as conn:
        # 소프트 삭제로 변경
        conn.execute(
            "UPDATE users SET is_deleted = 1, deleted_at = datetime('now') WHERE id = ?",
            (user_id,)
        )
        conn.commit()
    
    return success('사용자 상태가 변경되었습니다')

@admin_bp.route('/admin/api/users/<int:user_id>/restore', methods=['POST'])
def users_restore(user_id: int):
    """삭제/비활성/미승인 상태의 계정을 즉시 복구"""
    if not session.get('is_admin') or not session.get('user_id'):
        return error('forbidden', status=403)

    with get_conn() as conn:
        row = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return error('user not found', status=404)
        conn.execute(
            "UPDATE users SET is_deleted = 0, is_active = 1, approval_status = 'approved' WHERE id = ?",
            (user_id,)
        )
        conn.commit()
    return success('사용자가 복구되었습니다')


# 즉시 완전삭제: DB 물리삭제 + user_data 폴더 제거
@admin_bp.route('/admin/api/users/<int:user_id>/purge', methods=['POST'])
def users_purge(user_id: int):
    if not session.get('is_admin') or not session.get('user_id'):
        return error('forbidden', status=403)

    # 파일 경로
    base_users_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'user_data')
    user_dir = os.path.join(base_users_dir, str(user_id))

    with get_conn() as conn:
        # 존재 확인
        u = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not u:
            return error('user not found', status=404)

        # 연관 데이터 제거 (존재 시)
        try:
            conn.execute("DELETE FROM token_history WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM usage_logs WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM conversion_logs WHERE user_id = ?", (user_id,))
        except Exception:
            pass

        # 사용자 레코드 물리 삭제
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()

    # 파일 시스템 정리
    try:
        if os.path.isdir(user_dir):
            shutil.rmtree(user_dir)
    except Exception as e:
        # 파일 정리 실패해도 DB 삭제는 완료되었으므로 경고만 반환
        return success(f'사용자 삭제 완료(파일 일부 정리 실패: {str(e)})')

    return success('사용자와 관련 파일이 완전 삭제되었습니다')


# 일괄 완전삭제: 특정 관리자(keep_username) 제외하고 모두 삭제
@admin_bp.route('/admin/api/users/purge-all', methods=['POST'])
def users_purge_all():
    if not session.get('is_admin') or not session.get('user_id'):
        return error('forbidden', status=403)

    data = request.get_json(silent=True) or {}
    keep_username = data.get('keep_username') or 'kweon4309'

    base_users_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'user_data')

    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        # 보존 대상 확인
        keeper = conn.execute("SELECT id FROM users WHERE username = ? AND COALESCE(is_deleted,0)=0", (keep_username,)).fetchone()
        if not keeper:
            return error('keeper not found', status=404)
        keep_id = keeper['id']

        # 삭제 대상 ID 목록 수집 (관리자 포함 여부 무관, 단 보존자 제외)
        rows = conn.execute("SELECT id FROM users WHERE id != ?", (keep_id,)).fetchall()
        target_ids = [r['id'] for r in rows]

        # 연관 데이터 삭제
        for uid in target_ids:
            try:
                conn.execute("DELETE FROM token_history WHERE user_id = ?", (uid,))
                conn.execute("DELETE FROM usage_logs WHERE user_id = ?", (uid,))
                conn.execute("DELETE FROM conversion_logs WHERE user_id = ?", (uid,))
            except Exception:
                pass
        # 사용자 삭제
        conn.execute("DELETE FROM users WHERE id != ?", (keep_id,))
        conn.commit()

    # 파일 시스템 정리
    try:
        if os.path.isdir(base_users_dir):
            for name in os.listdir(base_users_dir):
                # 폴더명이 사용자 id라고 가정
                if name.isdigit() and int(name) != keep_id:
                    shutil.rmtree(os.path.join(base_users_dir, name), ignore_errors=True)
    except Exception:
        pass

    return success('보존 대상 제외 모든 사용자/파일 완전 삭제 완료')


@admin_bp.route('/admin/api/token-history', methods=['GET'])
def token_history():
    # 강화된 관리자 권한 확인
    if not session.get('is_admin') or not session.get('user_id'):
        return error('forbidden', status=403)
    
    # 관리자 본인인지 확인
    admin_user_id = session.get('user_id')
    with get_conn() as conn:
        admin_user = conn.execute("SELECT username, is_admin FROM users WHERE id = ?", (admin_user_id,)).fetchone()
        if not admin_user or not admin_user['is_admin']:
            return error('invalid admin', status=403)
        
        # 토큰 이력 조회
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


# 토큰 이력 선택 삭제 API
@admin_bp.route('/admin/api/token-history/delete', methods=['POST'])
def delete_token_history():
    # 관리자 권한 확인
    if not session.get('is_admin') or not session.get('user_id'):
        return error('forbidden', status=403)

    data = request.get_json(silent=True) or {}
    ids = data.get('ids') or []

    # 입력 검증
    if not isinstance(ids, list) or len(ids) == 0:
        return error('삭제할 항목이 없습니다', status=400)

    # 정수 캐스팅 및 유효성 검사
    try:
        id_list = [int(i) for i in ids]
    except Exception:
        return error('유효하지 않은 ID 목록입니다', status=400)

    admin_user_id = session.get('user_id')
    with get_conn() as conn:
        admin_user = conn.execute("SELECT username, is_admin FROM users WHERE id = ?", (admin_user_id,)).fetchone()
        if not admin_user or not admin_user['is_admin']:
            return error('invalid admin', status=403)

        # 삭제 (안전하게 플레이스홀더 구성)
        placeholders = ','.join(['?'] * len(id_list))
        conn.execute(f"DELETE FROM token_history WHERE id IN ({placeholders})", id_list)
        conn.commit()

    return success('선택한 토큰 이력이 삭제되었습니다')


# 이메일 인증 설정 API
@admin_bp.route('/admin/api/email-settings', methods=['GET'])
def get_email_settings():
    """이메일 인증 설정 조회 API"""
    if not session.get('is_admin') or not session.get('user_id'):
        return error('관리자 권한이 필요합니다', status=403)
    
    try:
        from core.email_verification_manager import EmailVerificationManager
        
        email_manager = EmailVerificationManager()
        stats = email_manager.get_verification_stats()
        
        # 현재 설정 조회
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
        return error(f'설정 조회 중 오류가 발생했습니다: {str(e)}', status=500)


@admin_bp.route('/admin/api/email-settings/update', methods=['POST'])
def update_email_settings():
    """이메일 인증 설정 업데이트 API"""
    if not session.get('is_admin') or not session.get('user_id'):
        return error('관리자 권한이 필요합니다', status=403)
    
    try:
        data = request.get_json(silent=True) or {}
        
        # 설정값 업데이트
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
        
        return success('이메일 인증 설정이 업데이트되었습니다')
        
    except Exception as e:
        return error(f'설정 업데이트 중 오류가 발생했습니다: {str(e)}', status=500)


# 새로운 API 엔드포인트들 (통합된 대시보드용)
@admin_bp.route('/admin/api/grant-tokens', methods=['POST'])
def grant_tokens():
    """토큰 지급 API (새로운 엔드포인트)"""
    if not session.get('is_admin') or not session.get('user_id'):
        return error('관리자 권한이 필요합니다', status=403)
    
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    amount = data.get('amount')
    
    if not user_id or not amount:
        return error('사용자 ID와 토큰 수량이 필요합니다', status=400)
    
    try:
        amount = int(amount)
        if amount <= 0:
            return error('토큰 수량은 0보다 커야 합니다', status=400)
    except ValueError:
        return error('유효하지 않은 토큰 수량입니다', status=400)
    
    admin_user_id = session.get('user_id')
    with get_conn() as conn:
        # 관리자 확인
        admin_user = conn.execute("SELECT username FROM users WHERE id = ? AND is_admin = 1", (admin_user_id,)).fetchone()
        if not admin_user:
            return error('관리자 권한이 없습니다', status=403)
        
        # 대상 사용자 확인
        target_user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        if not target_user:
            return error('사용자를 찾을 수 없습니다', status=404)
        
        # 토큰 지급
        conn.execute("UPDATE users SET token_balance = COALESCE(token_balance, 0) + ? WHERE id = ?", (amount, user_id))
        
        # 이력 기록
        conn.execute(
            "INSERT INTO token_history (user_id, changed_by, amount, change_type, created_at) VALUES (?, ?, ?, 'grant', datetime('now'))",
            (user_id, admin_user_id, amount)
        )
        
        conn.commit()
        
        return success('토큰이 성공적으로 지급되었습니다')


@admin_bp.route('/admin/api/reset-tokens', methods=['POST'])
def reset_tokens():
    """토큰 초기화 API (새로운 엔드포인트)"""
    if not session.get('is_admin') or not session.get('user_id'):
        return error('관리자 권한이 필요합니다', status=403)
    
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return error('사용자 ID가 필요합니다', status=400)
    
    admin_user_id = session.get('user_id')
    with get_conn() as conn:
        # 관리자 확인
        admin_user = conn.execute("SELECT username FROM users WHERE id = ? AND is_admin = 1", (admin_user_id,)).fetchone()
        if not admin_user:
            return error('관리자 권한이 없습니다', status=403)
        
        # 대상 사용자 확인
        target_user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        if not target_user:
            return error('사용자를 찾을 수 없습니다', status=404)
        
        # 토큰 초기화 (보유 토큰과 사용 토큰 모두 초기화)
        conn.execute("UPDATE users SET token_balance = 0, tokens_used = 0 WHERE id = ?", (user_id,))
        
        # 이력 기록
        conn.execute(
            "INSERT INTO token_history (user_id, changed_by, amount, change_type, created_at) VALUES (?, ?, 0, 'reset', datetime('now'))",
            (user_id, admin_user_id)
        )
        
        conn.commit()
        
        return success('토큰이 완전히 초기화되었습니다 (보유 토큰: 0, 사용 토큰: 0)')


@admin_bp.route('/admin/api/approve-user', methods=['POST'])
def approve_user():
    """사용자 승인 API (새로운 엔드포인트)"""
    if not session.get('is_admin') or not session.get('user_id'):
        return error('관리자 권한이 필요합니다', status=403)
    
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return error('사용자 ID가 필요합니다', status=400)
    
    with get_conn() as conn:
        # 대상 사용자 확인
        target_user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        if not target_user:
            return error('사용자를 찾을 수 없습니다', status=404)
        
        # 사용자 승인
        conn.execute(
            "UPDATE users SET approval_status = 'approved', is_active = 1 WHERE id = ?",
            (user_id,)
        )
        
        conn.commit()
        
        return success('사용자가 승인되었습니다')


@admin_bp.route('/admin/api/delete-user', methods=['POST'])
def delete_user():
    """사용자 삭제 API (새로운 엔드포인트)"""
    if not session.get('is_admin') or not session.get('user_id'):
        return error('관리자 권한이 필요합니다', status=403)
    
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return error('사용자 ID가 필요합니다', status=400)
    
    with get_conn() as conn:
        # 대상 사용자 확인
        target_user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        if not target_user:
            return error('사용자를 찾을 수 없습니다', status=404)
        
        # 소프트 삭제
        conn.execute(
            "UPDATE users SET is_deleted = 1, deleted_at = datetime('now') WHERE id = ?",
            (user_id,)
        )
        
        conn.commit()
        
        return success('사용자가 삭제되었습니다')


@admin_bp.route('/admin/api/user-conversions/<int:user_id>', methods=['GET'])
def user_conversions(user_id):
    """특정 사용자의 변환 이력 조회"""
    # 관리자 권한 확인
    if not session.get('is_admin') or not session.get('user_id'):
        return error('forbidden', status=403)
    
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        
        # 사용자 존재 확인
        user = conn.execute("SELECT id, username FROM users WHERE id = ? AND is_deleted = 0", (user_id,)).fetchone()
        if not user:
            return error('user not found', status=404)
        
        # 변환 이력 조회
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
    """사용자 VIP 등급 변경 API"""
    if not session.get('is_admin') or not session.get('user_id'):
        return error('관리자 권한이 필요합니다', status=403)
    
    data = request.get_json(silent=True) or {}
    plan_type = data.get('plan_type')
    
    # 유효한 plan_type 체크
    valid_plan_types = ['free', 'vip', 'premium-vip', 'gold-vip']
    if not plan_type or plan_type not in valid_plan_types:
        return error(f'유효하지 않은 플랜 타입입니다. 가능한 값: {", ".join(valid_plan_types)}', status=400)
    
    admin_user_id = session.get('user_id')
    conn = get_conn()
    try:
        conn.row_factory = sqlite3.Row
        
        # 관리자 확인
        admin_user = conn.execute("SELECT username FROM users WHERE id = ? AND is_admin = 1", (admin_user_id,)).fetchone()
        if not admin_user:
            return error('관리자 권한이 없습니다', status=403)
        
        # 대상 사용자 확인
        target_user = conn.execute("SELECT username, plan_type FROM users WHERE id = ?", (user_id,)).fetchone()
        if not target_user:
            return error('사용자를 찾을 수 없습니다', status=404)
        
        old_plan = target_user['plan_type']
        
        # plan_type 업데이트
        conn.execute("UPDATE users SET plan_type = ? WHERE id = ?", (plan_type, user_id))
        
        # 이력 기록
        conn.execute(
            "INSERT INTO token_history (user_id, changed_by, amount, change_type, meta, created_at) VALUES (?, ?, 0, 'plan_change', ?, datetime('now'))",
            (user_id, admin_user_id, f'plan:{old_plan}->{plan_type}')
        )
        
        conn.commit()
        
        print(f"VIP 등급 변경: 사용자 {target_user['username']} (ID:{user_id}) 플랜 변경 {old_plan} -> {plan_type}")
        
        return success(f'사용자 플랜이 {plan_type}으로 변경되었습니다 (이전: {old_plan})')
    finally:
        conn.close()


