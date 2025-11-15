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
import re
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

from .utils.data_validator import (
    is_valid_business_number,
    is_valid_store_name,
    is_valid_representative_name,
    is_valid_address,
    is_valid_email,
    is_valid_amount,
)
from .utils.sheet_detector import (
    detect_second_priority_sheet,
    find_business_number_columns,
    calculate_empty_ratio,
    has_email_in_business_number_column,
    has_standard_headers,
)
from .utils.config_loader import load_keywords, load_config
from .utils.column_scorer import (
    remap_headers_for_second_priority as remap_headers_external,
    find_best_column_match,
    calculate_column_score,
    calculate_business_number_score,
    calculate_email_score,
    calculate_general_field_score,
    validate_total_column_before_vat,
    get_synonyms,
)

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
        """
        2순위 시트에서 공급받는자 정보 추출 - 5형제 우선 검열
        
        핵심 개선사항:
        1. 🎯 5형제 우선 검열 (사업자등록번호, 상호, 대표명, 사업장주소, 사업자이메일)
        2. 1순위 검열과 동일한 사업자등록번호 추출 로직 적용
        3. 10자리 숫자 검증 및 개인사업자 1개 보유 규칙 적용
        4. 이메일과 사업자등록번호 명확한 분리
        5. 가족통합 프로세스 마지막에 사업자등록번호 기반 가족 찾기
        """
        self.logger.info("🔄 2순위 시트 공급받는자 정보 추출 시작")
        
        recipients = []
        
        try:
            # FieldExtractors 인스턴스 생성 (1순위와 동일한 추출기 사용)
            from .field_extractors import FieldExtractors
            field_extractors = FieldExtractors()
            
            for row_index, row in df.iterrows():
                try:
                    recipient_info = {
                        '상호': '',
                        '대표명': '',
                        '사업장주소': '',
                        '사업자등록번호': '',
                        '사업자이메일': '',
                        '공급가액': 0.0,
                        '부가세': 0.0,
                        '요금합계': 0.0,
                        'confidence': 0.0,
                        'source_row': row_index
                    }
                    
                    # 🎯 1단계: 사업자등록번호 우선 검열 (가장 먼저 처리)
                    business_number_found = False
                    if '사업자번호' in column_mapping:
                        col_idx = column_mapping['사업자번호']
                        if col_idx < len(row):
                            business_number_raw = str(row.iloc[col_idx]).strip()
                            
                            # 1순위 검열과 동일한 사업자등록번호 추출
                            business_number = field_extractors.extract_business_number(business_number_raw)
                            if business_number:
                                # 배달대행사 공급받는자 절대지침 검증 규칙 적용
                                if is_valid_business_number(business_number):
                                    recipient_info['사업자등록번호'] = business_number
                                    recipient_info['confidence'] += 0.4  # 사업자번호 우선 검열로 높은 점수
                                    business_number_found = True
                                    self.logger.info(f"🎯 2순위 사업자등록번호 우선 추출: '{business_number_raw}' → '{business_number}'")
                                else:
                                    self.logger.warning(f"⚠️ 2순위 사업자등록번호 검증 실패: '{business_number}' (배달대행사 절대지침 위반)")
                            else:
                                self.logger.debug(f"⚠️ 2순위 사업자등록번호 추출 실패: '{business_number_raw}'")
                    
                    # 사업자등록번호가 없으면 다른 필드들도 낮은 신뢰도로 처리
                    if not business_number_found:
                        self.logger.warning(f"⚠️ 행 {row_index}: 사업자등록번호 없음 - 다른 필드들 낮은 신뢰도로 처리")
                        recipient_info['confidence'] = 0.1  # 사업자번호 없으면 낮은 신뢰도
                    
                    # 1순위 검열과 동일한 상호명 추출 로직 적용
                    if '가맹점명' in column_mapping:
                        col_idx = column_mapping['가맹점명']
                        if col_idx < len(row):
                            store_name_raw = str(row.iloc[col_idx]).strip()
                            
                            # 배달대행사 공급받는자 절대지침: 상호명 검증 규칙 적용
                            if is_valid_store_name(store_name_raw):
                                store_name = field_extractors.extract_store_name(store_name_raw, row, [])
                                if store_name:
                                    recipient_info['상호'] = store_name
                                    recipient_info['confidence'] += 0.2
                                    self.logger.debug(f"✅ 2순위 상호명 추출: '{store_name_raw}' → '{store_name}'")
                                else:
                                    self.logger.debug(f"⚠️ 2순위 상호명 추출 실패: '{store_name_raw}'")
                            else:
                                self.logger.debug(f"⚠️ 2순위 상호명 검증 실패: '{store_name_raw}' (배달대행사 절대지침 위반)")
                    
                    # 1순위 검열과 동일한 대표자명 추출 로직 적용
                    if '대표자명' in column_mapping:
                        col_idx = column_mapping['대표자명']
                        if col_idx < len(row):
                            representative_raw = str(row.iloc[col_idx]).strip()
                            
                            # 배달대행사 공급받는자 절대지침: 대표자명 검증 규칙 적용
                            if is_valid_representative_name(representative_raw):
                                representative = field_extractors.extract_representative(representative_raw, row)
                                if representative:
                                    recipient_info['대표명'] = representative
                                    recipient_info['confidence'] += 0.2
                                    self.logger.debug(f"✅ 2순위 대표자명 추출: '{representative_raw}' → '{representative}'")
                                else:
                                    self.logger.debug(f"⚠️ 2순위 대표자명 추출 실패: '{representative_raw}'")
                            else:
                                self.logger.debug(f"⚠️ 2순위 대표자명 검증 실패: '{representative_raw}' (배달대행사 절대지침 위반)")
                    
                    # 1순위 검열과 동일한 주소 추출 로직 적용
                    if '주소' in column_mapping:
                        col_idx = column_mapping['주소']
                        if col_idx < len(row):
                            address_raw = str(row.iloc[col_idx]).strip()
                            
                            # 배달대행사 공급받는자 절대지침: 주소 검증 규칙 적용
                            if is_valid_address(address_raw):
                                address = field_extractors.extract_address(address_raw, row)
                                if address:
                                    recipient_info['사업장주소'] = address
                                    recipient_info['confidence'] += 0.2
                                    self.logger.debug(f"✅ 2순위 주소 추출: '{address_raw}' → '{address}'")
                                else:
                                    self.logger.debug(f"⚠️ 2순위 주소 추출 실패: '{address_raw}'")
                            else:
                                self.logger.debug(f"⚠️ 2순위 주소 검증 실패: '{address_raw}' (배달대행사 절대지침 위반)")
                    
                    # 1순위 검열과 동일한 이메일 추출 로직 적용
                    if '이메일' in column_mapping:
                        col_idx = column_mapping['이메일']
                        if col_idx < len(row):
                            email_raw = str(row.iloc[col_idx]).strip()
                            
                            # 배달대행사 공급받는자 절대지침: 이메일 검증 규칙 적용
                            if is_valid_email(email_raw):
                                email = field_extractors.extract_email(email_raw, row)
                                if email:
                                    recipient_info['사업자이메일'] = email
                                    recipient_info['confidence'] += 0.2
                                    self.logger.debug(f"✅ 2순위 이메일 추출: '{email_raw}' → '{email}'")
                                else:
                                    self.logger.debug(f"⚠️ 2순위 이메일 추출 실패: '{email_raw}'")
                            else:
                                self.logger.debug(f"⚠️ 2순위 이메일 검증 실패: '{email_raw}' (배달대행사 절대지침 위반)")
                    
                    # 배달대행사 공급받는자 절대지침: 금액 정보 검증 규칙 적용
                    if '공급가액' in column_mapping:
                        col_idx = column_mapping['공급가액']
                        if col_idx < len(row):
                            amount_raw = str(row.iloc[col_idx]).strip()
                            if is_valid_amount(amount_raw):
                                try:
                                    amount = float(str(row.iloc[col_idx]).replace(',', '').replace('원', ''))
                                    recipient_info['공급가액'] = amount
                                    recipient_info['confidence'] += 0.1
                                    self.logger.debug(f"✅ 2순위 공급가액 추출: '{amount_raw}' → {amount}")
                                except (ValueError, TypeError):
                                    self.logger.debug(f"⚠️ 2순위 공급가액 변환 실패: '{amount_raw}'")
                            else:
                                self.logger.debug(f"⚠️ 2순위 공급가액 검증 실패: '{amount_raw}' (배달대행사 절대지침 위반)")
                    
                    if '부가세' in column_mapping:
                        col_idx = column_mapping['부가세']
                        if col_idx < len(row):
                            tax_raw = str(row.iloc[col_idx]).strip()
                            if is_valid_amount(tax_raw):
                                try:
                                    tax = float(str(row.iloc[col_idx]).replace(',', '').replace('원', ''))
                                    recipient_info['부가세'] = tax
                                    recipient_info['confidence'] += 0.1
                                    self.logger.debug(f"✅ 2순위 부가세 추출: '{tax_raw}' → {tax}")
                                except (ValueError, TypeError):
                                    self.logger.debug(f"⚠️ 2순위 부가세 변환 실패: '{tax_raw}'")
                            else:
                                self.logger.debug(f"⚠️ 2순위 부가세 검증 실패: '{tax_raw}' (배달대행사 절대지침 위반)")
                    
                    # 요금합계 계산
                    recipient_info['요금합계'] = recipient_info['공급가액'] + recipient_info['부가세']
                    
                    # 최소 필수 정보가 있는 경우만 추가
                    if recipient_info['상호'] or recipient_info['사업자등록번호'] or recipient_info['사업자이메일']:
                        recipients.append(recipient_info)
                        self.logger.debug(f"✅ 2순위 공급받는자 추가: {recipient_info['상호']} (신뢰도: {recipient_info['confidence']:.2f})")
                    
                except Exception as e:
                    self.logger.error(f"2순위 시트 행 {row_index} 처리 중 오류: {e}")
                    continue
            
            self.logger.info(f"✅ 2순위 시트 공급받는자 추출 완료: {len(recipients)}건")
            
            # 🎯 가족통합 프로세스 마지막: 사업자등록번호 기반 가족 찾기 강화
            if recipients:
                self.logger.info("🎯 2순위 가족통합 프로세스 시작: 사업자등록번호 기반 가족 찾기")
                
                # FileParser의 통합 함수 사용 (1순위와 동일한 로직)
                from ..file_parser import FileParser
                parser = FileParser()
                merged_recipients = parser._merge_families_by_business_number(recipients)
                
                if len(merged_recipients) < len(recipients):
                    self.logger.info(f"🎯 2순위 가족통합 성공: {len(recipients)} → {len(merged_recipients)}건")
                    recipients = merged_recipients
                else:
                    self.logger.info(f"🎯 2순위 가족통합 적용: {len(recipients)}건 (통합 불필요, 보정 적용)")
                    recipients = merged_recipients
                
                # 🎯 사업자등록번호가 없는 경우 다른 필드로 대체하는 로직
                recipients_with_business_number = []
                recipients_without_business_number = []
                
                for recipient in recipients:
                    if recipient.get('사업자등록번호') and recipient.get('사업자등록번호').strip():
                        recipients_with_business_number.append(recipient)
                    else:
                        recipients_without_business_number.append(recipient)
                
                self.logger.info(f"🎯 사업자등록번호 보유: {len(recipients_with_business_number)}건, 미보유: {len(recipients_without_business_number)}건")
                
                # 사업자등록번호가 없는 경우 상호명으로 대체 가족 찾기
                if recipients_without_business_number:
                    self.logger.info("🎯 사업자등록번호 없는 경우 상호명 기반 가족 찾기 시도")
                    
                    # 상호명 기반으로 유사한 가족 찾기
                    for recipient in recipients_without_business_number:
                        store_name = recipient.get('상호', '').strip()
                        if store_name:
                            # 기존 사업자등록번호 보유자 중에서 상호명이 유사한 경우 찾기
                            for existing_recipient in recipients_with_business_number:
                                existing_store_name = existing_recipient.get('상호', '').strip()
                                if store_name in existing_store_name or existing_store_name in store_name:
                                    # 상호명이 유사하면 사업자등록번호 공유
                                    recipient['사업자등록번호'] = existing_recipient.get('사업자등록번호')
                                    recipient['confidence'] += 0.2  # 상호명 기반 매칭으로 신뢰도 증가
                                    self.logger.info(f"🎯 상호명 기반 사업자등록번호 매칭: '{store_name}' → '{existing_store_name}'")
                                    break
                
                recipients = recipients_with_business_number + recipients_without_business_number
                self.logger.info(f"🎯 2순위 최종 결과: {len(recipients)}건 (사업자등록번호 우선 검열 완료)")
            
            return recipients
            
        except Exception as e:
            self.logger.error(f"2순위 시트 공급받는자 추출 중 오류: {e}")
            return []
