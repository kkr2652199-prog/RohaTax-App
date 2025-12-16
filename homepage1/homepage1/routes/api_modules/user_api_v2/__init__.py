"""
User API v2 모듈 패키지
엔진룸 정비 - 무중단 교체 전략
Repository-Service-Router 패턴 적용
"""
from flask import Blueprint
from .routes import create_user_api_blueprint

# Blueprint 생성 및 노출
user_api_v2_bp = create_user_api_blueprint()

__all__ = ['user_api_v2_bp']

