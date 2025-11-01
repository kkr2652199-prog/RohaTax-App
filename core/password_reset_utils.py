"""
비밀번호 재설정 유틸리티
"""
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


def generate_reset_token() -> str:
    """
    비밀번호 재설정을 위한 안전한 토큰을 생성합니다.
    """
    return secrets.token_urlsafe(32)


def generate_reset_token_expiry() -> str:
    """
    비밀번호 재설정 토큰의 만료 시간을 생성합니다 (1시간 후).
    """
    expiry = datetime.now() + timedelta(hours=1)
    return expiry.isoformat()


def is_token_expired(expires_at: str) -> bool:
    """
    토큰이 만료되었는지 확인합니다.
    """
    try:
        expiry = datetime.fromisoformat(expires_at)
        return datetime.now() > expiry
    except Exception as e:
        logger.error(f"토큰 만료 확인 중 오류 발생: {e}")
        return True


def validate_reset_token(token: str) -> Optional[int]:
    """
    비밀번호 재설정 토큰을 검증하고 사용자 ID를 반환합니다.
    만료되었거나 사용된 토큰인 경우 None을 반환합니다.
    """
    from core.db import get_conn
    import sqlite3
    
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT user_id, expires_at, used FROM password_reset_tokens 
            WHERE token = ?
            """,
            (token,)
        ).fetchone()
        
        if not row:
            logger.warning("비밀번호 재설정 토큰을 찾을 수 없습니다.")
            return None
        
        if row['used'] == 1:
            logger.warning("이미 사용된 비밀번호 재설정 토큰입니다.")
            return None
        
        if is_token_expired(row['expires_at']):
            logger.warning("만료된 비밀번호 재설정 토큰입니다.")
            return None
        
        return row['user_id']


def mark_token_as_used(token: str) -> bool:
    """
    비밀번호 재설정 토큰을 사용된 것으로 표시합니다.
    """
    from core.db import get_conn
    
    try:
        with get_conn() as conn:
            cursor = conn.execute(
                "UPDATE password_reset_tokens SET used = 1 WHERE token = ?",
                (token,)
            )
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"비밀번호 재설정 토큰이 사용된 것으로 표시되었습니다: {token}")
                return True
            else:
                logger.warning(f"비밀번호 재설정 토큰 업데이트 실패: {token}")
                return False
    except Exception as e:
        logger.error(f"비밀번호 재설정 토큰 업데이트 중 오류 발생: {e}")
        return False


def create_reset_token(user_id: int) -> str:
    """
    비밀번호 재설정 토큰을 생성하고 데이터베이스에 저장합니다.
    """
    from core.db import get_conn
    
    token = generate_reset_token()
    expires_at = generate_reset_token_expiry()
    
    try:
        with get_conn() as conn:
            # 기존 토큰 무효화 (이전 토큰 사용 불가)
            conn.execute(
                "UPDATE password_reset_tokens SET used = 1 WHERE user_id = ? AND used = 0",
                (user_id,)
            )
            
            # 새 토큰 생성
            conn.execute(
                """
                INSERT INTO password_reset_tokens (user_id, token, expires_at) 
                VALUES (?, ?, ?)
                """,
                (user_id, token, expires_at)
            )
            conn.commit()
            
            logger.info(f"비밀번호 재설정 토큰 생성 완료 - 사용자 ID: {user_id}")
            return token
    except Exception as e:
        logger.error(f"비밀번호 재설정 토큰 생성 중 오류 발생: {e}")
        raise


def get_user_email_from_token(token: str) -> Optional[str]:
    """
    비밀번호 재설정 토큰으로부터 사용자 이메일을 조회합니다.
    """
    from core.db import get_conn
    import sqlite3
    
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT email FROM users u
            JOIN password_reset_tokens prt ON u.id = prt.user_id
            WHERE prt.token = ? AND prt.used = 0 AND prt.expires_at > datetime('now')
            """,
            (token,)
        ).fetchone()
        
        if row:
            return row['email']
        return None






