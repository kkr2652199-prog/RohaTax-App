"""
특별대우 로직 모듈

main_extractor.py의 특별대우 로직을 독립 모듈로 분리
"""

import pandas as pd
from typing import Dict, List, Any
import logging

from ..field_extractors import FieldExtractors
from .data_validator import (
    is_valid_business_number,
    is_valid_email,
    is_valid_address,
    is_valid_representative_name,
)
from .legacy_utils import extract_representative_simple

logger = logging.getLogger(__name__)


def enhance_first_priority_with_second_priority_logic(
    first_priority_recipients: List[Dict[str, Any]],
    df: pd.DataFrame,
    column_mapping: Dict,
    column_names: List[str],
    logger_instance: logging.Logger = None
) -> List[Dict[str, Any]]:
    """
    🎯 특별대우 로직: 1순위 결과를 2순위 검열 방식으로 재처리
    
    1순위 지침을 우선하면서 2순위 검열 방식의 장점을 통합:
    - 사업자등록번호 추출 강화
    - 배달대행사 절대지침 검증 적용
    - 오류 없이 1순위 지침 우선 적용
    
    Args:
        first_priority_recipients: 1순위에서 추출된 공급받는자 리스트
        df: 원본 데이터프레임
        column_mapping: 2순위용 컬럼 매핑
        column_names: 컬럼명 리스트
        logger_instance: 로거 인스턴스 (선택사항)
        
    Returns:
        List[Dict[str, Any]]: 강화된 공급받는자 리스트
    """
    log = logger_instance or logger
    
    try:
        log.info("🎯 특별대우: 1순위 결과를 2순위 방식으로 재처리 시작 (5형제 우선 검열)")
        
        enhanced_recipients = []
        column_names = [str(col).strip() for col in df.columns]
        
        # FieldExtractors 인스턴스 생성
        field_extractors = FieldExtractors()
        
        for recipient in first_priority_recipients:
            # 1순위 결과를 기반으로 2순위 검열 방식 적용
            enhanced_recipient = recipient.copy()
            
            # 사업자등록번호가 없는 경우 2순위 방식으로 재추출
            if not enhanced_recipient.get('사업자등록번호') or enhanced_recipient.get('사업자등록번호').strip() == '':
                log.info("🔍 5형제 중 사업자등록번호 누락 - 2순위 방식으로 재추출")
                
                # 🔍 디버깅: 실제 컬럼명 확인
                log.info(f"🔍 원본 데이터 컬럼명: {list(df.columns)}")
                log.info(f"🔍 찾을 상호명: '{enhanced_recipient.get('상호')}'")
                
                # 원본 데이터에서 해당 행 찾기
                found_match = False
                for idx, row in df.iterrows():
                    # 상호명으로 매칭하여 해당 행 찾기 (다양한 컬럼명 지원)
                    store_name_in_data = None
                    for col_name in ['상호명', '상호', '가맹점명', '업체명']:
                        if col_name in df.columns:
                            store_name_in_data = str(row.get(col_name, '')).strip()
                            if store_name_in_data and store_name_in_data != 'nan':
                                break
                    
                    if enhanced_recipient.get('상호') and store_name_in_data:
                        # 더 유연한 상호명 매칭 (부분 문자열, 공백 제거, 특수문자 제거)
                        store_name_clean = enhanced_recipient['상호'].replace(')', '').replace('(', '').replace('[', '').replace(']', '').replace(' ', '').strip()
                        data_name_clean = store_name_in_data.replace(')', '').replace('(', '').replace('[', '').replace(']', '').replace(' ', '').strip()
                        
                        # 부분 매칭 또는 정확한 매칭
                        if (store_name_clean in data_name_clean or 
                            data_name_clean in store_name_clean or
                            enhanced_recipient['상호'] in store_name_in_data or 
                            store_name_in_data in enhanced_recipient['상호']):
                            # 2순위 방식으로 사업자등록번호 추출 (다양한 컬럼명 지원)
                            business_number_raw = None
                            for col_name in ['사업자번호', '사업자등록번호', '사업자번호']:
                                if col_name in df.columns:
                                    business_number_raw = str(row.get(col_name, '')).strip()
                                    if business_number_raw and business_number_raw != 'nan':
                                        break
                            
                            if business_number_raw:
                                business_number = field_extractors.extract_business_number(business_number_raw)
                                if business_number and is_valid_business_number(business_number):
                                    enhanced_recipient['사업자등록번호'] = business_number
                                    log.info(f"✅ 특별대우 사업자등록번호 추출: '{business_number_raw}' → '{business_number}'")
                                    found_match = True
                                    break  # ← 무한 루프 방지
                
                if not found_match:
                    log.warning(f"⚠️ 사업자등록번호 재추출 실패: 상호명 '{enhanced_recipient.get('상호')}' 매칭 실패")
            
            # 이메일이 없는 경우 2순위 방식으로 재추출
            if not enhanced_recipient.get('사업자이메일') or enhanced_recipient.get('사업자이메일').strip() == '':
                log.info("🔍 5형제 중 사업자이메일 누락 - 2순위 방식으로 재추출")
                
                # 원본 데이터에서 해당 행 찾기
                found_match = False
                for idx, row in df.iterrows():
                    if enhanced_recipient.get('상호') and str(row.get('가맹점', '')).strip():
                        if enhanced_recipient['상호'] in str(row.get('가맹점', '')):
                            # 2순위 방식으로 이메일 추출
                            email_raw = str(row.get('사업자이메일', '')).strip()
                            if email_raw and email_raw != 'nan':
                                if is_valid_email(email_raw):
                                    email = field_extractors.extract_email(email_raw, row)
                                    if email:
                                        enhanced_recipient['사업자이메일'] = email
                                        log.info(f"✅ 특별대우 이메일 추출: '{email_raw}' → '{email}'")
                                        found_match = True
                                        break  # ← 무한 루프 방지
                
                if not found_match:
                    log.warning(f"⚠️ 이메일 재추출 실패: 상호명 '{enhanced_recipient.get('상호')}' 매칭 실패")
            
            # 주소가 없는 경우 2순위 방식으로 재추출
            if not enhanced_recipient.get('사업장주소') or enhanced_recipient.get('사업장주소').strip() == '':
                log.info("🔍 5형제 중 사업장주소 누락 - 2순위 방식으로 재추출")
                
                # 원본 데이터에서 해당 행 찾기
                found_match = False
                for idx, row in df.iterrows():
                    if enhanced_recipient.get('상호') and str(row.get('가맹점', '')).strip():
                        if enhanced_recipient['상호'] in str(row.get('가맹점', '')):
                            # 2순위 방식으로 주소 추출
                            address_raw = str(row.get('도착지주소', '')).strip()
                            if address_raw and address_raw != 'nan':
                                if is_valid_address(address_raw):
                                    address = field_extractors.extract_address(address_raw, row)
                                    if address:
                                        enhanced_recipient['사업장주소'] = address
                                        log.info(f"✅ 특별대우 주소 추출: '{address_raw}' → '{address}'")
                                        found_match = True
                                        break  # ← 무한 루프 방지
                
                if not found_match:
                    log.warning(f"⚠️ 주소 재추출 실패: 상호명 '{enhanced_recipient.get('상호')}' 매칭 실패")
            
            # 대표자명이 없는 경우 2순위 방식으로 재추출
            if not enhanced_recipient.get('대표명') or enhanced_recipient.get('대표명').strip() == '':
                log.info("🔍 5형제 중 대표명 누락 - 2순위 방식으로 재추출")
                
                # 원본 데이터에서 해당 행 찾기
                found_match = False
                for idx, row in df.iterrows():
                    if enhanced_recipient.get('상호') and str(row.get('가맹점', '')).strip():
                        if enhanced_recipient['상호'] in str(row.get('가맹점', '')):
                            # 2순위 방식으로 대표자명 추출 (우선순위 키워드 활용)
                            representative_candidate = extract_representative_simple(row, column_names)
                            if representative_candidate and is_valid_representative_name(representative_candidate):
                                enhanced_recipient['대표명'] = representative_candidate
                                log.info(
                                    "✅ 특별대우 대표자명 우선순위 추출: '%s'",
                                    representative_candidate,
                                )
                                found_match = True
                                break  # ← 무한 루프 방지

                            # 최후의 수단: 등록자명 컬럼 활용 (유효성 검증 후 적용)
                            representative_raw = str(row.get('등록자명', '')).strip()
                            if representative_raw and representative_raw.lower() not in {'nan', 'none', 'null', ''}:
                                if is_valid_representative_name(representative_raw):
                                    representative = field_extractors.extract_representative(representative_raw, row)
                                    if representative:
                                        enhanced_recipient['대표명'] = representative
                                        log.info(f"✅ 특별대우 대표자명(등록자명 활용) 추출: '{representative_raw}' → '{representative}'")
                                        found_match = True
                                        break  # ← 무한 루프 방지
                
                if not found_match:
                    log.warning(f"⚠️ 대표자명 재추출 실패: 상호명 '{enhanced_recipient.get('상호')}' 매칭 실패")
            
            enhanced_recipients.append(enhanced_recipient)
        
        log.info(f"✅ 특별대우 처리 완료: {len(enhanced_recipients)}건 (5형제 우선 검열)")
        return enhanced_recipients
        
    except Exception as e:
        log.error(f"❌ 특별대우 로직 오류: {str(e)}")
        return first_priority_recipients  # 오류 시 원본 반환

