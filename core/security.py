import os
import hmac
import hashlib
import uuid  # Python 3.14에서 성능이 향상된 UUID 모듈
from flask import session


def _get_csrf_secret() -> bytes:
    secret = session.get('_csrf_secret')
    if not secret:
        secret = os.urandom(32)
        session['_csrf_secret'] = secret
    return secret


def generate_csrf_token() -> str:
    secret = _get_csrf_secret()
    msg = os.urandom(16)
    token = hmac.new(secret, msg, hashlib.sha256).hexdigest()
    session['_csrf_token'] = token
    return token


def validate_csrf_token(token: str | None) -> bool:
    if not token:
        return False
    expected = session.get('_csrf_token')
    if not expected:
        return False
def generate_secure_id() -> str:
    """
    Python 3.14의 향상된 UUID 성능을 활용한 보안 ID 생성
    Free-Threaded Python의 GIL 제거로 인한 성능 향상 활용
    """
    # Python 3.14에서 UUID 생성 성능이 크게 향상됨
    return str(uuid.uuid4())


def generate_session_id() -> str:
    """
    세션용 고유 ID 생성 (Python 3.14 최적화)
    """
    return str(uuid.uuid4())


def generate_file_id() -> str:
    """
    파일 처리용 고유 ID 생성 (Python 3.14 최적화)
    """
    return str(uuid.uuid4())


















