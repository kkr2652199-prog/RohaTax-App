import sqlite3

from flask import request

from core.db import get_conn
from core.responses import success, error

from . import admin_bp
from ..utils.auth import ensure_admin_for_json


@admin_bp.route('/admin/api/email-settings', methods=['GET'])
def get_email_settings():
    """이메일 인증 관련 시스템 설정 값을 조회한다."""
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    try:
        from core.email_verification_manager import EmailVerificationManager

        email_manager = EmailVerificationManager()
        stats = email_manager.get_verification_stats()

        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT key, value
                FROM settings
                WHERE key LIKE 'email_verification_%'
                ORDER BY key
                """
            ).fetchall()

        settings_dict = {row['key']: row['value'] for row in rows}
        return success('ok', data={'stats': stats, 'settings': settings_dict})

    except Exception as exc:  # pylint: disable=broad-except
        return error(f'설정 조회 중 오류가 발생했습니다: {str(exc)}', status=500)


@admin_bp.route('/admin/api/email-settings/update', methods=['POST'])
def update_email_settings():
    """이메일 인증 시스템 설정 값을 갱신한다."""
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    try:
        data = request.get_json(silent=True) or {}
        keys = [
            'email_verification_enabled',
            'email_verification_expiry_hours',
            'email_verification_max_attempts',
            'email_verification_lockout_hours',
        ]

        with get_conn() as conn:
            for key in keys:
                value = data.get(key)
                if value is not None:
                    conn.execute(
                        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                        (key, str(value)),
                    )
            conn.commit()

        return success('이메일 인증 설정이 업데이트되었습니다')

    except Exception as exc:  # pylint: disable=broad-except
        return error(f'설정 업데이트 중 오류가 발생했습니다: {str(exc)}', status=500)
