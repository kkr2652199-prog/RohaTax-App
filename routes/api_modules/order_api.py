"""
주문 생성 API 모듈
상용화 준비: 주문 생성 및 세금 계산 로직 표준화
"""

from flask import Blueprint, request, jsonify, session
from core.db import get_conn_optimized as get_conn
from core.responses import success, error
from core.utils.tax_calculator import calculate_tax
import sqlite3
import logging
from datetime import datetime
from uuid import uuid4

logger = logging.getLogger(__name__)

order_bp = Blueprint('order_api', __name__, url_prefix='/api/orders')


@order_bp.route('/create', methods=['POST'])
def create_order():
    """
    주문 생성 API
    
    Request Body (JSON):
        {
            "product_id": 2
        }
    
    Response:
        {
            "success": true,
            "message": "주문이 생성되었습니다",
            "data": {
                "merchant_uid": "ORD-20251128-abc123...",
                "amount": 25000,
                "supply_price": 22727,
                "vat": 2273,
                "product_name": "Premium",
                "buyer_email": "user@example.com",
                "buyer_name": "사용자명"
            }
        }
    """
    # 1. 인증 확인
    user_id = session.get('user_id')
    if not user_id:
        return error('로그인이 필요합니다', status=401)
    
    # 2. 입력 데이터 확인
    data = request.get_json(silent=True) or {}
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)  # 기본값 1
    
    if not product_id:
        return error('product_id는 필수입니다', status=400)
    
    try:
        product_id = int(product_id)
        quantity = int(quantity) if quantity else 1
        if quantity < 1:
            return error('quantity는 1 이상이어야 합니다', status=400)
    except (ValueError, TypeError):
        return error('product_id와 quantity는 정수여야 합니다', status=400)
    
    # 3. 상품 정보 조회
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        product = conn.execute(
            """
            SELECT id, name, description, price, token_amount, type, is_active, one_time_limit
            FROM products
            WHERE id = ? AND COALESCE(is_active, 0) = 1
            """,
            (product_id,)
        ).fetchone()
        
        if not product:
            logger.warning(f"상품을 찾을 수 없음: product_id={product_id}")
            return error(f'상품을 찾을 수 없습니다: ID {product_id}', status=404)
        
        # 4. 사용자 정보 조회 (buyer_email, buyer_name, business_number)
        user = conn.execute(
            """
            SELECT email, username, company_name, business_number
            FROM users
            WHERE id = ? AND COALESCE(is_deleted, 0) = 0
            """,
            (user_id,)
        ).fetchone()
        
        if not user:
            logger.warning(f"사용자를 찾을 수 없음: user_id={user_id}")
            return error('사용자 정보를 찾을 수 없습니다', status=404)
        
        # 4-1. 무료 이벤트 1회 제한 / 사업자번호 기준 중복 구매 차단
        try:
            one_time_limit = product.get('one_time_limit', 0)
        except AttributeError:
            # sqlite3.Row인 경우 dict로 변환
            product = dict(product)
            one_time_limit = product.get('one_time_limit', 0)
        
        if one_time_limit == 1:
            # 검사 1: 동일 계정(user_id)이 이미 "무료 이벤트 그룹" 중 하나라도 완료했는지 확인
            #  - 대상 그룹: type IN ('event', 'event_period') AND price = 0 AND one_time_limit = 1
            exists_self = conn.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM payment_history ph
                JOIN orders o ON ph.order_id = o.merchant_uid
                WHERE ph.user_id = ?
                  AND ph.status = 'completed'
                  AND o.product_id IN (
                      SELECT id
                      FROM products
                      WHERE type IN ('event', 'event_period')
                        AND COALESCE(price, 0) = 0
                        AND COALESCE(one_time_limit, 0) = 1
                  )
                """,
                (user_id,)
            ).fetchone()
            
            if exists_self and (exists_self['cnt'] or 0) > 0:
                logger.info(
                    f"무료 이벤트 1회 제한 - 동일 계정 차단: user_id={user_id}, product_id={product_id}"
                )
                return error('이미 참여하신 이벤트입니다.', status=400)
            
            # 검사 2: 동일 사업자번호(business_number)를 가진 다른 계정이 이미 혜택을 받은 경우 차단
            business_number = user['business_number'] if 'business_number' in user.keys() else None
            if business_number:
                exists_same_biz = conn.execute(
                    """
                    SELECT COUNT(*) AS cnt
                    FROM payment_history ph
                    JOIN orders o ON ph.order_id = o.merchant_uid
                    JOIN users u ON u.id = ph.user_id
                    WHERE ph.status = 'completed'
                      AND u.business_number = ?
                      AND u.id != ?
                      AND o.product_id IN (
                          SELECT id
                          FROM products
                          WHERE type IN ('event', 'event_period')
                            AND COALESCE(price, 0) = 0
                            AND COALESCE(one_time_limit, 0) = 1
                      )
                    """,
                    (business_number, user_id)
                ).fetchone()
                
                if exists_same_biz and (exists_same_biz['cnt'] or 0) > 0:
                    logger.info(
                        "무료 이벤트 1회 제한 - 동일 사업자번호 차단: "
                        f"user_id={user_id}, business_number={business_number}, product_id={product_id}"
                    )
                    return error('귀하의 사업자번호로 이미 혜택을 받으셨습니다.', status=400)
        
        # 5. 금액 및 세금 계산 (부가세 별도 과금 방식 + 가변 부가세 로직)
        unit_price = product['price'] or 0
        # product.price는 공급가액이므로, 수량을 곱한 것이 총 공급가액
        supply_price = unit_price * quantity
        
        # 5-1. 결제 수단 및 증빙 신청 여부 확인
        payment_method = data.get('payment_method', 'card')  # 기본값: 카드
        if not payment_method or payment_method.strip() == '':
            payment_method = 'card'
        
        tax_evidence_requested = data.get('tax_evidence_requested', True)  # 기본값: 증빙 신청
        # Boolean 또는 문자열로 올 수 있으므로 정규화
        if isinstance(tax_evidence_requested, str):
            tax_evidence_requested = tax_evidence_requested.lower() in ('true', '1', 'yes')
        tax_evidence_requested = bool(tax_evidence_requested)
        
        # 5-2. 가변 부가세 계산 로직
        if payment_method == 'trans' and not tax_evidence_requested:
            # 계좌이체 + 증빙 미신청: 부가세 0원
            vat = 0
            total_amount = supply_price
        else:
            # 카드 또는 계좌이체 + 증빙 신청: 부가세 포함
            vat = round(supply_price * 0.1)
            total_amount = supply_price + vat
        
        # 6. merchant_uid 생성: ORD-{YYYYMMDD}-{UUID4}
        today = datetime.now().strftime('%Y%m%d')
        unique_id = str(uuid4()).replace('-', '')[:12]  # UUID4의 앞 12자리만 사용
        merchant_uid = f"ORD-{today}-{unique_id}"
        
        # 7. DB 저장 (INSERT)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO orders (
                    user_id, merchant_uid, product_id, product_name,
                    amount, supply_price, vat, quantity, status, payment_method, tax_evidence_requested, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ready', ?, ?, datetime('now', 'localtime'))
                """,
                (
                    user_id,
                    merchant_uid,
                    product_id,
                    product['name'],
                    total_amount,
                    supply_price,
                    vat,
                    quantity,  # 수량 저장
                    payment_method,  # 결제 수단 저장
                    int(tax_evidence_requested)  # 증빙 신청 여부 저장 (0 또는 1)
                )
            )
            conn.commit()
            
            logger.info(f"주문 생성 성공: merchant_uid={merchant_uid}, user_id={user_id}, product_id={product_id}, quantity={quantity}")
            
            # 8. 응답 반환
            return success(
                '주문이 생성되었습니다',
                data={
                    'merchant_uid': merchant_uid,
                    'amount': total_amount,
                    'supply_price': supply_price,
                    'vat': vat,
                    'quantity': quantity,
                    'product_id': product_id,
                    'product_name': product['name'],
                    'buyer_email': user['email'] or '',
                    'buyer_name': user['company_name'] or user['username'] or ''
                }
            )
            
        except sqlite3.IntegrityError as e:
            conn.rollback()
            logger.error(f"주문 생성 중 DB 무결성 오류: {str(e)}")
            return error('주문 생성 중 오류가 발생했습니다 (중복된 주문 ID)', status=500)
        except Exception as e:
            conn.rollback()
            logger.error(f"주문 생성 중 오류: {str(e)}")
            return error(f'주문 생성 중 오류가 발생했습니다: {str(e)}', status=500)

