"""서비스 레이어: 관리자 토큰 관리 로직."""

from __future__ import annotations

import sqlite3
import logging
import json
from datetime import datetime
from typing import Iterable, List, Sequence, Dict, Any

from core.db import get_conn_optimized as get_conn
from core.activity_service import record_activity  # 기록관 연동 모듈 추가

logger = logging.getLogger(__name__)


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
                'reason': '관리자에 의한 수동 지급 (관리자 수동)'
            },
            'token_change': amount,  # 지급은 양수
            'potential_cost': 0,     # 비용이 아니므로 0
            'token_balance_before': token_balance_before,
            'token_balance_after': token_balance_after,
            'user_plan_snapshot': plan_type
        }
        
        # 범용 기록 함수 호출 (이 함수가 token_balance를 업데이트함)
        record_activity(cursor, activity_data)
        
        # token_history에도 기록 (무료 토큰 - 만료 체크용)
        # 관리자가 지급한 토큰은 무료 토큰으로 분류
        import json
        from datetime import datetime, timedelta
        
        # 무료 토큰은 기본적으로 만료일 없음 (필요시 추가 가능)
        expires_at = None
        
        grant_meta = json.dumps({
            'granted_by': admin_user_id,
            'reason': '관리자에 의한 수동 지급',
            'activity_type': 'TOKEN_GRANT_BY_ADMIN'
        }, ensure_ascii=False)
        
        conn.execute(
            """
            INSERT INTO token_history
            (user_id, changed_by, amount, change_type, meta, expires_at, source_type, created_at)
            VALUES (?, ?, ?, 'grant', ?, ?, 'FREE', datetime('now', 'localtime'))
            """,
            (
                user_id,
                admin_user_id,
                amount,
                grant_meta,
                expires_at
            )
        )
        
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
            """
            SELECT 
                username,
                COALESCE(token_balance, 0) AS token_balance,
                COALESCE(tokens_used, 0)   AS tokens_used,
                plan_type,
                subscription_end_date,
                free_trial_expired_at
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()
        
        if not user_row:
            raise TokenServiceError(f'User not found: {user_id}')

        token_balance_before = user_row['token_balance'] or 0
        tokens_used_before = user_row['tokens_used'] or 0
        plan_type_before = user_row['plan_type'] or 'free'
        subscription_end_date_before = user_row['subscription_end_date']
        free_trial_expired_at_before = user_row['free_trial_expired_at']
        
        # 2. 완전 초기화: 토큰, 등급, 구독 기간, 무료 체험 정보 모두 초기화
        conn.execute(
            """
            UPDATE users
            SET
                token_balance        = 0,
                tokens_used          = 0,
                plan_type            = 'free',
                subscription_end_date = NULL,
                free_trial_expired_at = NULL,
                updated_at           = datetime('now', 'localtime')
            WHERE id = ?
            """,
            (user_id,),
        )

        # 2-1. 무료 이벤트(1인 1회 제한) 사용 이력 초기화
        # 기존 결제 내역은 남기되, status를 'reset_by_admin'으로 변경하여
        # 1회 제한 체크(where status='completed')에서는 제외되도록 처리한다.
        cursor.execute(
            """
            UPDATE payment_history
            SET status = 'reset_by_admin'
            WHERE user_id = ?
              AND status = 'completed'
              AND product_id IN (
                  SELECT id FROM products WHERE COALESCE(one_time_limit, 0) = 1
              )
            """,
            (user_id,),
        )
        
        # 2-2. 무료 토큰 로그 삭제 (token_history에서 무료 토큰 기록 삭제)
        # 일반사용자 관리 페이지에 남아있는 무료 토큰 로그도 함께 삭제
        # SQLite는 json_set을 지원하지 않으므로 Python에서 처리
        # source_type='FREE'인 기록과 무료 이벤트 상품(p.price=0, p.type='event')의 기록 모두 삭제
        free_token_records = cursor.execute(
            """
            SELECT th.id, th.meta
            FROM token_history th
            LEFT JOIN payment_history ph ON ph.user_id = th.user_id 
                AND ABS(JULIANDAY(ph.created_at) - JULIANDAY(th.created_at)) < 0.01
            LEFT JOIN products p ON p.id = ph.product_id
            WHERE th.user_id = ?
              AND th.change_type IN ('grant', 'expire')
              AND (
                  COALESCE(th.source_type, 'PAID') = 'FREE'
                  OR (p.type = 'event' AND p.price = 0 AND p.token_amount > 0)
              )
            """,
            (user_id,)
        ).fetchall()
        
        deleted_free_token_count = 0
        for record in free_token_records:
            try:
                # 기존 meta 파싱
                if record['meta']:
                    try:
                        meta_dict = json.loads(record['meta'])
                    except (json.JSONDecodeError, TypeError):
                        meta_dict = {}
                else:
                    meta_dict = {}
                
                # 삭제 정보 추가
                meta_dict['deleted'] = 1
                meta_dict['deleted_reason'] = '관리자에 의한 전체 초기화'
                meta_dict['deleted_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 업데이트
                cursor.execute(
                    """
                    UPDATE token_history
                    SET meta = ?
                    WHERE id = ?
                    """,
                    (json.dumps(meta_dict, ensure_ascii=False), record['id'])
                )
                deleted_free_token_count += 1
            except Exception as e:
                logger.error(f"무료 토큰 로그 삭제 중 오류 (record_id={record['id']}): {str(e)}")
                continue
        
        if deleted_free_token_count > 0:
            logger.info(
                f"무료 토큰 로그 삭제 완료: 사용자 ID {user_id}, 삭제된 기록 {deleted_free_token_count}건"
            )
        
        # --- [수정] 새로운 'activity_logs'에 기록 ---
        # 낡은 token_history 기록 로직은 제거합니다.
        
        # 등급 변경 여부 확인
        grade_changed = plan_type_before != 'free'
        
        activity_data = {
            'user_id': user_id,
            'performed_by_id': admin_user_id,
            'performed_by_type': 'ADMIN',
            'activity_type': 'GRADE_CHANGE' if grade_changed else 'TOKEN_RESET_BY_ADMIN',
            'details': {
                'reason': '관리자에 의한 완전 초기화 (토큰, 등급, 구독 기간 모두 초기화)',
                'reset_balance': token_balance_before,
                'reset_used': tokens_used_before,
                'old_plan_type': plan_type_before,
                'new_plan_type': 'free',
                'old_subscription_end_date': subscription_end_date_before,
                'new_subscription_end_date': None,
                'old_free_trial_expired_at': free_trial_expired_at_before,
                'new_free_trial_expired_at': None
            },
            'token_change': token_balance_before * -1,  # 보유 토큰을 0으로 만드는 변화량
            'potential_cost': 0,
            'token_balance_before': token_balance_before,
            'token_balance_after': 0,  # 초기화 후 잔액은 0
            'user_plan_snapshot': 'free'  # 초기화 후 등급은 free
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


def reset_free_tokens_only(user_id: int, admin_user_id: int) -> None:
    """
    무료로 지급된 토큰(TOKEN_GRANT_BY_ADMIN)만 초기화하고, 
    유료로 구매한 토큰(TOKEN_PURCHASE, TOKEN_CHARGE)은 유지합니다.
    이 활동을 activity_logs에 기록하여 마이홈 통합 관제실에도 반영됩니다.
    """
    
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 관리자 권한 확인
        _ensure_admin(conn, admin_user_id)
        _ensure_user_exists(conn, user_id)

        # 1. 초기화 전 사용자 정보 조회
        user_row = conn.execute(
            """
            SELECT 
                username,
                COALESCE(token_balance, 0) AS token_balance,
                COALESCE(tokens_used, 0)   AS tokens_used,
                plan_type
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()
        
        if not user_row:
            raise TokenServiceError(f'User not found: {user_id}')

        token_balance_before = user_row['token_balance'] or 0
        plan_type = user_row['plan_type'] or 'free'

        # 2. 가장 최근의 TOKEN_RESET_BY_ADMIN 이후의 무료 토큰 지급 내역 조회
        # (이미 초기화된 토큰은 제외하고, 그 이후에 지급된 무료 토큰만 계산)
        last_reset = conn.execute(
            """
            SELECT MAX(timestamp) as reset_time
            FROM activity_logs
            WHERE user_id = ? AND activity_type = 'TOKEN_RESET_BY_ADMIN'
              AND COALESCE(is_deleted, 0) = 0
            """,
            (user_id,)
        ).fetchone()
        
        reset_time = last_reset['reset_time'] if last_reset and last_reset['reset_time'] else None

        # 3. 무료 토큰 지급 내역 합계 계산 (TOKEN_GRANT_BY_ADMIN만)
        if reset_time:
            free_tokens_query = """
                SELECT COALESCE(SUM(token_change), 0) as total_free_tokens
                FROM activity_logs
                WHERE user_id = ?
                  AND activity_type = 'TOKEN_GRANT_BY_ADMIN'
                  AND timestamp > ?
                  AND COALESCE(is_deleted, 0) = 0
            """
            free_tokens_result = conn.execute(free_tokens_query, (user_id, reset_time)).fetchone()
        else:
            free_tokens_query = """
                SELECT COALESCE(SUM(token_change), 0) as total_free_tokens
                FROM activity_logs
                WHERE user_id = ?
                  AND activity_type = 'TOKEN_GRANT_BY_ADMIN'
                  AND COALESCE(is_deleted, 0) = 0
            """
            free_tokens_result = conn.execute(free_tokens_query, (user_id,)).fetchone()
        
        total_free_tokens = free_tokens_result['total_free_tokens'] or 0 if free_tokens_result else 0

        # 4. 무료 토큰이 없으면 초기화할 필요 없음
        if total_free_tokens <= 0:
            raise TokenServiceError('초기화할 무료 토큰이 없습니다')

        # 5. 토큰 잔액에서 무료 토큰만 차감 (유료 토큰은 유지)
        token_balance_after = max(0, token_balance_before - total_free_tokens)
        
        # 6. users 테이블 업데이트
        conn.execute(
            """
            UPDATE users
            SET
                token_balance = ?,
                updated_at = datetime('now', 'localtime')
            WHERE id = ?
            """,
            (token_balance_after, user_id),
        )

        # 7. activity_logs에 기록 (마이홈 통합 관제실에 반영됨)
        activity_data = {
            'user_id': user_id,
            'performed_by_id': admin_user_id,
            'performed_by_type': 'ADMIN',
            'activity_type': 'TOKEN_RESET_BY_ADMIN',
            'details': {
                'reason': '관리자에 의한 무료 토큰만 초기화',
                'reset_free_tokens': total_free_tokens,
                'reset_balance': total_free_tokens,
                'paid_tokens_preserved': token_balance_after,
                'note': '유료로 구매한 토큰은 유지되었습니다'
            },
            'token_change': total_free_tokens * -1,  # 무료 토큰만 차감
            'potential_cost': 0,
            'token_balance_before': token_balance_before,
            'token_balance_after': token_balance_after,
            'user_plan_snapshot': plan_type
        }
        
        # 범용 기록 함수 호출 (이 함수가 token_balance를 업데이트함)
        record_activity(cursor, activity_data)
        
        # 트랜잭션 커밋
        conn.commit()
