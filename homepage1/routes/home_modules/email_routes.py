from flask import Blueprint, render_template, request, redirect, url_for, flash
import logging
import sqlite3
from core.db import get_conn_optimized as get_conn
from core.responses import success, error
from core.email_verification_manager import EmailVerificationManager

email_bp = Blueprint('email', __name__)


@email_bp.route('/email-verification-pending/<int:user_id>')
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


@email_bp.route('/verify-email/<token>')
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


@email_bp.route('/resend-verification', methods=['POST'])
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
        
        return redirect(url_for('email.email_verification_pending', user_id=user_id))
        
    except Exception as e:
        flash(f'재발송 처리 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('registration.register'))


@email_bp.route('/api/check-verification-status/<int:user_id>')
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

