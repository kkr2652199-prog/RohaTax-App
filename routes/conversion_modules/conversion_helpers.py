"""
변환 관련 헬퍼 함수 모듈
공통으로 사용되는 유틸리티 함수들
"""

import os
import tempfile
import logging
import json
import sqlite3
from datetime import datetime
from flask import request
from core.file_parser import FileParser
from core.responses import error
from core.db import get_conn_optimized as get_conn
from core.subscription_utils import get_user_subscription, is_unlimited_user
from core.token_service import get_token_status_from_activity_log

logger = logging.getLogger(__name__)


def normalize_issue_date(s: str) -> str:
    """
    전자세금일자 문자열을 ISO 형식(YYYY-MM-DD)으로 정규화하는 함수
    
    지원 형식:
    - "251001" (6자리 숫자)
    - "25년10월01일" (한글 포함)
    - "2025-10-01" (ISO 형식)
    
    Args:
        s: 정규화할 날짜 문자열
        
    Returns:
        str: ISO 형식 날짜 문자열 (YYYY-MM-DD), 실패 시 빈 문자열
    """
    try:
        # 251001 형태
        if len(s) == 6 and s.isdigit():
            yy = int(s[0:2])
            mm = int(s[2:4])
            dd = int(s[4:6])
            yyyy = 2000 + yy
            return f"{yyyy:04d}-{mm:02d}-{dd:02d}"
        # 25년10월01일 형태
        if '년' in s and '월' in s and '일' in s:
            yy = int(s.split('년')[0][-2:])
            rest = s.split('년')[1]
            mm = int(rest.split('월')[0])
            dd = int(rest.split('월')[1].split('일')[0])
            yyyy = 2000 + yy
            return f"{yyyy:04d}-{mm:02d}-{dd:02d}"
        # ISO 날짜 시도
        return datetime.fromisoformat(s).date().isoformat()
    except Exception:
        return ''


def validate_and_extract_params(request):
    """
    변환 요청의 파라미터를 추출하고 유효성을 검사하는 함수
    
    Args:
        request: Flask request 객체
        
    Returns:
        tuple: (success: bool, result: dict or error_response)
               - success=True: result는 추출된 파라미터 딕셔너리
               - success=False: result는 에러 응답 객체
    """
    # CSRF 토큰 검증
    csrf_token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
    if not csrf_token:
        return False, error('보안 토큰이 없습니다. 다시 시도해주세요.', status=403)
    
    # Form Data에서 파라미터 추출
    template_id = (request.form.get('template_id') or 'hometax_official').strip()
    issue_date_raw = (request.form.get('issue_date') or '').strip()
    file_name = (request.form.get('file_name') or '').strip()
    industry_type = (request.form.get('industry_type') or 'delivery').strip()
    guidelines_json = request.form.get('guidelines', '{}')
    
    # 업종별 지침 파싱
    try:
        guidelines = json.loads(guidelines_json)
        logger.info(f"활성화된 지침: {guidelines.get('name', 'Unknown')}")
    except:
        guidelines = {}
    
    # 파일 업로드 확인
    if 'file' not in request.files:
        return False, error('배달대행사 정산서 파일을 업로드해주세요', status=400)
    
    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return False, error('파일이 선택되지 않았습니다', status=400)
    
    # 필수 파라미터 검증
    if not issue_date_raw:
        return False, error('전자세금일자를 선택하세요', status=400)
    if not file_name:
        return False, error('파일명을 입력하세요', status=400)
    
    # issue_date 정규화: "25년10월01일" 또는 "251001" 또는 ISO 모두 수용 → ISO(YYYY-MM-DD)
    issue_date = normalize_issue_date(issue_date_raw)
    if not issue_date:
        return False, error('전자세금일자 형식이 올바르지 않습니다', status=400)
    
    # 성공 시 추출된 파라미터 반환
    return True, {
        'template_id': template_id,
        'issue_date': issue_date,
        'issue_date_raw': issue_date_raw,
        'file_name': file_name,
        'industry_type': industry_type,
        'guidelines': guidelines,
        'uploaded_file': uploaded_file,
        'selectedCustomerId': request.form.get('selectedCustomerId', '').strip()
    }


