from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import re
import json
from core.db import get_conn_optimized as get_conn
from core.security import generate_csrf_token
from routes.utils.auth import current_user_id, ensure_logged_in_view
from core.activity_service import record_activity

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/profile/edit')
def profile_edit():
    """고객정보 수정 페이지"""
    response = ensure_logged_in_view()
    if response:
        return response
    user_id = current_user_id()
    
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        user = conn.execute(
            """
            SELECT username, email, company_name, business_number,
                   representative_name, phone, address, business_type, business_category,
                   COALESCE(plan_type, 'free') AS plan_type
            FROM users WHERE id = ? AND COALESCE(is_deleted, 0) = 0
            """,
            (user_id,)
        ).fetchone()
        
        if not user:
            flash('사용자 정보를 찾을 수 없습니다', 'error')
            return redirect(url_for('auth.login'))
    
    token = generate_csrf_token()
    return render_template('profile_v2.html', user=user, csrf_token=token)


@profile_bp.route('/profile/update', methods=['POST'])
def profile_update():
    """고객정보 수정 처리"""
    # AJAX 요청 여부를 먼저 확인 (로그인 체크 전에)
    is_ajax = request.headers.get('Content-Type', '').startswith('application/json') or \
              request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
              request.is_json or \
              'application/json' in request.headers.get('Accept', '')
    
    # AJAX 요청인 경우 JSON 기반 인증 체크
    if is_ajax:
        from routes.utils.auth import ensure_login_for_json
        user_id, guard_response = ensure_login_for_json()
        if guard_response:
            return guard_response
    else:
        # 일반 폼 요청인 경우 기존 방식 사용
        response = ensure_logged_in_view()
        if response:
            return response
        user_id = current_user_id()
    
    # 데이터 추출 (JSON 또는 Form Data)
    if is_ajax and request.is_json:
        data = request.get_json() or {}
        csrf_token = data.get('csrf_token', '')
        company_name = data.get('company_name', '').strip()
        representative_name = data.get('representative_name', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        address = data.get('address', '').strip()
        business_type = data.get('business_type', '').strip()
        business_category = data.get('business_category', '').strip()
    else:
        # Form Data 처리
        csrf_token = request.form.get('csrf_token')
        company_name = request.form.get('company_name', '').strip()
        representative_name = request.form.get('representative_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        business_type = request.form.get('business_type', '').strip()
        business_category = request.form.get('business_category', '').strip()
    
    # CSRF 토큰 검증
    if not csrf_token:
        if is_ajax:
            return jsonify({'success': False, 'message': '보안 토큰이 없습니다. 다시 시도해주세요.'}), 400
        flash('보안 토큰이 없습니다. 다시 시도해주세요.', 'error')
        return redirect(url_for('profile.profile_edit'))
    
    # 필수 필드 검증
    if not all([company_name, representative_name, phone, email, business_type, business_category]):
        error_msg = '모든 필수 항목을 입력해주세요'
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg}), 400
        flash(error_msg, 'error')
        return redirect(url_for('profile.profile_edit'))
    
    # 유효성 검사
    # 대표자명 검증
    if not re.match(r'^[가-힣a-zA-Z\s]+$', representative_name):
        error_msg = '대표자명은 한글, 영문만 입력 가능합니다'
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg}), 400
        flash(error_msg, 'error')
        return redirect(url_for('profile.profile_edit'))
    
    # 전화번호 검증 및 정규화
    digits_phone = re.sub(r'\D', '', phone)
    
    # 먼저 기본 형식 검증
    if not re.match(r'^(02|0[3-9]\d|010|070)\d{3,4}\d{4}$', digits_phone):
        error_msg = '올바른 전화번호 형식이 아닙니다 (예: 010-9702-3996 또는 01097023996)'
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg}), 400
        flash(error_msg, 'error')
        return redirect(url_for('profile.profile_edit'))
    
    # 정규화 (하이픈 추가)
    if digits_phone.startswith('02'):
        phone = f"{digits_phone[:2]}-{digits_phone[2:6]}-{digits_phone[6:]}"
    else:
        phone = f"{digits_phone[:3]}-{digits_phone[3:7]}-{digits_phone[7:]}"
    
    # 이메일 검증
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        error_msg = '올바른 이메일 형식이 아닙니다'
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg}), 400
        flash(error_msg, 'error')
        return redirect(url_for('profile.profile_edit'))
    
    # 업태 검증 (최소 길이 제거)
    if not re.match(r'^[가-힣a-zA-Z0-9\s]+$', business_type):
        error_msg = '업태는 한글, 영문, 숫자만 입력 가능합니다'
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg}), 400
        flash(error_msg, 'error')
        return redirect(url_for('profile.profile_edit'))
    
    # 종목 검증 (최소 길이 제거)
    if not re.match(r'^[가-힣a-zA-Z0-9\s]+$', business_category):
        error_msg = '종목은 한글, 영문, 숫자만 입력 가능합니다'
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg}), 400
        flash(error_msg, 'error')
        return redirect(url_for('profile.profile_edit'))
    
    # 데이터베이스 업데이트
    with get_conn() as conn:
        try:
            # 🔍 테스트 1: 이메일 중복 검사 (본인 제외, 삭제된 유저 제외)
            existing_email = conn.execute(
                "SELECT id FROM users WHERE email = ? AND id != ? AND COALESCE(is_deleted, 0) = 0", 
                (email, user_id)
            ).fetchone()
            if existing_email:
                error_msg = '이미 사용 중인 이메일입니다'
                if is_ajax:
                    return jsonify({'success': False, 'message': error_msg}), 400
                flash(error_msg, 'error')
                return redirect(url_for('profile.profile_edit'))
            
            # 🔍 테스트 2: 전화번호 중복 검사 (본인 제외, 삭제된 유저 제외)
            existing_phone = conn.execute(
                "SELECT id FROM users WHERE phone = ? AND id != ? AND COALESCE(is_deleted, 0) = 0", 
                (phone, user_id)
            ).fetchone()
            if existing_phone:
                error_msg = '이미 사용 중인 전화번호입니다'
                if is_ajax:
                    return jsonify({'success': False, 'message': error_msg}), 400
                flash(error_msg, 'error')
                return redirect(url_for('profile.profile_edit'))
            
            # 🔍 테스트 3: 기존 데이터 백업 (변경 이력 저장)
            old_user = conn.execute(
                "SELECT company_name, representative_name, phone, email, address, business_type, business_category FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
            
            # 🔍 테스트 4: 사용자 정보 업데이트 (사업자번호는 제외)
            conn.execute(
                """
                UPDATE users SET 
                    company_name = ?, representative_name = ?, phone = ?, 
                    email = ?, address = ?, business_type = ?, business_category = ?
                WHERE id = ?
                """,
                (company_name, representative_name, phone, email, address, 
                 business_type, business_category, user_id)
            )
            
            # 🔍 테스트 5: 업데이트 확인
            updated_user = conn.execute(
                "SELECT company_name, representative_name, phone, email, address, business_type, business_category FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
            
            # 🔍 테스트 6: 변경사항 검증 및 이력 기록 준비
            changes = []
            changed_fields = []
            changed_fields_kr = []
            change_details = {}
            
            # 각 필드별 변경사항 감지
            if old_user['company_name'] != updated_user['company_name']:
                changes.append(f"회사명: {old_user['company_name']} → {updated_user['company_name']}")
                changed_fields.append('company_name')
                changed_fields_kr.append('회사명')
                change_details['old_company_name'] = old_user['company_name'] or ''
                change_details['new_company_name'] = updated_user['company_name'] or ''
            
            if old_user['representative_name'] != updated_user['representative_name']:
                changes.append(f"대표자명: {old_user['representative_name']} → {updated_user['representative_name']}")
                changed_fields.append('representative_name')
                changed_fields_kr.append('대표자명')
                change_details['old_representative_name'] = old_user['representative_name'] or ''
                change_details['new_representative_name'] = updated_user['representative_name'] or ''
            
            if old_user['phone'] != updated_user['phone']:
                changes.append(f"전화번호: {old_user['phone']} → {updated_user['phone']}")
                changed_fields.append('phone')
                changed_fields_kr.append('전화번호')
                change_details['old_phone'] = old_user['phone'] or ''
                change_details['new_phone'] = updated_user['phone'] or ''
            
            if old_user['email'] != updated_user['email']:
                changes.append(f"이메일: {old_user['email']} → {updated_user['email']}")
                changed_fields.append('email')
                changed_fields_kr.append('이메일')
                change_details['old_email'] = old_user['email'] or ''
                change_details['new_email'] = updated_user['email'] or ''
            
            if old_user['address'] != updated_user['address']:
                changes.append(f"주소: {old_user['address']} → {updated_user['address']}")
                changed_fields.append('address')
                changed_fields_kr.append('주소')
                change_details['old_address'] = old_user['address'] or ''
                change_details['new_address'] = updated_user['address'] or ''
            
            if old_user['business_type'] != updated_user['business_type']:
                changes.append(f"업태: {old_user['business_type']} → {updated_user['business_type']}")
                changed_fields.append('business_type')
                changed_fields_kr.append('업태')
                change_details['old_business_type'] = old_user['business_type'] or ''
                change_details['new_business_type'] = updated_user['business_type'] or ''
            
            if old_user['business_category'] != updated_user['business_category']:
                changes.append(f"종목: {old_user['business_category']} → {updated_user['business_category']}")
                changed_fields.append('business_category')
                changed_fields_kr.append('종목')
                change_details['old_business_category'] = old_user['business_category'] or ''
                change_details['new_business_category'] = updated_user['business_category'] or ''
            
            # 변경 이력 기록 (activity_logs) - 변경된 필드가 있는 경우에만
            cursor = conn.cursor()
            if changed_fields:
                # 사용자 정보 조회 (토큰 잔액 및 플랜 타입 포함)
                user_info = conn.execute(
                    "SELECT username, COALESCE(token_balance, 0) AS token_balance, plan_type FROM users WHERE id = ?",
                    (user_id,)
                ).fetchone()
                
                activity_data = {
                    'user_id': user_id,
                    'performed_by_id': user_id,  # 본인이 수정
                    'performed_by_type': 'USER',
                    'activity_type': 'PROFILE_UPDATE',
                    'details': {
                        'action': '프로필 수정',
                        'changed_fields': changed_fields,
                        'changed_fields_kr': changed_fields_kr,
                        'changes': changed_fields,
                        **change_details
                    },
                    'token_change': 0,  # 프로필 수정은 토큰 변화 없음
                    'potential_cost': 0,
                    'token_balance_before': user_info['token_balance'] if user_info else 0,
                    'token_balance_after': user_info['token_balance'] if user_info else 0,
                    'user_plan_snapshot': user_info['plan_type'] if user_info else 'free'
                }
                
                record_activity(cursor, activity_data)
            
            conn.commit()
            
            # 🔍 테스트 7: 성공 메시지에 변경사항 포함
            if changes:
                success_msg = f'고객정보가 성공적으로 수정되었습니다. 변경사항: {", ".join(changes)}'
            else:
                success_msg = '고객정보가 성공적으로 수정되었습니다. (변경사항 없음)'
            
            # 🔍 테스트 8: 관리자 대시보드 연동 확인을 위한 로그
            print(f"[SUCCESS] 사용자 정보 업데이트 완료 - 사용자 ID: {user_id}, 변경사항: {len(changes)}개")
            
            # AJAX 요청인 경우 JSON 리턴
            if is_ajax:
                return jsonify({'success': True, 'message': '저장되었습니다'})
            
            # 일반 폼 전송인 경우 리다이렉트
            flash('저장되었습니다.', 'success')
            return redirect(url_for('profile.profile_edit'))
            
        except Exception as e:
            error_msg = f'정보 수정 중 오류가 발생했습니다: {str(e)}'
            print(f"[ERROR] 사용자 정보 업데이트 실패 - 사용자 ID: {user_id}, 오류: {str(e)}")
            # AJAX 요청인 경우 JSON 리턴
            if is_ajax:
                return jsonify({'success': False, 'message': error_msg}), 500
            flash(error_msg, 'error')
            return redirect(url_for('profile.profile_edit'))

