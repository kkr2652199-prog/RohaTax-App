"""
메인 공급받는자 추출기 모듈

기존 recipient_extractor.py의 핵심 기능을 모듈화된 구조로 재구성합니다.
"""

import re
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import logging
from pathlib import Path

from .field_extractors import FieldExtractors
from .column_mapping import ColumnMapper
from .intelligent_features import IntelligentFeatures
from .normalizers import normalize_colname
from .validation import Validator
from .second_priority_handler import SecondPriorityHandler
from .pipeline import RecipientExtractionPipeline
from .utils import (
    get_synonyms,
    extract_business_number_simple,
    extract_store_name_simple,
    extract_representative_simple,
    extract_address_simple,
    extract_email_simple,
    extract_amount,
    extract_total_amount_simple,
)
from .utils.data_validator import (
    is_valid_business_number,
    is_valid_email,
    is_valid_address,
    is_valid_representative_name,
)
from .utils.sub_guideline_processor import (
    check_and_apply_sub_guideline,
    extract_with_sub_guidelines,
    extract_with_basic_mode,
)
from .utils.config_manager import ConfigManager
from .utils.row_extractor import (
    extract_from_row_intelligent,
    extract_from_row_template_mode,
)
from .utils.sheet_selector import (
    select_optimal_sheet_by_family_rule,
    extract_family_from_sheet_simple,
    extract_numeric_value,
)
from .utils.second_priority_detector import (
    detect_second_priority_sheet,
)

logger = logging.getLogger(__name__)

# 컬럼명 정규화 함수

FORBIDDEN_COLUMN_NAMES = [
    normalize_colname("콜수수료 공급가"),
    normalize_colname("콜수수료부가세"),
]

