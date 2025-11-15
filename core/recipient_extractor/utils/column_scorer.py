"""
컬럼 매핑 및 점수 계산 모듈
- 2순위 시트 전용 헤더 재매핑 로직
- 컬럼 매칭 점수 계산 로직
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


def remap_headers_for_second_priority(
    df: pd.DataFrame,
    column_names: List[str],
    required_columns: List[str],
) -> Dict[str, int]:
    """
    2순위 시트 전용 헤더 재매핑 (5형제 우선)
    
    핵심 원칙:
    1. 5형제 우선 인식 (사업자등록번호, 상호, 대표명, 사업장주소, 사업자이메일)
    2. 사업자등록번호 우선 인식 (이메일 형식 제외)
    3. 이메일 엄격 검증 (@ 문자 필수)
    4. 데이터 내용 기반 검증
    """
    logger.info("🔄 2순위 시트 헤더 재매핑 시작")
    
    # 🔍 디버깅: 실제 컬럼명 출력
    logger.info(f"🔍 원본 데이터 컬럼명 목록: {column_names}")
    
    try:
        column_mapping = {}
        found_columns = 0
        
        # 필수 컬럼들을 순차적으로 매핑
        for required in required_columns:
            logger.info(f"🔍 {required} 컬럼 매칭 시도...")
            best_match = find_best_column_match(df, column_names, required)
            if best_match is not None:
                col_idx, col_name = best_match
                column_mapping[required] = col_idx
                found_columns += 1
                logger.info(f"✅ 2순위 매칭: {required} → {col_name} (컬럼 {col_idx})")
            else:
                logger.warning(f"⚠️ 2순위 매칭 실패: {required}")
        
        # 🎯 부가세 앞칸 규칙 우선 적용 (1순위와 동일한 로직)
        vat_col = column_mapping.get('부가세')
        if vat_col is not None:
            logger.info(f"🎯 2순위 부가세 앞칸 규칙 적용: 부가세 컬럼 {vat_col} 앞칸 확인")
            supply_col = validate_total_column_before_vat(df, vat_col)
            if supply_col is not None:
                column_mapping['공급가액'] = supply_col
                logger.info(f"✅ 2순위 부가세 앞칸 규칙으로 공급가액 확정: 컬럼 {supply_col}")
            else:
                logger.info(f"⚠️ 2순위 부가세 앞칸 규칙 적용 실패: 부가세 앞칸이 유효하지 않음")
        
        # 부가세 앞칸 규칙이 실패한 경우에만 일반 매칭 시도
        if '공급가액' not in column_mapping:
            logger.info(f"🔍 2순위 공급가액 컬럼 일반 매칭 시도...")
            best_match = find_best_column_match(df, column_names, '공급가액')
            if best_match is not None:
                col_idx, col_name = best_match
                column_mapping['공급가액'] = col_idx
                logger.info(f"✅ 2순위 공급가액 일반 매칭: 공급가액 → {col_name} (컬럼 {col_idx})")
            else:
                logger.warning(f"⚠️ 2순위 공급가액 매칭 실패")
        
        # 부가세 컬럼 매칭 (공급가액과 별도)
        if '부가세' not in column_mapping:
            logger.info(f"🔍 2순위 부가세 컬럼 매칭 시도...")
            best_match = find_best_column_match(df, column_names, '부가세')
            if best_match is not None:
                col_idx, col_name = best_match
                column_mapping['부가세'] = col_idx
                logger.info(f"✅ 2순위 부가세 매칭: 부가세 → {col_name} (컬럼 {col_idx})")
            else:
                logger.warning(f"⚠️ 2순위 부가세 매칭 실패")
        
        logger.info(f"2순위 시트 헤더 재매핑 완료: {found_columns}/5개 컬럼 매칭")
        
        # 최소 3개 컬럼 이상 매핑된 경우에만 반환
        if found_columns >= 3:
            return column_mapping
        else:
            logger.warning(f"2순위 시트 매핑 실패: {found_columns}/5개 컬럼만 매핑됨")
            return {}
            
    except Exception as e:
        logger.error(f"2순위 시트 헤더 재매핑 중 오류: {e}")
        return {}


def find_best_column_match(
    df: pd.DataFrame,
    column_names: List[str],
    required: str,
) -> Optional[Tuple[int, str]]:
    """필수 컬럼에 대한 최적 매칭 찾기 - 더 관대한 매칭"""
    best_score = -1
    best_match = None
    
    logger.info(f"🔍 {required} 컬럼 매칭 시작 - 전체 컬럼 수: {len(column_names)}")
    
    for col_idx, col_name in enumerate(column_names):
        score = calculate_column_score(df, col_idx, col_name, required)
        logger.debug(f"  컬럼 {col_idx}: '{col_name}' → 점수: {score:.1f}")
        
        if score > best_score:
            best_score = score
            best_match = (col_idx, col_name)
    
    # 점수가 -5보다 크면 매칭 성공 (더 관대한 기준)
    if best_score > -5:
        logger.info(f"✅ 최적 매칭: {required} → {best_match[1]} (점수: {best_score:.1f})")
        return best_match
    else:
        logger.warning(f"❌ 매칭 실패: {required} (최고 점수: {best_score:.1f})")
        return None


def calculate_column_score(
    df: pd.DataFrame,
    col_idx: int,
    col_name: str,
    required: str,
) -> float:
    """컬럼 매칭 점수 계산"""
    score = 0.0
    clean_name = str(col_name).replace('\n', ' ').strip().lower()
    
    # 헤더 키워드 매칭 점수
    if required == '사업자번호':
        score += calculate_business_number_score(df, col_idx, clean_name)
    elif required == '이메일':
        score += calculate_email_score(df, col_idx, clean_name)
    else:
        score += calculate_general_field_score(df, col_idx, clean_name, required)
    
    return score


def calculate_business_number_score(
    df: pd.DataFrame,
    col_idx: int,
    col_name: str,
) -> float:
    """사업자등록번호 컬럼 점수 계산 - 5형제 우선 검열 로직 강화 적용"""
    score = 0.0
    
    logger.debug(f"🔍 사업자번호 점수 계산: '{col_name}' (컬럼 {col_idx})")
    
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
            logger.debug(f"  ✅ 사업자번호 키워드 매칭: '{keyword}' → +15.0점")
            break
    
    # 이메일 관련 키워드가 있으면 강한 패널티
    email_keywords = ['이메일', 'email', '메일', 'mail', '전자우편']
    for keyword in email_keywords:
        if keyword in col_name:
            score -= 20.0  # 더 강한 패널티
            logger.warning(f"  ❌ 사업자등록번호 컬럼에 이메일 키워드 발견: {col_name} → -20.0점")
            break
    
    # 1순위 검열과 동일한 데이터 내용 기반 점수 계산
    if col_idx < len(df.columns):
        col_data = df.iloc[:, col_idx].dropna()
        business_number_count = 0
        email_count = 0
        valid_business_numbers = 0
        
        logger.debug(f"  📊 데이터 분석: {len(col_data)}개 행 확인")
        
        for value in col_data.head(50):  # 더 많은 행 확인 (1순위와 동일)
            if isinstance(value, str):
                value_str = str(value).strip()
                
                # 1순위 검열과 동일한 10자리 숫자 형식 확인
                if re.match(r'^\d{10}$', value_str):
                    business_number_count += 1
                    valid_business_numbers += 1
                    logger.debug(f"    ✅ 10자리 숫자 형식: '{value_str}'")
                # 하이픈 포함 패턴도 확인 (1순위와 동일)
                elif re.match(r'^\d{3}-?\d{2}-?\d{5}$', value_str):
                    # 하이픈 제거 후 10자리 확인
                    digits_only = re.sub(r'[^0-9]', '', value_str)
                    if len(digits_only) == 10:
                        business_number_count += 1
                        valid_business_numbers += 1
                        logger.debug(f"    ✅ 하이픈 포함 형식: '{value_str}' → '{digits_only}'")
                # 이메일 형식 확인
                elif '@' in value_str:
                    email_count += 1
                    logger.debug(f"    ❌ 이메일 형식 발견: '{value_str}'")
        
        # 이메일 형식이 있으면 강한 패널티
        if email_count > 0:
            score -= 25.0  # 더 강한 패널티
            logger.warning(f"  ❌ 사업자등록번호 컬럼에 이메일 형식 데이터 발견: {email_count}건 → -25.0점")
        
        # 사업자등록번호 형식이 있으면 높은 보너스 (1순위와 동일)
        if business_number_count > 0:
            score += 10.0  # 더 높은 보너스
            logger.info(f"  ✅ 사업자등록번호 형식 데이터 발견: {business_number_count}건 → +10.0점")
        
        # 유효한 사업자등록번호 비율에 따른 추가 점수
        if len(col_data) > 0:
            valid_ratio = valid_business_numbers / len(col_data.head(50))
            if valid_ratio > 0.3:  # 30% 이상이 유효한 사업자등록번호
                score += 5.0
                logger.info(f"  ✅ 사업자등록번호 유효 비율: {valid_ratio:.1%} → +5.0점")
    
    logger.debug(f"  📊 최종 점수: {score:.1f}")
    return score


def calculate_email_score(
    df: pd.DataFrame,
    col_idx: int,
    col_name: str,
) -> float:
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
            logger.warning(f"이메일 컬럼에 사업자번호 키워드 발견: {col_name}")
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
            logger.warning(f"이메일 컬럼에 사업자번호 형식 데이터 발견: {col_name}")
    
    return score


def calculate_general_field_score(
    df: pd.DataFrame,
    col_idx: int,
    col_name: str,
    required: str,
) -> float:
    """일반 필드 컬럼 점수 계산 - 더 관대한 매칭"""
    score = 0.0
    clean_name = str(col_name).replace('\n', ' ').strip().lower()
    
    # 헤더 키워드 매칭 (정확한 매칭)
    if required in clean_name:
        score += 10.0
    
    # 동의어 매칭
    synonyms = get_synonyms(required)
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


def validate_total_column_before_vat(
    df: pd.DataFrame,
    vat_col: int,
) -> Optional[int]:
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
        
        logger.debug(f"🔍 부가세 앞칸 검증: '{supply_col_name}' (컬럼 {supply_col}) → '{vat_col_name}' (컬럼 {vat_col})")
        
        # 공급가액 관련 키워드 확인
        supply_keywords = ['공급가액', '공급가', '배달요금', '총배달요금', '배달비', '총배달비', '정산금액']
        has_supply_keyword = any(keyword in supply_col_name for keyword in supply_keywords)
        
        # 부가세 관련 키워드 확인
        vat_keywords = ['부가세', '세액', '부가세액', 'VAT', '세금']
        has_vat_keyword = any(keyword in vat_col_name for keyword in vat_keywords)
        
        if has_supply_keyword and has_vat_keyword:
            logger.info(f"✅ 부가세 앞칸 규칙 검증 성공: '{supply_col_name}' → '{vat_col_name}'")
            return supply_col
        else:
            logger.debug(f"⚠️ 부가세 앞칸 규칙 검증 실패: 공급가 키워드={has_supply_keyword}, 부가세 키워드={has_vat_keyword}")
            return None
            
    except Exception as e:
        logger.error(f"부가세 앞칸 검증 중 오류: {e}")
        return None


def get_synonyms(field: str) -> List[str]:
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

