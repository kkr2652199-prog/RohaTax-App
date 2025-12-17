"""
행 단위 추출 로직 모듈

main_extractor.py에서 행 단위 추출 관련 메서드를 분리한 독립 모듈입니다.
"""

import re
import pandas as pd
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


def extract_from_row_intelligent(
    row: pd.Series,
    row_index: int,
    intelligent_mapping: Dict[str, int],
    field_extractors,
    store_keywords: List[str],
    logger_instance: logging.Logger = None
) -> Optional[Dict[str, Any]]:
    """지능앱 기술을 활용한 단일 행에서 공급받는자 정보 추출"""
    log = logger_instance or logger
    
    try:
        # 행의 모든 텍스트 수집
        row_text = ' '.join([str(cell) for cell in row.values if pd.notna(cell)])
        
        recipient_info = {
            '사업자등록번호': '',
            '상호': '',
            '대표명': '',
            '사업장주소': '',
            '사업자이메일': '',
            'confidence': 0.0,
            'source_row': row_index
        }
        
        # 지능앱 기술: 키워드 매핐을 활용한 정확한 컬럼 추출
        if intelligent_mapping:
            # 사업자등록번호 추출 (지능앱 매핑 활용)
            if 'recipient_business_number' in intelligent_mapping:
                col_idx = intelligent_mapping['recipient_business_number']
                if col_idx < len(row):
                    business_number = field_extractors.extract_business_number(str(row.iloc[col_idx]))
                    if business_number:
                        recipient_info['사업자등록번호'] = business_number
                        recipient_info['confidence'] += 0.3
            
            # 상호명 추출 (지능앱 매핑 활용)
            if 'store_name' in intelligent_mapping:
                col_idx = intelligent_mapping['store_name']
                if col_idx < len(row):
                    store_name = field_extractors.extract_store_name(str(row.iloc[col_idx]), row, store_keywords)
                    if store_name:
                        recipient_info['상호'] = store_name
                        recipient_info['confidence'] += 0.2
        
        # 기존 방식으로도 추출 (백업)
        if not recipient_info['사업자등록번호']:
            business_number = field_extractors.extract_business_number(row_text)
            if business_number:
                recipient_info['사업자등록번호'] = business_number
                recipient_info['confidence'] += 0.2
        
        if not recipient_info['상호']:
            store_name = field_extractors.extract_store_name(row_text, row, store_keywords)
            if store_name:
                recipient_info['상호'] = store_name
                recipient_info['confidence'] += 0.15
        
        # 대표명 추출
        representative = field_extractors.extract_representative(row_text, row)
        if representative:
            recipient_info['대표명'] = representative
            recipient_info['confidence'] += 0.2
        
        # 사업장주소 추출
        address = field_extractors.extract_address(row_text, row)
        if address:
            recipient_info['사업장주소'] = address
            recipient_info['confidence'] += 0.2
        
        # 이메일 추출 (지능앱 기술: 자동 수정 및 검증)
        email = field_extractors.extract_email(row_text, row)
        if email:
            # 지능앱 기술: 이메일 자동 수정 및 검증
            fixed_email = field_extractors.auto_correct_email(email)
            if fixed_email:
                recipient_info['사업자이메일'] = fixed_email
                recipient_info['confidence'] += 0.15
            else:
                recipient_info['사업자이메일'] = email
                recipient_info['confidence'] += 0.1
        
        # 최소 정보가 있는지 확인
        if recipient_info['사업자등록번호'] or recipient_info['상호'] or recipient_info['대표명']:
            return recipient_info
        
        return None
        
    except Exception as e:
        log.error(f"지능앱 행 추출 오류 (행 {row_index}): {str(e)}")
        return None


def extract_from_row_template_mode(
    row: pd.Series,
    index: int,
    field_extractors,
    config_manager,
    current_industry: str,
    logger_instance: logging.Logger = None,
    mapping: Dict[str, str] = None
) -> Dict[str, Any]:
    """템플릿 모드 추출: 서브지침 적용"""
    log = logger_instance or logger
    
    try:
        # 컬럼명들
        column_names = [str(col) for col in row.index]
        
        # 서브지침 설정에서 특별 매핑 정보 가져오기
        sub_guidelines = config_manager.get_sub_guidelines(current_industry)
        template_rule = sub_guidelines.get('delivery_template', {})
        
        # 템플릿용 컬럼 매핑 우선 적용
        recipient_info = {}
        
        # 1. 공급가액/부가세 컬럼 추출 (템플릿용 키워드 강화)
        amount_keywords = template_rule.get('amount_keywords', {})
        supply_keywords = amount_keywords.get('supply_amount', [])
        vat_keywords = amount_keywords.get('vat_amount', [])
        
        # 홈텍스 템플릿 컬럼 매핑 (정확한 키워드 우선)
        for col_name in column_names:
            col_lower = col_name.lower().replace('\n', ' ').strip()
            
            # 1. 공급가액 (홈텍스 표준 용어)
            regex_patterns = [
                r"공급가액.*합계", r"공급가액1", r"공급가액2", r"공급가액3", r"공급가액4",
                r"공급가액 합계", r"공급가액합계"
            ]
            if any(re.search(pattern, col_lower) for pattern in regex_patterns):
                amount = field_extractors.extract_amount(row[col_name])
                if amount > 0:
                    recipient_info['공급가액'] = amount
                    log.debug(f"🎯 템플릿 공급가액 발견: {col_name} = {amount}")
            
            # 2. 부가세 (홈텍스 표준 용어)
            vat_patterns = [r"세액.*합계", r"세액1", r"세액2", r"세액3", r"세액4", r"세액 합계"]
            if any(re.search(pattern, col_lower) for pattern in vat_patterns):
                amount = field_extractors.extract_amount(row[col_name])
                if amount > 0:
                    recipient_info['부가세'] = amount
                    log.debug(f"🎯 템플릿 부가세 발견: {col_name} = {amount}")
            
            # 3. 총금액 (보조용)
            total_patterns = [r"총금액", r"합계금액", r"요금합계", r"공급가액합계"]
            if any(re.search(pattern, col_lower) for pattern in total_patterns):
                amount = field_extractors.extract_amount(row[col_name])
                if amount > 0:
                    recipient_info['요금합계'] = amount
                    log.debug(f"🎯 템플릿 총금액 발견: {col_name} = {amount}")
        
        # 2. 공급받는자 정보 추출 (일반 모드와 동일하지만 신뢰도 요구사항 낮춤)
        from .legacy_utils import extract_business_number_simple, extract_store_name_simple, extract_representative_simple, extract_address_simple, extract_email_simple
        
        business_number = extract_business_number_simple(row, column_names)
        store_name = extract_store_name_simple(row, column_names)
        representative = extract_representative_simple(row, column_names)
        address = extract_address_simple(row, column_names)
        email = extract_email_simple(row, column_names)
        
        # 3. 기본 정보 설정
        recipient_info.update({
            '사업자등록번호': business_number,
            '상호': store_name,
            '대표명': representative,
            '사업장주소': address,
            '사업자이메일': email,
            '산업유형': 'business',
            '거래유형': 'goods',
            'confidence': 0.6,  # 템플릿 모드는 기본 신뢰도 낮춤
            'source_row': index,
            'extraction_method': 'template_mode'
        })
        
        return recipient_info
        
    except Exception as e:
        log.warning(f"템플릿 모드 추출 오류 (행 {index}): {e}")
        return None

