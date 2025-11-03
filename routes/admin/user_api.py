import os
import shutil
import sqlite3

from flask import request

from core.db import get_conn
from core.responses import success, error

from . import admin_bp
from ..utils.auth import current_user_id, ensure_admin_for_json


@admin_bp.route('/admin/api/users/<int:user_id>/approve', methods=['POST'])
def approve_user_by_id(user_id: int):
    """승인 대기 중인 사용자를 즉시 승인한다."""
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET approval_status = 'approved', is_active = 1 WHERE id = ?",
            (user_id,),
        )
        conn.commit()

    return success('User approved successfully')


@admin_bp.route('/admin/api/users/<int:user_id>/reject', methods=['POST'])
def reject_user_by_id(user_id: int):
    """승인 요청을 거절 처리한다."""
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET approval_status = 'rejected' WHERE id = ?",
            (user_id,),
        )
        conn.commit()

    return success('User rejected successfully')


@admin_bp.route('/admin/api/users/<int:user_id>', methods=['DELETE'])
def soft_delete_user(user_id: int):
    """사용자를 소프트 삭제 처리한다."""
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET is_deleted = 1, deleted_at = datetime('now') WHERE id = ?",
            (user_id,),
        )
        conn.commit()

    return success('User status updated')


@admin_bp.route('/admin/api/users/<int:user_id>/restore', methods=['POST'])
def restore_user(user_id: int):
    """삭제/비활성/미승인 상태의 계정을 즉시 복구한다."""
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    with get_conn() as conn:
        row = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return error('user not found', status=404)
        conn.execute(
            "UPDATE users SET is_deleted = 0, is_active = 1, approval_status = 'approved' WHERE id = ?",
            (user_id,),
        )
        conn.commit()

    return success('User restored successfully')


@admin_bp.route('/admin/api/users/<int:user_id>/purge', methods=['POST'])
def purge_user(user_id: int):
    """특정 사용자의 모든 데이터를 완전히 삭제한다."""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    base_users_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'user_data')
    user_dir = os.path.join(base_users_dir, str(user_id))

    with get_conn() as conn:
        user_row = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user_row:
            return error('user not found', status=404)

        try:
            conn.execute("DELETE FROM token_history WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM usage_logs WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM conversion_logs WHERE user_id = ?", (user_id,))
        except Exception:
            pass

        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()

    try:
        if os.path.isdir(user_dir):
            shutil.rmtree(user_dir)
    except Exception as exc:
        return success(f'User deleted (file cleanup issues: {str(exc)})')

    return success('User and related files purged')


@admin_bp.route('/admin/api/users/purge-all', methods=['POST'])
def purge_all_users():
    """지정한 관리자 계정을 제외하고 모든 사용자를 삭제한다."""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    data = request.get_json(silent=True) or {}
    keep_username = data.get('keep_username') or 'kweon4309'

    base_users_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'user_data')

    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        keeper = conn.execute(
            "SELECT id FROM users WHERE username = ? AND COALESCE(is_deleted,0)=0",
            (keep_username,),
        ).fetchone()
        if not keeper:
            return error('keeper not found', status=404)

        keep_id = keeper['id']
        rows = conn.execute("SELECT id FROM users WHERE id != ?", (keep_id,)).fetchall()
        target_ids = [row['id'] for row in rows]

        for target_id in target_ids:
            try:
                conn.execute("DELETE FROM token_history WHERE user_id = ?", (target_id,))
                conn.execute("DELETE FROM usage_logs WHERE user_id = ?", (target_id,))
                conn.execute("DELETE FROM conversion_logs WHERE user_id = ?", (target_id,))
            except Exception:
                pass

        conn.execute("DELETE FROM users WHERE id != ?", (keep_id,))
        conn.commit()

    try:
        if os.path.isdir(base_users_dir):
            for name in os.listdir(base_users_dir):
                if name.isdigit() and int(name) != keep_id:
                    shutil.rmtree(os.path.join(base_users_dir, name), ignore_errors=True)
    except Exception:
        pass

    return success('All users and files purged except keeper')


@admin_bp.route('/admin/api/approve-user', methods=['POST'])
def approve_user_from_payload():
    """사용자 ID를 payload로 받아 승인한다."""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    if not user_id:
        return error('User ID is required', status=400)

    with get_conn() as conn:
        target_user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        if not target_user:
            return error('User not found', status=404)

        conn.execute(
            "UPDATE users SET approval_status = 'approved', is_active = 1 WHERE id = ?",
            (user_id,),
        )
        conn.commit()

    return success('User approved successfully')


@admin_bp.route('/admin/api/delete-user', methods=['POST'])
def delete_user_from_payload():
    """사용자 ID를 payload로 받아 소프트 삭제한다."""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    if not user_id:
        return error('User ID is required', status=400)

    with get_conn() as conn:
        target_user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        if not target_user:
            return error('User not found', status=404)

        conn.execute(
            "UPDATE users SET is_deleted = 1, deleted_at = datetime('now') WHERE id = ?",
            (user_id,),
        )
        conn.commit()

    return success('User soft-deleted successfully')


@admin_bp.route('/admin/api/users/<int:user_id>/change-plan', methods=['POST'])
@admin_bp.route('/admin/api/users/<int:user_id>/update-plan', methods=['POST'])
def change_user_plan(user_id: int):
    """사용자의 요금제를 변경한다."""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    data = request.get_json(silent=True) or {}
    plan_type = data.get('plan_type')

    valid_plan_types = ['free', 'vip', 'premium-vip', 'gold-vip']
    if not plan_type or plan_type not in valid_plan_types:
        return error(f'유효하지 않은 플랜 유형입니다. 가능한 값: {", ".join(valid_plan_types)}', status=400)

    admin_user_id = current_user_id()
    conn = get_conn()
    try:
        conn.row_factory = sqlite3.Row

        admin_user = conn.execute(
            "SELECT username FROM users WHERE id = ? AND is_admin = 1",
            (admin_user_id,),
        ).fetchone()
        if not admin_user:
            return error('Administrator privileges required', status=403)

        target_user = conn.execute(
            "SELECT username, plan_type FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not target_user:
            return error('User not found', status=404)

        previous_plan = target_user['plan_type']
        conn.execute("UPDATE users SET plan_type = ? WHERE id = ?", (plan_type, user_id))
        conn.execute(
            "INSERT INTO token_history (user_id, changed_by, amount, change_type, meta, created_at) VALUES (?, ?, 0, 'plan_change', ?, datetime('now'))",
            (user_id, admin_user_id, f'plan:{previous_plan}->{plan_type}'),
        )
        conn.commit()

        return success(f'사용자 플랜이 {plan_type}으로 변경되었습니다 (이전: {previous_plan})')
    finally:
        conn.close()
