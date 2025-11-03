"""서비스 레이어: 관리자 시스템 설정 로직."""

from __future__ import annotations

import sqlite3
from typing import Dict

from core.db import get_conn


class SettingsServiceError(Exception):
    """시스템 설정 서비스 전용 예외."""


EMAIL_SETTING_KEYS = [
    'email_verification_enabled',
    'email_verification_expiry_hours',
    'email_verification_max_attempts',
    'email_verification_lockout_hours',
]


def fetch_email_settings() -> Dict:
    stats = {}
    try:
        from core.email_verification_manager import EmailVerificationManager

        email_manager = EmailVerificationManager()
        stats = email_manager.get_verification_stats()
    except Exception:  # pragma: no cover - optional dependency 환경에 따라 실패할 수 있음
        stats = {}

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
    return {'stats': stats, 'settings': settings_dict}


def update_email_settings(data: Dict[str, str]) -> None:
    with get_conn() as conn:
        for key in EMAIL_SETTING_KEYS:
            if key in data and data[key] is not None:
                conn.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    (key, str(data[key])),
                )
        conn.commit()
