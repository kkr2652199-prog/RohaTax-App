"""
관리자 결제 관리 API
Jet Engine 기반 최신 기술 스택 적용
"""

import logging
from typing import Optional
from flask import request, jsonify
from pydantic import ValidationError

from core.responses import success, error
from core.db import get_conn_optimized as get_conn
from core.payment.service import PaymentService
from core.payment.schemas import PaymentCreate, PaymentResponse, PaymentStatus
from ..utils.auth import ensure_admin_for_json
from . import admin_bp

logger = logging.getLogger(__name__)

# PaymentService 인스턴스 생성
payment_service = PaymentService()


@admin_bp.route('/admin/api/payments', methods=['GET'])
def get_payments():
    """
    결제 목록 조회 (관리자용)
    
    Query Parameters:
        page: 페이지 번호 (기본값: 1)
        per_page: 페이지당 항목 수 (기본값: 20)
        status: 결제 상태 필터 (pending, completed, failed, cancelled)
        user_id: 사용자 ID 필터
    """
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    try:
        # Query 파라미터 파싱
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_str = request.args.get('status', None, type=str)
        user_id = request.args.get('user_id', None, type=int)
        
        # 유효성 검증
        if page < 1:
            return error('페이지 번호는 1 이상이어야 합니다', status=400)
        if per_page < 1 or per_page > 100:
            return error('페이지당 항목 수는 1~100 사이여야 합니다', status=400)
        
        # Status 파싱
        status = None
        if status_str:
            try:
                status = PaymentStatus(status_str.lower())
            except ValueError:
                return error(f'유효하지 않은 결제 상태입니다: {status_str}', status=400)
        
        # 결제 목록 조회
        result = payment_service.get_all_payments(
            page=page,
            per_page=per_page,
            status=status,
            user_id=user_id
        )
        
        return success('ok', data=result)
        
    except Exception as e:
        logger.error(f"결제 목록 조회 중 오류: {str(e)}")
        return error(f'결제 목록 조회 중 오류가 발생했습니다: {str(e)}', status=500)


@admin_bp.route('/admin/api/payments', methods=['POST'])
def create_payment():
    """
    결제 생성 (관리자용)
    
    Request Body:
        user_id: 사용자 ID
        order_id: 주문 ID (Unique)
        amount: 결제 금액 (원 단위)
        token_amount: 지급될 토큰 수량
        pg_provider: PG사 정보 (선택사항)
        status: 결제 상태 (기본값: pending)
    """
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    try:
        # Request body 파싱 및 검증
        try:
            payment_data = PaymentCreate(**request.json)
        except ValidationError as e:
            return error(f'입력 데이터 검증 실패: {str(e)}', status=400)
        except Exception as e:
            return error(f'요청 데이터 파싱 실패: {str(e)}', status=400)
        
        # 결제 생성
        payment = payment_service.create_payment(payment_data)
        
        return success('결제가 생성되었습니다', data=payment.dict())
        
    except ValueError as e:
        logger.warning(f"결제 생성 실패: {str(e)}")
        return error(str(e), status=400)
    except Exception as e:
        logger.error(f"결제 생성 중 오류: {str(e)}")
        return error(f'결제 생성 중 오류가 발생했습니다: {str(e)}', status=500)


@admin_bp.route('/admin/api/payments/<int:payment_id>', methods=['GET'])
def get_payment(payment_id: int):
    """
    결제 상세 조회 (관리자용)
    
    Path Parameters:
        payment_id: 결제 ID
    """
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    try:
        payment = payment_service.get_payment_by_id(payment_id)
        return success('ok', data=payment.dict())
        
    except ValueError as e:
        return error(str(e), status=404)
    except Exception as e:
        logger.error(f"결제 조회 중 오류: {str(e)}")
        return error(f'결제 조회 중 오류가 발생했습니다: {str(e)}', status=500)


@admin_bp.route('/admin/api/payments/<int:payment_id>/status', methods=['PATCH'])
def update_payment_status(payment_id: int):
    """
    결제 상태 업데이트 (관리자용)
    
    Path Parameters:
        payment_id: 결제 ID
        
    Request Body:
        status: 새로운 결제 상태 (pending, completed, failed, cancelled)
    """
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    try:
        # Request body 파싱
        data = request.json or {}
        status_str = data.get('status')
        
        if not status_str:
            return error('결제 상태(status)는 필수입니다', status=400)
        
        # Status 파싱
        try:
            status = PaymentStatus(status_str.lower())
        except ValueError:
            return error(f'유효하지 않은 결제 상태입니다: {status_str}', status=400)
        
        # 결제 상태 업데이트
        payment = payment_service.update_payment_status(payment_id, status)
        
        return success('결제 상태가 업데이트되었습니다', data=payment.dict())
        
    except ValueError as e:
        return error(str(e), status=404)
    except Exception as e:
        logger.error(f"결제 상태 업데이트 중 오류: {str(e)}")
        return error(f'결제 상태 업데이트 중 오류가 발생했습니다: {str(e)}', status=500)


@admin_bp.route('/admin/api/payments/order/<order_id>', methods=['GET'])
def get_payment_by_order_id(order_id: str):
    """
    주문 ID로 결제 조회 (관리자용)
    
    Path Parameters:
        order_id: 주문 ID
    """
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    try:
        payment = payment_service.get_payment_by_order_id(order_id)
        
        if not payment:
            return error(f'주문 ID에 해당하는 결제를 찾을 수 없습니다: {order_id}', status=404)
        
        return success('ok', data=payment.dict())
        
    except Exception as e:
        logger.error(f"결제 조회 중 오류: {str(e)}")
        return error(f'결제 조회 중 오류가 발생했습니다: {str(e)}', status=500)

