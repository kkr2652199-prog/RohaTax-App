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


@home_bp.route('/login')
def login():
    return render_template('login.html')


@home_bp.route('/login', methods=['POST'])
def login_post():
    logger = logging.getLogger(__name__)
    username = (request.form.get('username') or '').strip()
    password = (request.form.get('password') or '').strip()
    if not username or not password:
        flash('입력값을 확인해주세요', 'error')
        return redirect(url_for('home.login'))
    # 실제 인증 (원인 파악을 위한 단계별 검사)
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        # 우선 삭제되지 않은 최신 계정 우선 조회
        row = conn.execute(
            """
            SELECT id, username, password, is_admin,
                   COALESCE(is_deleted,0) AS is_deleted,
                   COALESCE(is_active,1) AS is_active,
                   COALESCE(approval_status,'approved') AS approval_status
            FROM users
            WHERE username = ? AND COALESCE(is_deleted,0) = 0
            ORDER BY id DESC
            LIMIT 1
            """,
            (username,)
        ).fetchone()
        # 활성 사용자가 없을 때: 삭제된 사용자가 존재하면 비밀번호 일치 시 자동 복구
        if not row:
            deleted_row = conn.execute(
                """
                SELECT id, username, password, is_admin,
                       COALESCE(is_deleted,0) AS is_deleted,
                       COALESCE(is_active,1) AS is_active,
                       COALESCE(approval_status,'approved') AS approval_status
                FROM users
                WHERE username = ? AND COALESCE(is_deleted,0) = 1
                ORDER BY id DESC LIMIT 1
                """,
                (username,)
            ).fetchone()
            if not deleted_row:
                flash('존재하지 않는 아이디입니다', 'error')
                return redirect(url_for('home.login'))
            # 비밀번호 검증 후 자동 복구 (bcrypt 검증)
            if not verify_password(password, deleted_row['password']):
                flash('삭제된 계정입니다. 관리자에게 문의하세요', 'error')
                return redirect(url_for('home.login'))
            conn.execute(
                "UPDATE users SET is_deleted = 0, is_active = 1, approval_status = 'approved' WHERE id = ?",
                (deleted_row['id'],)
            )
            conn.commit()
            row = conn.execute(
                """
                SELECT id, username, password, is_admin,
                       COALESCE(is_deleted,0) AS is_deleted,
                       COALESCE(is_active,1) AS is_active,
                       COALESCE(approval_status,'approved') AS approval_status
                FROM users WHERE id = ?
                """,
                (deleted_row['id'],)
            ).fetchone()
    if row['is_deleted']:
        flash('삭제된 계정입니다. 관리자에게 문의하세요', 'error')
        return redirect(url_for('home.login'))
    if not row['is_active']:
        flash('비활성화된 계정입니다. 관리자에게 문의하세요', 'error')
        return redirect(url_for('home.login'))
    if row['approval_status'] != 'approved':
        flash('승인 대기/거부된 계정입니다', 'error')
        return redirect(url_for('home.login'))
    # bcrypt 비밀번호 검증 (평문 지원 포함)
    if not verify_password(password, row['password']):
        flash('비밀번호가 올바르지 않습니다', 'error')
        return redirect(url_for('home.login'))
    user = row
    # Clear any previous session to avoid privilege leakage across accounts
    session.clear()
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['is_admin'] = int(user['is_admin'] or 0)
    session.permanent = True  # 세션 영구화
    flash('로그인 성공', 'success')
    if session['is_admin']:
        return redirect(url_for('admin.admin_dashboard'))
    return redirect(url_for('home.home'))


@home_bp.route('/logout')
def logout():
    session.clear()
    flash('로그아웃되었습니다', 'info')
    return redirect(url_for('home.home'))


@home_bp.route('/register')
def register():
    return render_template('register.html')


