"""토큰 관련 비즈니스 로직을 담당하는 서비스 모듈"""
import sqlite3
import logging
from core.db import get_conn

logger = logging.getLogger(__name__)


def calculate_available_tokens(balance: int, used: int) -> int:
    """
    토큰 잔량을 계산하는 표준 유틸리티 함수
    
    Args:
        balance: 총 지급된 토큰
        used: 사용된 토큰
        
    Returns:
        int: 사용 가능한 토큰 (balance - used)
    """
    return max(0, (balance or 0) - (used or 0))


def get_token_status_from_user_table(user_id: int) -> dict:
    """
    users 테이블 기반의 빠른 토큰 상태 조회 함수
    
    성능 최적화를 위해 users 테이블의 캐시된 값을 사용합니다.
    정확성이 중요한 경우 get_token_status_from_activity_log()를 사용하세요.
    
    Args:
        user_id: 사용자 ID
        
    Returns:
        dict: {
            'token_balance': int,  # 총 지급된 토큰
            'tokens_used': int,    # 사용된 토큰
            'available_tokens': int  # 사용 가능한 토큰
        }
        사용자를 찾을 수 없으면 None 반환
    """
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        user = conn.execute(
            "SELECT token_balance, COALESCE(tokens_used, 0) as tokens_used FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        
        if not user:
            logger.warning(f"사용자 ID {user_id}를 찾을 수 없음")
            return None
        
        token_balance = user['token_balance'] or 0
        tokens_used = user['tokens_used'] or 0
        available_tokens = calculate_available_tokens(token_balance, tokens_used)
        
        return {
            'token_balance': token_balance,
            'tokens_used': tokens_used,
            'available_tokens': available_tokens
        }


def get_token_status_from_activity_log(user_id: int) -> dict:
    """
    activity_logs 기반의 가장 정확한 토큰 상태 계산 함수
    
    activity_logs 테이블의 모든 토큰 변경 이력을 집계하여 정확한 잔액을 계산합니다.
    TOKEN_RESET_BY_ADMIN 이벤트 이후의 로그만을 대상으로 계산합니다.
    
    Args:
        user_id: 사용자 ID
        
    Returns:
        dict: {
            'token_balance': int,  # 총 지급된 토큰 (activity_logs 기반)
            'tokens_used': int,    # 사용된 토큰 (activity_logs 기반)
            'available_tokens': int  # 사용 가능한 토큰
        }
        사용자를 찾을 수 없으면 None 반환
    """
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        
        # 사용자 존재 확인
        user = conn.execute(
            "SELECT id FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        
        if not user:
            logger.warning(f"사용자 ID {user_id}를 찾을 수 없음")
            return None
        
        # activity_logs 기반 토큰 계산
        summary = conn.execute(
            """
            WITH last_reset AS (
                -- 1. 가장 최근의 TOKEN_RESET_BY_ADMIN 이벤트의 timestamp를 찾는다.
                SELECT MAX(timestamp) as reset_time
                FROM activity_logs
                WHERE user_id = ? AND activity_type = 'TOKEN_RESET_BY_ADMIN'
                  AND COALESCE(is_deleted, 0) = 0
            )
            SELECT
                -- 2. 해당 리셋 시간 이후의 모든 로그만을 대상으로 집계한다.
                -- 단, TOKEN_RESET_BY_ADMIN의 token_change는 사용량 계산에서 제외한다.
                COALESCE(SUM(CASE WHEN al.token_change > 0 AND al.activity_type != 'TOKEN_RESET_BY_ADMIN' THEN al.token_change ELSE 0 END), 0) as total_charged,
                COALESCE(SUM(CASE WHEN al.token_change < 0 AND al.activity_type != 'TOKEN_RESET_BY_ADMIN' THEN ABS(al.token_change) ELSE 0 END), 0) as total_used
            FROM activity_logs al, last_reset lr
            WHERE al.user_id = ?
              AND (lr.reset_time IS NULL OR al.timestamp >= lr.reset_time)
              AND COALESCE(al.is_deleted, 0) = 0
            -- 만약 리셋 기록이 없다면 (lr.reset_time IS NULL), 모든 로그를 포함한다.
            """,
            (user_id, user_id)
        ).fetchone()
        
        total_charged = summary['total_charged'] if summary else 0
        total_used = summary['total_used'] if summary else 0
        available_tokens = calculate_available_tokens(total_charged, total_used)
        
        return {
            'token_balance': total_charged,
            'tokens_used': total_used,
            'available_tokens': available_tokens
        }


def get_user_token_status(user_id: int) -> dict:
    """
    사용자의 토큰 상태를 조회하는 함수 (하위 호환성 유지)
    
    현재는 users 테이블 기반의 빠른 조회를 사용합니다.
    정확성이 중요한 경우 get_token_status_from_activity_log()를 직접 호출하세요.
    
    Args:
        user_id: 사용자 ID
        
    Returns:
        dict: {
            'token_balance': int,  # 총 지급된 토큰
            'tokens_used': int,    # 사용된 토큰
            'available_tokens': int  # 사용 가능한 토큰
        }
        사용자를 찾을 수 없으면 None 반환
    """
    return get_token_status_from_user_table(user_id)





