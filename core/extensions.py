"""
Flask 확장 모듈
===============
Flask 애플리케이션에서 사용하는 확장 객체들을 중앙에서 관리합니다.
순환 참조를 방지하기 위해 app 인스턴스를 여기서 생성하지 않고,
각 확장 객체는 init_app() 메서드를 통해 나중에 초기화됩니다.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Rate Limiting 확장 객체
# app은 init_app()을 통해 나중에 초기화됩니다.
limiter = Limiter(
    key_func=get_remote_address,  # IP 주소 기반 제한
    default_limits=["200 per day", "50 per hour"],  # 기본 제한
    storage_uri="memory://",  # 메모리 기반 (프로덕션에서는 Redis 권장)
)