class RecipientExtractor:
    """업종별 공급받는자 정보 추출기 (지능앱 기술 통합)"""
    
    def __init__(self):
        """공급받는자 추출기 초기화"""
        self.logger = logger
        
        # 설정 관리자 초기화
        self.config_manager = ConfigManager(self.logger)
        
        # 모듈화된 구성요소들
        self.field_extractors = FieldExtractors()
        self.column_mapper = ColumnMapper()
        self.intelligent_features = IntelligentFeatures()
        self.validator = Validator()
        self.second_priority_handler = SecondPriorityHandler()
        self.pipeline = RecipientExtractionPipeline(self)
        self.normalize_colname = normalize_colname
    
    @property
    def current_industry(self):
        """현재 업종 반환"""
        return self.config_manager.current_industry
    
    @property
    def current_guideline(self):
        """현재 지침 반환"""
        return self.config_manager.current_guideline
    
    @property
    def store_keywords(self):
        """현재 상호 키워드 반환"""
        return self.config_manager.store_keywords
    
    def set_industry_guideline(self, industry: str, guideline: Dict[str, Any] = None) -> None:
        """업종별 지침 설정 (설정 파일 기반)"""
        self.config_manager.set_industry_guideline(industry, guideline)
    
    def get_current_guideline(self) -> Dict[str, Any]:
        """현재 적용된 지침 반환 (설정 파일 기반)"""
        return self.config_manager.get_current_guideline()
    
    def is_guideline_ready(self) -> bool:
        """현재 지침이 사용 준비되었는지 확인"""
        return self.config_manager.is_guideline_ready()
    
    def extract_recipients_simple(
        self, parsed_data: Dict[str, Any], industry: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Delegate simple recipient extraction to the pipeline."""
        return self.pipeline.extract_recipients_simple(parsed_data, industry)

    def extract_recipients(
        self, parsed_data: Dict[str, Any], industry: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Delegate full recipient extraction to the pipeline."""
        return self.pipeline.extract_recipients(parsed_data, industry)

    def _extract_from_row_intelligent(self, row: pd.Series, row_index: int, intelligent_mapping: Dict[str, int]) -> Optional[Dict[str, Any]]:
        """지능앱 기술을 활용한 단일 행에서 공급받는자 정보 추출 (외부 모듈 위임)"""
        return extract_from_row_intelligent(
            row, row_index, intelligent_mapping,
            self.field_extractors, self.store_keywords, self.logger
        )
    
    def _extract_from_row_template_mode(self, row: pd.Series, index: int, mapping: Dict[str, str] = None) -> Dict[str, Any]:
        """템플릿 모드 추출: 서브지침 적용 (외부 모듈 위임)"""
        return extract_from_row_template_mode(
            row, index, self.field_extractors, self.config_manager,
            self.current_industry, self.logger, mapping
        )
    
    def _check_and_apply_sub_guideline(self, industry: str, parsed_data: Dict[str, Any]) -> bool:
        """서브지침 활성화 조건 확인 (외부 모듈 위임)"""
        return check_and_apply_sub_guideline(industry, parsed_data, self.logger)
    
    def _extract_with_sub_guidelines(self, df: pd.DataFrame, column_mapping: Dict, column_names: List[str]) -> List[Dict]:
        """서브지침 기반 고급 추출 (외부 모듈 위임)"""
        return extract_with_sub_guidelines(df, column_mapping, column_names, self.column_mapper, self.logger)
    
    def _extract_with_basic_mode(self, df: pd.DataFrame, column_mapping: Dict, column_names: List[str]) -> List[Dict]:
        """기본 모드 추출 (외부 모듈 위임)"""
        return extract_with_basic_mode(df, column_mapping, column_names)
    
    def get_extraction_summary(self, recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """추출 결과 요약"""
        return self.validator.get_extraction_summary(recipients)
    
    def _select_optimal_sheet_by_family_rule(self, parsed_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """시트 우선순위 선택 로직 (외부 모듈 위임)"""
        return select_optimal_sheet_by_family_rule(parsed_data, self.logger)
    
    def _extract_family_from_sheet_simple(self, sheet_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """시트에서 가족 정보 추출 (외부 모듈 위임)"""
        return extract_family_from_sheet_simple(sheet_info, self.logger)
    
    def _extract_numeric_value(self, cell_value) -> float:
        """셀 값에서 숫자 추출 (외부 모듈 위임)"""
        return extract_numeric_value(cell_value)
    
    def _detect_second_priority_sheet(self, recipients: List[Dict[str, Any]]) -> bool:
        """2순위 시트 감지 로직 (외부 모듈 위임)"""
        return detect_second_priority_sheet(recipients, self.logger)

    def _enhance_first_priority_with_second_priority_logic(self, first_priority_recipients: List[Dict[str, Any]], 
                                                          df, column_mapping: Dict, column_names: List[str]) -> List[Dict[str, Any]]:
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
            
        Returns:
            List[Dict[str, Any]]: 강화된 공급받는자 리스트
        """
        try:
            self.logger.info("🎯 특별대우: 1순위 결과를 2순위 방식으로 재처리 시작 (5형제 우선 검열)")
            
            enhanced_recipients = []
            column_names = [str(col).strip() for col in df.columns]
            
            for recipient in first_priority_recipients:
                # 1순위 결과를 기반으로 2순위 검열 방식 적용
                enhanced_recipient = recipient.copy()
                
                # 사업자등록번호가 없는 경우 2순위 방식으로 재추출
                if not enhanced_recipient.get('사업자등록번호') or enhanced_recipient.get('사업자등록번호').strip() == '':
                    self.logger.info("🔍 5형제 중 사업자등록번호 누락 - 2순위 방식으로 재추출")
                    
                    # 2순위 방식으로 사업자등록번호 추출
                    from .field_extractors import FieldExtractors
                    field_extractors = FieldExtractors()
                    
                    # 🔍 디버깅: 실제 컬럼명 확인
                    self.logger.info(f"🔍 원본 데이터 컬럼명: {list(df.columns)}")
                    self.logger.info(f"🔍 찾을 상호명: '{enhanced_recipient.get('상호')}'")
                    
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
                                        self.logger.info(f"✅ 특별대우 사업자등록번호 추출: '{business_number_raw}' → '{business_number}'")
                                        found_match = True
                                        break  # ← 무한 루프 방지
                    
                    if not found_match:
                        self.logger.warning(f"⚠️ 사업자등록번호 재추출 실패: 상호명 '{enhanced_recipient.get('상호')}' 매칭 실패")
                
                # 이메일이 없는 경우 2순위 방식으로 재추출
                if not enhanced_recipient.get('사업자이메일') or enhanced_recipient.get('사업자이메일').strip() == '':
                    self.logger.info("🔍 5형제 중 사업자이메일 누락 - 2순위 방식으로 재추출")
                    
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
                                            self.logger.info(f"✅ 특별대우 이메일 추출: '{email_raw}' → '{email}'")
                                            found_match = True
                                            break  # ← 무한 루프 방지
                    
                    if not found_match:
                        self.logger.warning(f"⚠️ 이메일 재추출 실패: 상호명 '{enhanced_recipient.get('상호')}' 매칭 실패")
                
                # 주소가 없는 경우 2순위 방식으로 재추출
                if not enhanced_recipient.get('사업장주소') or enhanced_recipient.get('사업장주소').strip() == '':
                    self.logger.info("🔍 5형제 중 사업장주소 누락 - 2순위 방식으로 재추출")
                    
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
                                            self.logger.info(f"✅ 특별대우 주소 추출: '{address_raw}' → '{address}'")
                                            found_match = True
                                            break  # ← 무한 루프 방지
                    
                    if not found_match:
                        self.logger.warning(f"⚠️ 주소 재추출 실패: 상호명 '{enhanced_recipient.get('상호')}' 매칭 실패")
                
                # 대표자명이 없는 경우 2순위 방식으로 재추출
                if not enhanced_recipient.get('대표명') or enhanced_recipient.get('대표명').strip() == '':
                    self.logger.info("🔍 5형제 중 대표명 누락 - 2순위 방식으로 재추출")
                    
                    # 원본 데이터에서 해당 행 찾기
                    found_match = False
                    for idx, row in df.iterrows():
                        if enhanced_recipient.get('상호') and str(row.get('가맹점', '')).strip():
                            if enhanced_recipient['상호'] in str(row.get('가맹점', '')):
                                # 2순위 방식으로 대표자명 추출 (우선순위 키워드 활용)
                                representative_candidate = extract_representative_simple(row, column_names)
                                if representative_candidate and is_valid_representative_name(representative_candidate):
                                    enhanced_recipient['대표명'] = representative_candidate
                                    self.logger.info(
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
                                            self.logger.info(f"✅ 특별대우 대표자명(등록자명 활용) 추출: '{representative_raw}' → '{representative}'")
                                            found_match = True
                                            break  # ← 무한 루프 방지
                    
                    if not found_match:
                        self.logger.warning(f"⚠️ 대표자명 재추출 실패: 상호명 '{enhanced_recipient.get('상호')}' 매칭 실패")
                
                enhanced_recipients.append(enhanced_recipient)
            
            self.logger.info(f"✅ 특별대우 처리 완료: {len(enhanced_recipients)}건 (5형제 우선 검열)")
            return enhanced_recipients
            
        except Exception as e:
            self.logger.error(f"❌ 특별대우 로직 오류: {str(e)}")
            return first_priority_recipients  # 오류 시 원본 반환


# 테스트용 함수
def test_recipient_extractor():
    """RecipientExtractor 테스트"""
    extractor = RecipientExtractor()
    
    # 테스트 데이터
    test_data = {
        'recipients': [
            {'사업자등록번호': '1234567890', '상호': '테스트상호1', '대표명': '테스트대표1'},
            {'사업자등록번호': '0987654321', '상호': '테스트상호2', '대표명': '테스트대표2'}
        ]
    }
    
    recipients = test_data['recipients']
    
    print("추출된 공급받는자 정보:")
    for i, recipient in enumerate(recipients, 1):
        print(f"{i}. {recipient}")
    
    # 추출 결과 요약
    summary = extractor.get_extraction_summary(recipients)
    print(f"\n추출 결과 요약: {summary}")

if __name__ == "__main__":
    test_recipient_extractor()
