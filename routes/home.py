from flask import Blueprint, render_template, request, redirect, url_for, flash
import logging
from core.responses import success, error
from core.db import get_conn_optimized as get_conn
from core.validation_utils import RegistrationValidator
from core.email_verification_manager import EmailVerificationManager
from core.password_utils import hash_password, verify_password
from core.password_reset_utils import (
    create_reset_token, 
    validate_reset_token, 
    mark_token_as_used
)
from core.email_sender import send_password_reset_email
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


@home_bp.route('/email-verification-pending/<int:user_id>')
def email_verification_pending(user_id):
    """이메일 인증 대기 페이지"""
    try:
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            user = conn.execute(
                """
                SELECT username, email, email_verified, email_verification_token
                FROM users WHERE id = ? AND is_deleted = 0
                """,
                (user_id,)
            ).fetchone()
            
            if not user:
                flash('사용자 정보를 찾을 수 없습니다', 'error')
                return redirect(url_for('registration.register'))
            
            if user['email_verified']:
                flash('이미 이메일 인증이 완료되었습니다', 'info')
                return redirect(url_for('auth.login'))
            
            return render_template('email_verification_pending.html', user=user)
            
    except Exception as e:
        flash(f'페이지 로드 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('registration.register'))


@home_bp.route('/verify-email/<token>')
def verify_email(token):
    """이메일 인증 처리"""
    try:
        email_manager = EmailVerificationManager()
        is_valid, message, user_id = email_manager.verify_token(token)
        
        if is_valid:
            flash(message, 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(message, 'error')
            return redirect(url_for('registration.register'))
            
    except Exception as e:
        flash(f'인증 처리 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('registration.register'))


@home_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """이메일 인증 재발송"""
    try:
        user_id = request.form.get('user_id')
        email = request.form.get('email')
        
        if not user_id or not email:
            flash('필수 정보가 누락되었습니다', 'error')
            return redirect(url_for('registration.register'))
        
        email_manager = EmailVerificationManager()
        success, message = email_manager.resend_verification_email(int(user_id), email)
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
        
        return redirect(url_for('home.email_verification_pending', user_id=user_id))
        
    except Exception as e:
        flash(f'재발송 처리 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('registration.register'))


@home_bp.route('/api/check-verification-status/<int:user_id>')
def check_verification_status(user_id):
    """이메일 인증 상태 확인 API"""
    try:
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            user = conn.execute(
                """
                SELECT email_verified FROM users 
                WHERE id = ? AND is_deleted = 0
                """,
                (user_id,)
            ).fetchone()
            
            if not user:
                return error("사용자를 찾을 수 없습니다"), 404
            
            return success({
                "verified": bool(user['email_verified']),
                "user_id": user_id
            })
            
    except Exception as e:
        return error(f"상태 확인 중 오류가 발생했습니다: {str(e)}"), 500


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



@home_bp.route('/forgot-password')
def forgot_password():
    """비밀번호 찾기 페이지"""
    return render_template('forgot_password.html')


@home_bp.route('/forgot-password', methods=['POST'])
def forgot_password_post():
    """비밀번호 찾기 처리"""
    logger = logging.getLogger(__name__)
    email = (request.form.get('email') or '').strip()
    
    if not email:
        flash('이메일을 입력해주세요', 'error')
        return redirect(url_for('home.forgot_password'))
    
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        user = conn.execute(
            "SELECT id, username, email FROM users WHERE email = ? AND is_deleted = 0",
            (email,)
        ).fetchone()
        
        if not user:
            # 보안을 위해 이메일이 없는 경우에도 성공 메시지 표시
            flash('입력하신 이메일로 비밀번호 재설정 링크를 보냈습니다. 이메일을 확인해주세요.', 'success')
            return redirect(url_for('auth.login'))
        
        try:
            # 비밀번호 재설정 토큰 생성
            token = create_reset_token(user['id'])
            
            # 이메일 발송 시도
            email_sent = send_password_reset_email(email, token, user['username'])
            
            if email_sent:
                flash('입력하신 이메일로 비밀번호 재설정 링크를 보냈습니다. 이메일을 확인해주세요.', 'success')
            else:
                # 이메일 발송 실패 시 콘솔에 토큰 출력 (개발 단계)
                flash('입력하신 이메일로 비밀번호 재설정 링크를 보냈습니다. 이메일을 확인해주세요.', 'success')
            
            logger.info(f"비밀번호 재설정 요청 처리 완료 - 사용자: {user['username']}, 이메일 발송: {email_sent}")
            
        except Exception as e:
            logger.error(f"비밀번호 재설정 토큰 생성 중 오류 발생: {e}")
            flash('비밀번호 재설정 요청 처리 중 오류가 발생했습니다. 다시 시도해주세요.', 'error')
    
    return redirect(url_for('auth.login'))


@home_bp.route('/reset-password/<token>')
def reset_password(token):
    """비밀번호 재설정 페이지"""
    # 토큰 유효성 검증
    user_id = validate_reset_token(token)
    
    if not user_id:
        flash('유효하지 않거나 만료된 링크입니다.', 'error')
        return redirect(url_for('home.forgot_password'))
    
    return render_template('reset_password.html', token=token)


@home_bp.route('/reset-password/<token>', methods=['POST'])
def reset_password_post(token):
    """비밀번호 재설정 처리"""
    logger = logging.getLogger(__name__)
    
    # 토큰 유효성 검증
    user_id = validate_reset_token(token)
    
    if not user_id:
        flash('유효하지 않거나 만료된 링크입니다.', 'error')
        return redirect(url_for('home.forgot_password'))
    
    password = (request.form.get('password') or '').strip()
    password_confirm = (request.form.get('password_confirm') or '').strip()
    
    if not password or not password_confirm:
        flash('비밀번호를 입력해주세요.', 'error')
        return redirect(url_for('home.reset_password', token=token))
    
    if password != password_confirm:
        flash('비밀번호가 일치하지 않습니다.', 'error')
        return redirect(url_for('home.reset_password', token=token))
    
    if len(password) < 6:
        flash('비밀번호는 6자 이상이어야 합니다.', 'error')
        return redirect(url_for('home.reset_password', token=token))
    
    # 비밀번호 업데이트
    try:
        hashed_password = hash_password(password)
        
        with get_conn() as conn:
            conn.execute(
                "UPDATE users SET password = ?, updated_at = datetime('now') WHERE id = ?",
                (hashed_password, user_id)
            )
            conn.commit()
        
        # 토큰을 사용된 것으로 표시
        mark_token_as_used(token)
        
        flash('비밀번호가 성공적으로 재설정되었습니다. 로그인해주세요.', 'success')
        logger.info(f"비밀번호 재설정 완료 - 사용자 ID: {user_id}")
        
    except Exception as e:
        logger.error(f"비밀번호 재설정 중 오류 발생: {e}")
        flash('비밀번호 재설정 중 오류가 발생했습니다. 다시 시도해주세요.', 'error')
    
    return redirect(url_for('auth.login'))

