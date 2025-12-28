"""
보안 강화 및 프로덕션 환경 설정
- 환경별 설정 관리
- 보안 헤더 설정
- HTTPS 설정
- 접근 제어
"""

import os
import logging
from typing import Dict, Any
from datetime import timedelta

logger = logging.getLogger(__name__)

class SecurityConfig:
    """보안 설정 관리 클래스"""
    
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """환경별 설정 로드"""
        base_config = {
            'SECRET_KEY': os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
            'DEBUG': os.getenv('DEBUG', 'false').lower() == 'true',
            'PORT': int(os.getenv('PORT', '8080')),
            'HOST': os.getenv('HOST', '127.0.0.1'),
        }
        
        if self.environment == 'production':
            return self._production_config(base_config)
        elif self.environment == 'staging':
            return self._staging_config(base_config)
        else:
            return self._development_config(base_config)
    
    def _development_config(self, base: Dict[str, Any]) -> Dict[str, Any]:
        """개발 환경 설정"""
        return {
            **base,
            'DEBUG': True,
            'LOG_LEVEL': 'DEBUG',
            'CORS_ORIGINS': ['http://localhost:8080', 'http://127.0.0.1:8080'],
            'SESSION_COOKIE_SECURE': False,
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax',
            'PERMANENT_SESSION_LIFETIME': timedelta(hours=24),
            'MAX_CONTENT_LENGTH': 50 * 1024 * 1024,  # 50MB
            'RATE_LIMIT': '1000/hour',
            'SECURITY_HEADERS': {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'SAMEORIGIN',
                'X-XSS-Protection': '1; mode=block',
                'Content-Security-Policy': (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://static.cloudflareinsights.com https://unpkg.com https://cdn.tailwindcss.com; "
                    "script-src-elem 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://static.cloudflareinsights.com https://unpkg.com https://cdn.tailwindcss.com; "
                    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                    "style-src-elem 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                    "img-src 'self' data: https://cdn.jsdelivr.net https://assets.codepen.io https://images.unsplash.com; "
                    "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
                    "connect-src 'self' https://static.cloudflareinsights.com https://generativelanguage.googleapis.com https://ai.googleapis.com https://us-central1-aiplatform.googleapis.com"
                )
            }
        }
    
    def _staging_config(self, base: Dict[str, Any]) -> Dict[str, Any]:
        """스테이징 환경 설정"""
        return {
            **base,
            'DEBUG': False,
            'LOG_LEVEL': 'INFO',
            'CORS_ORIGINS': [os.getenv('STAGING_URL', 'https://staging.1tax.app')],
            'SESSION_COOKIE_SECURE': True,
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Strict',
            'PERMANENT_SESSION_LIFETIME': timedelta(hours=12),
            'MAX_CONTENT_LENGTH': 25 * 1024 * 1024,  # 25MB
            'RATE_LIMIT': '500/hour',
            'SECURITY_HEADERS': {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
                'Content-Security-Policy': (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://static.cloudflareinsights.com https://unpkg.com https://cdn.tailwindcss.com; "
                    "script-src-elem 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://static.cloudflareinsights.com https://unpkg.com https://cdn.tailwindcss.com; "
                    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                    "style-src-elem 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                    "img-src 'self' data: https://cdn.jsdelivr.net https://assets.codepen.io https://images.unsplash.com; "
                    "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
                    "connect-src 'self' https://static.cloudflareinsights.com https://generativelanguage.googleapis.com https://ai.googleapis.com https://us-central1-aiplatform.googleapis.com"
                )
            }
        }
    
    def _production_config(self, base: Dict[str, Any]) -> Dict[str, Any]:
        """프로덕션 환경 설정"""
        return {
            **base,
            'DEBUG': False,
            'LOG_LEVEL': 'WARNING',
            'CORS_ORIGINS': [os.getenv('PRODUCTION_URL', 'https://1tax.app')],
            'SESSION_COOKIE_SECURE': True,
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Strict',
            'PERMANENT_SESSION_LIFETIME': timedelta(hours=8),
            'MAX_CONTENT_LENGTH': 10 * 1024 * 1024,  # 10MB
            'RATE_LIMIT': '100/hour',
            'SECURITY_HEADERS': {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
                'Content-Security-Policy': (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://static.cloudflareinsights.com https://unpkg.com https://cdn.tailwindcss.com; "
                    "script-src-elem 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://static.cloudflareinsights.com https://unpkg.com https://cdn.tailwindcss.com; "
                    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                    "style-src-elem 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                    "img-src 'self' data: https://cdn.jsdelivr.net https://assets.codepen.io https://images.unsplash.com; "
                    "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
                    "connect-src 'self' https://static.cloudflareinsights.com https://generativelanguage.googleapis.com https://ai.googleapis.com https://us-central1-aiplatform.googleapis.com"
                ),
                'Referrer-Policy': 'strict-origin-when-cross-origin',
                'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
            },
            'DATABASE_URL': os.getenv('DATABASE_URL'),
            'REDIS_URL': os.getenv('REDIS_URL'),
            'SENTRY_DSN': os.getenv('SENTRY_DSN')
        }
    
    def get_security_headers(self) -> Dict[str, str]:
        """보안 헤더 반환"""
        return self.config.get('SECURITY_HEADERS', {})
    
    def is_production(self) -> bool:
        """프로덕션 환경 여부"""
        return self.environment == 'production'
    
    def is_secure_cookie_required(self) -> bool:
        """보안 쿠키 필요 여부"""
        return self.config.get('SESSION_COOKIE_SECURE', False)
    
    def get_rate_limit(self) -> str:
        """속도 제한 설정"""
        return self.config.get('RATE_LIMIT', '1000/hour')
    
    def get_max_file_size(self) -> int:
        """최대 파일 크기"""
        return self.config.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024)

