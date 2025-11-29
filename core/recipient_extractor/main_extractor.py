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
from .utils.enhancement_handler import (
    enhance_first_priority_with_second_priority_logic,
)

logger = logging.getLogger(__name__)
# 제트엔진 모드: 로그 레벨 최적화 (WARNING 이상만 출력)
logger.setLevel(logging.WARNING)

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
        """특별대우 로직: 1순위 결과를 2순위 검열 방식으로 재처리 (외부 모듈 위임)"""
        return enhance_first_priority_with_second_priority_logic(
            first_priority_recipients, df, column_mapping, column_names, self.logger
        )


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