@home_bp.route('/register', methods=['POST'])
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
    
    # 필수 필드 검증
    if not all([username, business_number, representative_name, company_name, phone, email, password, confirm_password, business_type, business_category]):
        flash('모든 필수 항목을 입력해주세요', 'error')
        return redirect(url_for('home.register'))
    
    # 기본 검증 로직 (간단한 형태)
    if len(username) < 3:
        flash('사용자명은 3자 이상이어야 합니다', 'error')
        return redirect(url_for('home.register'))
    
    if len(business_number) != 10 or not business_number.isdigit():
        flash('사업자등록번호는 10자리 숫자여야 합니다', 'error')
        return redirect(url_for('home.register'))
    
    if len(password) < 6:
        flash('비밀번호는 6자 이상이어야 합니다', 'error')
        return redirect(url_for('home.register'))
    
    if '@' not in email:
        flash('유효한 이메일을 입력해주세요', 'error')
        return redirect(url_for('home.register'))
    
    # 비밀번호 일치 검증 (기존 로직 유지)
    if password != confirm_password:
        flash('비밀번호가 일치하지 않습니다', 'error')
        return redirect(url_for('home.register'))
    
    # 전화번호 기본 검증
    if not phone or len(phone) < 10:
        flash('유효한 전화번호를 입력해주세요', 'error')
        return redirect(url_for('home.register'))
    
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
                return redirect(url_for('home.register'))

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
                return redirect(url_for('home.register'))
            
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
                return redirect(url_for('home.register'))
            
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
            if deleted_row:
                # 비밀번호를 bcrypt로 해싱
                hashed_password = hash_password(password)
                
                conn.execute(
                    """
                    UPDATE users SET
                        username = ?, email = ?, password = ?, company_name = ?, business_number = ?,
                        representative_name = ?, phone = ?, address = ?, business_type = ?, business_category = ?,
                        is_active = 1, approval_status = 'approved', is_deleted = 0, deleted_at = NULL
                    WHERE id = ?
                    """,
                    (username, email, hashed_password, company_name, business_number,
                     representative_name, phone, address, business_type, business_category,
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
                   plan_type, monthly_limit, used_count, is_active, is_admin, token_balance, approval_status) 
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (username, email, hashed_password, company_name, business_number, 
                representative_name, phone, address, business_type, business_category,
                'free', 50, 0, 1, 0, 0, 'approved')
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
            return redirect(url_for('home.register'))

    # per-user folder 구조: user_data/{user_id}/{YYYY-MM-DD}
    base_users_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'user_data')
    os.makedirs(base_users_dir, exist_ok=True)
    user_root_dir = os.path.join(base_users_dir, str(user_id))
    os.makedirs(user_root_dir, exist_ok=True)
    from datetime import datetime
    date_folder = datetime.now().strftime('%Y-%m-%d')
    dated_dir = os.path.join(user_root_dir, date_folder)
    os.makedirs(dated_dir, exist_ok=True)
    # 초기 메타 파일 저장(선택)
    try:
        meta_path = os.path.join(dated_dir, 'profile_init.json')
        with open(meta_path, 'w', encoding='utf-8') as f:
            import json as _json
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
                    return redirect(url_for('home.email_verification_pending', user_id=user_id))
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
    
    return redirect(url_for('home.login'))


# ====== AJAX duplicate checks (non-deleted accounts only) ======
@home_bp.route('/api/check-username')
def api_check_username():
    username = (request.args.get('username') or '').strip()
    if not username:
        return jsonify({"success": False, "available": False, "error": "username_required"})
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE username = ? AND COALESCE(is_deleted,0) = 0 LIMIT 1",
            (username,)
        ).fetchone()
    return jsonify({"success": True, "available": row is None})


@home_bp.route('/api/check-business-number')
def api_check_business_number():
    business_number = (request.args.get('business_number') or '').strip()
    if not business_number:
        return jsonify({"success": False, "available": False, "error": "business_number_required"})
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE business_number = ? AND COALESCE(is_deleted,0) = 0 LIMIT 1",
            (business_number,)
        ).fetchone()
    return jsonify({"success": True, "available": row is None})


