"""서비스 레이어: 관리자 토큰 관리 로직."""

from __future__ import annotations

import sqlite3
from typing import Iterable, List, Sequence, Dict, Any

from core.db import get_conn_optimized as get_conn
from core.activity_service import record_activity  # 기록관 연동 모듈 추가


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
    """사용자에게 토큰을 지급하고, 이 활동을 activity_logs에 기록합니다."""
    
    if not isinstance(amount, int) or amount <= 0:
        raise TokenServiceError('Token amount must be greater than zero')

    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 관리자 권한 확인
        _ensure_admin(conn, admin_user_id)
        _ensure_user_exists(conn, user_id)

        # 1. 사용자 정보 조회 (토큰 잔액 및 플랜 타입 포함)
        user_row = conn.execute(
            "SELECT username, COALESCE(token_balance, 0) AS token_balance, plan_type FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        
        if not user_row:
            raise TokenServiceError(f'User not found: {user_id}')

        # 2. 토큰 잔액 계산
        token_balance_before = user_row['token_balance'] or 0
        token_balance_after = token_balance_before + amount
        plan_type = user_row['plan_type'] or 'free'

        # --- [수정] 새로운 'activity_logs'에 기록 및 토큰 업데이트 ---
        # 낡은 token_history 기록 로직은 제거합니다.
        # record_activity() 함수가 token_balance를 업데이트하므로 여기서는 업데이트하지 않음
        
        activity_data = {
            'user_id': user_id,
            'performed_by_id': admin_user_id,
            'performed_by_type': 'ADMIN',
            'activity_type': 'TOKEN_GRANT_BY_ADMIN',
            'details': {
                'granted_amount': amount,
                'reason': '관리자에 의한 수동 지급'
            },
            'token_change': amount,  # 지급은 양수
            'potential_cost': 0,     # 비용이 아니므로 0
            'token_balance_before': token_balance_before,
            'token_balance_after': token_balance_after,
            'user_plan_snapshot': plan_type
        }
        
        # 범용 기록 함수 호출 (이 함수가 token_balance를 업데이트함)
        record_activity(cursor, activity_data)
        
        # 트랜잭션 커밋
        conn.commit()


def reset_tokens(user_id: int, admin_user_id: int) -> None:
    """사용자의 토큰을 초기화하고, 이 활동을 activity_logs에 기록합니다."""
    
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 관리자 권한 확인
        _ensure_admin(conn, admin_user_id)
        _ensure_user_exists(conn, user_id)

        # 1. 초기화 전 사용자 정보 조회
        user_row = conn.execute(
            "SELECT username, COALESCE(token_balance, 0) AS token_balance, COALESCE(tokens_used, 0) AS tokens_used, plan_type FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        
        if not user_row:
            raise TokenServiceError(f'User not found: {user_id}')

        token_balance_before = user_row['token_balance'] or 0
        tokens_used_before = user_row['tokens_used'] or 0
        plan_type = user_row['plan_type'] or 'free'
        
        # 2. 토큰 관련 필드 초기화
        conn.execute(
            "UPDATE users SET token_balance = 0, tokens_used = 0 WHERE id = ?",
            (user_id,),
        )
        
        # --- [수정] 새로운 'activity_logs'에 기록 ---
        # 낡은 token_history 기록 로직은 제거합니다.
        
        activity_data = {
            'user_id': user_id,
            'performed_by_id': admin_user_id,
            'performed_by_type': 'ADMIN',
            'activity_type': 'TOKEN_RESET_BY_ADMIN',
            'details': {
                'reason': '관리자에 의한 토큰 초기화',
                'reset_balance': token_balance_before,
                'reset_used': tokens_used_before
            },
            'token_change': token_balance_before * -1,  # 보유 토큰을 0으로 만드는 변화량
            'potential_cost': 0,
            'token_balance_before': token_balance_before,
            'token_balance_after': 0,  # 초기화 후 잔액은 0
            'user_plan_snapshot': plan_type
        }
        
        # 범용 기록 함수 호출
        record_activity(cursor, activity_data)
        
        # 트랜잭션 커밋
        conn.commit()


def get_token_history(limit: int = 50) -> List[Dict[str, Any]]:
    """
    [최종 변경] 비활성화된(is_deleted=1) 사용자 목록을 조회하여,
    프론트엔드가 기대하는 '이력' 형식으로 가공하여 반환합니다.
    """
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT
                id,
                username,
                email,
                deleted_at as timestamp_utc
            FROM
                users
            WHERE
                is_deleted = 1
            ORDER BY
                deleted_at DESC
            LIMIT ?
        """
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        # 프론트엔드 호환성을 위해 기존 history 형식으로 변환
        return [
            {
                "id": row["id"],
                "target_username": row["username"],
                "email": row["email"],
                "timestamp_utc": row["timestamp_utc"],
                "action": "deactivated"
            } 
            for row in rows
        ]


# --- [제거됨] 불필요한 삭제 함수 ---
# delete_token_history_entries 함수는 activity_logs의 감사 추적 목적상 제거되었습니다.
# activity_logs는 삭제 불가능한 영구 기록으로 관리됩니다.


def grant_tokens_bulk(user_id: int, amount: int, admin_user_id: int) -> None:
    grant_tokens(user_id, amount, admin_user_id)


def reset_tokens_bulk(user_id: int, admin_user_id: int) -> None:
    reset_tokens(user_id, admin_user_id)
