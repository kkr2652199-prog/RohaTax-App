"""
비밀번호 해싱 유틸리티 모듈
bcrypt를 사용한 안전한 비밀번호 해싱 및 검증
"""

import bcrypt
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """
    비밀번호를 bcrypt로 해싱하여 안전하게 저장
    
    Args:
        password: 사용자가 입력한 평문 비밀번호
        
    Returns:
        str: bcrypt 해시된 비밀번호 문자열
        
    Example:
        >>> hashed = hash_password("mySecret123")
        >>> print(hashed)
        '$2b$12$LQv3c1yqBWcVmGd.eHo9Nu.kHWhpz5rOntvyBOHIS0Hg7EXiK9H4W'
    """
    try:
        # bcrypt로 비밀번호 해싱 (salt 자동 생성)
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"비밀번호 해싱 실패: {str(e)}")
        raise ValueError(f"비밀번호 해싱 중 오류가 발생했습니다: {str(e)}")


def verify_password(password: str, hashed: str) -> bool:
    """
    사용자가 입력한 비밀번호와 저장된 해시를 비교 검증
    bcrypt와 pbkdf2 형식을 모두 지원합니다.
    
    Args:
        password: 사용자가 입력한 평문 비밀번호
        hashed: 데이터베이스에 저장된 해시값 (bcrypt 또는 pbkdf2)
        
    Returns:
        bool: 비밀번호 일치 여부 (True: 일치, False: 불일치)
        
    Example:
        >>> stored_hash = "$2b$12$LQv3c1yqBWcVmGd.eHo9Nu.kHWhpz5rOntvyBOHIS0Hg7EXiK9H4W"
        >>> verify_password("mySecret123", stored_hash)
        True
        >>> verify_password("wrongPassword", stored_hash)
        False
    """
    try:
        # bcrypt 형식 확인
        if hashed.startswith('$2b$') or hashed.startswith('$2a$'):
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        
        # pbkdf2 형식 확인 (salt:hash 형식)
        if ':' in hashed:
            import hashlib
            try:
                salt, stored_hash = hashed.split(':', 1)
                password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
                return password_hash.hex() == stored_hash
            except Exception as e:
                logger.warning(f"pbkdf2 검증 실패: {str(e)}")
                return False
        
        # 평문 비밀번호인 경우 (구버전 데이터)
        logger.warning("평문 비밀번호 감지: 마이그레이션이 필요할 수 있습니다")
        return password == hashed
    except Exception as e:
        logger.error(f"비밀번호 검증 실패: {str(e)}")
        return False


def needs_migration(stored_password: str) -> bool:
    """
    비밀번호가 마이그레이션(해싱)이 필요한지 확인
    
    Args:
        stored_password: 저장된 비밀번호 문자열
        
    Returns:
        bool: 마이그레이션 필요 여부 (True: 필요, False: 불필요)
        
    Example:
        >>> needs_migration("plainPassword123")
        True  # 평문이므로 마이그레이션 필요
        >>> needs_migration("$2b$12$...")
        False  # 이미 해시되어 있음
    """
    return not stored_password.startswith('$2b$') and not stored_password.startswith('$2a$')


def migrate_password(old_password: str) -> str:
    """
    평문 비밀번호를 bcrypt 해시로 마이그레이션
    
    Args:
        old_password: 평문 비밀번호
        
    Returns:
        str: bcrypt 해시된 비밀번호
        
    Example:
        >>> migrated = migrate_password("oldPlainPassword")
        >>> print(migrated)
        '$2b$12$LQv3c1yqBWcVmGd.eHo9Nu.kHWhpz5rOntvyBOHIS0Hg7EXiK9H4W'
    """
    return hash_password(old_password)