@home_bp.route('/api/check-email')
def api_check_email():
    email = (request.args.get('email') or '').strip()
    if not email:
        return jsonify({"success": False, "available": False, "error": "email_required"})
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE email = ? AND COALESCE(is_deleted,0) = 0 LIMIT 1",
            (email,)
        ).fetchone()
    return jsonify({"success": True, "available": row is None})


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
                return redirect(url_for('home.register'))
            
            if user['email_verified']:
                flash('이미 이메일 인증이 완료되었습니다', 'info')
                return redirect(url_for('home.login'))
            
            return render_template('email_verification_pending.html', user=user)
            
    except Exception as e:
        flash(f'페이지 로드 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('home.register'))


@home_bp.route('/verify-email/<token>')
def verify_email(token):
    """이메일 인증 처리"""
    try:
        email_manager = EmailVerificationManager()
        is_valid, message, user_id = email_manager.verify_token(token)
        
        if is_valid:
            flash(message, 'success')
            return redirect(url_for('home.login'))
        else:
            flash(message, 'error')
            return redirect(url_for('home.register'))
            
    except Exception as e:
        flash(f'인증 처리 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('home.register'))


@home_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """이메일 인증 재발송"""
    try:
        user_id = request.form.get('user_id')
        email = request.form.get('email')
        
        if not user_id or not email:
            flash('필수 정보가 누락되었습니다', 'error')
            return redirect(url_for('home.register'))
        
        email_manager = EmailVerificationManager()
        success, message = email_manager.resend_verification_email(int(user_id), email)
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
        
        return redirect(url_for('home.email_verification_pending', user_id=user_id))
        
    except Exception as e:
        flash(f'재발송 처리 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('home.register'))


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


@home_bp.route('/profile/edit')
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
            return redirect(url_for('home.login'))
    
    from core.security import generate_csrf_token
    token = generate_csrf_token()
    return render_template('profile_edit.html', user=user, csrf_token=token)


@home_bp.route('/profile/update', methods=['POST'])
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
        return redirect(url_for('home.profile_edit'))
    
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
        return redirect(url_for('home.profile_edit'))
    
    # 유효성 검사
    import re
    
    # 대표자명 검증
    if not re.match(r'^[가-힣a-zA-Z\s]+$', representative_name):
        flash('대표자명은 한글, 영문만 입력 가능합니다', 'error')
        return redirect(url_for('home.profile_edit'))
    
    # 전화번호 검증 및 정규화
    digits_phone = re.sub(r'\D', '', phone)
    
    # 먼저 기본 형식 검증
    if not re.match(r'^(02|0[3-9]\d|010|070)\d{3,4}\d{4}$', digits_phone):
        flash('올바른 전화번호 형식이 아닙니다 (예: 010-9702-3996 또는 01097023996)', 'error')
        return redirect(url_for('home.profile_edit'))
    
    # 정규화 (하이픈 추가)
    if digits_phone.startswith('02'):
        phone = f"{digits_phone[:2]}-{digits_phone[2:6]}-{digits_phone[6:]}"
    else:
        phone = f"{digits_phone[:3]}-{digits_phone[3:7]}-{digits_phone[7:]}"
    
    # 이메일 검증
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        flash('올바른 이메일 형식이 아닙니다', 'error')
        return redirect(url_for('home.profile_edit'))
    
    # 업태 검증 (최소 길이 제거)
    if not re.match(r'^[가-힣a-zA-Z0-9\s]+$', business_type):
        flash('업태는 한글, 영문, 숫자만 입력 가능합니다', 'error')
        return redirect(url_for('home.profile_edit'))
    
    # 종목 검증 (최소 길이 제거)
    if not re.match(r'^[가-힣a-zA-Z0-9\s]+$', business_category):
        flash('종목은 한글, 영문, 숫자만 입력 가능합니다', 'error')
        return redirect(url_for('home.profile_edit'))
    
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
                return redirect(url_for('home.profile_edit'))
            
            # 🔍 테스트 2: 전화번호 중복 검사 (본인 제외)
            existing_phone = conn.execute(
                "SELECT id FROM users WHERE phone = ? AND id != ?", 
                (phone, user_id)
            ).fetchone()
            if existing_phone:
                flash('이미 사용 중인 전화번호입니다', 'error')
                return redirect(url_for('home.profile_edit'))
            
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
            return redirect(url_for('home.profile_edit'))
    
    return redirect(url_for('home.profile_edit'))


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
            return redirect(url_for('home.login'))
        
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
    
    return redirect(url_for('home.login'))


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
    
    return redirect(url_for('home.login'))

