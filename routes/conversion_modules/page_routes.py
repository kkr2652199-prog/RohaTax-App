"""
페이지 렌더링 라우트 모듈
변환 페이지 렌더링 등의 페이지 관련 기능
"""

from flask import Blueprint, render_template, session
from core.security import generate_csrf_token
from .utils.auth import is_authenticated

page_bp = Blueprint('page', __name__)


@page_bp.route('/conversion')
def conversion():
    """변환 페이지 렌더링"""
    # 로그인 확인
    if not is_authenticated():
        return render_template(
            'conversion.html',
            guest_mode=True,
            csrf_token=generate_csrf_token(),
        )

    return render_template(
        'conversion.html',
        guest_mode=False,
        csrf_token=generate_csrf_token(),
    )

