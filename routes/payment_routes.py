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


# 결제 완료 API는 payment_complete_api.py로 이동됨
# 중복 라우트 방지를 위해 이 함수는 제거됨

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
    is_active=1인 모든 상품을 조회하여 템플릿에 전달
    이벤트 상품과 일반 상품을 구분하여 전달
    """
    try:
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            products = conn.execute(
                """
                SELECT id, name, description, price, token_amount, duration_days, 
                       type, vat_included, is_active
                FROM products
                WHERE COALESCE(is_active, 0) = 1
                ORDER BY 
                    CASE 
                        WHEN type IN ('event', 'event_period') THEN 0
                        ELSE 1
                    END,
                    id
                """
            ).fetchall()
            
            products_list = [dict(row) for row in products]
            
            # 이벤트 상품과 일반 상품 분리
            event_products = [p for p in products_list if p['type'] in ['event', 'event_period']]
            regular_products = [p for p in products_list if p['type'] not in ['event', 'event_period']]
        
        return render_template('payment/shop.html', 
                             products=products_list,
                             event_products=event_products,
                             regular_products=regular_products)
        
    except Exception as exc:
        return error(f'상점 페이지 로딩 실패: {str(exc)}', status=500)