class SecurityMiddleware:
    """보안 미들웨어"""
    
    def __init__(self, app, security_config: SecurityConfig):
        self.app = app
        self.security_config = security_config
        self._setup_security()
    
    def _setup_security(self):
        """보안 설정 적용"""
        # 보안 헤더 설정
        @self.app.after_request
        def set_security_headers(response):
            from flask import request
            # /studio/app 경로는 라우트에서 직접 헤더를 설정하므로 예외 처리
            if request.path.startswith('/studio/app'):
                # X-Frame-Options는 라우트에서 설정하므로 제외
                headers = self.security_config.get_security_headers()
                for header, value in headers.items():
                    if header == 'X-Frame-Options':
                        continue  # 라우트에서 설정한 값 유지
                    response.headers[header] = value
            else:
                # 다른 경로는 모든 보안 헤더 적용
                headers = self.security_config.get_security_headers()
                for header, value in headers.items():
                    response.headers[header] = value
            return response
        
        # CORS 설정
        if hasattr(self.app, 'after_request'):
            @self.app.after_request
            def set_cors_headers(response):
                origins = self.security_config.config.get('CORS_ORIGINS', [])
                if origins:
                    response.headers['Access-Control-Allow-Origin'] = ', '.join(origins)
                    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                return response
        
        logger.info(f"보안 미들웨어 설정 완료 ({self.security_config.environment})")
    
    def validate_request(self, request) -> bool:
        """요청 검증"""
        # 파일 크기 검증
        if request.content_length and request.content_length > self.security_config.get_max_file_size():
            logger.warning(f"파일 크기 초과: {request.content_length} bytes")
            return False
        
        # Content-Type 검증
        if request.method == 'POST':
            content_type = request.content_type
            if not content_type or not content_type.startswith(('application/json', 'multipart/form-data', 'application/x-www-form-urlencoded')):
                logger.warning(f"잘못된 Content-Type: {content_type}")
                return False
        
        return True

class AccessControl:
    """접근 제어 시스템"""
    
    def __init__(self):
        self.blocked_ips = set()
        self.failed_attempts = {}
        self.max_failed_attempts = 5
        self.block_duration = 3600  # 1시간
    
    def check_ip_access(self, ip: str) -> bool:
        """IP 접근 권한 확인"""
        if ip in self.blocked_ips:
            logger.warning(f"차단된 IP 접근 시도: {ip}")
            return False
        return True
    
    def record_failed_attempt(self, ip: str):
        """실패한 접근 시도 기록"""
        if ip not in self.failed_attempts:
            self.failed_attempts[ip] = 0
        
        self.failed_attempts[ip] += 1
        
        if self.failed_attempts[ip] >= self.max_failed_attempts:
            self.blocked_ips.add(ip)
            logger.warning(f"IP 차단: {ip} (실패 횟수: {self.failed_attempts[ip]})")
    
    def reset_failed_attempts(self, ip: str):
        """실패 시도 횟수 초기화"""
        if ip in self.failed_attempts:
            del self.failed_attempts[ip]

# 전역 인스턴스
security_config = SecurityConfig()
access_control = AccessControl()
