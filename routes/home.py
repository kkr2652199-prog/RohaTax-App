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

home_bp = Blueprint('home', __name__)


@home_bp.route('/')
def home():
    return render_template('homepage.html')

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




