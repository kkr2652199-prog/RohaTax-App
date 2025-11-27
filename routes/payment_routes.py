from datetime import datetime, timedelta
from uuid import uuid4

from flask import Blueprint, request, render_template

from core.db import get_conn
from core.responses import success, error
import sqlite3

payment_bp = Blueprint('payment_routes', __name__)


def _ensure_free_trial_column(cursor):
    """
    users 테이블에 free_trial_expired_at 컬럼이 없으면 추가
    """
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'free_trial_expired_at' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN free_trial_expired_at TEXT")


@payment_bp.route('/api/payment/complete', methods=['POST'])
def complete_payment():
    """
    기간제 상품 구매 시 결제 완료 처리
    """
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    payment_method = data.get('payment_method', 'card')

    if not user_id or not product_id:
        return error('user_id와 product_id는 필수입니다.', status=400)

    try:
        with get_conn() as conn:
            conn.row_factory = None
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION")

            product = cursor.execute(
                """
                SELECT id, name, type, price, token_amount, duration_days
                FROM products
                WHERE id = ?
                """,
                (product_id,)
            ).fetchone()

            if not product:
                cursor.execute("ROLLBACK")
                return error(f"상품을 찾을 수 없습니다: ID {product_id}", status=404)

            amount = product[3] or 0
            token_amount = product[4] if product[4] is not None else 0
            supply_price = amount
            vat = 0
            expiration_iso = None

            if product[2] == 'event_period':
                duration_days = product[5] or 0
                amount = 0
                supply_price = 0
                token_amount = 0
                expiration = datetime.now() + timedelta(days=max(1, duration_days))
                expiration_iso = expiration.strftime('%Y-%m-%d %H:%M:%S')
                _ensure_free_trial_column(cursor)
                cursor.execute(
                    """
                    UPDATE users
                    SET free_trial_expired_at = ?, updated_at = datetime('now', 'localtime')
                    WHERE id = ?
                    """,
                    (expiration_iso, user_id)
                )

            order_uid = f"PAY-{uuid4().hex}"
            cursor.execute(
                """
                INSERT INTO orders 
                (user_id, product_id, order_uid, status, amount, token_amount, supply_price, vat, payment_method, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), datetime('now', 'localtime'))
                """,
                (
                    user_id,
                    product_id,
                    order_uid,
                    'completed',
                    amount,
                    token_amount,
                    supply_price,
                    vat,
                    payment_method
                )
            )

            conn.commit()

            return success(
                '기간제 상품 결제 완료',
                data={
                    'order_uid': order_uid,
                    'product_id': product_id,
                    'free_trial_expired_at': expiration_iso
                }
            )

    except Exception as exc:
        return error(f'결제 처리를 실패했습니다: {str(exc)}', status=500)


@payment_bp.route('/pricing', methods=['GET'])
def pricing():
    """
    요금제 페이지
    모든 상품을 조회하여 템플릿에 전달 (is_active 필터링은 템플릿에서 처리)
    """
    try:
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            products = conn.execute(
                """
                SELECT id, name, description, price, token_amount, duration_days, 
                       type, vat_included, is_active
                FROM products
                ORDER BY id
                """
            ).fetchall()
            
            products_list = [dict(row) for row in products]
        
        return render_template('pricing.html', products=products_list)
        
    except Exception as exc:
        return error(f'요금제 페이지 로딩 실패: {str(exc)}', status=500)



