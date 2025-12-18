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
    """
    상점/쇼룸/홈페이지 공통으로 사용하는 상품 컨텍스트 생성
    - products: 전체 상품 목록
    - event_products: 무료/이벤트 상품 (무료 토큰, 무료 기간 등)
    - regular_products: 정식 유료 상품 (Standard / Premium / Gold 등)
    - standard_product, premium_product, gold_product: 대표 요금제 3종
    - free_token_product, free_period_product: 무료 2종 (토큰/기간 기반 자동 선택)
    - discount_rate, premium_per_token_price: Premium 할인/단가 정보
    """
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

        # 1) 이벤트/정기 상품 분리
        event_products = [
            p for p in products_list
            if p.get('type') in ['event', 'event_period']
        ]
        regular_products = [
            p for p in products_list
            if p.get('type') not in ['event', 'event_period']
            and (p.get('is_active') or 0) == 1
        ]

        # 2) 정식 요금제(Standard / Premium / Gold)를 이름 기준으로 탐색
        def _find_by_name(name: str):
            target = name.strip().lower()
            return next(
                (p for p in products_list if p.get('name', '').strip().lower() == target),
                None,
            )

        standard_product = _find_by_name("standard")
        premium_product = _find_by_name("premium")
        gold_product = _find_by_name("gold")

        standard_price = standard_product.get('price', 500) if standard_product else 500

        # 3) Premium 할인율 계산 (Standard 단가 × 건수 vs Premium 패키지 가격)
        discount_rate = 0
        if premium_product and standard_price > 0:
            premium_token_amount = premium_product.get('token_amount', 0)
            base_total = standard_price * max(premium_token_amount, 0)
            if base_total > 0:
                premium_price = premium_product.get('price', 0)
                discount_rate = int(((base_total - premium_price) / base_total) * 100)
                discount_rate = max(0, discount_rate)

        # 4) Premium 1건당 단가
        premium_per_token_price = 0
        if premium_product and premium_product.get('token_amount', 0) > 0:
            premium_per_token_price = int(
                premium_product.get('price', 0) / premium_product.get('token_amount', 1)
            )

        # 5) 홈페이지/쇼룸에서 사용할 대표 무료 이벤트 상품 자동 선택
        free_token_product = next(
            (p for p in event_products if (p.get('token_amount') or 0) > 0),
            None,
        )
        free_period_product = next(
            (p for p in event_products if (p.get('duration_days') or 0) > 0),
            None,
        )

        user_info = {
            'user_id': session.get('user_id'),
            'username': session.get('username'),
            'is_admin': int(bool(session.get('is_admin'))),
        }

        return {
            'products': products_list,
            'event_products': event_products,
            'regular_products': regular_products,
            # 정식 요금제 대표 3종 (상점/홈페이지 공통 사용)
            'standard_product': standard_product,
            'premium_product': premium_product,
            'gold_product': gold_product,
            # 무료 이벤트 대표 2종 (토큰/기간)
            'free_token_product': free_token_product,
            'free_period_product': free_period_product,
            # 할인/단가 정보
            'discount_rate': discount_rate,
            'premium_per_token_price': premium_per_token_price,
            # 사용자 정보
            'user_info': user_info,
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



