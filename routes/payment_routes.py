import sqlite3
from datetime import datetime, timedelta
from uuid import uuid4

from flask import Blueprint, render_template, request, session

from core.db import get_conn
from core.responses import error, success

payment_bp = Blueprint('payment_routes', __name__)


def _ensure_free_trial_column(cursor):
    """
    users 테이블에 free_trial_expired_at 컬럼이 없으면 추가
    """
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'free_trial_expired_at' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN free_trial_expired_at TEXT")


# 결제 완료 API는 payment_complete_api.py로 이동됨
# 중복 라우트 방지를 위해 이 함수는 제거됨

def _build_shop_context():
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        products = conn.execute(
            """
            SELECT id, name, description, price, token_amount, duration_days, 
                   type, vat_included, is_active
            FROM products
            ORDER BY 
                CASE 
                    WHEN type IN ('event', 'event_period') THEN 0
                    ELSE 1
                END,
                id
            """
        ).fetchall()

        products_list = [dict(row) for row in products]
        
        event_products = [
            p for p in products_list
            if p.get('type') in ['event', 'event_period']
        ]
        regular_products = [
            p for p in products_list
            if p.get('type') not in ['event', 'event_period']
            and (p.get('is_active') or 0) == 1
        ]

        standard_product = next(
            (p for p in products_list if p.get('name', '').strip().lower() == 'standard'), 
            None
        )
        standard_price = standard_product.get('price', 500) if standard_product else 500

        premium_product = next(
            (p for p in products_list if p.get('name', '').strip().lower() == 'premium'), 
            None
        )
        discount_rate = 0

        if premium_product and standard_price > 0:
            premium_token_amount = premium_product.get('token_amount', 0)
            base_total = standard_price * premium_token_amount
            if base_total > 0:
                premium_price = premium_product.get('price', 0)
                discount_rate = int(((base_total - premium_price) / base_total) * 100)
                discount_rate = max(0, discount_rate)

        premium_per_token_price = 0
        if premium_product and premium_product.get('token_amount', 0) > 0:
            premium_per_token_price = int(premium_product.get('price', 0) / premium_product.get('token_amount', 1))

        user_info = {
            'user_id': session.get('user_id'),
            'username': session.get('username'),
            'is_admin': int(bool(session.get('is_admin')))
        }

        return {
            'products': products_list,
            'event_products': event_products,
            'regular_products': regular_products,
            'discount_rate': discount_rate,
            'premium_per_token_price': premium_per_token_price,
            'user_info': user_info
        }


@payment_bp.route('/pricing', methods=['GET'])
def pricing():
    """
    요금제 페이지 (기존 호환성 유지)
    """
    return shop()

@payment_bp.route('/shop', methods=['GET'])
def shop():
    """
    상점 페이지
    """
    try:
        context = _build_shop_context()
        return render_template('payment/shop.html', **context)
    except Exception as exc:
        return error(f'상점 페이지 로딩 실패: {str(exc)}', status=500)


@payment_bp.route('/showroom', methods=['GET'])
def showroom():
    """
    3D 쇼룸 페이지 (기능은 shop과 동일)
    """
    try:
        context = _build_shop_context()
        return render_template('payment/showroom.html', **context)
    except Exception as exc:
        return error(f'쇼룸 페이지 로딩 실패: {str(exc)}', status=500)



