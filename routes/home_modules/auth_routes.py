from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import logging
import sqlite3
from core.db import get_conn_optimized as get_conn
from core.password_utils import verify_password

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login')
def login():
    return render_template('login.html')


@auth_bp.route('/login', methods=['POST'])
def login_post():
    logger = logging.getLogger(__name__)
    username = (request.form.get('username') or '').strip()
    password = (request.form.get('password') or '').strip()
    if not username or not password:
        flash('입력값을 확인해주세요', 'error')
        return redirect(url_for('auth.login'))
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
                return redirect(url_for('auth.login'))
            # 비밀번호 검증 후 자동 복구 (bcrypt 검증)
            if not verify_password(password, deleted_row['password']):
                flash('삭제된 계정입니다. 관리자에게 문의하세요', 'error')
                return redirect(url_for('auth.login'))
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
        return redirect(url_for('auth.login'))
    if not row['is_active']:
        flash('비활성화된 계정입니다. 관리자에게 문의하세요', 'error')
        return redirect(url_for('auth.login'))
    if row['approval_status'] != 'approved':
        flash('승인 대기/거부된 계정입니다', 'error')
        return redirect(url_for('auth.login'))
    # bcrypt 비밀번호 검증 (평문 지원 포함)
    if not verify_password(password, row['password']):
        flash('비밀번호가 올바르지 않습니다', 'error')
        return redirect(url_for('auth.login'))
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


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('로그아웃되었습니다', 'info')
    return redirect(url_for('home.home'))

