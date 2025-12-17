"""
User API 모듈 패키지
API Turbocharger 리팩토링 - Phase 1
"""
from flask import Blueprint
from .router import create_user_api_blueprint

# Blueprint 생성 및 등록
user_api_bp = create_user_api_blueprint()

__all__ = ['user_api_bp']

