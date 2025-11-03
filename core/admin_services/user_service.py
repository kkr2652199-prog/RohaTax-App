"""서비스 레이어: 관리자 사용자 관리 로직."""

from __future__ import annotations

import os
import shutil
import sqlite3
from typing import Dict, List

from core.db import get_conn
from core.user_profile_service import user_profile_service


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
ROUTES_DIR = os.path.join(PROJECT_ROOT, 'routes')
BASE_USERS_DIR = os.path.join(ROUTES_DIR, 'user_data')


class UserServiceError(Exception):
    """일반 사용자 서비스 예외."""


def fetch_general_users() -> List[Dict]:
    users = user_profile_service.get_all_users_with_recent_usage()
    return [user for user in users if not user.get('is_admin', False)]


def fetch_admin_users() -> List[Dict]:
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, username, email, company_name, business_number, representative_name,
                   phone, address, plan_type, monthly_limit, used_count, is_active,
                   created_at, COALESCE(token_balance, 0) AS token_balance,
                   COALESCE(tokens_used, 0) AS tokens_used,
                   COALESCE(approval_status, 'pending') AS approval_status
            FROM users
            WHERE COALESCE(is_deleted, 0) = 0 AND is_admin = 1
            ORDER BY created_at ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def fetch_dashboard_stats() -> Dict:
    with get_conn() as conn:
        total_issued_tokens = conn.execute(
            "SELECT COALESCE(SUM(token_balance), 0) AS total_issued FROM users WHERE COALESCE(is_deleted, 0) = 0"
        ).fetchone()["total_issued"]

        active_users_count = conn.execute(
            """
            SELECT COUNT(*) AS active_count
            FROM users
            WHERE COALESCE(is_deleted, 0) = 0 AND is_active = 1 AND COALESCE(is_admin, 0) = 0
            """
        ).fetchone()["active_count"]

    return {
        "total_issued_tokens": total_issued_tokens,
        "active_users_count": active_users_count,
        "system_error_rate": 0.1,
        "system_uptime": 99.9,
    }


def update_user_email(user_id: int, email: str) -> None:
    with get_conn() as conn:
        cursor = conn.execute("UPDATE users SET email = ? WHERE id = ?", (email, user_id))
        if cursor.rowcount == 0:
            raise UserServiceError("user not found")
        conn.commit()


def fetch_user_conversions(user_id: int) -> List[Dict]:
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        user = conn.execute(
            "SELECT id FROM users WHERE id = ? AND is_deleted = 0",
            (user_id,),
        ).fetchone()
        if not user:
            raise UserServiceError("user not found")

        conversions = conn.execute(
            """
            SELECT id, original_filename, created_at, status, tokens_used, file_size
            FROM conversion_logs
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 20
            """,
            (user_id,),
        ).fetchall()

    return [dict(conv) for conv in conversions]


def approve_user(user_id: int) -> None:
    _execute_user_update(
        "UPDATE users SET approval_status = 'approved', is_active = 1 WHERE id = ?",
        (user_id,),
    )


def reject_user(user_id: int) -> None:
    _execute_user_update(
        "UPDATE users SET approval_status = 'rejected' WHERE id = ?",
        (user_id,),
    )


def soft_delete_user(user_id: int) -> None:
    _execute_user_update(
        "UPDATE users SET is_deleted = 1, deleted_at = datetime('now') WHERE id = ?",
        (user_id,),
    )


def restore_user(user_id: int) -> None:
    _execute_user_update(
        "UPDATE users SET is_deleted = 0, is_active = 1, approval_status = 'approved' WHERE id = ?",
        (user_id,),
    )


def purge_user(user_id: int) -> str:
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        user_row = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user_row:
            raise UserServiceError("user not found")

        try:
            conn.execute("DELETE FROM token_history WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM usage_logs WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM conversion_logs WHERE user_id = ?", (user_id,))
        except Exception:
            pass

        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()

    message = "User and related files purged"
    user_dir = os.path.join(BASE_USERS_DIR, str(user_id))
    try:
        if os.path.isdir(user_dir):
            shutil.rmtree(user_dir)
    except Exception as exc:  # pragma: no cover - 파일 시스템 상태 의존
        message = f"User deleted (file cleanup issues: {exc})"

    return message


def purge_all_users(keep_username: str) -> str:
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        keeper = conn.execute(
            "SELECT id FROM users WHERE username = ? AND COALESCE(is_deleted,0)=0",
            (keep_username,),
        ).fetchone()
        if not keeper:
            raise UserServiceError("keeper not found")

        keep_id = keeper["id"]
        rows = conn.execute("SELECT id FROM users WHERE id != ?", (keep_id,)).fetchall()
        target_ids = [row["id"] for row in rows]

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
        if os.path.isdir(BASE_USERS_DIR):
            for name in os.listdir(BASE_USERS_DIR):
                if name.isdigit() and int(name) != keep_id:
                    shutil.rmtree(os.path.join(BASE_USERS_DIR, name), ignore_errors=True)
    except Exception:  # pragma: no cover - 파일 시스템 상태 의존
        pass

    return "All users and files purged except keeper"


def approve_user_from_payload(user_id: int) -> None:
    approve_user(user_id)


def delete_user_from_payload(user_id: int) -> None:
    soft_delete_user(user_id)


VALID_PLAN_TYPES = ['free', 'vip', 'premium-vip', 'gold-vip']


def change_user_plan(user_id: int, plan_type: str, admin_user_id: int) -> str:
    if plan_type not in VALID_PLAN_TYPES:
        raise UserServiceError(
            '유효하지 않은 플랜 유형입니다. 가능한 값: ' + ', '.join(VALID_PLAN_TYPES)
        )

    with get_conn() as conn:
        conn.row_factory = sqlite3.Row

        admin_user = conn.execute(
            "SELECT username FROM users WHERE id = ? AND is_admin = 1",
            (admin_user_id,),
        ).fetchone()
        if not admin_user:
            raise UserServiceError('Administrator privileges required')

        target_user = conn.execute(
            "SELECT username, plan_type FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not target_user:
            raise UserServiceError('User not found')

        previous_plan = target_user['plan_type']
        conn.execute("UPDATE users SET plan_type = ? WHERE id = ?", (plan_type, user_id))
        conn.execute(
            """
            INSERT INTO token_history (user_id, changed_by, amount, change_type, meta, created_at)
            VALUES (?, ?, 0, 'plan_change', ?, datetime('now'))
            """,
            (user_id, admin_user_id, f'plan:{previous_plan}->{plan_type}')
        )
        conn.commit()

    return f'사용자 플랜이 {plan_type}으로 변경되었습니다 (이전: {previous_plan})'


def _execute_user_update(query: str, params: tuple) -> None:
    with get_conn() as conn:
        cursor = conn.execute(query, params)
        if cursor.rowcount == 0:
            raise UserServiceError("user not found")
        conn.commit()
