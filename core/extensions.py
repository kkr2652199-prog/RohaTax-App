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
# NOTE: 스마트폰 UI/UX 개발 서버에서는 요청 제한이 개발 속도를 크게 저해하므로 기본 비활성화한다.
# - production: 기존처럼 활성화
# - non-production: 비활성화(DEV_RATE_LIMIT=1 로 강제 활성화 가능)
is_production = os.environ.get("FLASK_ENV") == "production"
force_dev_rate_limit = os.environ.get("DEV_RATE_LIMIT", "0") == "1"
is_development = (not is_production) or (is_production and force_dev_rate_limit)

# Rate Limiting 확장 객체
# app은 init_app()을 통해 나중에 초기화됩니다.
# 개발 환경에서는 제한을 완화 (1000 per hour, 10000 per day)
# 프로덕션에서는 엄격한 제한 (200 per day, 50 per hour)
if is_production and not force_dev_rate_limit:
    default_limits = ["200 per day", "50 per hour"]  # 프로덕션: 엄격한 제한
    limiter_enabled = True
else:
    # 개발 서버: 기본 비활성화(요청제한 초과 방지)
    default_limits = []
    limiter_enabled = False

limiter = Limiter(
    key_func=get_remote_address,  # IP 주소 기반 제한
    default_limits=default_limits,
    storage_uri="memory://",  # 메모리 기반 (프로덕션에서는 Redis 권장)
    enabled=limiter_enabled,
)

