"""토큰 관련 비즈니스 로직을 담당하는 서비스 모듈"""
import sqlite3
import logging
from core.db import get_conn

logger = logging.getLogger(__name__)


def get_user_token_status(user_id: int) -> dict:
    """
    사용자의 토큰 상태를 조회하는 함수
    
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
        available_tokens = token_balance - tokens_used
        
        return {
            'token_balance': token_balance,
            'tokens_used': tokens_used,
            'available_tokens': available_tokens
        }





