"""
서브지침 처리 모듈
홈택스 템플릿 형태 감지 및 서브지침 기반 추출 로직
"""

import pandas as pd
from typing import Dict, List, Any, Optional
import logging

from ..normalizers import normalize_colname
from .legacy_utils import (
    extract_business_number_simple,
    extract_store_name_simple,
    extract_representative_simple,
    extract_address_simple,
    extract_email_simple,
    extract_amount,
)

logger = logging.getLogger(__name__)


def check_and_apply_sub_guideline(industry: str, parsed_data: Dict[str, Any], logger_instance: Optional[logging.Logger] = None) -> bool:
    """서브지침 활성화 조건 확인"""
    log = logger_instance or logger
    try:
        # 홈텍스 구조 감지
        optimal_sheet = parsed_data.get('optimal_sheet', {})
        sheet_name = optimal_sheet.get('sheet_name', '')
        
        # 템플릿 시트명 감지
        template_indicators = ['엑셀업로드양식', '올바른 예시', '잘못된 예시', '항목설명', '데이터입력']
        
        if any(indicator in sheet_name for indicator in template_indicators):
            log.info(f"🏗️ 홈텍스 템플릿 구조 감지: '{sheet_name}' 시트")
            return True
        
        # 컬럼 구조 감지 (Column_ 패턴)
        df = parsed_data.get('raw_data')
        if df is not None:
            column_names = [str(col).strip() for col in df.columns]
            normalized_column_names = [normalize_colname(col) for col in column_names]
            template_columns = [col for col in normalized_column_names if 'column_' in col or '열' == col]
            
            if len(template_columns) > 5:  # 홈텍스 형태의 컬럼 구조
                log.info(f"🏗️ 홈텍스 패턴 구조 감지: {len(template_columns)}개 템플릿 컬럼")
                return True
        
        return False
        
    except Exception as e:
        log.error(f"서브지침 감지 오류: {e}")
        return False


def extract_with_sub_guidelines(
    df: pd.DataFrame,
    column_mapping: Dict,
    column_names: List[str],
    column_mapper,
    logger_instance: Optional[logging.Logger] = None
) -> List[Dict]:
    """서브지침 기반 고급 추출"""
    log = logger_instance or logger
    log.info("🔧 서브지침 시스템: 템플릿 형태 감지로 고급 추출 시작")
    
    # 동적 컬럼 매핑 강화
    supply_amount_col, vat_amount_col = column_mapper.dynamic_column_mapping(df, column_names)
    
    recipients = []
    
    # 템플릿 형태 파일 처리를 위한 강화된 추출
    for idx, row in df.iterrows():
        try:
            # 기본 정보 추출 (공급받는자 통합 지침 적용)
            business_number = extract_business_number_simple(row, column_names)
            store_name = extract_store_name_simple(row, column_names)
            representative = extract_representative_simple(row, column_names)
            address = extract_address_simple(row, column_names)
            email = extract_email_simple(row, column_names)
            
            # 금액 정보 추출
            supply_amount = 0
            vat_amount = 0
            
            if supply_amount_col is not None:
                supply_amount = extract_amount(row.iloc[supply_amount_col])
            if vat_amount_col is not None:
                vat_amount = extract_amount(row.iloc[vat_amount_col])
            
            # 유효한 데이터만 수집
            if business_number or store_name or representative:
                recipient_info = {
                    '사업자등록번호': business_number,
                    '상호': store_name,
                    '대표명': representative,
                    '사업장주소': address,
                    '사업자이메일': email,
                    '공급가액': supply_amount,
                    '부가세': vat_amount,
                    '요금합계': supply_amount + vat_amount,
                    'confidence': 0.9,  # 서브지침 적용 시 높은 신뢰도
                    'source_row': idx + 1,
                    'validation_status': 'sub_guideline_verified'
                }
                recipients.append(recipient_info)
                
        except Exception as e:
            log.error(f"서브지침 추출 오류 (행 {idx+1}): {e}")
            continue
    
    # 🎯 사업자번호 기반 가족 통합 서브지침 적용 (항상 실행)
    if recipients:
        # FileParser의 통합 함수 사용
        from ...file_parser import FileParser
        parser = FileParser()
        merged_recipients = parser._merge_families_by_business_number(recipients)
        
        if len(merged_recipients) < len(recipients):
            log.info(f"🎯 사업자번호 기반 가족 통합 적용: {len(recipients)} → {len(merged_recipients)}건")
            recipients = merged_recipients
        else:
            # 통합은 불필요하지만 보정된 값은 반영해야 함
            recipients = merged_recipients
            log.info(f"🎯 사업자번호 기반 가족 통합 적용: {len(recipients)}건 (통합 불필요, 보정 적용)")
    
    # 통계를 recipients에 추가 (기본 통계 초기화)
    if recipients:
        # 기본 통계 초기화 (서브지침 모드에서는 간단한 통계만)
        basic_stats = {
            'email_auto_fixed_count': 0,
            'business_number_auto_fixed_count': 0,
            'vat_included_count': len([r for r in recipients if r.get('부가세', 0) > 0]),
            'vat_zero_count': len([r for r in recipients if r.get('부가세', 0) <= 0]),
            'perfect_info_count': 0,
            'rows_processed': len(recipients),
            'total_supply_amount': sum(r.get('공급가액', 0) for r in recipients),
            'total_tax_amount': sum(r.get('부가세', 0) for r in recipients)
        }
        recipients[0]['_stats'] = basic_stats
    
    return recipients


def extract_with_basic_mode(df: pd.DataFrame, column_mapping: Dict, column_names: List[str]) -> List[Dict]:
    """기본 모드 추출"""
    return []  # 기본 추출 로직은 하위에서 처리

