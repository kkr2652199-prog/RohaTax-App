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
        """지능앱 기술을 활용한 단일 행에서 공급받는자 정보 추출"""
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
                        business_number = self.field_extractors.extract_business_number(str(row.iloc[col_idx]))
                        if business_number:
                            recipient_info['사업자등록번호'] = business_number
                            recipient_info['confidence'] += 0.3
                
                # 상호명 추출 (지능앱 매핑 활용)
                if 'store_name' in intelligent_mapping:
                    col_idx = intelligent_mapping['store_name']
                    if col_idx < len(row):
                        store_name = self.field_extractors.extract_store_name(str(row.iloc[col_idx]), row, self.store_keywords)
                        if store_name:
                            recipient_info['상호'] = store_name
                            recipient_info['confidence'] += 0.2
            
            # 기존 방식으로도 추출 (백업)
            if not recipient_info['사업자등록번호']:
                business_number = self.field_extractors.extract_business_number(row_text)
                if business_number:
                    recipient_info['사업자등록번호'] = business_number
                    recipient_info['confidence'] += 0.2
            
            if not recipient_info['상호']:
                store_name = self.field_extractors.extract_store_name(row_text, row, self.store_keywords)
                if store_name:
                    recipient_info['상호'] = store_name
                    recipient_info['confidence'] += 0.15
            
            # 대표명 추출
            representative = self.field_extractors.extract_representative(row_text, row)
            if representative:
                recipient_info['대표명'] = representative
                recipient_info['confidence'] += 0.2
            
            # 사업장주소 추출
            address = self.field_extractors.extract_address(row_text, row)
            if address:
                recipient_info['사업장주소'] = address
                recipient_info['confidence'] += 0.2
            
            # 이메일 추출 (지능앱 기술: 자동 수정 및 검증)
            email = self.field_extractors.extract_email(row_text, row)
            if email:
                # 지능앱 기술: 이메일 자동 수정 및 검증
                fixed_email = self.field_extractors.auto_correct_email(email)
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
            self.logger.error(f"지능앱 행 추출 오류 (행 {row_index}): {str(e)}")
            return None
    
    def _extract_from_row_template_mode(self, row: pd.Series, index: int, mapping: Dict[str, str] = None) -> Dict[str, Any]:
        """템플릿 모드 추출: 서브지침 적용"""
        try:
            # 컬럼명들
            column_names = [str(col) for col in row.index]
            
            # 서브지침 설정에서 특별 매핑 정보 가져오기
            sub_guidelines = self.config_manager.get_sub_guidelines(self.current_industry)
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
                    amount = self.field_extractors.extract_amount(row[col_name])
                    if amount > 0:
                        recipient_info['공급가액'] = amount
                        self.logger.debug(f"🎯 템플릿 공급가액 발견: {col_name} = {amount}")
                
                # 2. 부가세 (홈텍스 표준 용어)
                vat_patterns = [r"세액.*합계", r"세액1", r"세액2", r"세액3", r"세액4", r"세액 합계"]
                if any(re.search(pattern, col_lower) for pattern in vat_patterns):
                    amount = self.field_extractors.extract_amount(row[col_name])
                    if amount > 0:
                        recipient_info['부가세'] = amount
                        self.logger.debug(f"🎯 템플릿 부가세 발견: {col_name} = {amount}")
                
                # 3. 총금액 (보조용)
                total_patterns = [r"총금액", r"합계금액", r"요금합계", r"공급가액합계"]
                if any(re.search(pattern, col_lower) for pattern in total_patterns):
                    amount = self.field_extractors.extract_amount(row[col_name])
                    if amount > 0:
                        recipient_info['요금합계'] = amount
                        self.logger.debug(f"🎯 템플릿 총금액 발견: {col_name} = {amount}")
            
            # 2. 공급받는자 정보 추출 (일반 모드와 동일하지만 신뢰도 요구사항 낮춤)
            from .utils import extract_business_number_simple, extract_store_name_simple, extract_representative_simple, extract_address_simple, extract_email_simple
            
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
            self.logger.warning(f"템플릿 모드 추출 오류 (행 {index}): {e}")
            return None
    
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
        """
        🎯 지능앱 시트 우선순위 선택 로직 (단순화)
        
        가족 규칙에 따라 최적의 시트를 선택:
        1. 각 시트에서 독립된 단일 셀 값으로 가족(아빠값, 엄마값) 구성
        2. 전체 시트 중 최대 아빠값을 가진 시트를 1순위로 선택
        3. 아빠값이 동일한 경우 시트 순서(작은 번호) 우선
        
        Args:
            parsed_data: 파싱된 데이터 (모든 시트 정보 포함)
            
        Returns:
            선택된 시트 정보 또는 None
        """
        try:
            # 모든 시트 정보 가져오기
            all_sheets = parsed_data.get('all_sheets', {})
            if not all_sheets:
                self.logger.warning("시트 우선순위 선택: 모든 시트 정보가 없습니다")
                return None
            
            self.logger.info(f"🎯 시트 우선순위 선택 시작: {len(all_sheets)}개 시트 검토")
            
            sheet_candidates = []
            
            # 각 시트별로 가족 검증 및 아빠값 추출
            for sheet_name, sheet_info in all_sheets.items():
                try:
                    self.logger.info(f"🔍 시트 '{sheet_name}' 검토 중...")
                    
                    # 시트에서 가족 정보 추출 (단순화된 로직)
                    family_info = self._extract_family_from_sheet_simple(sheet_info)
                    
                    if family_info and family_info.get('dad_value', 0) > 0:
                        sheet_candidates.append({
                            'sheet_name': sheet_name,
                            'dad_value': family_info['dad_value'],
                            'mom_value': family_info.get('mom_value', 0),
                            'family_info': family_info
                        })
                        
                        self.logger.info(f"✅ 시트 '{sheet_name}' 가족 발견: 아빠값={family_info['dad_value']:,.0f}원, 엄마값={family_info.get('mom_value', 0):,.0f}원")
                    else:
                        self.logger.info(f"❌ 시트 '{sheet_name}' 가족 없음")
                        
                except Exception as e:
                    self.logger.warning(f"시트 '{sheet_name}' 검토 중 오류: {str(e)}")
                    continue
            
            if not sheet_candidates:
                self.logger.warning("🎯 시트 우선순위 선택: 가족을 찾은 시트가 없습니다")
                return None
            
            # 최대 아빠값을 가진 시트 선택 (결정적 정렬)
            sheet_candidates.sort(key=lambda x: (x['dad_value'], x.get('sheet_name', '')), reverse=True)
            best_sheet = sheet_candidates[0]
            
            self.logger.info(f"🎯 최적 시트 선택: '{best_sheet['sheet_name']}' (아빠값: {best_sheet['dad_value']:,.0f}원, 엄마값: {best_sheet['mom_value']:,.0f}원)")
            
            # DataFrame 생성하여 반환
            try:
                # 선택된 시트의 데이터로 DataFrame 생성
                selected_sheet_name = best_sheet['sheet_name']
                sheet_info = all_sheets[selected_sheet_name]
                
                # 헤더와 데이터 추출
                headers = sheet_info.get('headers', [])
                data = sheet_info.get('data', [])
                
                # DataFrame 체크: data가 DataFrame인 경우 처리
                if isinstance(data, pd.DataFrame):
                    data = data.values.tolist()
                
                if headers and len(headers) > 0 and (isinstance(data, list) and len(data) > 0):
                    # 첫 번째 행을 헤더로 사용
                    header_row = headers[0] if headers else []
                    # DataFrame 생성
                    df = pd.DataFrame(data, columns=header_row)
                    
                    # 반환 딕셔너리에 dataframe 추가
                    best_sheet['dataframe'] = df
                    self.logger.info(f"🎯 DataFrame 생성 완료: '{selected_sheet_name}' ({len(df)}행, {len(df.columns)}열)")
                else:
                    self.logger.warning(f"시트 '{selected_sheet_name}' 데이터가 없어 DataFrame 생성 실패")
                    return None
                    
            except Exception as e:
                self.logger.error(f"DataFrame 생성 오류: {str(e)}")
                return None
            
            return best_sheet
            
        except Exception as e:
            self.logger.error(f"시트 우선순위 선택 오류: {str(e)}")
            return None
    
    def _extract_family_from_sheet_simple(self, sheet_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        시트에서 가족 정보 추출 (단순화된 로직)
        
        Args:
            sheet_info: 시트 정보 (file_parser에서 수집한 데이터)
            
        Returns:
            가족 정보 또는 None
        """
        try:
            # 시트 데이터에서 헤더와 데이터 추출
            headers = sheet_info.get('headers', [])
            data = sheet_info.get('data', [])
            
            # DataFrame 체크: data가 DataFrame인 경우 처리
            if isinstance(data, pd.DataFrame):
                data = data.values.tolist()
            
            if not headers or (isinstance(data, list) and len(data) == 0):
                return None
            
            # 첫 번째 행을 헤더로 사용
            header_row = headers[0] if headers else []
            
            # 아빠값(공급가액)과 엄마값(부가세) 컬럼 찾기
            dad_col = None
            mom_col = None
            
            for i, header in enumerate(header_row):
                header_lower = str(header).lower().strip()
                
                # 아빠값 컬럼 찾기 (공급가액 관련)
                if any(keyword in header_lower for keyword in ['공급가액', '총금액', '합계', '배달요금', '총배달']):
                    if '부가세' not in header_lower:  # 부가세가 포함된 컬럼은 제외
                        dad_col = i
                        self.logger.debug(f"아빠값 컬럼 발견: {header} (컬럼 {i})")
                
                # 엄마값 컬럼 찾기 (부가세 관련)
                elif any(keyword in header_lower for keyword in ['부가세', '세액', 'vat']):
                    if '합계' not in header_lower:  # 합계는 제외
                        mom_col = i
                        self.logger.debug(f"엄마값 컬럼 발견: {header} (컬럼 {i})")
            
            if dad_col is None or mom_col is None:
                self.logger.debug(f"가족 구성 실패: 아빠값 컬럼={dad_col}, 엄마값 컬럼={mom_col}")
                return None
            
            # 각 행에서 최대 아빠값 찾기
            max_dad_value = 0
            max_mom_value = 0
            
            for row_data in data:
                if len(row_data) > max(dad_col, mom_col):
                    try:
                        dad_value = self._extract_numeric_value(row_data[dad_col])
                        mom_value = self._extract_numeric_value(row_data[mom_col])
                        
                        # 가족 검증: 둘 다 양수여야 함
                        if dad_value > 0 and mom_value > 0:
                            if dad_value > max_dad_value:
                                max_dad_value = dad_value
                                max_mom_value = mom_value
                                
                                # 10% 관계 검증
                                ratio = mom_value / dad_value if dad_value > 0 else 0
                                if 0.095 <= ratio <= 0.105:  # 9.5% ~ 10.5% 범위
                                    self.logger.debug(f"완벽한 가족 발견: 아빠={dad_value}, 엄마={mom_value}, 비율={ratio:.3f}")
                                
                    except Exception as e:
                        self.logger.debug(f"행 처리 오류: {e}")
                        continue
            
            if max_dad_value > 0:
                return {
                    'dad_value': max_dad_value,
                    'mom_value': max_mom_value,
                    'dad_col': dad_col,
                    'mom_col': mom_col
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"가족 정보 추출 오류: {e}")
            return None
    
    def _extract_numeric_value(self, cell_value) -> float:
        """셀 값에서 숫자 추출"""
        try:
            if pd.isna(cell_value):
                return 0.0
            
            # 문자열인 경우 숫자만 추출
            if isinstance(cell_value, str):
                # 천단위 구분자 제거
                cleaned = cell_value.replace(',', '').replace('원', '').replace('￦', '').replace('₩', '')
                # 괄호로 둘러싸인 음수 처리
                if cleaned.startswith('(') and cleaned.endswith(')'):
                    cleaned = '-' + cleaned[1:-1]
                # 숫자만 추출
                import re
                numbers = re.findall(r'-?\d+\.?\d*', cleaned)
                if numbers:
                    return float(numbers[0])
                return 0.0
            
            # 숫자 타입인 경우
            return float(cell_value)
            
        except Exception:
            return 0.0
    
    def _detect_second_priority_sheet(self, recipients: List[Dict[str, Any]]) -> bool:
        """
        🎯 2순위 시트 감지: 분산된 가족이 있는지 확인
        
        분산된 가족 통합 예외 지침 적용 조건:
        - 같은 사업자번호의 여러 행이 있는지 확인
        - 상호나 대표자명이 다른 경우가 있는지 확인
        
        Args:
            recipients: 추출된 공급받는자 리스트
            
        Returns:
            bool: 2순위 시트 여부 (분산된 가족이 있으면 True)
        """
        if not recipients:
            return False
        
        # 사업자번호별로 그룹화
        business_groups = {}
        for recipient in recipients:
            business_num = recipient.get('사업자등록번호', '')
            if business_num and business_num != '':
                if business_num not in business_groups:
                    business_groups[business_num] = []
                business_groups[business_num].append(recipient)
        
        # 분산된 가족이 있는지 확인
        for business_num, group in business_groups.items():
            if len(group) > 1:
                # 같은 사업자번호의 여러 행이 있음
                # 상호나 대표자명이 다른지 확인
                store_names = [r.get('상호', '') for r in group if r.get('상호', '')]
                representative_names = [r.get('대표명', '') for r in group if r.get('대표명', '')]
                
                # 상호나 대표자명이 다른 경우가 있으면 분산된 가족
                if len(set(store_names)) > 1 or len(set(representative_names)) > 1:
                    self.logger.info(f"🎯 2순위 시트 감지: 사업자번호 {business_num} - 분산된 가족 {len(group)}건")
                    return True
        
        return False

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
