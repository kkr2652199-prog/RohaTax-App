"""
가상 결제 완료 API 모듈
상용화 준비: 주문(orders) → 결제 완료(payment_history) 사이클 완결
"""

from flask import Blueprint, request, session
from core.db import get_conn_optimized as get_conn
from core.responses import success, error
import sqlite3
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

payment_complete_bp = Blueprint('payment_complete_api', __name__, url_prefix='/api/payment')


@payment_complete_bp.route('/complete', methods=['POST'])
def complete_payment():
    """
    가상 결제 완료 처리 API
    
    Request Body (JSON):
        {
            "merchant_uid": "ORD-20251128-abc123..."
        }
    
    Response:
        {
            "success": true,
            "message": "결제가 완료되었습니다",
            "data": {
                "new_token_balance": 100,
                "payment_id": 1
            }
        }
    """
    # 1. 입력 데이터 확인
    data = request.get_json(silent=True) or {}
    merchant_uid = data.get('merchant_uid')
    
    if not merchant_uid:
        return error('merchant_uid는 필수입니다', status=400)
    
    try:
        with get_conn() as conn:
            # get_conn_optimized는 이미 row_factory를 설정하므로 중복 설정 제거
            
            # 2. orders 테이블에서 주문 찾기 (user_id, product_id 추출)
            order = conn.execute(
                """
                SELECT id, user_id, merchant_uid, product_id, product_name,
                       amount, supply_price, vat, status
                FROM orders
                WHERE merchant_uid = ? AND status = 'ready'
                """,
                (merchant_uid,)
            ).fetchone()
            
            if not order:
                logger.warning(f"주문을 찾을 수 없음: merchant_uid={merchant_uid}")
                return error(f'주문을 찾을 수 없습니다: {merchant_uid}', status=404)
            
            # 주문서에서 user_id와 product_id 추출 (보안상 주문서 데이터 사용)
            user_id = order['user_id']
            product_id = order['product_id']
            order_amount = order['amount']
            
            if not user_id or not product_id:
                logger.warning(f"주문서에 필수 정보 없음: user_id={user_id}, product_id={product_id}")
                return error('주문서에 user_id 또는 product_id가 없습니다.', status=400)
            
            # 세션 인증 확인 (선택적 - 주문서의 user_id와 비교)
            session_user_id = session.get('user_id')
            if session_user_id and session_user_id != user_id:
                logger.warning(f"주문 소유자 불일치: order_user_id={user_id}, session_user_id={session_user_id}")
                return error('주문 소유자가 일치하지 않습니다', status=403)
            
            # 4. 상품 정보 조회 (토큰 지급 및 기간 연장을 위해)
            product = conn.execute(
                """
                SELECT id, name, type, price, token_amount, duration_days
                FROM products
                WHERE id = ?
                """,
                (product_id,)
            ).fetchone()
            
            if not product:
                logger.warning(f"상품을 찾을 수 없음: product_id={product_id}")
                return error(f'상품을 찾을 수 없습니다: ID {product_id}', status=404)
            
            product_type = product['type']
            token_amount = product['token_amount'] or 0
            duration_days = product['duration_days']
            
            # 5. payment_history 테이블에 데이터 복사
            # 주문서(orders)의 정보를 그대로 베껴서 결제 장부(payment_history)에 기록
            cursor = conn.execute(
                """
                INSERT INTO payment_history (
                    user_id, order_id, amount, token_amount, status, pg_provider,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, 'completed', 'test_virtual',
                        datetime('now', 'localtime'), datetime('now', 'localtime'))
                """,
                (
                    user_id,  # 주문서에서 추출한 user_id
                    merchant_uid,  # order_id에 merchant_uid 저장
                    order_amount,  # 주문서에서 추출한 amount
                    token_amount  # 상품 정보에서 가져온 token_amount
                )
            )
            
            payment_id = cursor.lastrowid
            
            # 6. orders 테이블 상태를 'paid'로 업데이트
            conn.execute(
                """
                UPDATE orders
                SET status = 'paid', updated_at = datetime('now', 'localtime')
                WHERE merchant_uid = ?
                """,
                (merchant_uid,)
            )
            
            # 7. 토큰 지급 (token_amount > 0인 경우만)
            new_token_balance = None
            if token_amount > 0:
                # 현재 토큰 잔액 조회
                user_row = conn.execute(
                    """
                    SELECT COALESCE(token_balance, 0) AS token_balance
                    FROM users
                    WHERE id = ?
                    """,
                    (user_id,)
                ).fetchone()
                
                if user_row:
                    current_balance = user_row['token_balance'] or 0
                    new_token_balance = current_balance + token_amount
                    
                    conn.execute(
                        """
                        UPDATE users
                        SET token_balance = ?, updated_at = datetime('now', 'localtime')
                        WHERE id = ?
                        """,
                        (new_token_balance, user_id)
                    )
                    logger.info(f"토큰 지급 완료: user_id={user_id}, {current_balance} + {token_amount} = {new_token_balance}")
            
            # 8. 기간제 상품 처리 (event_period 타입)
            if product_type == 'event_period' and duration_days:
                # free_trial_expired_at 컬럼 확인 및 추가
                columns_info = conn.execute("PRAGMA table_info(users)").fetchall()
                columns = [row[1] for row in columns_info]
                if 'free_trial_expired_at' not in columns:
                    conn.execute("ALTER TABLE users ADD COLUMN free_trial_expired_at TEXT")
                
                # 기간 연장 계산
                expiration = datetime.now() + timedelta(days=max(1, duration_days))
                expiration_iso = expiration.strftime('%Y-%m-%d %H:%M:%S')
                
                conn.execute(
                    """
                    UPDATE users
                    SET free_trial_expired_at = ?, updated_at = datetime('now', 'localtime')
                    WHERE id = ?
                    """,
                    (expiration_iso, user_id)
                )
                logger.info(f"기간제 상품 기간 연장: user_id={user_id}, {duration_days}일 → {expiration_iso}")
            
            # 트랜잭션 커밋 (컨텍스트 매니저가 자동으로 처리하지만, 명시적으로 커밋)
            conn.commit()
            
            logger.info(f"가상 결제 완료: merchant_uid={merchant_uid}, payment_id={payment_id}, user_id={user_id}")
            
            # 9. 응답 반환
            return success(
                '결제가 완료되었습니다',
                data={
                    'payment_id': payment_id,
                    'merchant_uid': merchant_uid,
                    'new_token_balance': new_token_balance,
                    'token_amount': token_amount,
                    'product_type': product_type
                }
            )
    
    except sqlite3.Error as e:
        logger.error(f"DB 오류: {str(e)}")
        return error(f'결제 처리 중 데이터베이스 오류가 발생했습니다: {str(e)}', status=500)
    except Exception as e:
        logger.error(f"결제 처리 중 오류: {str(e)}")
        return error(f'결제 처리 중 오류가 발생했습니다: {str(e)}', status=500)