def prepare_supplier_info(user, form_data, user_id):
    """
    공급자 정보를 준비하는 함수
    
    골드 회원의 경우 선택한 고객 정보를 사용하고,
    그 외의 경우 사용자 프로필 정보를 사용합니다.
    
    Args:
        user: 사용자 정보 객체 (DB에서 조회한 user)
        form_data: 검증된 파라미터 딕셔너리
        user_id: 사용자 ID
        
    Returns:
        dict: 공급자 정보 딕셔너리
    """
    selected_customer_id = form_data.get('selectedCustomerId', '').strip()
    supplier = None
    
    # 골드 회원이고 고객을 선택한 경우
    user_plan_type = user['plan_type'] if 'plan_type' in user.keys() else None
    if selected_customer_id and user_plan_type in ['gold', 'gold-vip']:
        logger.info(f"골드 고객 선택됨: customer_id={selected_customer_id}")
        
        with get_conn() as conn:
            customer = conn.execute(
                "SELECT * FROM gold_customers WHERE id = ? AND user_id = ? AND is_deleted = 0",
                (int(selected_customer_id), user_id)
            ).fetchone()
            
            if customer:
                business_kind = customer['business_kind'] if 'business_kind' in customer.keys() else '{}'
                try:
                    business_kind_dict = json.loads(business_kind) if isinstance(business_kind, str) else business_kind
                except:
                    business_kind_dict = {}
                
                supplier = {
                    'supplier_name': customer['company_name'] if 'company_name' in customer.keys() else '',
                    'supplier_business_number': customer['business_number'] if 'business_number' in customer.keys() else '',
                    'supplier_representative': customer['representative_name'] if 'representative_name' in customer.keys() else '',
                    'supplier_email': customer['email'] if 'email' in customer.keys() else '',
                    'supplier_address': customer['address'] if 'address' in customer.keys() else '',
                    'supplier_business_type': business_kind_dict.get('업태', ''),
                    'supplier_business_category': business_kind_dict.get('종목', ''),
                }
                logger.info(f"골드 고객 정보 적용: {supplier['supplier_name']}")
    
    # 골드 고객 미선택 또는 비골드 회원: 기본 프로필 공급자 사용
    if not supplier:
        supplier = {
            'supplier_name': user['company_name'] or user['username'],
            'supplier_business_number': user['business_number'] or '',
            'supplier_representative': user['representative_name'] or '',
            'supplier_email': user['email'] or '',
            'supplier_address': user['address'] or '',
            'supplier_business_type': user['business_type'] if 'business_type' in user.keys() else '',
            'supplier_business_category': user['business_category'] if 'business_category' in user.keys() else '',
        }
        logger.info(f"기본 프로필 공급자 사용: {supplier['supplier_name']}")
    
    return supplier


def check_token_balance(user_id, template_count):
    """
    토큰 잔량을 확인하고 부족 시 에러를 반환하는 함수
    
    무제한 회원(Gold VIP 등)의 경우 토큰 확인을 건너뛰고,
    일반 회원의 경우 activity_logs 기반으로 정확한 토큰 잔량을 계산하여
    템플릿 생성에 필요한 토큰이 충분한지 확인합니다.
    
    Args:
        user_id: 사용자 ID
        template_count: 생성할 템플릿 개수
        
    Returns:
        tuple: (success: bool, error_response or None)
               - success=True: 토큰이 충분하거나 무제한 회원, error_response는 None
               - success=False: 토큰이 부족, error_response는 에러 응답 객체
    """
    # ============================================
    # VIP/GoldVIP 무제한 처리
    # ============================================
    logger.info(f"사용자 플랜 확인 시작: user_id={user_id}")
    subscription_info = get_user_subscription(user_id)
    logger.info(f"구독 정보: {subscription_info}")
    
    is_unlimited = is_unlimited_user(user_id)
    logger.info(f"is_unlimited_user 결과: {is_unlimited}")
    
    if is_unlimited:
        required_tokens = 0  # Gold VIP는 토큰 차감 안함
        logger.info(f"GoldVIP 무제한 사용: 템플릿 {template_count}개 변환")
    else:
        # VIP/Premium VIP/Free 회원: 템플릿 건수만큼 토큰 필요
        required_tokens = template_count
        logger.info(f"템플릿 건수: {template_count}개, 필요 토큰: {required_tokens}개")
    
    # ============================================
    # 토큰 잔량 정밀 확인 (activity_logs 기반)
    # ============================================
    # [중앙은행 함수 사용] activity_logs 기반으로 정확한 토큰 잔량 계산
    token_status = get_token_status_from_activity_log(user_id)
    if not token_status:
        logger.error(f"사용자 ID {user_id}의 토큰 상태를 조회할 수 없음")
        return error('토큰 상태를 확인할 수 없습니다', status=500)
    
    total_tokens = token_status['token_balance']
    used_tokens = token_status['tokens_used']
    available_tokens = token_status['available_tokens']
    
    if not is_unlimited and available_tokens < required_tokens:
        # 부족한 토큰 정확히 계산
        shortage = required_tokens - available_tokens
        missing_tokens = shortage
        
        logger.warning(
            f"토큰 부족 - 템플릿 {template_count}개, 필요 {required_tokens}토큰, "
            f"보유 {available_tokens}토큰, 부족 {shortage}토큰"
        )
        
        return False, error(
            f'토큰이 부족합니다. 템플릿 {template_count}개 생성에 {required_tokens}토큰이 필요하지만, '
            f'현재 {available_tokens}토큰을 보유하고 있어 {shortage}토큰이 부족합니다. '
            f'필요한 토큰({shortage}개 × 200원 = {shortage * 200}원)을 구매한 후 다시 시도해주세요.',
            status=400,
            data={
                'template_count': template_count,
                'required_tokens': required_tokens,
                'available_tokens': available_tokens,
                'shortage': shortage,
                'estimated_cost': shortage * 200  # 1토큰 = 200원
            }
        )
    
    # 토큰 잔량 확인 완료
    logger.info(
        f"토큰 잔량 확인 완료: 필요 {required_tokens}토큰, 보유 {available_tokens}토큰"
    )
    
    return True, None


