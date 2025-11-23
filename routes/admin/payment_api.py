"""
관리자 결제 관리 API
Jet Engine 기반 최신 기술 스택 적용
"""

import logging
import sqlite3
from typing import Optional
from flask import request, jsonify
from pydantic import ValidationError

from core.responses import success, error
from core.db import get_conn_optimized as get_conn
from core.payment.service import PaymentService
from core.payment.schemas import PaymentCreate, PaymentCreateManual, PaymentResponse, PaymentStatus
from flask import session
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


@admin_bp.route('/admin/api/payments-manual/create', methods=['POST'])
def create_manual_payment():
    """
    수동 결제 생성 (관리자용 - 요금제 기반)
    
    Request Body:
        user_id: 사용자 ID
        product_id: 상품 ID (1: Standard, 2: Premium, 3: Gold)
        quantity: 수량 (Standard 상품에만 적용, 기본값: 1)
        status: 결제 상태 (기본값: completed)
    """
    # 관리자 인증 확인
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    try:
        # Request body 확인
        if not request.json:
            return error('요청 데이터가 없습니다', status=400)
        
        # Request body 파싱 및 검증
        try:
            payment_data = PaymentCreateManual(**request.json)
        except ValidationError as e:
            logger.warning(f"수동 결제 생성 유효성 검사 실패: {e.errors()}")
            return error('유효하지 않은 수동 결제 데이터입니다', errors=e.errors(), status=400)
        except Exception as e:
            logger.error(f"수동 결제 요청 데이터 파싱 실패: {str(e)}")
            return error(f'요청 데이터 파싱 실패: {str(e)}', status=400)
        
        admin_user_id = session.get('user_id')  # 세션에서 관리자 ID 가져오기
        if not admin_user_id:
            return error('관리자 인증 정보가 없습니다.', status=401)

        # 결제 생성 서비스 호출
        payment = payment_service.create_payment(
            user_id=payment_data.user_id,
            product_id=payment_data.product_id,
            quantity=payment_data.quantity,
            admin_user_id=admin_user_id,
            status=payment_data.status
        )
        
        return success('수동 결제가 성공적으로 생성되었습니다', data=payment.model_dump(), status=201)
        
    except ValueError as e:
        logger.warning(f"수동 결제 생성 실패: {str(e)}")
        return error(str(e), status=400)
    except Exception as e:
        logger.error(f"수동 결제 생성 중 오류: {str(e)}")
        return error(f'수동 결제 생성 중 오류가 발생했습니다: {str(e)}', status=500)


@admin_bp.route('/admin/api/payments/<int:payment_id>/cancel', methods=['PATCH'])
def cancel_payment(payment_id: int):
    """
    결제 취소 (관리자용)
    
    Path Parameters:
        payment_id: 취소할 결제 ID
        
    Returns:
        JSON: 취소된 결제 정보
    """
    # 관리자 인증 확인
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    try:
        admin_user_id = session.get('user_id')  # 세션에서 관리자 ID 가져오기
        if not admin_user_id:
            return error('관리자 인증 정보가 없습니다.', status=401)
        
        # 결제 취소 서비스 호출
        payment = payment_service.cancel_payment(
            payment_id=payment_id,
            admin_user_id=admin_user_id
        )
        
        return success('결제가 성공적으로 취소되었습니다', data=payment.model_dump(), status=200)
        
    except ValueError as e:
        logger.warning(f"결제 취소 실패: {str(e)}")
        return error(str(e), status=400)
    except Exception as e:
        logger.error(f"결제 취소 중 오류: {str(e)}")
        return error(f'결제 취소 중 오류가 발생했습니다: {str(e)}', status=500)


@admin_bp.route('/admin/api/payments', methods=['POST'])
def create_payment():
    """
    결제 생성 (관리자용 - 레거시 호환성)
    
    Request Body (기존 형식):
        user_id, order_id, amount, token_amount, pg_provider, status
    """
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    try:
        # Request body 파싱
        data = request.json or {}
        
        try:
            payment_data = PaymentCreate(**data)
        except ValidationError as e:
            return error(f'입력 데이터 검증 실패: {str(e)}', status=400)
        except Exception as e:
            return error(f'요청 데이터 파싱 실패: {str(e)}', status=400)
        
        # 기존 로직 (order_id 기반)
        # 주의: 이 방식은 토큰 지급을 하지 않음 (레거시 호환성)
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            
            # 주문 ID 중복 확인
            existing = conn.execute(
                "SELECT id FROM payment_history WHERE order_id = ?",
                (payment_data.order_id,)
            ).fetchone()
            
            if existing:
                return error(f"이미 존재하는 주문 ID입니다: {payment_data.order_id}", status=400)
            
            # 결제 생성
            cursor = conn.execute(
                """
                INSERT INTO payment_history 
                (user_id, order_id, amount, token_amount, status, pg_provider, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), datetime('now', 'localtime'))
                """,
                (
                    payment_data.user_id,
                    payment_data.order_id,
                    payment_data.amount,
                    payment_data.token_amount,
                    payment_data.status.value,
                    payment_data.pg_provider,
                )
            )
            
            conn.commit()
            payment_id = cursor.lastrowid
            
            payment = payment_service.get_payment_by_id(payment_id)
            return success('결제가 생성되었습니다', data=payment.model_dump())
        
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
        return success('ok', data=payment.model_dump())
        
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
        
        return success('결제 상태가 업데이트되었습니다', data=payment.model_dump())
        
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
        
        return success('ok', data=payment.model_dump())
        
    except Exception as e:
        logger.error(f"결제 조회 중 오류: {str(e)}")
        return error(f'결제 조회 중 오류가 발생했습니다: {str(e)}', status=500)

