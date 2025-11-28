"""
가상 결제 완료 API 모듈
상용화 준비: 주문(orders) → 결제 완료(payment_history) 사이클 완결
PaymentService 통합: 관리자와 동일한 결제 엔진 사용
"""

from flask import Blueprint, request, session
from core.db import get_conn_optimized as get_conn
from core.responses import success, error
from core.payment.service import PaymentService
from core.payment.schemas import PaymentStatus
import sqlite3
import logging

logger = logging.getLogger(__name__)

payment_complete_bp = Blueprint('payment_complete_api', __name__, url_prefix='/api/payment')


@payment_complete_bp.route('/complete', methods=['POST'])
def complete_payment():
    """
    가상 결제 완료 처리 API (PaymentService 통합)
    
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
            conn.row_factory = sqlite3.Row
            
            # 2. orders 테이블에서 주문 찾기 (user_id, product_id, quantity 추출)
            order_row = conn.execute(
                """
                SELECT id, user_id, merchant_uid, product_id, product_name,
                       amount, supply_price, vat, quantity, status
                FROM orders
                WHERE merchant_uid = ? AND status = 'ready'
                """,
                (merchant_uid,)
            ).fetchone()
            
            if not order_row:
                logger.warning(f"주문을 찾을 수 없음: merchant_uid={merchant_uid}")
                return error(f'주문을 찾을 수 없습니다: {merchant_uid}', status=404)
            
            # sqlite3.Row를 dict로 변환 (안전한 접근을 위해)
            order = dict(order_row)
            
            # 주문서에서 필수 정보 추출
            user_id = order['user_id']
            product_id = order['product_id']
            quantity = order.get('quantity', 1)  # 기본값 1
            
            if not user_id or not product_id:
                logger.warning(f"주문서에 필수 정보 없음: user_id={user_id}, product_id={product_id}")
                return error('주문서에 user_id 또는 product_id가 없습니다.', status=400)
            
            # 세션 인증 확인 (선택적 - 주문서의 user_id와 비교)
            session_user_id = session.get('user_id')
            if session_user_id and session_user_id != user_id:
                logger.warning(f"주문 소유자 불일치: order_user_id={user_id}, session_user_id={session_user_id}")
                return error('주문 소유자가 일치하지 않습니다', status=403)
            
            # 3. PaymentService 호출 (쌍둥이 엔진 가동)
            service = PaymentService()
            payment_result = service.create_payment(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity,  # DB에서 꺼낸 수량
                admin_user_id=user_id,  # 본인이 본인에게
                status=PaymentStatus.COMPLETED,
                order_id=merchant_uid  # merchant_uid를 order_id로 사용
            )
            
            # 4. orders 테이블 상태를 'paid'로 업데이트
            conn.execute(
                """
                UPDATE orders
                SET status = 'paid', updated_at = datetime('now', 'localtime')
                WHERE merchant_uid = ?
                """,
                (merchant_uid,)
            )
            conn.commit()
            
            # 5. 사용자 최신 토큰 잔액 조회 (응답용)
            user_row = conn.execute(
                """
                SELECT COALESCE(token_balance, 0) AS token_balance
                FROM users
                WHERE id = ?
                """,
                (user_id,)
            ).fetchone()
            
            new_token_balance = user_row['token_balance'] if user_row else 0
            
            logger.info(
                f"가상 결제 완료 (PaymentService 통합): merchant_uid={merchant_uid}, "
                f"payment_id={payment_result.id}, user_id={user_id}, quantity={quantity}"
            )
            
            # 6. 응답 반환
            return success(
                '결제가 완료되었습니다',
                data={
                    'payment_id': payment_result.id,
                    'merchant_uid': merchant_uid,
                    'new_token_balance': new_token_balance,
                    'token_amount': payment_result.token_amount,
                    'amount': payment_result.amount,
                    'quantity': quantity
                }
            )
    
    except ValueError as e:
        # PaymentService에서 발생한 검증 오류
        logger.warning(f"결제 처리 검증 오류: {str(e)}")
        return error(str(e), status=400)
    except sqlite3.Error as e:
        logger.error(f"DB 오류: {str(e)}")
        return error(f'결제 처리 중 데이터베이스 오류가 발생했습니다: {str(e)}', status=500)
    except Exception as e:
        logger.error(f"결제 처리 중 오류: {str(e)}")
        return error(f'결제 처리 중 오류가 발생했습니다: {str(e)}', status=500)

