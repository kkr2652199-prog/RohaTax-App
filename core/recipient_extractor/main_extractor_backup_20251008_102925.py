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
from .validation import Validator
from .utils import get_synonyms, extract_business_number_simple, extract_store_name_simple, extract_representative_simple, extract_address_simple, extract_email_simple, extract_amount, extract_total_amount_simple
from ..industry_config_loader import industry_config_loader

logger = logging.getLogger(__name__)

# 컬럼명 정규화 함수 추가

def normalize_colname(col):
    return str(col).replace('\n', '').replace(' ', '').replace('\t', '').strip().lower()

FORBIDDEN_COLUMN_NAMES = [normalize_colname("콜수수료 공급가"), normalize_colname("콜수수료부가세")]

class RecipientExtractor:
    """업종별 공급받는자 정보 추출기 (지능앱 기술 통합)"""
    
    def __init__(self):
        """공급받는자 추출기 초기화"""
        self.logger = logger
        self.current_industry = None
        self.current_guideline = None
        
        # 설정 파일 로더 초기화
        self.config_loader = industry_config_loader
        self.logger.info("업종별 설정 파일 로더 초기화 완료")
        
        # 기본 키워드 (배달대행사용)
        self.store_keywords = self._get_store_keywords('delivery')
        
        # 모듈화된 구성요소들
        self.field_extractors = FieldExtractors()
        self.column_mapper = ColumnMapper()
        self.intelligent_features = IntelligentFeatures()
        self.validator = Validator()
    
    def _get_store_keywords(self, industry: str) -> List[str]:
        """설정 파일에서 업종별 상호 키워드를 가져옴"""
        config = self.config_loader.get_industry_config(industry)
        if config and 'store_keywords' in config:
            return config['store_keywords']
        return []
    
    def _get_industry_config(self, industry: str) -> Dict[str, Any]:
        """설정 파일에서 업종별 설정을 가져옴"""
        return self.config_loader.get_industry_config(industry) or {}
    
    def _get_sub_guidelines(self, industry: str) -> Dict[str, Any]:
        """서브 지침 가져오기"""
        main_config = self._get_industry_config(industry)
        return main_config.get('sub_guidelines', {})
    
    def set_industry_guideline(self, industry: str, guideline: Dict[str, Any] = None) -> None:
        """업종별 지침 설정 (설정 파일 기반)"""
        self.current_industry = industry
        
        # 설정 파일에서 업종별 규칙 로드
        config = self._get_industry_config(industry)
        if config:
            self.current_guideline = config
            self.store_keywords = config.get('store_keywords', [])
            self.logger.info(f"업종별 지침 적용: {config.get('name', 'Unknown')}")
        else:
            # 알 수 없는 업종인 경우 배달대행사 기본값 사용
            self.current_industry = 'delivery'
            self.current_guideline = self._get_industry_config('delivery')
            self.store_keywords = self._get_store_keywords('delivery')
            self.logger.warning(f"알 수 없는 업종 '{industry}', 배달대행사 지침으로 대체")
    
    def get_current_guideline(self) -> Dict[str, Any]:
        """현재 적용된 지침 반환 (설정 파일 기반)"""
        return self.current_guideline or self._get_industry_config('delivery')
    
    def is_guideline_ready(self) -> bool:
        """현재 지침이 사용 준비되었는지 확인"""
        if not self._current_guideline:
            return False
        return self.current_guideline.get('status', 'ready') == 'ready'
    
    def extract_recipients_simple(self, parsed_data: Dict[str, Any], industry: str = None) -> List[Dict[str, Any]]:
        """단순한 공급받는자 정보 추출 (지능앱 시트 검열 기술 적용)"""
        if parsed_data['parsing_status'] != 'success':
            self.logger.error("파싱 실패된 데이터로부터 추출 시도")
            return []
        
        # 업종별 지침 설정
        if industry:
            self.set_industry_guideline(industry)
        
        try:
            df = parsed_data['raw_data']
            recipients = []
            
            # 🎯 지능앱 시트 우선순위 선택 로직 적용 (1순위 시트가 이미 선택된 경우 중복 선택 방지)
            sheet_inspection_result = parsed_data.get('sheet_inspection_result', {})
            is_priority_sheet_selected = sheet_inspection_result.get('priority') == '1순위'
            
            if is_priority_sheet_selected:
                self.logger.info(f"🎯 1순위 시트 이미 선택됨: '{parsed_data.get('selected_sheet', 'Unknown')}' - 중복 선택 방지")
                # 이미 선택된 1순위 시트 데이터 사용 (중복 검열 방지)
                df = parsed_data.get('raw_data')
                if df is None:
                    self.logger.warning("1순위 시트 데이터가 없습니다. 기본 시트 선택 로직 실행")
                    sheet_priority_result = self._select_optimal_sheet_by_family_rule(parsed_data)
                    if sheet_priority_result:
                        df = sheet_priority_result['dataframe']
                        parsed_data['raw_data'] = df
                        parsed_data['selected_sheet'] = sheet_priority_result['sheet_name']
                else:
                    self.logger.info(f"✅ 1순위 시트 데이터 사용: '{parsed_data.get('selected_sheet', 'Unknown')}' - 중복 검열 완전 방지")
            else:
                # 1순위 시트가 선택되지 않은 경우에만 시트 선택 로직 실행
                self.logger.info("🔍 1순위 시트 없음 - 시트 선택 로직 실행")
                sheet_priority_result = self._select_optimal_sheet_by_family_rule(parsed_data)
                if sheet_priority_result:
                    self.logger.info(f"🎯 시트 우선순위 선택 완료: '{sheet_priority_result['sheet_name']}' (아빠값: {sheet_priority_result['dad_value']}, 엄마값: {sheet_priority_result['mom_value']})")
                    # 선택된 시트의 데이터로 업데이트
                    df = sheet_priority_result['dataframe']
                    parsed_data['raw_data'] = df
                    parsed_data['selected_sheet'] = sheet_priority_result['sheet_name']
            
            # 지능앱 시트 검열 결과 활용
            sheet_inspection_result = parsed_data.get('sheet_inspection_result')
            selected_sheet = parsed_data.get('selected_sheet', 'Unknown')
            
            if sheet_inspection_result:
                score = sheet_inspection_result.get('score', 0.0)
                matched_fields = sheet_inspection_result.get('matched_fields', 0)
                data_quality = sheet_inspection_result.get('data_quality', 0.0)
                self.logger.info(f"지능앱 시트 검열 결과 활용: '{selected_sheet}' 시트 (점수: {score:.2f})")
                self.logger.info(f"매칭된 필드: {matched_fields}개, 데이터 품질: {data_quality:.2f}")
            
            # 업종별 절대지침: 5가지 컬럼 찾기
            required_columns = ['가맹점명', '대표자명', '주소', '사업자번호', '이메일']
            
            # FileParser에서 이미 헤더를 컬럼명으로 설정했으므로 컬럼명을 직접 사용
            column_names = [str(col).strip() for col in df.columns]
            normalized_column_names = [normalize_colname(col) for col in column_names]
            self.logger.info(f"컬럼명 확인: {column_names}")
            
            # 5가지 컬럼이 있는지 확인
            found_columns = 0
            column_mapping = {}
            
            for required in required_columns:
                for col_idx, col_name in enumerate(normalized_column_names):
                    # 개행문자 제거하여 정확한 비교
                    clean_col_name = str(col_name).replace('\n', ' ').strip()
                    
                    # 🚨 중요한 수정: 홈텍스 템플릿에서는 "공급받는자" 키워드 우선
                    if '공급받는자' in clean_col_name and required in clean_col_name:
                        found_columns += 1
                        column_mapping[required] = col_idx
                        self.logger.info(f"✅ 홈텍스 템플릿 매칭: {required} → {clean_col_name} (컬럼 {col_idx})")
                        break
                    elif required in clean_col_name or any(keyword in clean_col_name for keyword in get_synonyms(required)):
                        # 🔍 디버깅: 매칭 테스트 로그 추가
                        synonyms = get_synonyms(required)
                        matched_keywords = [k for k in synonyms if k in clean_col_name]
                        self.logger.debug(f"매칭 테스트: {required} vs '{clean_col_name}' -> 동의어 매칭: {matched_keywords}")
                        # 공급자 정보는 제외 (공급받는자가 우선)
                        if '공급자' in clean_col_name and required in clean_col_name:
                            continue  # 공급자 정보는 스킵, 공급받는자만 추출
                        found_columns += 1
                        column_mapping[required] = col_idx
                        self.logger.info(f"컬럼 매칭: {required} → {clean_col_name} (컬럼 {col_idx})")
                        break
            
            if found_columns < 5:
                self.logger.error(f"5가지 필수 컬럼을 찾을 수 없습니다. 찾은 컬럼: {found_columns}개")
                self.logger.error(f"찾은 컬럼 매핑: {column_mapping}")
                return []
            
            # 서브지침 시스템 기반 강화 추출
            if self._check_and_apply_sub_guideline(industry, parsed_data):
                self.logger.info("🚀 서브지침 시스템 활성화 - 고급 추출 모드")
                extracted_data = self._extract_with_sub_guidelines(df, column_mapping, column_names)
            else:
                # 기본 추출
                extracted_data = self._extract_with_basic_mode(df, column_mapping, column_names)
            
            # 지능앱 동적 컬럼 매핑: 스코어링 기반 최적 컬럼 선택
            supply_amount_col, vat_amount_col = self.column_mapper.dynamic_column_mapping(df, column_names)
            if vat_amount_col is None:
                self.logger.info("FAMILY_RULE: MOM_NOT_FOUND -> considering AUX_RULE on mapping stage")
            
            if supply_amount_col is None or vat_amount_col is None:
                self.logger.error("지능앱 동적 매핑: 공급가액 또는 부가세 컬럼을 찾을 수 없습니다")
                return []
            
            # 데이터 추출 (모든 행)
            skipped_vat_rows = 0
            for row_idx in range(len(df)):
                row = df.iloc[row_idx]
                
                # 5가지 필수 정보 추출
                business_number = extract_business_number_simple(row, column_names)
                store_name = extract_store_name_simple(row, column_names)
                representative = extract_representative_simple(row, column_names)
                address = extract_address_simple(row, column_names)
                email = extract_email_simple(row, column_names)
                
                # 6번, 7번 컬럼에서 금액 추출
                supply_amount = extract_amount(row.iloc[supply_amount_col])
                vat_amount = extract_amount(row.iloc[vat_amount_col])
                try:
                    supply_header = column_names[supply_amount_col] if 0 <= supply_amount_col < len(column_names) else f"idx{supply_amount_col}"
                    vat_header = column_names[vat_amount_col] if 0 <= vat_amount_col < len(column_names) else f"idx{vat_amount_col}"
                    self.logger.info(f"💾 금액 추출 원천(row {row_idx}): 공급가액[{supply_header}]={supply_amount}, 부가세[{vat_header}]={vat_amount}")
                except Exception:
                    pass

                # 총금액(합계) 추출: 첨파 파일의 총금액이 있으면 그대로 사용, 없으면 공급가액+부가세
                total_amount = extract_total_amount_simple(
                    row=row,
                    column_names=column_names,
                    default_total=supply_amount + vat_amount
                )

                # 부가세 검증
                try:
                    if vat_amount is None or vat_amount <= 0:
                        skipped_vat_rows += 1
                        self.logger.debug(f"FAMILY_RULE_SKIP: row={row_idx} mom_missing_or_zero")
                        continue
                except Exception:
                    skipped_vat_rows += 1
                    continue
                
                # 최소 정보가 있는지 확인
                if business_number or store_name or representative:
                    recipient_info = {
                        '사업자등록번호': business_number,
                        '상호': store_name,
                        '대표명': representative,
                        '사업장주소': address,
                        '사업자이메일': email,
                        '공급가액': supply_amount,
                        '부가세': vat_amount,
                        '요금합계': total_amount,
                        'source_row': row_idx,
                        'industry': self.current_industry,
                        'selected_sheet': selected_sheet  # 지능앱 시트 검열 결과 추가
                    }
                    recipients.append(recipient_info)
            
            # 중복 제거를 선행하면 합산 대상 행이 소실될 수 있으므로,
            # 먼저 통합(합산)부터 수행하고 필요 시 이후 단계에서 정리한다.
            unique_recipients = recipients
            
            # 🎯 사업자번호 기반 가족 통합 서브지침 적용 (항상 실행)
            if unique_recipients:
                # 2순위 시트 감지: 분산된 가족이 있는지 확인
                is_second_priority_sheet = self._detect_second_priority_sheet(unique_recipients)
                
                # FileParser의 통합 함수 사용
                from ..file_parser import FileParser
                parser = FileParser()
                merged_recipients = parser._merge_families_by_business_number(unique_recipients)
                
                if len(merged_recipients) < len(unique_recipients):
                    self.logger.info(f"🎯 사업자번호 기반 가족 통합 적용: {len(unique_recipients)} → {len(merged_recipients)}건")
                    unique_recipients = merged_recipients
                else:
                    # 통합은 불필요하지만 보정된 값은 반영해야 함
                    unique_recipients = merged_recipients
                    if is_second_priority_sheet:
                        self.logger.info(f"🎯 사업자번호 기반 가족 통합 적용: {len(unique_recipients)}건 (2순위 시트, 분산된 가족 통합)")
                    else:
                        self.logger.info(f"🎯 사업자번호 기반 가족 통합 적용: {len(unique_recipients)}건 (통합 불필요, 보정 적용)")
            
            guideline_name = self.get_current_guideline().get('name', '알 수 없는 지침')
            if skipped_vat_rows > 0:
                self.logger.info(f"부가세 누락/0/비숫자 스킵 행: {skipped_vat_rows}건")
            self.logger.info(f"지능앱 추출 완료: {len(unique_recipients)}건 (지침: {guideline_name}, 시트: {selected_sheet})")
            return unique_recipients
            
        except Exception as e:
            self.logger.error(f"지능앱 추출 오류: {str(e)}")
            return []
    
    def extract_recipients(self, parsed_data: Dict[str, Any], industry: str = None) -> List[Dict[str, Any]]:
        """파싱된 데이터에서 공급받는자 정보 추출 (업종별 지침 적용 + 지능앱 기술 통합)"""
        if parsed_data['parsing_status'] != 'success':
            self.logger.error("파싱 실패된 데이터로부터 추출 시도")
            return []
        
        # 업종별 지침 설정 + 서브지침 시스템
        sub_guideline_applied = False
        
        if industry:
            self.set_industry_guideline(industry)
            
            # 템플릿 형태 감지 및 서브지침 적용 (강화 버전)
            template_type = self.intelligent_features.detect_template_type(parsed_data)
            
            # 강제 템플릿 감지 로직 추가
            force_template_detection = False
            if 'optimal_sheet' in parsed_data:
                sheet_name = parsed_data['optimal_sheet']['sheet_name']
                # 홈텍스 구조 시트명 감지
                template_sheet_names = ['엑셀업로드양식', '올바른 예시', '잘못된 예시', '항목설명']
                if any(name in sheet_name for name in template_sheet_names):
                    force_template_detection = True
                    self.logger.info(f"🏗️ 홈텍스 템플릿 구조 감지: '{sheet_name}' 시트")
            
            if template_type == "template_type" or force_template_detection:
                sub_guidelines = self._get_sub_guidelines(industry)
                if 'delivery_template' in sub_guidelines:
                    sub_guideline_applied = True
                    self.logger.info("🔧 서브지침 시스템: 템플릿 형태 감지로 서브지침 적용")
        
        try:
            df = parsed_data['raw_data']
            recipients = []
            
            # ===== 지능앱 기술 통합 적용 + 서브지침 강화 =====
            self.logger.info("지능앱 기술 통합 적용 시작" + (" + 서브지침 강화" if sub_guideline_applied else ""))
            
            # 1. 지능앱 기술: 공급받는자 키워드 매핑 우선순위 적용
            intelligent_mapping = self.intelligent_features.map_recipient_keywords_intelligent(df, self.current_guideline)
            if intelligent_mapping:
                self.logger.info(f"지능앱 키워드 매핑 적용: {intelligent_mapping}")
            
            # 🔍 디버깅: 실제 컬럼명 확인
            column_names = [str(col).strip() for col in df.columns]
            self.logger.info(f"🔍 실제 파일 컬럼명: {column_names[:10]}...")  # 처음 10개만 표시
            
            # 🔍 디버깅: 필수 필드별 매칭 상태 확인
            required_fields = ['사업자등록번호', '상호', '대표자명', '사업장주소', '이메일']
            for field in required_fields:
                synonyms = self.field_extractor.get_synonyms(field)
                matched_cols = []
                for col_name in column_names:
                    if any(synonym in col_name for synonym in synonyms):
                        matched_cols.append(col_name)
                if matched_cols:
                    self.logger.info(f"✅ {field} 매칭 성공: {matched_cols}")
                else:
                    self.logger.warning(f"❌ {field} 매칭 실패 - 동의어: {synonyms[:5]}...")
            
            # 각 행에서 공급받는자 정보 추출 (지능앱 기술 + 서브지침 적용)
            for index, row in df.iterrows():
                if sub_guideline_applied:
                    # 서브지침 적용: 템플릿용 특별 추출 로직
                    recipient_info = self._extract_from_row_template_mode(row, index, intelligent_mapping)
                else:
                    # 일반 지침 적용
                    recipient_info = self._extract_from_row_intelligent(row, index, intelligent_mapping)

                # 사전 필터링을 적용하지 않고 원본 추출을 모두 수집한다.
                if recipient_info:
                    recipient_info['industry'] = self.current_industry
                    recipient_info['guideline_mode'] = "sub" if sub_guideline_applied else "main"
                    recipients.append(recipient_info)
            
            # 중복 제거 (사업자등록번호 기준)
            unique_recipients = self.validator.remove_duplicates(recipients)
            
            # 🎯 사업자번호 기반 가족 통합 서브지침 적용 (항상 실행)
            if unique_recipients:
                self.logger.info(f"🎯 원본 추출 건수(사전필터 없음): {len(unique_recipients)}건")
                # FileParser의 통합 함수 사용
                from ..file_parser import FileParser
                parser = FileParser()
                merged_recipients = parser._merge_families_by_business_number(unique_recipients)

                # 통합 후 금액 기준 최종 필터: 아빠(공급가액)와 엄마(부가세) 모두 존재/양수
                def _money(v):
                    try:
                        return float(v)
                    except Exception:
                        return 0.0

                filtered_after_merge = []
                for r in merged_recipients:
                    supply = _money(r.get('공급가액', r.get('supply_amount', 0)))
                    vat = _money(r.get('부가세', r.get('vat', 0)))
                    if supply > 0 and vat > 0:
                        filtered_after_merge.append(r)

                self.logger.info(f"🎯 가족 통합 결과: {len(merged_recipients)}건 → 최종(공급+부가세 보유) {len(filtered_after_merge)}건")
                unique_recipients = filtered_after_merge
            
            guideline_name = self.get_current_guideline().get('name', '알 수 없는 지침')
            self.logger.info(f"공급받는자 정보 추출 완료: {len(unique_recipients)}건 (지침: {guideline_name}, 지능앱 기술 적용)")
            return unique_recipients
            
        except Exception as e:
            self.logger.error(f"공급받는자 정보 추출 오류: {str(e)}")
            return []
    
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
            sub_guidelines = self._get_sub_guidelines(self.current_industry)
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
            business_number = self.field_extractor.extract_business_number_simple(row, column_names)
            store_name = self.field_extractor.extract_store_name_simple(row, column_names)
            representative = self.field_extractor.extract_representative_simple(row, column_names)
            address = self.field_extractor.extract_address_simple(row, column_names)
            email = self.field_extractor.extract_email_simple(row, column_names)
            
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
        """서브지침 활성화 조건 확인"""
        try:
            # 홈텍스 구조 감지
            optimal_sheet = parsed_data.get('optimal_sheet', {})
            sheet_name = optimal_sheet.get('sheet_name', '')
            
            # 템플릿 시트명 감지
            template_indicators = ['엑셀업로드양식', '올바른 예시', '잘못된 예시', '항목설명', '데이터입력']
            
            if any(indicator in sheet_name for indicator in template_indicators):
                self.logger.info(f"🏗️ 홈텍스 템플릿 구조 감지: '{sheet_name}' 시트")
                return True
            
            # 컬럼 구조 감지 (Column_ 패턴)
            df = parsed_data.get('raw_data')
            if df is not None:
                column_names = [str(col).strip() for col in df.columns]
                normalized_column_names = [normalize_colname(col) for col in column_names]
                template_columns = [col for col in normalized_column_names if 'column_' in col or '열' == col]
                
                if len(template_columns) > 5:  # 홈텍스 형태의 컬럼 구조
                    self.logger.info(f"🏗️ 홈텍스 패턴 구조 감지: {len(template_columns)}개 템플릿 컬럼")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"서브지침 감지 오류: {e}")
            return False
    
    def _extract_with_sub_guidelines(self, df: pd.DataFrame, column_mapping: Dict, column_names: List[str]) -> List[Dict]:
        """서브지침 기반 고급 추출"""
        self.logger.info("🔧 서브지침 시스템: 템플릿 형태 감지로 고급 추출 시작")
        
        # 동적 컬럼 매핑 강화
        supply_amount_col, vat_amount_col = self.column_mapper.dynamic_column_mapping(df, column_names)
        
        recipients = []
        
        # 템플릿 형태 파일 처리를 위한 강화된 추출
        for idx, row in df.iterrows():
            try:
                # 기본 정보 추출 (공급받는자 통합 지침 적용)
                business_number = self.field_extractor.extract_business_number_simple(row, column_names)
                store_name = self.field_extractor.extract_store_name_simple(row, column_names)
                representative = self.field_extractor.extract_representative_simple(row, column_names)
                address = self.field_extractor.extract_address_simple(row, column_names)
                email = self.field_extractor.extract_email_simple(row, column_names)
                
                # 금액 정보 추출
                supply_amount = 0
                vat_amount = 0
                
                if supply_amount_col is not None:
                    supply_amount = self.field_extractor.extract_amount(row.iloc[supply_amount_col])
                if vat_amount_col is not None:
                    vat_amount = self.field_extractor.extract_amount(row.iloc[vat_amount_col])
                
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
                self.logger.error(f"서브지침 추출 오류 (행 {idx+1}): {e}")
                continue
        
        # 🎯 사업자번호 기반 가족 통합 서브지침 적용 (항상 실행)
        if recipients:
            # FileParser의 통합 함수 사용
            from ..file_parser import FileParser
            parser = FileParser()
            merged_recipients = parser._merge_families_by_business_number(recipients)
            
            if len(merged_recipients) < len(recipients):
                self.logger.info(f"🎯 사업자번호 기반 가족 통합 적용: {len(recipients)} → {len(merged_recipients)}건")
                recipients = merged_recipients
            else:
                # 통합은 불필요하지만 보정된 값은 반영해야 함
                recipients = merged_recipients
                self.logger.info(f"🎯 사업자번호 기반 가족 통합 적용: {len(recipients)}건 (통합 불필요, 보정 적용)")
        
        return recipients
    
    def _extract_with_basic_mode(self, df: pd.DataFrame, column_mapping: Dict, column_names: List[str]) -> List[Dict]:
        """기본 모드 추출"""
        return []  # 기본 추출 로직은 하위에서 처리
    
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
            
            # 최대 아빠값을 가진 시트 선택
            best_sheet = max(sheet_candidates, key=lambda x: x['dad_value'])
            
            self.logger.info(f"🎯 최적 시트 선택: '{best_sheet['sheet_name']}' (아빠값: {best_sheet['dad_value']:,.0f}원, 엄마값: {best_sheet['mom_value']:,.0f}원)")
            
            # DataFrame 생성하여 반환
            try:
                # 선택된 시트의 데이터로 DataFrame 생성
                selected_sheet_name = best_sheet['sheet_name']
                sheet_info = all_sheets[selected_sheet_name]
                
                # 헤더와 데이터 추출
                headers = sheet_info.get('headers', [])
                data = sheet_info.get('data', [])
                
                if headers and data:
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
            
            # DataFrame 생성하여 반환
            try:
                # 선택된 시트의 데이터로 DataFrame 생성
                selected_sheet_name = best_sheet['sheet_name']
                sheet_info = all_sheets[selected_sheet_name]
                
                # 헤더와 데이터 추출
                headers = sheet_info.get('headers', [])
                data = sheet_info.get('data', [])
                
                if headers and data:
                    # 첫 번째 행을 헤더로 사용
                    header_row = headers[0] if headers else []
                    # DataFrame 생성
                    df = pd.DataFrame(data, columns=header_row)
                    
                    # 반환 딕셔너리에 dataframe 추가
                    best_sheet['dataframe'] = df
                    self.logger.info(f"🎯 DataFrame 생성 완료: '{selected_sheet_name}' ({len(df)}행, {len(df.columns)}열)")
                else:
                    self.logger.warning(f"시트 '{selected_sheet_name}' 데이터가 없습니다")
                    best_sheet['dataframe'] = pd.DataFrame()
                    
            except Exception as e:
                self.logger.error(f"DataFrame 생성 실패: {str(e)}")
                best_sheet['dataframe'] = pd.DataFrame()
            
            # DataFrame 생성하여 반환
            try:
                # 선택된 시트의 데이터로 DataFrame 생성
                selected_sheet_name = best_sheet['sheet_name']
                sheet_info = all_sheets[selected_sheet_name]
                
                # 헤더와 데이터 추출
                headers = sheet_info.get('headers', [])
                data = sheet_info.get('data', [])
                
                if headers and data:
                    # 첫 번째 행을 헤더로 사용
                    header_row = headers[0] if headers else []
                    # DataFrame 생성
                    df = pd.DataFrame(data, columns=header_row)
                    
                    # 반환 딕셔너리에 dataframe 추가
                    best_sheet['dataframe'] = df
                    self.logger.info(f"🎯 DataFrame 생성 완료: '{selected_sheet_name}' ({len(df)}행, {len(df.columns)}열)")
                else:
                    self.logger.warning(f"⚠️ 시트 '{selected_sheet_name}' 데이터 없음 - 빈 DataFrame 생성")
                    best_sheet['dataframe'] = pd.DataFrame()
                    
            except Exception as e:
                self.logger.error(f"❌ DataFrame 생성 실패: {str(e)}")
                best_sheet['dataframe'] = pd.DataFrame()
            
            # DataFrame 생성하여 반환
            try:
                # 선택된 시트의 데이터로 DataFrame 생성
                selected_sheet_name = best_sheet['sheet_name']
                sheet_info = all_sheets[selected_sheet_name]
                
                # 헤더와 데이터 추출
                headers = sheet_info.get('headers', [])
                data = sheet_info.get('data', [])
                
                if headers and data:
                    # 첫 번째 행을 헤더로 사용
                    header_row = headers[0] if headers else []
                    # DataFrame 생성
                    df = pd.DataFrame(data, columns=header_row)
                    
                    # 반환 딕셔너리에 dataframe 추가
                    best_sheet['dataframe'] = df
                    self.logger.info(f"🎯 DataFrame 생성 완료: '{selected_sheet_name}' ({len(df)}행, {len(df.columns)}열)")
                else:
                    self.logger.warning(f"🎯 DataFrame 생성 실패: '{selected_sheet_name}' - 헤더 또는 데이터 없음")
                    best_sheet['dataframe'] = None
                    
            except Exception as e:
                self.logger.error(f"🎯 DataFrame 생성 오류: {str(e)}")
                best_sheet['dataframe'] = None
            
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
            
            if not headers or not data:
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
