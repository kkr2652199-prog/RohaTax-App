from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import logging
import sqlite3
from core.db import get_conn_optimized as get_conn
from core.password_reset_utils import (
    create_reset_token,
    validate_reset_token,
    mark_token_as_used
)
from core.password_utils import hash_password
from core.sms_utils import (
    send_verification_code,
    verify_code,
    get_user_by_phone
)

password_bp = Blueprint('password', __name__)
logger = logging.getLogger(__name__)


@password_bp.route('/forgot-password')
def forgot_password():
    """비밀번호 찾기 페이지 (휴대폰 번호 기반)"""
    return render_template('forgot_password.html')


@password_bp.route('/api/send-sms-code', methods=['POST'])
def send_sms_code():
    """가상 SMS 인증번호 발송 API"""
    try:
        phone = (request.form.get('phone') or '').strip()
        
        if not phone:
            return jsonify({'success': False, 'message': '휴대폰 번호를 입력해주세요.'}), 400
        
        logger.info(f"SMS 인증번호 발송 요청 - 전화번호: {phone}")
        
        # 휴대폰 번호로 사용자 조회
        try:
            user = get_user_by_phone(phone)
            logger.info(f"사용자 조회 결과: {user is not None}")
        except Exception as e:
            logger.error(f"사용자 조회 중 오류: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'message': '사용자 조회 중 오류가 발생했습니다.'
            }), 500
        
        if not user:
            # 보안을 위해 사용자가 없는 경우에도 성공 메시지 표시
            logger.warning(f"등록되지 않은 전화번호로 인증번호 발송 요청: {phone}")
            return jsonify({
                'success': True, 
                'message': '인증번호가 발송되었습니다. 서버 로그를 확인해주세요.'
            }), 200
        
        # 가상 SMS 인증번호 발송
        try:
            success, code = send_verification_code(phone)
            logger.info(f"인증번호 발송 결과: success={success}, code={'***' if code else None}")
        except Exception as e:
            logger.error(f"인증번호 발송 중 오류: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'message': '인증번호 발송 중 오류가 발생했습니다. 다시 시도해주세요.'
            }), 500
        
        if success:
            # 세션에 휴대폰 번호 저장 (인증 완료 후 사용)
            session['password_reset_phone'] = phone
            session['password_reset_user_id'] = user['id']
            
            return jsonify({
                'success': True,
                'message': '인증번호가 발송되었습니다. 서버 로그를 확인해주세요.'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '인증번호 발송 중 오류가 발생했습니다. 다시 시도해주세요.'
            }), 500
            
    except Exception as e:
        logger.error(f"SMS 인증번호 발송 API 오류: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': '인증번호 발송 중 오류가 발생했습니다.'
        }), 500


@password_bp.route('/api/verify-sms-code', methods=['POST'])
def verify_sms_code():
    """SMS 인증번호 검증 API"""
    try:
        phone = (request.form.get('phone') or '').strip()
        input_code = (request.form.get('code') or '').strip()
        
        if not phone or not input_code:
            return jsonify({
                'success': False,
                'message': '휴대폰 번호와 인증번호를 입력해주세요.'
            }), 400
        
        # 인증번호 검증
        is_valid, error_message = verify_code(phone, input_code)
        
        if is_valid:
            # 세션에 인증 완료 표시
            session['sms_verified'] = True
            session['verified_phone'] = phone
            
            # 비밀번호 재설정 토큰 생성
            user = get_user_by_phone(phone)
            if user:
                token = create_reset_token(user['id'])
                return jsonify({
                    'success': True,
                    'message': '인증이 완료되었습니다.',
                    'redirect_url': url_for('password.reset_password', token=token)
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': '사용자를 찾을 수 없습니다.'
                }), 404
        else:
            return jsonify({
                'success': False,
                'message': error_message or '인증번호가 일치하지 않습니다.'
            }), 400
            
    except Exception as e:
        logger.error(f"SMS 인증번호 검증 API 오류: {e}")
        return jsonify({
            'success': False,
            'message': '인증번호 검증 중 오류가 발생했습니다.'
        }), 500


@password_bp.route('/reset-password/<token>')
def reset_password(token):
    """비밀번호 재설정 페이지"""
    # 토큰 유효성 검증
    user_id = validate_reset_token(token)
    
    if not user_id:
        flash('유효하지 않거나 만료된 링크입니다.', 'error')
        return redirect(url_for('password.forgot_password'))
    
    return render_template('reset_password.html', token=token)


@password_bp.route('/reset-password/<token>', methods=['POST'])
def reset_password_post(token):
    """비밀번호 재설정 처리"""
    # 토큰 유효성 검증
    user_id = validate_reset_token(token)
    
    if not user_id:
        flash('유효하지 않거나 만료된 링크입니다.', 'error')
        return redirect(url_for('password.forgot_password'))
    
    # SMS 인증 확인 (세션에 인증된 번호가 있는지 확인)
    if not session.get('sms_verified'):
        flash('휴대폰 인증이 필요합니다.', 'error')
        return redirect(url_for('password.forgot_password'))
    
    password = (request.form.get('password') or '').strip()
    password_confirm = (request.form.get('password_confirm') or '').strip()
    
    if not password or not password_confirm:
        flash('비밀번호를 입력해주세요.', 'error')
        return redirect(url_for('password.reset_password', token=token))
    
    if password != password_confirm:
        flash('비밀번호가 일치하지 않습니다.', 'error')
        return redirect(url_for('password.reset_password', token=token))
    
    # 비밀번호 규칙 검증 (회원가입과 동일: 영문+숫자, 8자 이상)
    import re
    if len(password) < 8:
        flash('비밀번호는 8자 이상이어야 합니다.', 'error')
        return redirect(url_for('password.reset_password', token=token))
    
    has_letter = bool(re.search(r'[a-zA-Z]', password))
    has_number = bool(re.search(r'\d', password))
    if not (has_letter and has_number):
        flash('비밀번호는 영문과 숫자를 포함해야 합니다.', 'error')
        return redirect(url_for('password.reset_password', token=token))
    
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
        
        # 세션 정리
        session.pop('sms_verified', None)
        session.pop('verified_phone', None)
        session.pop('password_reset_phone', None)
        session.pop('password_reset_user_id', None)
        
        flash('비밀번호가 성공적으로 재설정되었습니다. 로그인해주세요.', 'success')
        logger.info(f"비밀번호 재설정 완료 - 사용자 ID: {user_id}")
        
    except Exception as e:
        logger.error(f"비밀번호 재설정 중 오류 발생: {e}")
        flash('비밀번호 재설정 중 오류가 발생했습니다. 다시 시도해주세요.', 'error')
    
    return redirect(url_for('auth.login'))

