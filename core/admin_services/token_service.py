"""서비스 레이어: 관리자 토큰 관리 로직."""

from __future__ import annotations

import sqlite3
from typing import Iterable, List, Sequence

from core.db import get_conn_optimized as get_conn


class TokenServiceError(Exception):
    """토큰 서비스 전용 예외."""


def _ensure_admin(conn, admin_user_id: int) -> None:
    row = conn.execute(
        "SELECT username, is_admin FROM users WHERE id = ?",
        (admin_user_id,),
    ).fetchone()
    if not row or not row["is_admin"]:
        raise TokenServiceError('Administrator privileges required')


def _ensure_user_exists(conn, user_id: int) -> None:
    row = conn.execute(
        "SELECT id FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if not row:
        raise TokenServiceError('User not found')


def grant_tokens(user_id: int, amount: int, admin_user_id: int) -> None:
    if amount <= 0:
        raise TokenServiceError('Token amount must be greater than zero')

    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        _ensure_admin(conn, admin_user_id)
        _ensure_user_exists(conn, user_id)

        conn.execute(
            "UPDATE users SET token_balance = COALESCE(token_balance,0) + ? WHERE id = ?",
            (amount, user_id),
        )
        conn.execute(
            """
            INSERT INTO token_history (user_id, changed_by, amount, change_type, created_at)
            VALUES (?, ?, ?, 'grant', datetime('now'))
            """,
            (user_id, admin_user_id, amount),
        )
        conn.commit()


def reset_tokens(user_id: int, admin_user_id: int) -> None:
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        _ensure_admin(conn, admin_user_id)
        _ensure_user_exists(conn, user_id)

        conn.execute(
            "UPDATE users SET token_balance = 0, tokens_used = 0 WHERE id = ?",
            (user_id,),
        )
        conn.execute(
            """
            INSERT INTO token_history (user_id, changed_by, amount, change_type, created_at)
            VALUES (?, ?, 0, 'reset', datetime('now'))
            """,
            (user_id, admin_user_id),
        )
        conn.commit()


def get_token_history(admin_user_id: int, limit: int = 50) -> List[dict]:
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        _ensure_admin(conn, admin_user_id)

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
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def delete_token_history_entries(ids: Sequence[int], admin_user_id: int) -> None:
    if not ids:
        raise TokenServiceError('No token history selected')

    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        _ensure_admin(conn, admin_user_id)

        placeholders = ','.join(['?'] * len(ids))
        conn.execute(
            f"DELETE FROM token_history WHERE id IN ({placeholders})",
            list(ids),
        )
        conn.commit()


def grant_tokens_bulk(user_id: int, amount: int, admin_user_id: int) -> None:
    grant_tokens(user_id, amount, admin_user_id)


def reset_tokens_bulk(user_id: int, admin_user_id: int) -> None:
    reset_tokens(user_id, admin_user_id)
