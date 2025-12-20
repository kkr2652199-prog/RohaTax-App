import os
import secrets
import sys


def get_env(key: str, default: str | None = None) -> str:
    """
    환경 변수 조회 유틸리티.
    - 값이 설정되지 않았거나 빈 문자열("")인 경우 default를 사용한다.
    - default도 없으면 빈 문자열을 반환한다.
    """
    value = os.getenv(key)
    if value is None or value == "":
        return default or ""
    return value


class Settings:
    # 환경 감지
    ENVIRONMENT: str = get_env("ENVIRONMENT", "development")
    
    # SECRET_KEY 필수화 (프로덕션에서는 필수, 개발에서는 경고)
    SECRET_KEY: str = get_env("SECRET_KEY", "")
    
    if not SECRET_KEY:
        if ENVIRONMENT == "production":
            print("❌ CRITICAL: SECRET_KEY must be set in production environment!")
            print("Set SECRET_KEY environment variable and restart the server.")
            sys.exit(1)
        else:
            # 개발 환경: 임시 키 생성 및 경고
            SECRET_KEY = secrets.token_hex(32)
            print("⚠️  WARNING: SECRET_KEY not set. Using temporary key for development.")
            print(f"⚠️  Generated temporary key: {SECRET_KEY}")
            print("⚠️  Set SECRET_KEY in .env file for consistent sessions.")
    
    # DEBUG 모드 (기본값 false로 변경, 성능 최적화)
    # 개발 환경에서도 기본적으로 False로 설정하여 성능 저하 방지
    # 필요시 .env 파일에서 DEBUG=true로 명시적 설정
    # 프로덕션 환경에서는 무조건 False로 강제 (보안)
    if ENVIRONMENT == "production":
        # 프로덕션 환경에서는 DEBUG 모드 강제 비활성화
        DEBUG = False
        if get_env("DEBUG", "false").lower() == "true":
            print("❌ CRITICAL: DEBUG mode cannot be enabled in production!")
            print("DEBUG mode is automatically disabled in production for security.")
            sys.exit(1)
    else:
        # 개발/스테이징 환경에서는 환경 변수로 제어
        DEBUG = get_env("DEBUG", "false").lower() == "true"
    
    PORT: int = int(get_env("PORT", "5001"))  # homepage1 워크트리 기본 포트: 5001
    HOST: str = get_env("HOST", "127.0.0.1")
    
    # 데이터베이스 설정
    DATABASE_URL: str = get_env("DATABASE_URL", "sqlite:///database/app.db")
    
    # 파일 업로드 설정
    MAX_FILE_SIZE: int = int(get_env("MAX_FILE_SIZE", "52428800"))  # 50MB
    UPLOAD_FOLDER: str = get_env("UPLOAD_FOLDER", "uploads")
    OUTPUT_FOLDER: str = get_env("OUTPUT_FOLDER", "output")
    
    # 세션 설정
    SESSION_TIMEOUT: int = int(get_env("SESSION_TIMEOUT", "86400"))  # 24시간
    PERMANENT_SESSION_LIFETIME: int = int(get_env("PERMANENT_SESSION_LIFETIME", "86400"))
    
    # 로깅 설정
    LOG_LEVEL: str = get_env("LOG_LEVEL", "INFO")
    LOG_FOLDER: str = get_env("LOG_FOLDER", "logs")
    
    # 보안 설정
    CSRF_ENABLED: bool = get_env("CSRF_ENABLED", "true").lower() == "true"
    RATE_LIMIT_ENABLED: bool = get_env("RATE_LIMIT_ENABLED", "true").lower() == "true"
    
    # 토큰 시스템 설정
    DEFAULT_TOKEN_BALANCE: int = int(get_env("DEFAULT_TOKEN_BALANCE", "100"))
    TOKEN_COST_PER_CONVERSION: int = int(get_env("TOKEN_COST_PER_CONVERSION", "1"))
    
    # 프론트엔드 URL 설정 (이메일 링크용)
    FRONTEND_URL: str = get_env("FRONTEND_URL", "http://localhost:3000")


settings = Settings()





