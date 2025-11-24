from flask import Blueprint, render_template, request, redirect, url_for, flash
import sqlite3
import re
from core.db import get_conn_optimized as get_conn
from core.security import generate_csrf_token
from routes.utils.auth import current_user_id, ensure_logged_in_view

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
    response = ensure_logged_in_view()
    if response:
        return response
    user_id = current_user_id()
    
    # CSRF 토큰 검증 (간단히 처리)
    csrf_token = request.form.get('csrf_token')
    if not csrf_token:
        flash('보안 토큰이 없습니다. 다시 시도해주세요.', 'error')
        return redirect(url_for('profile.profile_edit'))
    
    # 수정 가능한 필드들만 받기 (사업자번호는 제외)
    company_name = request.form.get('company_name', '').strip()
    representative_name = request.form.get('representative_name', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    address = request.form.get('address', '').strip()
    business_type = request.form.get('business_type', '').strip()
    business_category = request.form.get('business_category', '').strip()
    
    # 필수 필드 검증
    if not all([company_name, representative_name, phone, email, business_type, business_category]):
        flash('모든 필수 항목을 입력해주세요', 'error')
        return redirect(url_for('profile.profile_edit'))
    
    # 유효성 검사
    # 대표자명 검증
    if not re.match(r'^[가-힣a-zA-Z\s]+$', representative_name):
        flash('대표자명은 한글, 영문만 입력 가능합니다', 'error')
        return redirect(url_for('profile.profile_edit'))
    
    # 전화번호 검증 및 정규화
    digits_phone = re.sub(r'\D', '', phone)
    
    # 먼저 기본 형식 검증
    if not re.match(r'^(02|0[3-9]\d|010|070)\d{3,4}\d{4}$', digits_phone):
        flash('올바른 전화번호 형식이 아닙니다 (예: 010-9702-3996 또는 01097023996)', 'error')
        return redirect(url_for('profile.profile_edit'))
    
    # 정규화 (하이픈 추가)
    if digits_phone.startswith('02'):
        phone = f"{digits_phone[:2]}-{digits_phone[2:6]}-{digits_phone[6:]}"
    else:
        phone = f"{digits_phone[:3]}-{digits_phone[3:7]}-{digits_phone[7:]}"
    
    # 이메일 검증
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        flash('올바른 이메일 형식이 아닙니다', 'error')
        return redirect(url_for('profile.profile_edit'))
    
    # 업태 검증 (최소 길이 제거)
    if not re.match(r'^[가-힣a-zA-Z0-9\s]+$', business_type):
        flash('업태는 한글, 영문, 숫자만 입력 가능합니다', 'error')
        return redirect(url_for('profile.profile_edit'))
    
    # 종목 검증 (최소 길이 제거)
    if not re.match(r'^[가-힣a-zA-Z0-9\s]+$', business_category):
        flash('종목은 한글, 영문, 숫자만 입력 가능합니다', 'error')
        return redirect(url_for('profile.profile_edit'))
    
    # 데이터베이스 업데이트
    with get_conn() as conn:
        try:
            # 🔍 테스트 1: 이메일 중복 검사 (본인 제외)
            existing_email = conn.execute(
                "SELECT id FROM users WHERE email = ? AND id != ?", 
                (email, user_id)
            ).fetchone()
            if existing_email:
                flash('이미 사용 중인 이메일입니다', 'error')
                return redirect(url_for('profile.profile_edit'))
            
            # 🔍 테스트 2: 전화번호 중복 검사 (본인 제외)
            existing_phone = conn.execute(
                "SELECT id FROM users WHERE phone = ? AND id != ?", 
                (phone, user_id)
            ).fetchone()
            if existing_phone:
                flash('이미 사용 중인 전화번호입니다', 'error')
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
            
            # 🔍 테스트 6: 변경사항 검증
            changes = []
            if old_user['company_name'] != updated_user['company_name']:
                changes.append(f"회사명: {old_user['company_name']} → {updated_user['company_name']}")
            if old_user['representative_name'] != updated_user['representative_name']:
                changes.append(f"대표자명: {old_user['representative_name']} → {updated_user['representative_name']}")
            if old_user['phone'] != updated_user['phone']:
                changes.append(f"전화번호: {old_user['phone']} → {updated_user['phone']}")
            if old_user['email'] != updated_user['email']:
                changes.append(f"이메일: {old_user['email']} → {updated_user['email']}")
            if old_user['address'] != updated_user['address']:
                changes.append(f"주소: {old_user['address']} → {updated_user['address']}")
            if old_user['business_type'] != updated_user['business_type']:
                changes.append(f"업태: {old_user['business_type']} → {updated_user['business_type']}")
            if old_user['business_category'] != updated_user['business_category']:
                changes.append(f"종목: {old_user['business_category']} → {updated_user['business_category']}")
            
            conn.commit()
            
            # 🔍 테스트 7: 성공 메시지에 변경사항 포함
            if changes:
                flash(f'고객정보가 성공적으로 수정되었습니다. 변경사항: {", ".join(changes)}', 'success')
            else:
                flash('고객정보가 성공적으로 수정되었습니다. (변경사항 없음)', 'success')
            
            # 🔍 테스트 8: 관리자 대시보드 연동 확인을 위한 로그
            print(f"✅ 사용자 정보 업데이트 완료 - 사용자 ID: {user_id}, 변경사항: {len(changes)}개")
            
        except Exception as e:
            flash(f'정보 수정 중 오류가 발생했습니다: {str(e)}', 'error')
            print(f"❌ 사용자 정보 업데이트 실패 - 사용자 ID: {user_id}, 오류: {str(e)}")
            return redirect(url_for('profile.profile_edit'))
    
    return redirect(url_for('profile.profile_edit'))

