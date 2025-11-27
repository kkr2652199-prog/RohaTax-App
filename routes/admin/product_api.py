"""
상품(패키지) 관리 API
관리자용 상품 CRUD 엔드포인트
"""

from flask import Blueprint, jsonify, request
from core.responses import success, error
from core.product.service import ProductService
from core.product.schemas import ProductCreate, ProductUpdate, ProductResponse
from pydantic import ValidationError
from ..utils.auth import ensure_admin_for_json
from . import admin_bp
import logging

logger = logging.getLogger(__name__)
product_service = ProductService()

DEFAULT_PRODUCTS = [
    {
        'name': 'Standard',
        'description': '기본 토큰 상품',
        'price': 500,
        'token_amount': 1,
        'type': 'basic',
        'vat_included': False,
        'duration_days': None,
        'is_active': True,
    },
    {
        'name': 'Premium Package',
        'description': '할인 패키지',
        'price': 25000,
        'token_amount': 100,
        'type': 'package',
        'vat_included': False,
        'duration_days': None,
        'is_active': True,
    },
    {
        'name': 'Gold Membership',
        'description': '무제한 이용권',
        'price': 70000,
        'token_amount': -1,
        'type': 'subscription',
        'vat_included': False,
        'duration_days': None,
        'is_active': True,
    },
    {
        'name': 'Welcome Event',
        'description': '신규 가입자를 위한 무료 토큰 혜택',
        'price': 0,
        'token_amount': 50,
        'type': 'event',
        'vat_included': True,
        'duration_days': None,
        'is_active': False,
    },
    {
        'name': 'Welcome Period Event',
        'description': '신규 가입자를 위한 기간제 혜택',
        'price': 0,
        'token_amount': 0,
        'type': 'event_period',
        'vat_included': True,
        'duration_days': 3,
        'is_active': False,
    },
]


def ensure_default_products(existing_products: list[dict]) -> None:
    """
    기본 상품 5종이 존재하지 않으면 자동으로 복구한다.
    """
    existing_names = {
        (product.get('name') or '').strip().lower()
        for product in existing_products
    }

    created_names = []

    for default_product in DEFAULT_PRODUCTS:
        normalized_name = default_product['name'].strip().lower()
        if normalized_name in existing_names:
            continue

        try:
            product_service.create_product(ProductCreate(**default_product))
            created_names.append(default_product['name'])
        except Exception as exc:
            logger.error(f"기본 상품 '{default_product['name']}' 복구 중 오류: {exc}")

    if created_names:
        logger.info(
            "상품 데이터가 유실되어 기본 상품을 복구했습니다: %s",
            ', '.join(created_names)
        )


@admin_bp.route('/admin/api/products', methods=['GET'])
def get_products():
    """
    상품 목록 조회
    
    Query Parameters:
        page: 페이지 번호 (기본값: 1)
        per_page: 페이지당 항목 수 (기본값: 20)
        is_active: 활성화 상태 필터 (true/false, 선택사항)
    """
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        is_active_param = request.args.get('is_active', type=str)
        
        # is_active 파라미터 파싱
        is_active = None
        if is_active_param:
            if is_active_param.lower() == 'true':
                is_active = True
            elif is_active_param.lower() == 'false':
                is_active = False
        
        # 전체 상품을 한 번 조회하여 유실 여부 확인
        all_products_snapshot = product_service.get_all_products(
            page=1,
            per_page=1000,
            is_active=None
        )

        if all_products_snapshot.get('total', 0) < 5:
            ensure_default_products(all_products_snapshot.get('products', []))
            # 복구 후 다시 전체 스냅샷 갱신
            all_products_snapshot = product_service.get_all_products(
                page=1,
                per_page=1000,
                is_active=None
            )

        # 클라이언트 요청 기준으로 다시 조회
        result = product_service.get_all_products(
            page=page,
            per_page=per_page,
            is_active=is_active
        )
        
        return success('ok', data=result)
        
    except Exception as e:
        logger.error(f"상품 목록 조회 중 오류: {str(e)}")
        return error(f'상품 목록 조회 중 오류가 발생했습니다: {str(e)}', status=500)


