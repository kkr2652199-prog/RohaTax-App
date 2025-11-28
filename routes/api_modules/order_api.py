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
    
    if not product_id:
        return error('product_id는 필수입니다', status=400)
    
    try:
        product_id = int(product_id)
    except (ValueError, TypeError):
        return error('product_id는 정수여야 합니다', status=400)
    
    # 3. 상품 정보 조회
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        product = conn.execute(
            """
            SELECT id, name, description, price, token_amount, type, is_active
            FROM products
            WHERE id = ? AND COALESCE(is_active, 0) = 1
            """,
            (product_id,)
        ).fetchone()
        
        if not product:
            logger.warning(f"상품을 찾을 수 없음: product_id={product_id}")
            return error(f'상품을 찾을 수 없습니다: ID {product_id}', status=404)
        
        # 4. 사용자 정보 조회 (buyer_email, buyer_name)
        user = conn.execute(
            """
            SELECT email, username, company_name
            FROM users
            WHERE id = ? AND COALESCE(is_deleted, 0) = 0
            """,
            (user_id,)
        ).fetchone()
        
        if not user:
            logger.warning(f"사용자를 찾을 수 없음: user_id={user_id}")
            return error('사용자 정보를 찾을 수 없습니다', status=404)
        
        # 5. 금액 및 세금 계산
        total_amount = product['price'] or 0
        
        # 세금 계산기 사용
        supply_price, vat = calculate_tax(total_amount)
        
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
                    amount, supply_price, vat, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 'ready', datetime('now', 'localtime'))
                """,
                (
                    user_id,
                    merchant_uid,
                    product_id,
                    product['name'],
                    total_amount,
                    supply_price,
                    vat
                )
            )
            conn.commit()
            
            logger.info(f"주문 생성 성공: merchant_uid={merchant_uid}, user_id={user_id}, product_id={product_id}")
            
            # 8. 응답 반환
            return success(
                '주문이 생성되었습니다',
                data={
                    'merchant_uid': merchant_uid,
                    'amount': total_amount,
                    'supply_price': supply_price,
                    'vat': vat,
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

