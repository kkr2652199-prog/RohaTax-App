import sqlite3

from flask import request

from core.db import get_conn
from core.responses import success, error

from . import admin_bp
from ..utils.auth import current_user_id, ensure_admin_for_json


@admin_bp.route('/admin/api/users/<int:user_id>/tokens/grant', methods=['POST'])
def grant_tokens_to_user(user_id: int):
    """특정 사용자에게 토큰을 지급한다."""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    conn = get_conn()
    admin_user = conn.execute(
        "SELECT username, is_admin FROM users WHERE id = ?",
        (admin_user_id,),
    ).fetchone()
    if not admin_user or not admin_user['is_admin']:
        return error('invalid admin', status=403)

    data = request.get_json(silent=True) or {}
    amount = int(data.get('amount', 0))
    if amount <= 0:
        return error('amount must be > 0', status=400)

    target_user = conn.execute(
        "SELECT username FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if not target_user:
        return error('user not found', status=404)

    conn.execute(
        "UPDATE users SET token_balance = COALESCE(token_balance,0) + ? WHERE id = ?",
        (amount, user_id),
    )
    conn.execute(
        "INSERT INTO token_history (user_id, changed_by, amount, change_type, created_at) VALUES (?, ?, ?, 'grant', datetime('now'))",
        (user_id, admin_user_id, amount),
    )
    conn.commit()

    return success('granted')


@admin_bp.route('/admin/api/users/<int:user_id>/tokens/reset', methods=['POST'])
def reset_tokens_for_user(user_id: int):
    """특정 사용자의 토큰 잔액과 사용량을 초기화한다."""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    conn = get_conn()
    admin_user = conn.execute(
        "SELECT username, is_admin FROM users WHERE id = ?",
        (admin_user_id,),
    ).fetchone()
    if not admin_user or not admin_user['is_admin']:
        return error('invalid admin', status=403)

    target_user = conn.execute(
        "SELECT username FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if not target_user:
        return error('user not found', status=404)

    conn.execute(
        "UPDATE users SET token_balance = 0, tokens_used = 0 WHERE id = ?",
        (user_id,),
    )
    conn.execute(
        "INSERT INTO token_history (user_id, changed_by, amount, change_type, created_at) VALUES (?, ?, 0, 'reset', datetime('now'))",
        (user_id, admin_user_id),
    )
    conn.commit()

    return success('reset')


@admin_bp.route('/admin/api/token-history', methods=['GET'])
def get_token_history():
    """최근 토큰 변경 이력을 조회한다."""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    admin_user_id = current_user_id()
    with get_conn() as conn:
        admin_user = conn.execute(
            "SELECT username, is_admin FROM users WHERE id = ?",
            (admin_user_id,),
        ).fetchone()
        if not admin_user or not admin_user['is_admin']:
            return error('invalid admin', status=403)

        rows = conn.execute(
            """
            SELECT th.id,
                   th.change_type AS action,
                   th.amount,
                   strftime('%Y-%m-%dT%H:%M:%SZ', th.created_at) AS timestamp_utc,
                   admin.username AS admin_username,
                   target.username AS target_username
            FROM token_history th
            JOIN users admin ON th.changed_by = admin.id
            JOIN users target ON th.user_id = target.id
            ORDER BY th.created_at DESC
            LIMIT 50
            """
        ).fetchall()

        history = [dict(row) for row in rows]
        return success('ok', data={'history': history})


@admin_bp.route('/admin/api/token-history/delete', methods=['POST'])
def delete_token_history_entries():
    """선택된 토큰 이력 항목을 삭제한다."""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    data = request.get_json(silent=True) or {}
    ids = data.get('ids') or []
    if not isinstance(ids, list) or len(ids) == 0:
        return error('No token history selected', status=400)

    try:
        id_list = [int(entry) for entry in ids]
    except Exception:
        return error('Invalid token history ID list', status=400)

    admin_user_id = current_user_id()
    with get_conn() as conn:
        admin_user = conn.execute(
            "SELECT username, is_admin FROM users WHERE id = ?",
            (admin_user_id,),
        ).fetchone()
        if not admin_user or not admin_user['is_admin']:
            return error('invalid admin', status=403)

        placeholders = ','.join(['?'] * len(id_list))
        conn.execute(
            f"DELETE FROM token_history WHERE id IN ({placeholders})",
            id_list,
        )
        conn.commit()

    return success('Selected token history entries deleted')


@admin_bp.route('/admin/api/grant-tokens', methods=['POST'])
def grant_tokens_via_payload():
    """사용자 ID와 금액을 payload로 받아 토큰을 지급한다."""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    amount = data.get('amount')

    if not user_id or not amount:
        return error('User ID and token amount are required', status=400)

    try:
        amount = int(amount)
        if amount <= 0:
            return error('Token amount must be greater than zero', status=400)
    except ValueError:
        return error('Invalid token amount', status=400)

    admin_user_id = current_user_id()
    with get_conn() as conn:
        admin_user = conn.execute(
            "SELECT username FROM users WHERE id = ? AND is_admin = 1",
            (admin_user_id,),
        ).fetchone()
        if not admin_user:
            return error('Administrator privileges required', status=403)

        target_user = conn.execute(
            "SELECT username FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not target_user:
            return error('User not found', status=404)

        conn.execute(
            "UPDATE users SET token_balance = COALESCE(token_balance, 0) + ? WHERE id = ?",
            (amount, user_id),
        )
        conn.execute(
            "INSERT INTO token_history (user_id, changed_by, amount, change_type, created_at) VALUES (?, ?, ?, 'grant', datetime('now'))",
            (user_id, admin_user_id, amount),
        )
        conn.commit()

    return success('Tokens granted successfully')


@admin_bp.route('/admin/api/reset-tokens', methods=['POST'])
def reset_tokens_via_payload():
    """사용자 ID를 payload로 받아 토큰을 초기화한다."""
    admin_user_id, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    if not user_id:
        return error('User ID is required', status=400)

    admin_user_id = current_user_id()
    with get_conn() as conn:
        admin_user = conn.execute(
            "SELECT username FROM users WHERE id = ? AND is_admin = 1",
            (admin_user_id,),
        ).fetchone()
        if not admin_user:
            return error('Administrator privileges required', status=403)

        target_user = conn.execute(
            "SELECT username FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not target_user:
            return error('User not found', status=404)

        conn.execute(
            "UPDATE users SET token_balance = 0, tokens_used = 0 WHERE id = ?",
            (user_id,),
        )
        conn.execute(
            "INSERT INTO token_history (user_id, changed_by, amount, change_type, created_at) VALUES (?, ?, 0, 'reset', datetime('now'))",
            (user_id, admin_user_id),
        )
        conn.commit()

    return success('Tokens fully reset (balance 0, used 0)')
