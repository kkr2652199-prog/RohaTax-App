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

logger = logging.getLogger(__name__)

class SecondPriorityHandler:
    """2순위 시트 전용 처리기"""
    
    def __init__(self):
        self.logger = logger
        # 2순위 검열 전용 필수 컬럼 (배달대행사 공급받는자 절대지침 반영)
        # 5형제: 사업자등록번호, 상호, 대표명, 사업장주소, 사업자이메일
        self.required_columns = ['사업자등록번호', '상호', '대표명', '사업장주소', '사업자이메일']
        self.amount_columns = ['공급가액', '부가세', '요금합계']  # 아빠값(공급가액/요금합계), 엄마값(부가세)
        
        # 배달대행사 공급받는자 절대지침 키워드 세트 (상호명)
        self.store_keywords = [
            '가맹점', '상호', '매장', '점포', '상점', '업체', '사업체', '매장명', '점포명', '상호명', '업소명', 
            '사업장명', '가게', '가게명', '업소', '사업장', '점', '상점명', '가맹점명', '업체명', '사업체명'
        ]
        
        self.korean_cities = [
            '서울특별시', '서울시', '부산광역시', '부산시', '대구광역시', '대구시', '인천광역시', '인천시', 
            '광주광역시', '광주시', '대전광역시', '대전시', '울산광역시', '울산시', '세종특별자치시', '세종시', 
            '경기도', '강원도', '충청북도', '충청남도', '전라북도', '전라남도', '경상북도', '경상남도', 
            '제주특별자치도', '제주도', '서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종'
        ]
        
        self.email_domains = [
            'naver.com', 'daum.net', 'gmail.com', 'nate.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 
            'hanmail.net', 'kakao.com', 'tistory.com', 'live.com', 'msn.com', 'icloud.com', 'me.com', 
            'mac.com', 'aol.com', 'zoho.com', 'protonmail.com'
        ]
        
        self.korean_surnames = [
            '김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', '한', '오', '서', '신', '권', '황', '안', '송', '전', '고', 
            '문', '양', '손', '배', '조', '백', '허', '유', '남', '심', '노', '정', '하', '곽', '성', '차', '주', '우', '구', '신', 
            '원', '태', '나', '전', '민', '유', '진', '지', '엄', '채', '천', '양', '공', '현', '방', '변', '여', '추', '노', '도', '소'
        ]
        
        self.foreign_names = [
            'John', 'David', 'Michael', 'James', 'Robert', 'William', 'Richard', 'Charles', 'Thomas', 'Christopher', 
            'Daniel', 'Matthew', 'Anthony', 'Mark', 'Donald', 'Steven', 'Paul', 'Andrew', 'Joshua', 'Kenneth', 
            'Kevin', 'Brian', 'George', 'Timothy', 'Ronald', 'Jason', 'Edward', 'Jeffrey', 'Ryan', 'Jacob', 'Gary', 'Nicholas'
        ]
        
    def is_second_priority_sheet(self, df: pd.DataFrame, column_names: List[str]) -> bool:
        """2순위 시트 감지 로직 (외부 모듈 호출)"""
        return detect_second_priority_sheet(df, column_names)
    
    def remap_headers_for_second_priority(self, df: pd.DataFrame, column_names: List[str]) -> Dict[str, int]:
        """
        2순위 시트 전용 헤더 재매핑 (5형제 우선)
        
        핵심 원칙:
        1. 5형제 우선 인식 (사업자등록번호, 상호, 대표명, 사업장주소, 사업자이메일)
        2. 사업자등록번호 우선 인식 (이메일 형식 제외)
        3. 이메일 엄격 검증 (@ 문자 필수)
        4. 데이터 내용 기반 검증
        """
        self.logger.info("🔄 2순위 시트 헤더 재매핑 시작")
        
        # 🔍 디버깅: 실제 컬럼명 출력
        self.logger.info(f"🔍 원본 데이터 컬럼명 목록: {column_names}")
        
        try:
            column_mapping = {}
            found_columns = 0
            
            # 필수 컬럼들을 순차적으로 매핑
            for required in self.required_columns:
                self.logger.info(f"🔍 {required} 컬럼 매칭 시도...")
                best_match = self._find_best_column_match(df, column_names, required)
                if best_match is not None:
                    col_idx, col_name = best_match
                    column_mapping[required] = col_idx
                    found_columns += 1
                    self.logger.info(f"✅ 2순위 매칭: {required} → {col_name} (컬럼 {col_idx})")
                else:
                    self.logger.warning(f"⚠️ 2순위 매칭 실패: {required}")
            
            # 🎯 부가세 앞칸 규칙 우선 적용 (1순위와 동일한 로직)
            vat_col = column_mapping.get('부가세')
            if vat_col is not None:
                self.logger.info(f"🎯 2순위 부가세 앞칸 규칙 적용: 부가세 컬럼 {vat_col} 앞칸 확인")
                supply_col = self._validate_total_column_before_vat(df, vat_col)
                if supply_col is not None:
                    column_mapping['공급가액'] = supply_col
                    self.logger.info(f"✅ 2순위 부가세 앞칸 규칙으로 공급가액 확정: 컬럼 {supply_col}")
                else:
                    self.logger.info(f"⚠️ 2순위 부가세 앞칸 규칙 적용 실패: 부가세 앞칸이 유효하지 않음")
            
            # 부가세 앞칸 규칙이 실패한 경우에만 일반 매칭 시도
            if '공급가액' not in column_mapping:
                self.logger.info(f"🔍 2순위 공급가액 컬럼 일반 매칭 시도...")
                best_match = self._find_best_column_match(df, column_names, '공급가액')
                if best_match is not None:
                    col_idx, col_name = best_match
                    column_mapping['공급가액'] = col_idx
                    self.logger.info(f"✅ 2순위 공급가액 일반 매칭: 공급가액 → {col_name} (컬럼 {col_idx})")
                else:
                    self.logger.warning(f"⚠️ 2순위 공급가액 매칭 실패")
            
            # 부가세 컬럼 매칭 (공급가액과 별도)
            if '부가세' not in column_mapping:
                self.logger.info(f"🔍 2순위 부가세 컬럼 매칭 시도...")
                best_match = self._find_best_column_match(df, column_names, '부가세')
                if best_match is not None:
                    col_idx, col_name = best_match
                    column_mapping['부가세'] = col_idx
                    self.logger.info(f"✅ 2순위 부가세 매칭: 부가세 → {col_name} (컬럼 {col_idx})")
                else:
                    self.logger.warning(f"⚠️ 2순위 부가세 매칭 실패")
            
            self.logger.info(f"2순위 시트 헤더 재매핑 완료: {found_columns}/5개 컬럼 매칭")
            
            # 최소 3개 컬럼 이상 매핑된 경우에만 반환
            if found_columns >= 3:
                return column_mapping
            else:
                self.logger.warning(f"2순위 시트 매핑 실패: {found_columns}/5개 컬럼만 매핑됨")
                return {}
                
        except Exception as e:
            self.logger.error(f"2순위 시트 헤더 재매핑 중 오류: {e}")
            return {}
    
    
    def _find_best_column_match(self, df: pd.DataFrame, column_names: List[str], required: str) -> Optional[Tuple[int, str]]:
        """필수 컬럼에 대한 최적 매칭 찾기 - 더 관대한 매칭"""
        best_score = -1
        best_match = None
        
        self.logger.info(f"🔍 {required} 컬럼 매칭 시작 - 전체 컬럼 수: {len(column_names)}")
        
        for col_idx, col_name in enumerate(column_names):
            score = self._calculate_column_score(df, col_idx, col_name, required)
            self.logger.debug(f"  컬럼 {col_idx}: '{col_name}' → 점수: {score:.1f}")
            
            if score > best_score:
                best_score = score
                best_match = (col_idx, col_name)
        
        # 점수가 -5보다 크면 매칭 성공 (더 관대한 기준)
        if best_score > -5:
            self.logger.info(f"✅ 최적 매칭: {required} → {best_match[1]} (점수: {best_score:.1f})")
            return best_match
        else:
            self.logger.warning(f"❌ 매칭 실패: {required} (최고 점수: {best_score:.1f})")
            return None
    
    def _calculate_column_score(self, df: pd.DataFrame, col_idx: int, col_name: str, required: str) -> float:
        """컬럼 매칭 점수 계산"""
        score = 0.0
        clean_name = str(col_name).replace('\n', ' ').strip().lower()
        
        # 헤더 키워드 매칭 점수
        if required == '사업자번호':
            score += self._calculate_business_number_score(df, col_idx, clean_name)
        elif required == '이메일':
            score += self._calculate_email_score(df, col_idx, clean_name)
        else:
            score += self._calculate_general_field_score(df, col_idx, clean_name, required)
        
        return score
    
    def _calculate_business_number_score(self, df: pd.DataFrame, col_idx: int, col_name: str) -> float:
        """사업자등록번호 컬럼 점수 계산 - 5형제 우선 검열 로직 강화 적용"""
        score = 0.0
        
        self.logger.debug(f"🔍 사업자번호 점수 계산: '{col_name}' (컬럼 {col_idx})")
        
        # 1순위 검열과 동일한 헤더 키워드 점수 (확장된 동의어 포함)
        business_keywords = [
            '사업자', '등록번호', '법인등록번호', '사업자번호',
            '사업자등록번호', '공급받는자 등록번호', '업체 사업자등록번호', 
            '가맹점 사업자번호', '고객사업자 번호', '고객 사업자등록번호',
            '거래처 사업자번호', '매장 사업자번호', '점포 사업자번호', '업소 사업자번호'
        ]
        for keyword in business_keywords:
            if keyword in col_name:
                score += 15.0  # 1순위와 동일한 높은 점수
                self.logger.debug(f"  ✅ 사업자번호 키워드 매칭: '{keyword}' → +15.0점")
                break
        
        # 이메일 관련 키워드가 있으면 강한 패널티
        email_keywords = ['이메일', 'email', '메일', 'mail', '전자우편']
        for keyword in email_keywords:
            if keyword in col_name:
                score -= 20.0  # 더 강한 패널티
                self.logger.warning(f"  ❌ 사업자등록번호 컬럼에 이메일 키워드 발견: {col_name} → -20.0점")
                break
        
        # 1순위 검열과 동일한 데이터 내용 기반 점수 계산
        if col_idx < len(df.columns):
            col_data = df.iloc[:, col_idx].dropna()
            business_number_count = 0
            email_count = 0
            valid_business_numbers = 0
            
            self.logger.debug(f"  📊 데이터 분석: {len(col_data)}개 행 확인")
            
            for value in col_data.head(50):  # 더 많은 행 확인 (1순위와 동일)
                if isinstance(value, str):
                    value_str = str(value).strip()
                    
                    # 1순위 검열과 동일한 10자리 숫자 형식 확인
                    if re.match(r'^\d{10}$', value_str):
                        business_number_count += 1
                        valid_business_numbers += 1
                        self.logger.debug(f"    ✅ 10자리 숫자 형식: '{value_str}'")
                    # 하이픈 포함 패턴도 확인 (1순위와 동일)
                    elif re.match(r'^\d{3}-?\d{2}-?\d{5}$', value_str):
                        # 하이픈 제거 후 10자리 확인
                        digits_only = re.sub(r'[^0-9]', '', value_str)
                        if len(digits_only) == 10:
                            business_number_count += 1
                            valid_business_numbers += 1
                            self.logger.debug(f"    ✅ 하이픈 포함 형식: '{value_str}' → '{digits_only}'")
                    # 이메일 형식 확인
                    elif '@' in value_str:
                        email_count += 1
                        self.logger.debug(f"    ❌ 이메일 형식 발견: '{value_str}'")
            
            # 이메일 형식이 있으면 강한 패널티
            if email_count > 0:
                score -= 25.0  # 더 강한 패널티
                self.logger.warning(f"  ❌ 사업자등록번호 컬럼에 이메일 형식 데이터 발견: {email_count}건 → -25.0점")
            
            # 사업자등록번호 형식이 있으면 높은 보너스 (1순위와 동일)
            if business_number_count > 0:
                score += 10.0  # 더 높은 보너스
                self.logger.info(f"  ✅ 사업자등록번호 형식 데이터 발견: {business_number_count}건 → +10.0점")
            
            # 유효한 사업자등록번호 비율에 따른 추가 점수
            if len(col_data) > 0:
                valid_ratio = valid_business_numbers / len(col_data.head(50))
                if valid_ratio > 0.3:  # 30% 이상이 유효한 사업자등록번호
                    score += 5.0
                    self.logger.info(f"  ✅ 사업자등록번호 유효 비율: {valid_ratio:.1%} → +5.0점")
        
        self.logger.debug(f"  📊 최종 점수: {score:.1f}")
        return score
    
    def _calculate_email_score(self, df: pd.DataFrame, col_idx: int, col_name: str) -> float:
        """이메일 컬럼 점수 계산 - 사업자번호 중복 매핑 방지"""
        score = 0.0
        
        # 헤더 키워드 점수 (확장된 동의어 포함)
        email_keywords = [
            '이메일', 'email', '메일', 'mail', '전자우편',
            '사업장 이메일', '고객 이메일', '이메일주소', '공급받는자 이메일',
            '거래처 이메일', '업체 이메일', '매장 이메일', '점포 이메일',
            '메일주소', '연락처 이메일'
        ]
        for keyword in email_keywords:
            if keyword in col_name:
                score += 10.0
                break
        
        # 사업자번호 관련 키워드가 있으면 강한 패널티
        business_keywords = ['사업자', '등록번호', '법인등록번호', '사업자번호']
        for keyword in business_keywords:
            if keyword in col_name:
                score -= 15.0  # 강한 패널티
                self.logger.warning(f"이메일 컬럼에 사업자번호 키워드 발견: {col_name}")
                break
        
        # 데이터 내용 기반 점수
        if col_idx < len(df.columns):
            col_data = df.iloc[:, col_idx].dropna()
            email_count = 0
            business_number_count = 0
            
            for value in col_data.head(20):  # 상위 20개 행 확인
                if isinstance(value, str):
                    # 이메일 형식 확인
                    if '@' in value:
                        email_count += 1
                    # 사업자번호 형식 확인
                    elif re.match(r'^\d{10}$', value.strip()):
                        business_number_count += 1
            
            # 이메일 형식이 있으면 보너스
            if email_count > 0:
                score += 5.0
            
            # 사업자번호 형식이 있으면 강한 패널티
            if business_number_count > 0:
                score -= 20.0  # 더 강한 패널티
                self.logger.warning(f"이메일 컬럼에 사업자번호 형식 데이터 발견: {col_name}")
        
        return score
    
    def _calculate_general_field_score(self, df: pd.DataFrame, col_idx: int, col_name: str, required: str) -> float:
        """일반 필드 컬럼 점수 계산 - 더 관대한 매칭"""
        score = 0.0
        clean_name = str(col_name).replace('\n', ' ').strip().lower()
        
        # 헤더 키워드 매칭 (정확한 매칭)
        if required in clean_name:
            score += 10.0
        
        # 동의어 매칭
        synonyms = self._get_synonyms(required)
        for synonym in synonyms:
            if synonym.lower() in clean_name:
                score += 5.0
                break
        
        # 부분 매칭 (더 관대한 매칭)
        if required == '가맹점명':
            if any(keyword in clean_name for keyword in ['점', '매장', '업체', '상호', '가맹점', '가게', '업장']):
                score += 3.0
        elif required == '대표자명':
            if any(keyword in clean_name for keyword in ['대표', '사장', '원장', '성명', '이름', '담당자']):
                score += 3.0
        elif required == '주소':
            if any(keyword in clean_name for keyword in ['주소', '소재지', '위치', '도로명', '지번']):
                score += 3.0
        
        # 데이터 내용 기반 점수 (빈 값이 적으면 보너스)
        if col_idx < len(df.columns):
            col_data = df.iloc[:, col_idx].dropna()
            if len(col_data) > 0:
                score += 2.0  # 데이터가 있으면 기본 점수 증가
        
        # 기본 점수 (매칭이 전혀 안 되어도 최소 점수)
        score += 1.0
        
        return score
    
    def _validate_total_column_before_vat(self, df: pd.DataFrame, vat_col: int) -> Optional[int]:
        """
        부가세 앞칸이 유효한 공급가액 컬럼인지 검증 (아빠값 규칙 - 1순위와 동일한 로직)
        
        Args:
            df: 데이터프레임
            vat_col: 부가세 컬럼 인덱스
            
        Returns:
            유효한 공급가액 컬럼 인덱스 또는 None
        """
        try:
            if vat_col <= 0:
                return None
                
            supply_col = vat_col - 1
            
            # 컬럼명 확인
            if supply_col >= len(df.columns):
                return None
                
            supply_col_name = str(df.columns[supply_col]).strip()
            vat_col_name = str(df.columns[vat_col]).strip()
            
            self.logger.debug(f"🔍 부가세 앞칸 검증: '{supply_col_name}' (컬럼 {supply_col}) → '{vat_col_name}' (컬럼 {vat_col})")
            
            # 공급가액 관련 키워드 확인
            supply_keywords = ['공급가액', '공급가', '배달요금', '총배달요금', '배달비', '총배달비', '정산금액']
            has_supply_keyword = any(keyword in supply_col_name for keyword in supply_keywords)
            
            # 부가세 관련 키워드 확인
            vat_keywords = ['부가세', '세액', '부가세액', 'VAT', '세금']
            has_vat_keyword = any(keyword in vat_col_name for keyword in vat_keywords)
            
            if has_supply_keyword and has_vat_keyword:
                self.logger.info(f"✅ 부가세 앞칸 규칙 검증 성공: '{supply_col_name}' → '{vat_col_name}'")
                return supply_col
            else:
                self.logger.debug(f"⚠️ 부가세 앞칸 규칙 검증 실패: 공급가 키워드={has_supply_keyword}, 부가세 키워드={has_vat_keyword}")
                return None
                
        except Exception as e:
            self.logger.error(f"부가세 앞칸 검증 중 오류: {e}")
            return None
    
    def _get_synonyms(self, field: str) -> List[str]:
        """필드별 동의어 반환 - 1순위 헤더세트를 2순위에도 그대로 적용"""
        synonym_map = {
            # 1) 가맹점명(상호)
            '가맹점명': [
                '가맹점', '상호', '업체명', '점포명', '매장명', '업소명', '사업장명',
                '거래처명', '고객명', '고객사업장명', '공급받는자 상호', '공급받는자 업체명'
            ],
            # 2) 대표자명
            '대표자명': [
                '대표자명', '대표자', '대표', '사장', '원장', '대표이사', '성명', '이름',
                '사업장 대표명', '공급받는자 대표명', '공급받는자 성명', '점주명', '업주명'
            ],
            # 3) 주소(사업장주소)
            '주소': [
                '주소', '사업장주소', '소재지', '위치', '도로명주소', '지번주소',
                '가맹점 주소', '매장주소', '점포주소', '업소주소', '공급받는자 주소',
                '공급받는자 사업장주소', '출발지주소', 
            
            ],
            # 4) 이메일
            '이메일': [
                '이메일', 'email', '메일', 'mail', '전자우편', '이메일주소', '메일주소',
                '사업자이메일', '사업장 이메일', '고객 이메일', '공급받는자 이메일',
                '거래처 이메일', '업체 이메일', '매장 이메일', '점포 이메일', '연락처 이메일'
            ],
            # 5) 사업자등록번호
            '사업자번호': [
                '사업자번호', '사업자등록번호', '사업자', '등록번호', '법인등록번호',
                '공급받는자 등록번호', '업체 사업자등록번호', '가맹점 사업자번호',
                '고객사업자 번호', '고객 사업자등록번호', '거래처 사업자번호',
                '매장 사업자번호', '점포 사업자번호', '업소 사업자번호'
            ],
            # 금액 계열 (1순위 금액 규칙 동일 적용)
            '공급가액': [
                # 총액성 키워드는 제거하여 충돌 완화
                # 우선 대상은 실제 공급가 관련 키워드만 유지
                '공급가액', '공급가', '배달요금'
            ],
            '부가세': [
                '부가세', '세액', '부가세액', 'VAT', '세금', 
            ],
            '요금합계': [
                '요금합계', '합계', '총합계', '총금액', '합계금액'
            ],
        }
        return synonym_map.get(field, [])
    
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
