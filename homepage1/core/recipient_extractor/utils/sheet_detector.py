"""
시트 감지 모듈
- 2순위 시트 감지 로직
- 사업자등록번호 컬럼 분석
- 표준 헤더 확인
"""

import logging
from typing import List
import pandas as pd

logger = logging.getLogger(__name__)


def detect_second_priority_sheet(df: pd.DataFrame, column_names: List[str]) -> bool:
    """
    2순위 시트 감지 로직 (5형제 기준)
    
    감지 조건:
    1. 사업자등록번호 빈 비율 50% 이상
    2. 이메일 형식 데이터가 사업자등록번호 컬럼에 있음
    3. 표준 헤더명이 아닌 경우
    4. 5형제 중 누락된 필드가 많은 경우
    """
    try:
        # 조건 1: 사업자등록번호 빈 비율 확인
        business_number_cols = find_business_number_columns(column_names)
        if business_number_cols:
            empty_ratio = calculate_empty_ratio(df, business_number_cols[0])
            if empty_ratio >= 0.5:
                logger.info(f"2순위 시트 감지: 사업자등록번호 빈 비율 {empty_ratio:.1%}")
                return True
        
        # 조건 2: 이메일 형식 데이터가 사업자등록번호 컬럼에 있는지 확인
        if has_email_in_business_number_column(df, column_names):
            logger.info("2순위 시트 감지: 이메일 형식 데이터가 사업자등록번호 컬럼에 존재")
            return True
        
        # 조건 3: 표준 헤더명이 아닌 경우
        if not has_standard_headers(column_names):
            logger.info("2순위 시트 감지: 표준 헤더명이 아님")
            return True
            
        return False
        
    except Exception as e:
        logger.error(f"2순위 시트 감지 중 오류: {e}")
        return False


def find_business_number_columns(column_names: List[str]) -> List[int]:
    """사업자등록번호 관련 컬럼 찾기"""
    business_keywords = ['사업자', '등록번호', '법인등록번호', '사업자번호']
    matches = []
    
    for idx, col_name in enumerate(column_names):
        clean_name = str(col_name).replace('\n', ' ').strip().lower()
        if any(keyword in clean_name for keyword in business_keywords):
            matches.append(idx)
    
    return matches


def calculate_empty_ratio(df: pd.DataFrame, col_idx: int) -> float:
    """컬럼의 빈 값 비율 계산"""
    if col_idx >= len(df.columns):
        return 1.0
    
    col_data = df.iloc[:, col_idx]
    total_rows = len(col_data)
    empty_rows = col_data.isna().sum() + (col_data == '').sum()
    
    return empty_rows / total_rows if total_rows > 0 else 1.0


def has_email_in_business_number_column(df: pd.DataFrame, column_names: List[str]) -> bool:
    """사업자등록번호 컬럼에 이메일 형식 데이터가 있는지 확인"""
    business_cols = find_business_number_columns(column_names)
    
    for col_idx in business_cols:
        if col_idx >= len(df.columns):
            continue
            
        col_data = df.iloc[:, col_idx].dropna()
        email_count = 0
        
        for value in col_data.head(10):  # 상위 10개 행만 확인
            if isinstance(value, str) and '@' in value:
                email_count += 1
        
        if email_count > 0:
            logger.warning(f"컬럼 {col_idx} ({column_names[col_idx]})에 이메일 형식 데이터 {email_count}개 발견")
            return True
    
    return False


def has_standard_headers(column_names: List[str]) -> bool:
    """표준 헤더 존재 여부: 5개 중 최소 3개 이상 존재해야 True"""
    standard_headers = ['가맹점명', '대표자명', '주소', '사업자번호', '이메일']
    found = 0
    for header in standard_headers:
        if any(header in str(col).replace('\n', ' ').strip() for col in column_names):
            found += 1
    return found >= 3

