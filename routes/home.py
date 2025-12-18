from flask import Blueprint, render_template, request, redirect, url_for, flash
import logging
from core.responses import success, error
from core.db import get_conn_optimized as get_conn
from core.validation_utils import RegistrationValidator
from core.password_utils import hash_password, verify_password
import os
import sqlite3
from flask import session
from flask import jsonify

from .utils.auth import current_user_id, ensure_admin_view, ensure_logged_in_view
from routes.payment_routes import _build_shop_context

home_bp = Blueprint('home', __name__)


@home_bp.route('/')
def home():
    """
    메인 홈페이지
    - payment_routes._build_shop_context()에서 생성한 공통 상품 컨텍스트 사용
    - 상점/쇼룸과 동일한 event_products / free_token_product / free_period_product 등을 전달
    """
    try:
        context = _build_shop_context()
        return render_template('homepage.html', **context)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"홈페이지 컨텍스트 생성 실패: {str(e)}")
        # 에러 발생 시 최소한 페이지는 열리도록 기본 값만 전달
        return render_template('homepage.html', products=[])

@home_bp.route('/old')
def old_home():
    return render_template('index.html')




@home_bp.route('/admin/email-settings')
def admin_email_settings():
    """관리자 이메일 인증 설정 페이지 (리다이렉트)"""
    response = ensure_admin_view()
    if response:
        return response
    
    # 관리자 대시보드의 설정 탭으로 리다이렉트
    return redirect(url_for('admin.admin_dashboard') + '#settings')


@home_bp.route('/admin/email-settings/update', methods=['POST'])
def admin_email_settings_update():
    """관리자 이메일 인증 설정 업데이트 (리다이렉트)"""
    response = ensure_admin_view()
    if response:
        return response
    
    # 관리자 대시보드의 설정 탭으로 리다이렉트
    return redirect(url_for('admin.admin_dashboard') + '#settings')