@admin_bp.route('/admin/api/products', methods=['POST'])
def create_product():
    """
    상품 생성
    
    Request Body:
        name: 상품명 (필수)
        description: 상품 설명 (선택)
        price: 가격 (필수, 원 단위)
        token_amount: 지급 토큰 수 (필수, 무제한은 -1)
        is_active: 판매 중 여부 (기본값: true)
    """
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    try:
        data = request.get_json()
        
        if not data:
            return error('요청 데이터가 없습니다', status=400)
        
        # Pydantic 모델로 검증
        try:
            product_create = ProductCreate(**data)
        except ValidationError as e:
            return error(f'입력 데이터 검증 실패: {str(e)}', status=400)
        
        # 상품 생성
        product = product_service.create_product(product_create)
        
        # Pydantic v1/v2 호환성
        if hasattr(product, 'model_dump'):
            product_dict = product.model_dump()
        else:
            product_dict = product.dict()
        
        return success('상품이 생성되었습니다', data=product_dict, status=201)
        
    except ValueError as e:
        logger.warning(f"상품 생성 검증 오류: {str(e)}")
        return error(str(e), status=400)
    except Exception as e:
        logger.error(f"상품 생성 중 오류: {str(e)}")
        return error(f'상품 생성 중 오류가 발생했습니다: {str(e)}', status=500)


@admin_bp.route('/admin/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id: int):
    """
    상품 상세 조회
    
    Path Parameters:
        product_id: 상품 ID
    """
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    try:
        product = product_service.get_product_by_id(product_id)
        
        # Pydantic v1/v2 호환성
        if hasattr(product, 'model_dump'):
            product_dict = product.model_dump()
        else:
            product_dict = product.dict()
        
        return success('ok', data=product_dict)
        
    except ValueError as e:
        logger.warning(f"상품 조회 오류: {str(e)}")
        return error(str(e), status=404)
    except Exception as e:
        logger.error(f"상품 조회 중 오류: {str(e)}")
        return error(f'상품 조회 중 오류가 발생했습니다: {str(e)}', status=500)


@admin_bp.route('/admin/api/products/<int:product_id>', methods=['PATCH'])
def update_product(product_id: int):
    """
    상품 정보 수정
    
    Path Parameters:
        product_id: 상품 ID
    
    Request Body:
        name: 상품명 (선택)
        description: 상품 설명 (선택)
        price: 가격 (선택, 원 단위)
        token_amount: 지급 토큰 수 (선택, 무제한은 -1)
        is_active: 판매 중 여부 (선택)
    """
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    try:
        data = request.get_json()
        
        if not data:
            return error('요청 데이터가 없습니다', status=400)
        
        # Pydantic 모델로 검증
        try:
            product_update = ProductUpdate(**data)
        except ValidationError as e:
            return error(f'입력 데이터 검증 실패: {str(e)}', status=400)
        
        # 상품 수정
        product = product_service.update_product(product_id, product_update)
        
        # Pydantic v1/v2 호환성
        if hasattr(product, 'model_dump'):
            product_dict = product.model_dump()
        else:
            product_dict = product.dict()
        
        return success('상품이 수정되었습니다', data=product_dict)
        
    except ValueError as e:
        logger.warning(f"상품 수정 검증 오류: {str(e)}")
        return error(str(e), status=400)
    except Exception as e:
        logger.error(f"상품 수정 중 오류: {str(e)}")
        return error(f'상품 수정 중 오류가 발생했습니다: {str(e)}', status=500)


@admin_bp.route('/admin/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id: int):
    """
    상품 삭제 (소프트 삭제)
    
    Path Parameters:
        product_id: 상품 ID
    """
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response
    
    try:
        product_service.delete_product(product_id)
        return success('상품이 삭제되었습니다')
        
    except ValueError as e:
        logger.warning(f"상품 삭제 검증 오류: {str(e)}")
        return error(str(e), status=404)
    except Exception as e:
        logger.error(f"상품 삭제 중 오류: {str(e)}")
        return error(f'상품 삭제 중 오류가 발생했습니다: {str(e)}', status=500)

