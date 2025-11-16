from flask import redirect, render_template, url_for

import sqlite3

from . import admin_bp
from ..utils.auth import current_user_id, ensure_admin_view
from core.db import get_conn_optimized as get_conn

try:
    from core.email_verification_manager import EmailVerificationManager
except ImportError:  # pragma: no cover - optional dependency
    EmailVerificationManager = None


@admin_bp.route('/admin')
def admin_dashboard():
    """Render the administrator dashboard view."""

    response = ensure_admin_view()
    if response is not None:
        return response

    admin_user_id = current_user_id()
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        admin_user = conn.execute(
            "SELECT username, is_admin FROM users WHERE id = ?",
            (admin_user_id,),
        ).fetchone()
        if not admin_user or not admin_user['is_admin']:
            return redirect(url_for('auth.login'))

        general_users_rows = conn.execute(
            """
            SELECT id, username, email, company_name, business_number, representative_name,
                   phone, address, business_type, business_category, plan_type,
                   used_count, monthly_limit, token_balance, tokens_used, is_active,
                   approval_status, created_at
            FROM users
            WHERE COALESCE(is_deleted, 0) = 0 AND COALESCE(is_admin, 0) = 0
            ORDER BY created_at DESC
            """
        ).fetchall()
        general_users = [dict(row) for row in general_users_rows]

        admin_users = conn.execute(
            """
            SELECT id, username, email, company_name, business_number, representative_name,
                   phone, address, plan_type, monthly_limit, used_count, is_active,
                   created_at, COALESCE(token_balance, 0) AS token_balance,
                   COALESCE(tokens_used, 0) AS tokens_used,
                   COALESCE(approval_status, 'pending') AS approval_status
            FROM users
            WHERE COALESCE(is_deleted, 0) = 0 AND is_admin = 1
            ORDER BY created_at ASC
            """
        ).fetchall()

        total_issued_tokens = conn.execute(
            "SELECT COALESCE(SUM(token_balance), 0) as total_issued FROM users WHERE COALESCE(is_deleted, 0) = 0"
        ).fetchone()[0]

        active_users_count = conn.execute(
            """
            SELECT COUNT(*) as active_count
            FROM users
            WHERE COALESCE(is_deleted, 0) = 0 AND is_active = 1 AND COALESCE(is_admin, 0) = 0
            """
        ).fetchone()[0]

        token_history = conn.execute(
            """
            SELECT th.id,
                   th.change_type AS action,
                   th.amount,
                   strftime('%Y-%m-%dT%H:%M:%SZ', th.created_at) AS timestamp_utc,
                   admin.username AS admin_username,
                   target.username AS target_username
            FROM token_history th
            JOIN users admin ON th.changed_by = admin.id
            JOIN users target ON th.user_id = target.id
            ORDER BY th.created_at DESC
            LIMIT 20
            """
        ).fetchall()

        conversions_summary = conn.execute(
            """
            SELECT user_id, COUNT(*) AS conversions
            FROM conversion_logs
            GROUP BY user_id
            ORDER BY conversions DESC
            LIMIT 5
            """
        ).fetchall()

        email_stats = {}
        email_settings = {}
        if EmailVerificationManager is not None:
            try:
                email_manager = EmailVerificationManager()
                email_stats = email_manager.get_verification_stats()
            except Exception:  # pragma: no cover - email manager optional
                email_stats = {}

        settings_rows = conn.execute(
            """
            SELECT key, value FROM settings
            WHERE key LIKE 'email_verification_%'
            ORDER BY key
            """
        ).fetchall()
        email_settings = {row[0]: row[1] for row in settings_rows}

    initial_payload = {
        'general_users': general_users,
        'admin_users': [dict(row) for row in admin_users],
        'dashboard_stats': {
            'total_issued_tokens': total_issued_tokens,
            'active_users_count': active_users_count,
            'system_error_rate': 0.1,
            'system_uptime': 99.9,
        },
        'token_history': [dict(row) for row in token_history],
        'top_conversions': [dict(user) for user in conversions_summary],
        'email_stats': email_stats,
        'email_settings': email_settings,
    }

    return render_template('admin.html', admin_initial_data=initial_payload)
