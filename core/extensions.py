"""
Flask 확장 모듈
===============
Flask 애플리케이션에서 사용하는 확장 객체들을 중앙에서 관리합니다.
순환 참조를 방지하기 위해 app 인스턴스를 여기서 생성하지 않고,
각 확장 객체는 init_app() 메서드를 통해 나중에 초기화됩니다.
"""

import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# 개발 환경 여부 확인
is_development = os.environ.get('FLASK_ENV') != 'production'

# Rate Limiting 확장 객체
# app은 init_app()을 통해 나중에 초기화됩니다.
# 개발 환경에서는 제한을 완화 (1000 per hour, 10000 per day)
# 프로덕션에서는 엄격한 제한 (200 per day, 50 per hour)
if is_development:
    default_limits = ["10000 per day", "1000 per hour"]  # 개발 환경: 매우 완화된 제한
else:
    default_limits = ["200 per day", "50 per hour"]  # 프로덕션: 엄격한 제한

limiter = Limiter(
    key_func=get_remote_address,  # IP 주소 기반 제한
    default_limits=default_limits,
    storage_uri="memory://",  # 메모리 기반 (프로덕션에서는 Redis 권장)
)

