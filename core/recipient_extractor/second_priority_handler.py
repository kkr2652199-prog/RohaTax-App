"""
2순위 시트 전용 처리 모듈
- 5개 필수 컬럼 매칭 실패 시 완전 중단 문제 해결
- 사업자등록번호와 이메일 컬럼 혼동 문제 해결
- 2순위 시트 감지 로직 강화
- 지침 파일과 코드 연동

사업자등록번호와 이메일 명확한 분리 기준:
- 사업자등록번호: 국세청 발급, 10자리 숫자만, @ 문자 포함 시 이메일로 분류
- 이메일: @ 문자 필수, 사용자명@도메인 형식

2순위 시트 처리 시 이메일 데이터 삭제 규칙:
- 사업자등록번호 컬럼에서 @ 문자가 포함된 데이터 발견 시 해당 행의 사업자등록번호 필드 삭제
- 삭제 후 남은 데이터 중 10자리 숫자 형식만 사업자등록번호로 인식
- 삭제된 이메일 데이터는 별도 이메일 컬럼으로 재분류
"""

import logging
from typing import Dict, List, Any
import pandas as pd

from .utils.sheet_detector import detect_second_priority_sheet
from .utils.config_loader import load_keywords, load_config
from .utils.column_scorer import remap_headers_for_second_priority as remap_headers_external
from .utils.extractor import extract_recipients_from_second_priority as extract_recipients_external

logger = logging.getLogger(__name__)

class SecondPriorityHandler:
    """2순위 시트 전용 처리기"""
    
    def __init__(self):
        self.logger = logger
        
        # 설정값 로드
        config = load_config()
        self.required_columns = config['required_columns']
        self.amount_columns = config['amount_columns']
        
        # 키워드 리스트 로드
        keywords = load_keywords()
        self.store_keywords = keywords['store']
        self.korean_cities = keywords['korean_cities']
        self.email_domains = keywords['email_domains']
        self.korean_surnames = keywords['korean_surnames']
        self.foreign_names = keywords['foreign_names']
        
    def is_second_priority_sheet(self, df: pd.DataFrame, column_names: List[str]) -> bool:
        """2순위 시트 감지 로직 (외부 모듈 호출)"""
        return detect_second_priority_sheet(df, column_names)
    
    def remap_headers_for_second_priority(self, df: pd.DataFrame, column_names: List[str]) -> Dict[str, int]:
        """2순위 시트 전용 헤더 재매핑 (외부 모듈 호출)"""
        return remap_headers_external(df, column_names, self.required_columns)
    
    def extract_recipients_from_second_priority(self, df: pd.DataFrame, column_mapping: Dict[str, int], column_names: List[str]) -> List[Dict[str, Any]]:
        """2순위 시트에서 공급받는자 정보 추출 (외부 모듈 호출)"""
        return extract_recipients_external(df, column_mapping, column_names)
