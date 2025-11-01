"""
변환 라우트 통합 모듈
분리된 라우트 모듈들을 통합하여 관리
"""

from flask import Blueprint

# 분리된 라우트 모듈들 import
from .conversion_modules.main_routes import main_bp
from .conversion_modules.token_routes import token_bp
from .conversion_modules.user_routes import user_bp
from .conversion_modules.template_routes import template_bp
from .conversion_modules.security_routes import security_bp
from .conversion_modules.convert_routes import convert_bp

# 메인 블루프린트 생성
conversion_bp = Blueprint('conversion', __name__)

# 분리된 블루프린트들을 메인 블루프린트에 등록
conversion_bp.register_blueprint(main_bp)
conversion_bp.register_blueprint(token_bp)
conversion_bp.register_blueprint(user_bp)
conversion_bp.register_blueprint(template_bp)
conversion_bp.register_blueprint(security_bp)
conversion_bp.register_blueprint(convert_bp)

# 공통 유틸리티 함수
def _row_value(row, key, default=None):
    """sqlite3.Row 안전 접근 헬퍼"""
    try:
        value = row[key]
    except Exception:
        return default
    return default if value is None else value


