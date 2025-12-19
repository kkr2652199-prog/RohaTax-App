from flask import Blueprint, render_template, request, redirect, url_for, flash
import os
import sqlite3
import re
from datetime import datetime
import json as _json
from core.db import get_conn_optimized as get_conn
from core.email_verification_manager import EmailVerificationManager
from core.password_utils import hash_password

registration_bp = Blueprint('registration', __name__)


@registration_bp.route('/register')
def register():
    return render_template('register.html')


@registration_bp.route('/register', methods=['POST'])
def register_post():
    # 필수 필드들
    username = request.form.get('username')
    business_number = request.form.get('business_number')
    representative_name = request.form.get('representative_name')
    company_name = request.form.get('company_name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    address = request.form.get('address', '')  # 선택사항 (사업자 주소)
    business_type = request.form.get('business_type', '')  # 업태
    business_category = request.form.get('business_category', '')  # 종목
    
    # 약관 동의 확인
    terms_agreed = request.form.get('terms_agreed')
    privacy_agreed = request.form.get('privacy_agreed')
    
    if not terms_agreed or not privacy_agreed:
        flash('이용약관 및 개인정보 수집 및 이용 동의는 필수입니다', 'error')
        return redirect(url_for('registration.register'))
    
    # 필수 필드 검증
    if not all([username, business_number, representative_name, company_name, phone, email, password, confirm_password, business_type, business_category]):
        flash('모든 필수 항목을 입력해주세요', 'error')
        return redirect(url_for('registration.register'))
    
    # 기본 검증 로직 (간단한 형태)
    if len(username) < 3:
        flash('사용자명은 3자 이상이어야 합니다', 'error')
        return redirect(url_for('registration.register'))
    
    if len(business_number) != 10 or not business_number.isdigit():
        flash('사업자등록번호는 10자리 숫자여야 합니다', 'error')
        return redirect(url_for('registration.register'))
    
    # 비밀번호 검증: 영문+숫자 조합, 8자 이상
    if len(password) < 8:
        flash('비밀번호는 8자 이상이어야 합니다', 'error')
        return redirect(url_for('registration.register'))
    
    has_letter = bool(re.search(r'[a-zA-Z]', password))
    has_number = bool(re.search(r'\d', password))
    if not (has_letter and has_number):
        flash('비밀번호는 영문과 숫자를 포함해야 합니다', 'error')
        return redirect(url_for('registration.register'))
    
    if '@' not in email:
        flash('유효한 이메일을 입력해주세요', 'error')
        return redirect(url_for('registration.register'))
    
    # 비밀번호 일치 검증 (기존 로직 유지)
    if password != confirm_password:
        flash('비밀번호가 일치하지 않습니다', 'error')
        return redirect(url_for('registration.register'))
    
    # 전화번호 기본 검증
    if not phone or len(phone) < 10:
        flash('유효한 전화번호를 입력해주세요', 'error')
        return redirect(url_for('registration.register'))
    
    # 실제 사용자 저장
    with get_conn() as conn:
        try:
            # 검증 로그 기록 (성공)
            conn.execute(
                "INSERT INTO validation_logs (user_id, validation_type, success, errors) VALUES (?, ?, ?, ?)",
                (None, 'registration_validation', 1, '기본 검증 통과')
            )
            
            # 아이디 중복 검사
            existing_username = conn.execute(
                "SELECT id FROM users WHERE username = ? AND COALESCE(is_deleted,0) = 0",
                (username,)
            ).fetchone()
            if existing_username:
                # 검증 로그 기록 (실패)
                conn.execute(
                    "INSERT INTO validation_logs (user_id, validation_type, success, errors) VALUES (?, ?, ?, ?)",
                    (None, 'username_duplicate_check', 0, f'아이디 중복: {username}')
                )
                flash('이미 사용 중인 아이디입니다', 'error')
                return redirect(url_for('registration.register'))

            # 사업자등록번호 중복 검사
            existing_business = conn.execute(
                "SELECT id FROM users WHERE business_number = ? AND COALESCE(is_deleted,0) = 0",
                (business_number,)
            ).fetchone()
            if existing_business:
                # 검증 로그 기록 (실패)
                conn.execute(
                    "INSERT INTO validation_logs (user_id, validation_type, success, errors) VALUES (?, ?, ?, ?)",
                    (None, 'business_number_duplicate_check', 0, f'사업자등록번호 중복: {business_number}')
                )
                flash('이미 등록된 사업자등록번호입니다', 'error')
                return redirect(url_for('registration.register'))
            
            # 이메일 중복 검사
            existing_email = conn.execute(
                "SELECT id FROM users WHERE email = ? AND COALESCE(is_deleted,0) = 0",
                (email,)
            ).fetchone()
            if existing_email:
                # 검증 로그 기록 (실패)
                conn.execute(
                    "INSERT INTO validation_logs (user_id, validation_type, success, errors) VALUES (?, ?, ?, ?)",
                    (None, 'email_duplicate_check', 0, f'이메일 중복: {email}')
                )
                flash('이미 등록된 이메일입니다', 'error')
                return redirect(url_for('registration.register'))
            
            # 삭제된 레코드가 있는 경우 복구 경로
            deleted_row = conn.execute(
                """
                SELECT id FROM users
                WHERE (username = ? OR email = ? OR business_number = ?)
                  AND COALESCE(is_deleted,0) = 1
                ORDER BY id DESC LIMIT 1
                """,
                (username, email, business_number)
            ).fetchone()
            # 약관 동의 일시 기록
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            terms_agreed_value = 1 if terms_agreed == '1' else 0
            privacy_agreed_value = 1 if privacy_agreed == '1' else 0
            
            if deleted_row:
                # 비밀번호를 bcrypt로 해싱
                hashed_password = hash_password(password)
                
                conn.execute(
                    """
                    UPDATE users SET
                        username = ?, email = ?, password = ?, company_name = ?, business_number = ?,
                        representative_name = ?, phone = ?, address = ?, business_type = ?, business_category = ?,
                        is_active = 1, approval_status = 'approved', is_deleted = 0, deleted_at = NULL,
                        terms_agreed = ?, privacy_agreed = ?, terms_agreed_at = ?, privacy_agreed_at = ?
                    WHERE id = ?
                    """,
                    (username, email, hashed_password, company_name, business_number,
                     representative_name, phone, address, business_type, business_category,
                     terms_agreed_value, privacy_agreed_value, current_time, current_time,
                     deleted_row['id'])
                )
                user_id = deleted_row['id']
                conn.commit()
            else:
                # 비밀번호를 bcrypt로 해싱
                hashed_password = hash_password(password)
                
                cur = conn.execute(
                """INSERT INTO users (username, email, password, company_name, business_number, 
                   representative_name, phone, address, business_type, business_category, 
                   plan_type, monthly_limit, used_count, is_active, is_admin, token_balance, approval_status,
                   terms_agreed, privacy_agreed, terms_agreed_at, privacy_agreed_at) 
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (username, email, hashed_password, company_name, business_number, 
                representative_name, phone, address, business_type, business_category,
                'free', 50, 0, 1, 0, 0, 'approved',
                terms_agreed_value, privacy_agreed_value, current_time, current_time)
            )
                user_id = cur.lastrowid
            
            # 사용자 생성 성공 로그 기록
            conn.execute(
                "INSERT INTO usage_logs (user_id, action, meta) VALUES (?, ?, ?)",
                (user_id, 'user_registration', f'{{"username": "{username}", "company_name": "{company_name}", "business_number": "{business_number}"}}')
            )
            
            # 검증 로그 업데이트 (user_id 추가)
            conn.execute(
                "UPDATE validation_logs SET user_id = ? WHERE validation_type = 'registration_validation' AND user_id IS NULL ORDER BY timestamp DESC LIMIT 1",
                (user_id,)
            )
            
            conn.commit()
            
        except Exception as e:
            # 오류 로그 기록
            conn.execute(
                "INSERT INTO validation_logs (user_id, validation_type, success, errors) VALUES (?, ?, ?, ?)",
                (None, 'registration_error', 0, f'회원가입 오류: {str(e)}')
            )
            conn.commit()
            flash(f'회원가입 중 오류가 발생했습니다: {str(e)}', 'error')
            return redirect(url_for('registration.register'))

    # per-user folder 구조: user_data/{user_id}/{YYYY-MM-DD}
    base_users_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'user_data')
    os.makedirs(base_users_dir, exist_ok=True)
    user_root_dir = os.path.join(base_users_dir, str(user_id))
    os.makedirs(user_root_dir, exist_ok=True)
    date_folder = datetime.now().strftime('%Y-%m-%d')
    dated_dir = os.path.join(user_root_dir, date_folder)
    os.makedirs(dated_dir, exist_ok=True)
    # 초기 메타 파일 저장(선택)
    try:
        meta_path = os.path.join(dated_dir, 'profile_init.json')
        with open(meta_path, 'w', encoding='utf-8') as f:
            _json.dump({
                "user_id": user_id,
                "username": username,
                "company_name": company_name,
                "created_at": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    # 📧 이메일 인증 처리 (옵션)
    email_manager = EmailVerificationManager()
    if email_manager.is_verification_enabled():
        try:
            # 인증 토큰 생성 및 저장
            token, _ = email_manager.generate_verification_token(user_id, email)
            if email_manager.save_verification_token(user_id, email, token):
                # 인증 이메일 발송
                if email_manager.send_verification_email(user_id, email, token):
                    flash('회원가입이 완료되었습니다. 이메일 인증을 완료해주세요.', 'success')
                    return redirect(url_for('email.email_verification_pending', user_id=user_id))
                else:
                    flash('회원가입은 완료되었지만 이메일 발송에 실패했습니다. 관리자에게 문의해주세요.', 'warning')
            else:
                flash('회원가입은 완료되었지만 이메일 인증 설정에 실패했습니다.', 'warning')
        except Exception as e:
            # 이메일 인증 실패해도 회원가입은 성공으로 처리
            flash(f'회원가입이 완료되었습니다. (이메일 인증 오류: {str(e)})', 'warning')
    else:
        # 이메일 인증 비활성화 시 기존 흐름 유지
        flash('회원가입이 완료되었습니다. 로그인해 주세요.', 'success')
    
    return redirect(url_for('auth.login'))

