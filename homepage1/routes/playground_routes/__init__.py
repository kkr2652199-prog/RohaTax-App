"""
Playground Routes - 블로그 포스팅 생성 도구
기존 앱과 100% 격리된 독립 모듈
"""

from flask import Blueprint

playground_bp = Blueprint(
    'playground',
    __name__,
    url_prefix='/playground',
    template_folder='../../templates/playground',
    static_folder='../../static'
)

# 라우트 모듈 import (순환 참조 방지)
# Blueprint 정의 이후에 상대 경로로 모듈을 로드하여
# app이 playground_bp를 import 할 때 라우트도 함께 등록되도록 보장한다.

# [삭제됨] 기존 블로그 엔진 비활성화 - kweon21로 대체
# from . import blog_engine

# [봉인] Power Blog 라우트 비활성화 - kweon21로 대체
# from . import power_blog_routes  # Power Blog 라우트 등록

# [리다이렉트] playground는 이제 /studio로 리다이렉트
@playground_bp.route('/')
def index():
    """Playground를 AI 블로그 스튜디오로 리다이렉트"""
    from flask import redirect, url_for
    return redirect(url_for('kweon21.kweon21_index', path=''))

