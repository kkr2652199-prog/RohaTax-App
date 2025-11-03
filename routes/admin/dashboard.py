from flask import redirect, render_template, url_for

from . import admin_bp
from ..utils.auth import current_user_id, ensure_admin_view
from core.db import get_conn


@admin_bp.route('/admin')
def admin_dashboard():
    """Render the administrator dashboard view."""

    response = ensure_admin_view()
    if response is not None:
        return response

    admin_user_id = current_user_id()
    with get_conn() as conn:
        admin_user = conn.execute(
            "SELECT username, is_admin FROM users WHERE id = ?",
            (admin_user_id,),
        ).fetchone()
        if not admin_user or not admin_user['is_admin']:
            return redirect(url_for('home.login'))

    return render_template('admin.html')
